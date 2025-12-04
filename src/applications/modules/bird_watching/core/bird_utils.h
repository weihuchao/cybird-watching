#ifndef BIRD_UTILS_H
#define BIRD_UTILS_H

#include <cstdint>

namespace BirdWatching {
namespace Utils {

/**
 * @brief 智能检测小鸟的帧数
 * 
 * 使用优化的查找算法，先尝试常见帧数，再精确查找
 * 避免扫描整个目录，大幅提升检测速度
 * 
 * @param bird_id 小鸟ID
 * @return 检测到的帧数，如果没有找到则返回0
 */
uint8_t detectFrameCount(uint16_t bird_id);

} // namespace Utils
} // namespace BirdWatching

#endif // BIRD_UTILS_H
