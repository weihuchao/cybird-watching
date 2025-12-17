#include "bird_manager.h"
#include "bird_utils.h"
#include "system/logging/log_manager.h"
#include "drivers/sensors/imu/imu.h"
#include "drivers/io/rgb_led/rgb_led.h"
#include "config/ui_texts.h"
#include <cstdlib>
#include "esp_system.h"

// 声明外部全局对象
extern Pixel rgb;

// 声明外部C接口，用于访问GUI对象
extern "C" {
    #include "applications/gui/core/gui_guider.h"
    extern lv_ui guider_ui;
}

namespace BirdWatching {

BirdManager::BirdManager()
    : initialized_(false)
    , first_bird_loaded_(false)
    , animation_(nullptr)
    , selector_(nullptr)
    , display_obj_(nullptr)
    , last_auto_trigger_time_(0)
    , last_stats_save_time_(0)
    , system_start_time_(0)
    , bird_info_show_time_(0)
    , bird_info_visible_(false)
{
    trigger_request_.pending = false;
    trigger_request_.type = TRIGGER_AUTO;
    trigger_request_.bird_id = 0;
    trigger_request_.record_stats = true;
}

BirdManager::~BirdManager() {
    if (animation_) {
        delete animation_;
    }
    if (selector_) {
        delete selector_;
    }
}

bool BirdManager::initialize(lv_obj_t* display_obj) {
    LOG_INFO("BIRD", "Initializing Bird Watching Manager...");

    // 保存显示对象引用
    display_obj_ = display_obj;

    // 记录系统启动时间
    system_start_time_ = getCurrentTime();
    last_auto_trigger_time_ = system_start_time_;
    last_stats_save_time_ = system_start_time_;

    // 初始化各个子系统
    if (!initializeSubsystems(display_obj)) {
        LOG_ERROR("BIRD", "Failed to initialize bird watching subsystems");
        return false;
    }

    // 初始化随机数生成器
    // ESP32的std::rand()质量较差，这里仅用于记录种子信息
    uint32_t raw_seed = system_start_time_;

    // 使用ESP32硬件真随机数生成器(TRNG)作为种子
    // 基于射频噪声，质量远超软件LCG
    uint32_t hw_random = esp_random();
    
    // 日志输出
    char seed_msg[256];
    snprintf(seed_msg, sizeof(seed_msg), 
             "Random seed: context=0x%08X (millis only), HW_RNG=0x%08X", 
             raw_seed, hw_random);
    LOG_INFO("BIRD", seed_msg);
    
    // 虽然我们主要使用esp_random()，但仍初始化rand()以备用
    std::srand(hw_random);

    initialized_ = true;
    LOG_INFO("BIRD", "Bird Watching Manager initialized successfully");
    LOG_INFO("BIRD", "Gesture trigger enabled - shake to summon birds");

    // 加载首次启动的小鸟
    loadInitialBird();

    return true;
}

void BirdManager::update() {
    if (!initialized_) {
        return;
    }
}

void BirdManager::processTriggerRequest() {
    if (!initialized_) {
        return;
    }

    // 注意: 此函数在UI任务中调用,已持有LVGL锁

    // 安全地处理动画播放
    if (trigger_request_.pending) {
        bool record_stats = trigger_request_.record_stats;
        trigger_request_.pending = false;

        if (isPlaying()) {
            animation_->stop();
        }

        if (trigger_request_.bird_id > 0) {
            // 播放指定的小鸟
            playBird(trigger_request_.bird_id, record_stats);
        } else {
            // 播放随机小鸟（总是记录统计）
            playRandomBird();
        }
    }
}

bool BirdManager::triggerBird(TriggerType trigger_type) {
    if (!initialized_) {
        LOG_ERROR("BIRD_MGR", "Bird manager not initialized");
        return false;
    }

    // 设置触发请求,由UI任务处理
    trigger_request_.pending = true;
    trigger_request_.type = trigger_type;
    trigger_request_.bird_id = 0; // 随机小鸟
    trigger_request_.record_stats = true;

    return true;
}

bool BirdManager::triggerBirdById(uint16_t bird_id, TriggerType trigger_type) {
    if (!initialized_) {
        LOG_ERROR("BIRD_MGR", "Bird manager not initialized");
        return false;
    }

    if (bird_id == 0) {
        LOG_ERROR("BIRD_MGR", "Invalid bird_id: 0");
        return false;
    }

    // 验证小鸟ID是否存在
    const auto& birds = getAllBirds();
    bool bird_exists = false;
    for (const auto& bird : birds) {
        if (bird.id == bird_id) {
            bird_exists = true;
            break;
        }
    }

    if (!bird_exists) {
        LOG_ERROR("BIRD_MGR", String("Bird ID not found: ") + String(bird_id));
        return false;
    }

    // 设置触发请求,由UI任务处理
    trigger_request_.pending = true;
    trigger_request_.type = trigger_type;
    trigger_request_.bird_id = bird_id; // 指定小鸟
    trigger_request_.record_stats = true;

    LOG_INFO("BIRD_MGR", String("Trigger request set for bird ID: ") + String(bird_id));
    return true;
}

bool BirdManager::playBirdWithoutRecording(uint16_t bird_id) {
    if (!initialized_) {
        LOG_ERROR("BIRD_MGR", "Bird manager not initialized");
        return false;
    }

    if (bird_id == 0) {
        LOG_ERROR("BIRD_MGR", "Invalid bird_id");
        return false;
    }

    // 设置触发请求,由UI任务处理（不记录统计）
    trigger_request_.pending = true;
    trigger_request_.type = TRIGGER_AUTO;
    trigger_request_.bird_id = bird_id;
    trigger_request_.record_stats = false;

    return true;
}

void BirdManager::onGestureEvent(int gesture_type) {
    if (!config_.enable_gesture_trigger) {
        return;
    }
    triggerBird(TRIGGER_GESTURE);
    rgb.flashBlue(100); // 蓝光闪一下
}

void BirdManager::setConfig(const BirdConfig& config) {
    config_ = config;
    LOG_INFO("BIRD", "Bird manager configuration updated");
}

void BirdManager::saveConfig() {
    // TODO: 实现配置保存
    LOG_INFO("BIRD", "Configuration saving not yet implemented");
}

bool BirdManager::initializeSubsystems(lv_obj_t* display_obj) {
    // display_obj现在是scenes对象
    // 需要从scenes中获取scenes_canvas作为动画显示对象
    // guider_ui已在文件顶部通过extern "C"声明
    lv_obj_t* canvas_obj = guider_ui.scenes_canvas;
    
    // 初始化动画播放器（使用scenes_canvas）
    animation_ = new BirdAnimation();
    if (!animation_ || !animation_->init(canvas_obj)) {
        LOG_ERROR("BIRD", "Failed to initialize bird animation system");
        return false;
    }

    // 初始化小鸟选择器
    selector_ = new BirdSelector();
    if (!selector_ || !selector_->initialize("/configs/bird_config.csv")) {
        LOG_ERROR("BIRD", "Failed to initialize bird selector");
        return false;
    }

    LOG_INFO("BIRD", "All subsystems initialized successfully");
    return true;
}

void BirdManager::handleAutoTrigger() {
    // 已移除自动定时触发逻辑，改为仅通过IMU摇晃手势触发
    // 此函数保留以便将来可能需要的功能扩展
}

bool BirdManager::playRandomBird() {
    if (!selector_ || !animation_) {
        LOG_ERROR("BIRD", "Bird selector or animation not available");
        return false;
    }

    // 随机选择一只小鸟
    BirdInfo bird = selector_->getRandomBird();
    if (bird.id == 0) {
        LOG_ERROR("BIRD", "Failed to select random bird");
        return false;
    }

    return playBird(bird.id, true);
}

bool BirdManager::playBird(uint16_t bird_id, bool record_stats) {
    if (!selector_ || !animation_) {
        LOG_ERROR("BIRD", "Bird selector or animation not available");
        return false;
    }

    // 从选择器获取小鸟信息
    const std::vector<BirdInfo>& all_birds = selector_->getAllBirds();
    const BirdInfo* bird_info = nullptr;
    
    for (const auto& bird : all_birds) {
        if (bird.id == bird_id) {
            bird_info = &bird;
            break;
        }
    }

    if (!bird_info) {
        LOG_ERROR("BIRD", (String("Bird not found with ID: ") + String(bird_id)).c_str());
        return false;
    }

    // 加载小鸟动画
    if (!animation_->loadBird(*bird_info)) {
        LOG_ERROR("BIRD", "Failed to load bird");
        return false;
    }

    // 播放动画（循环播放）
    animation_->startLoop();

    LOG_INFO("BIRD", (String("Playing bird animation (ID: ") + String(bird_id) + 
             ", record: " + String(record_stats ? "yes" : "no") + ")").c_str());
    return true;
}

void BirdManager::loadInitialBird() {
    if (first_bird_loaded_) {
        return;
    }

    if (!selector_) {
        LOG_ERROR("BIRD", "Selector not available");
        return;
    }

    // 没有历史数据：正常触发一次，计数
    LOG_INFO("BIRD", "No historical data, triggering first bird with counting");
    triggerBird(TRIGGER_AUTO);
    
    first_bird_loaded_ = true;
}

void BirdManager::updateGestureDetection() {
    // 手势检测已集成到TaskManager的系统任务中
    // 通过IMU.detectGesture()实时检测并触发相应事件
}

void BirdManager::handleGesture(GestureType gesture) {
    switch (gesture) {
        case GESTURE_FORWARD_TILT:
            LOG_INFO("BIRD", "Forward tilt detected, triggering bird");
            triggerBird(TRIGGER_GESTURE);
            break;

        default:
            break;
    }
}

uint32_t BirdManager::getCurrentTime() const {
    // 使用Arduino的millis()函数
    return millis();
}

uint32_t BirdManager::getNextAutoTriggerTime() const {
    return last_auto_trigger_time_ + (config_.auto_trigger_interval * 1000);
}

const std::vector<BirdInfo>& BirdManager::getAllBirds() const {
    if (!selector_) {
        static std::vector<BirdInfo> empty;
        return empty;
    }
    return selector_->getAllBirds();
}

} // namespace BirdWatching