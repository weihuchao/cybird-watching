#ifndef BIRD_STATS_H
#define BIRD_STATS_H

#include "bird_types.h"
#include <string>
#include <vector>
#include <map>

namespace BirdWatching {

class BirdStatistics {
public:
    BirdStatistics();
    ~BirdStatistics();

    // 初始化统计数据
    bool initialize(const std::string& data_file = "S:/data/bird_stats.json");

    // 记录一次小鸟遇见
    void recordEncounter(const std::string& bird_name);

    // 获取总观鸟次数
    int getTotalEncounters() const { return total_encounters_; }

    // 获取指定小鸟的统计信息
    const BirdStats* getBirdStats(const std::string& bird_name) const;

    // 获取所有小鸟的统计信息
    std::vector<BirdStats> getAllStats() const;

    // 获取观鸟进度百分比（遇到的不同种类占总种类的比例）
    float getProgressPercentage(int total_bird_species) const;

    // 获取最常遇见的小鸟
    std::string getMostSeenBird() const;

    // 获取最稀有的小鸟
    std::string getRarestBird() const;

    // 保存统计数据到文件
    bool saveToFile();

    // 从文件加载统计数据
    bool loadFromFile();

    // 重置统计数据
    void resetStats();

    // 打印统计信息到日志
    void printStats() const;

private:
    std::map<std::string, BirdStats> stats_;   // 统计数据映射
    int total_encounters_;                    // 总遇见次数
    std::string data_file_;                   // 数据文件路径

    // 从文件解析统计数据
    bool parseStatsFromFile(const char* content);

    // 将统计数据格式化为JSON字符串
    std::string formatStatsAsJson() const;

    // 更新或创建小鸟统计记录
    BirdStats& updateOrCreateBirdStats(const std::string& bird_name);
};

} // namespace BirdWatching

#endif // BIRD_STATS_H