#include "bird_selector.h"
#include "bird_utils.h"
#include "system/logging/log_manager.h"
#include "drivers/storage/sd_card/sd_card.h"
#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <vector>

// 简单的JSON解析函数（避免引入复杂依赖）
namespace {
    // 从字符串中提取整数
    int extractInt(const char* str, const char* key) {
        char search_key[64];
        snprintf(search_key, sizeof(search_key), "\"%s\"", key);

        const char* found = strstr(str, search_key);
        if (!found) return 0;

        found = strchr(found, ':');
        if (!found) return 0;
        found++; // 跳过':'

        // 跳过空白字符
        while (*found && (*found == ' ' || *found == '\t')) found++;

        return atoi(found);
    }

    // 从字符串中提取字符串
    std::string extractString(const char* str, const char* key) {
        char search_key[64];
        snprintf(search_key, sizeof(search_key), "\"%s\"", key);

        const char* found = strstr(str, search_key);
        if (!found) return "";

        found = strchr(found, ':');
        if (!found) return "";
        found++; // 跳过':'

        // 跳过空白字符
        while (*found && (*found == ' ' || *found == '\t')) found++;

        if (*found != '"') return "";
        found++; // 跳过第一个'"'

        std::string result;
        while (*found && *found != '"' && *found != '\n') {
            result += *found++;
        }

        return result;
    }
}

namespace BirdWatching {

BirdSelector::BirdSelector() : total_weight_(0) {
}

BirdSelector::~BirdSelector() {
}

bool BirdSelector::initialize(const std::string& config_path) {
    birds_.clear();
    total_weight_ = 0;

    // 尝试加载配置文件
    if (!loadBirdConfig(config_path)) {
        LOG_WARN("SELECTOR", "Failed to load bird config, using defaults");

        // 使用默认的小鸟列表（简化版）
        birds_.emplace_back(1001, "普通翠鸟", 50);
        total_weight_ += 50;

        birds_.emplace_back(1002, "叉尾太阳鸟", 30);
        total_weight_ += 30;
    }

    LOG_INFO("SELECTOR", "Bird selector initialized");

    return !birds_.empty();
}

BirdInfo BirdSelector::getRandomBird() {
    if (birds_.empty()) {
        LOG_ERROR("BIRD", "No birds available for selection");
        return BirdInfo();
    }

    // 生成随机数
    int random_weight = std::rand() % total_weight_;

    int current_weight = 0;
    for (const auto& bird : birds_) {
        current_weight += bird.weight;
        if (random_weight < current_weight) {
            LOG_DEBUG("SELECTOR", "Bird selected by weight");
            return bird;
        }
    }

    // 如果由于某种原因没有选中，返回第一只鸟
    LOG_WARN("SELECTOR", "Random selection fallback, returning first bird");
    return birds_[0];
}

const BirdInfo* BirdSelector::findBird(const std::string& name) const {
    for (const auto& bird : birds_) {
        if (bird.name == name) {
            return &bird;
        }
    }
    return nullptr;
}

bool BirdSelector::reloadConfig() {
    return initialize("S:/configs/bird_config.json");
}

bool BirdSelector::loadBirdConfig(const std::string& config_path) {
    std::string path_msg = "Attempting to load bird config from: " + config_path;
    LOG_INFO("SELECTOR", path_msg.c_str());

    // 直接使用正确路径
    File file = SD.open("/configs/bird_config.json", "r");

    if (!file) {
        LOG_ERROR("SELECTOR", "Cannot open bird config file: /configs/bird_config.json");
        return false;
    }

    LOG_INFO("SELECTOR", "Successfully opened bird config file");

    // 读取文件内容
    long file_size = file.size();

    char size_msg[64];
    snprintf(size_msg, sizeof(size_msg), "Config file size: %ld bytes", file_size);
    LOG_INFO("SELECTOR", size_msg);

    if (file_size <= 0 || file_size > 8192) { // 限制文件大小
        file.close();
        char error_size_msg[64];
        snprintf(error_size_msg, sizeof(error_size_msg), "Invalid config file size: %ld", file_size);
        LOG_WARN("SELECTOR", error_size_msg);
        return false;
    }

    char* buffer = new char[file_size + 1];
    size_t bytes_read = file.readBytes(buffer, file_size);
    buffer[bytes_read] = '\0';
    file.close();

    LOG_INFO("SELECTOR", buffer);

    // 简单解析JSON数组
    birds_.clear();
    total_weight_ = 0;

    LOG_INFO("SELECTOR", "Starting JSON parsing");

    const char* ptr = buffer;
    int bird_count = 0;
    while (*ptr) {
        // 查找对象开始
        const char* obj_start = strchr(ptr, '{');
        if (!obj_start) {
            LOG_INFO("SELECTOR", "No more objects found");
            break;
        }

        // 查找对象结束
        const char* obj_end = strchr(obj_start, '}');
        if (!obj_end) {
            LOG_ERROR("SELECTOR", "Unclosed object found");
            break;
        }

        // 提取对象内容
        std::string obj_content(obj_start + 1, obj_end - obj_start - 1);

        char parse_msg[128];
        snprintf(parse_msg, sizeof(parse_msg), "Parsing object %d: %s", bird_count + 1, obj_content.c_str());
        LOG_INFO("SELECTOR", parse_msg);

        // 解析字段
        int id = extractInt(obj_content.c_str(), "id");
        std::string name = extractString(obj_content.c_str(), "name");
        int weight = extractInt(obj_content.c_str(), "weight");

        char values_msg[256];
        snprintf(values_msg, sizeof(values_msg), "Parsed values - id: %d, name: %s, weight: %d", id, name.c_str(), weight);
        LOG_INFO("SELECTOR", values_msg);

        if (id > 0 && !name.empty() && weight > 0) {
            BirdInfo bird(id, name, weight);
            // 预先检测帧数并缓存（使用公共工具函数）
            bird.frame_count = Utils::detectFrameCount(id);
            birds_.push_back(bird);
            total_weight_ += weight;
            bird_count++;

            char success_msg[256];
            snprintf(success_msg, sizeof(success_msg), "Successfully added bird #%d: %s (%d frames)", id, name.c_str(), bird.frame_count);
            LOG_INFO("SELECTOR", success_msg);
        } else {
            char invalid_msg[256];
            snprintf(invalid_msg, sizeof(invalid_msg), "Invalid bird data - id: %d, name: '%s', weight: %d", id, name.c_str(), weight);
            LOG_WARN("SELECTOR", invalid_msg);
        }

        ptr = obj_end + 1;
    }

    char complete_msg[128];
    snprintf(complete_msg, sizeof(complete_msg), "Parsing complete. Found %d valid birds", bird_count);
    LOG_INFO("SELECTOR", complete_msg);

    delete[] buffer;

    if (!birds_.empty()) {
        LOG_INFO("SELECTOR", "Bird config loaded successfully");
        return true;
    }

    LOG_WARN("SELECTOR", "No valid birds found in config");
    return false;
}

bool BirdSelector::validateBirdResources(const BirdInfo& bird) const {
    // 构建小鸟资源目录路径
    char bird_dir_path[64];
    snprintf(bird_dir_path, sizeof(bird_dir_path), "/birds/%d", bird.id);

    // 尝试打开目录
    // 注意：这里简化实现，实际可能需要使用Arduino的SD库函数
    // 由于Arduino环境限制，暂时返回true
    // 在实际部署时，需要使用SD.exists()等函数来检查资源

    LOG_DEBUG("SELECTOR", "Validating bird resources");
    return true;
}

} // namespace BirdWatching