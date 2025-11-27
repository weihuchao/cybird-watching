#include "bird_stats.h"
#include "system/logging/log_manager.h"
#include <ctime>
#include <cstring>
#include <cstdio>

// 简单的文件操作（避免复杂的文件系统依赖）
extern "C" {
    // 声明SD卡文件操作函数（需要在别处实现）
    int sd_card_read_file(const char* path, char* buffer, int max_size);
    int sd_card_write_file(const char* path, const char* data);
}

namespace BirdWatching {

BirdStatistics::BirdStatistics() : total_encounters_(0) {
}

BirdStatistics::~BirdStatistics() {
    saveToFile();
}

bool BirdStatistics::initialize(const std::string& data_file) {
    data_file_ = data_file;

    // 尝试加载现有统计数据
    bool loaded = loadFromFile();
    if (!loaded) {
        LOG_INFO("BIRD", "No existing bird stats found, starting with empty statistics");
        resetStats();
    }

    LOG_INFO("BIRD", "Bird statistics initialized");
    return true;
}

void BirdStatistics::recordEncounter(const std::string& bird_name) {
    if (bird_name.empty()) {
        LOG_ERROR("BIRD", "Cannot record encounter with empty bird name");
        return;
    }

    time_t current_time = time(nullptr);
    BirdStats& bird_stats = updateOrCreateBirdStats(bird_name);

    // 更新统计信息
    bird_stats.encounter_count++;
    bird_stats.last_seen = current_time;

    // 如果是第一次遇见，记录首次时间
    if (bird_stats.first_seen == 0) {
        bird_stats.first_seen = current_time;
    }

    total_encounters_++;

    LOG_INFO("BIRD", "Recorded bird encounter");

    // 定期保存统计数据
    if (total_encounters_ % 10 == 0) {
        saveToFile();
    }
}

const BirdStats* BirdStatistics::getBirdStats(const std::string& bird_name) const {
    auto it = stats_.find(bird_name);
    if (it != stats_.end()) {
        return &(it->second);
    }
    return nullptr;
}

std::vector<BirdStats> BirdStatistics::getAllStats() const {
    std::vector<BirdStats> result;
    result.reserve(stats_.size());

    for (const auto& pair : stats_) {
        result.push_back(pair.second);
    }

    return result;
}

float BirdStatistics::getProgressPercentage(int total_bird_species) const {
    if (total_bird_species <= 0) {
        return 0.0f;
    }

    int seen_species = stats_.size();
    return (static_cast<float>(seen_species) / total_bird_species) * 100.0f;
}

std::string BirdStatistics::getMostSeenBird() const {
    if (stats_.empty()) {
        return "";
    }

    const BirdStats* most_seen = nullptr;
    int max_count = 0;

    for (const auto& pair : stats_) {
        if (pair.second.encounter_count > max_count) {
            max_count = pair.second.encounter_count;
            most_seen = &(pair.second);
        }
    }

    return most_seen ? most_seen->bird_name : "";
}

std::string BirdStatistics::getRarestBird() const {
    if (stats_.empty()) {
        return "";
    }

    const BirdStats* rarest = nullptr;
    int min_count = INT_MAX;

    for (const auto& pair : stats_) {
        if (pair.second.encounter_count > 0 && pair.second.encounter_count < min_count) {
            min_count = pair.second.encounter_count;
            rarest = &(pair.second);
        }
    }

    return rarest ? rarest->bird_name : "";
}

bool BirdStatistics::saveToFile() {
    if (data_file_.empty()) {
        LOG_ERROR("BIRD", "No data file specified for saving statistics");
        return false;
    }

    std::string json_data = formatStatsAsJson();
    if (json_data.empty()) {
        LOG_ERROR("BIRD", "Failed to format statistics as JSON");
        return false;
    }

    // TODO: 实现实际的文件写入
    // int result = sd_card_write_file(data_file_.c_str(), json_data.c_str());
    // return result == 0;

    LOG_INFO("BIRD", "Statistics saved");
    return true;
}

bool BirdStatistics::loadFromFile() {
    if (data_file_.empty()) {
        LOG_ERROR("BIRD", "No data file specified for loading statistics");
        return false;
    }

    // TODO: 实现实际的文件读取
    /*
    char buffer[4096];
    int result = sd_card_read_file(data_file_.c_str(), buffer, sizeof(buffer) - 1);
    if (result <= 0) {
        return false;
    }
    buffer[result] = '\0';

    return parseStatsFromFile(buffer);
    */

    LOG_INFO("BIRD", "Statistics loading not yet implemented");
    return false;
}

void BirdStatistics::resetStats() {
    stats_.clear();
    total_encounters_ = 0;
    LOG_INFO("BIRD", "Bird statistics reset");
}

void BirdStatistics::printStats() const {
    Serial.println("Total bird encounters: " + String(total_encounters_));

    if (stats_.empty()) {
        Serial.println("No birds encountered yet");
        return;
    }

    Serial.println("Birds encountered:");
    for (const auto& pair : stats_) {
        const BirdStats& stat = pair.second;
        Serial.println("  - " + String(stat.bird_name.c_str()) + ": " + String(stat.encounter_count) + " times");
    }

    if (!stats_.empty()) {
        Serial.println("Most seen bird: " + String(getMostSeenBird().c_str()));
        Serial.println("Rarest bird: " + String(getRarestBird().c_str()));
    }

    LOG_DEBUG("BIRD", "Statistics printed to serial");
}

bool BirdStatistics::parseStatsFromFile(const char* content) {
    // TODO: 实现简单的JSON解析
    // 由于复杂度考虑，暂时跳过文件加载实现
    LOG_DEBUG("BIRD", "Stats file parsing not yet implemented");
    return false;
}

std::string BirdStatistics::formatStatsAsJson() const {
    // 简单的JSON格式化
    std::string json = "{\n";
    json += "  \"total_encounters\": " + std::to_string(total_encounters_) + ",\n";
    json += "  \"birds\": [\n";

    bool first = true;
    for (const auto& pair : stats_) {
        if (!first) {
            json += ",\n";
        }
        first = false;

        const BirdStats& stat = pair.second;
        json += "    {\n";
        json += "      \"name\": \"" + stat.bird_name + "\",\n";
        json += "      \"encounter_count\": " + std::to_string(stat.encounter_count) + ",\n";
        json += "      \"first_seen\": " + std::to_string(stat.first_seen) + ",\n";
        json += "      \"last_seen\": " + std::to_string(stat.last_seen) + "\n";
        json += "    }";
    }

    json += "\n  ]\n";
    json += "}";

    return json;
}

BirdStats& BirdStatistics::updateOrCreateBirdStats(const std::string& bird_name) {
    auto it = stats_.find(bird_name);
    if (it == stats_.end()) {
        // 创建新的统计记录
        stats_[bird_name] = BirdStats(bird_name);
    }
    return stats_[bird_name];
}

} // namespace BirdWatching