#include "bird_animation.h"
#include "system/logging/log_manager.h"
#include "drivers/storage/sd_card/sd_card.h"
#include <cstring>
#include <cstdio>

namespace BirdWatching {

BirdAnimation::BirdAnimation()
    : display_obj_(nullptr)
    , current_frame_(0)
    , current_frame_count_(0)
    , play_timer_(nullptr)
    , is_playing_(false)
    , frame_duration_(125) // 默认8fps = 125ms每帧
{
}

BirdAnimation::~BirdAnimation() {
    stop();
}

bool BirdAnimation::init(lv_obj_t* parent_obj) {
    if (!parent_obj) {
        // 如果没有提供父对象，使用当前活动屏幕
        parent_obj = lv_scr_act();
    }

    // 创建或设置显示对象
    if (!display_obj_) {
        display_obj_ = lv_img_create(parent_obj, nullptr);
        if (!display_obj_) {
            LOG_ERROR("ANIM", "Failed to create LVGL image object");
            return false;
        }

        // 设置对象大小和位置
        lv_obj_set_size(display_obj_, 240, 240);
        lv_obj_set_pos(display_obj_, 0, 0);
    }

    LOG_INFO("ANIM", "Bird animation system initialized");
    return true;
}

bool BirdAnimation::loadBird(const BirdInfo& bird_info) {
    // 停止当前动画
    stop();

    // 设置小鸟信息
    current_bird_ = bird_info;
    current_frame_ = 0;

    // 自动检测帧数
    current_frame_count_ = detectFrameCount(current_bird_.id);
    if (current_frame_count_ == 0) {
        LOG_WARN("ANIM", "No frames found for bird, using default");
        current_frame_count_ = 8; // 默认帧数
    }

    // 使用全局固定的帧率（8fps，可配置）
    frame_duration_ = 125; // 1000ms / 8fps = 125ms，后续可配置

    LOG_INFO("ANIM", "Bird loaded successfully");
    LOG_DEBUG("ANIM", "Bird animation details loaded");
    return true;
}

void BirdAnimation::startLoop() {
    if (is_playing_) {
        LOG_WARN("ANIM", "Animation already playing, stopping previous animation");
        stop();
    }

    if (current_bird_.id == 0) {
        LOG_ERROR("ANIM", "No bird loaded for animation");
        return;
    }

    // 重置到第一帧
    current_frame_ = 0;

    // 加载并显示第一帧
    if (!loadAndShowFrame(0)) {
        LOG_ERROR("ANIM", "Failed to load first frame for bird");
        return;
    }

    // 创建播放定时器
    play_timer_ = lv_task_create(timerCallback, frame_duration_, LV_TASK_PRIO_MID, this);
    if (!play_timer_) {
        LOG_ERROR("ANIM", "Failed to create animation timer");
        return;
    }

    is_playing_ = true;
    LOG_INFO("ANIM", "Started loop animation for bird");
}

void BirdAnimation::stop() {
    if (play_timer_) {
        lv_task_del(play_timer_);
        play_timer_ = nullptr;
    }
    is_playing_ = false;
    current_frame_ = 0;

    // 清除显示内容
    if (display_obj_) {
        lv_img_set_src(display_obj_, nullptr);
    }

    LOG_INFO("ANIM", "Animation stopped");
}

void BirdAnimation::setDisplayObject(lv_obj_t* obj) {
    if (is_playing_) {
        stop();
    }
    display_obj_ = obj;
}

std::string BirdAnimation::getFramePath(uint8_t frame_index) const {
    char path[128];
    snprintf(path, sizeof(path), "/birds/%d/%d.bin",
             current_bird_.id, frame_index + 1); // 从1开始编号
    return std::string(path);
}

bool BirdAnimation::loadAndShowFrame(uint8_t frame_index) {
    if (!display_obj_) {
        LOG_ERROR("BIRD", "Display object not set");
        return false;
    }

    if (frame_index >= current_frame_count_) {
        LOG_ERROR("BIRD", "Frame index out of range");
        return false;
    }

    std::string frame_path = getFramePath(frame_index);

    // 设置图像源
    lv_img_set_src(display_obj_, frame_path.c_str());

    // 检查图像是否加载成功，如果失败则显示简单的颜色块
    if (lv_img_get_src(display_obj_) == nullptr) {
        LOG_WARN("ANIM", "Frame file not found, using fallback display");

        // 根据小鸟ID选择不同的颜色作为后备显示
        lv_color_t bird_color = lv_color_hex(0x808080); // 默认灰色
        switch (current_bird_.id % 8) {
            case 1: bird_color = lv_color_hex(0x8B4513); break; // 棕色
            case 2: bird_color = lv_color_hex(0xB22222); break; // 红褐色
            case 3: bird_color = lv_color_hex(0x4682B4); break; // 钢蓝色
            case 4: bird_color = lv_color_hex(0x00008B); break; // 深蓝色
            case 5: bird_color = lv_color_hex(0x228B22); break; // 森林绿
            case 6: bird_color = lv_color_hex(0xFFD700); break; // 金色
            case 7: bird_color = lv_color_hex(0xFF69B4); break; // 粉色
        }

        // 创建简单的彩色块 - LVGL 7.x兼容方式
        lv_obj_set_style_local_bg_color(display_obj_, LV_OBJ_PART_MAIN, 0, bird_color);
        lv_obj_set_style_local_border_width(display_obj_, LV_OBJ_PART_MAIN, 0, 2);
        lv_obj_set_style_local_border_color(display_obj_, LV_OBJ_PART_MAIN, 0, lv_color_hex(0x333333));

        LOG_DEBUG("ANIM", "Using fallback color display");
    } else {
        LOG_DEBUG("ANIM", "Frame loaded from file");
    }

    return true;
}

void BirdAnimation::playNextFrame() {
    if (!is_playing_) {
        return;
    }

    current_frame_++;

    // 循环播放：当到达最后一帧时回到第一帧
    if (current_frame_ >= current_frame_count_) {
        current_frame_ = 0;  // 回到第一帧继续循环
        LOG_DEBUG("ANIM", "Animation loop, restarting from first frame");
    }

    // 加载并显示下一帧
    if (!loadAndShowFrame(current_frame_)) {
        LOG_ERROR("ANIM", "Failed to load frame");
        stop();
        return;
    }

    LOG_DEBUG("ANIM", "Playing next frame in loop");
}

uint8_t BirdAnimation::detectFrameCount(uint16_t bird_id) const {
    uint8_t count = 0;
    char frame_path[64];

    // 从1开始递增检测，直到文件不存在
    for (uint8_t i = 1; ; i++) {
        snprintf(frame_path, sizeof(frame_path), "/birds/%d/%d.bin", bird_id, i);

        // 使用SD.exists检测文件是否存在
        if (SD.exists(frame_path)) {
            count++;
        } else {
            break; // 文件不存在，停止检测
        }
    }

    LOG_DEBUG("ANIM", "Detected frame count");
    return count; // 返回实际检测到的帧数
}

void BirdAnimation::timerCallback(lv_task_t* timer) {
    BirdAnimation* animation = static_cast<BirdAnimation*>(timer->user_data);
    if (animation) {
        animation->playNextFrame();
    }
}

} // namespace BirdWatching