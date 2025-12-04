#include "bird_utils.h"
#include "drivers/storage/sd_card/sd_card.h"
#include <cstdio>
#include <Arduino.h>

namespace BirdWatching {
namespace Utils {

uint8_t detectFrameCount(uint16_t bird_id) {
    // 优化策略：直接尝试打开文件，而不是扫描整个目录
    // 假设帧数在合理范围内（1-100），使用智能查找
    uint8_t max_frames = 0;
    
    // 首先尝试常见的帧数（快速路径）
    const uint8_t common_counts[] = {8, 16, 24, 32, 48, 64};
    for (uint8_t test_count : common_counts) {
        char path[128];
        snprintf(path, sizeof(path), "/birds/%d/%d.bin", bird_id, test_count);
        File test_file = SD.open(path);
        if (test_file) {
            test_file.close();
            max_frames = test_count;
        } else {
            break; // 没找到这个文件，说明帧数小于这个值
        }
    }
    
    // 如果找到了一个常见值，向后查找确切数量
    if (max_frames > 0) {
        for (uint8_t i = max_frames + 1; i <= 100; i++) {
            char path[128];
            snprintf(path, sizeof(path), "/birds/%d/%d.bin", bird_id, i);
            File test_file = SD.open(path);
            if (test_file) {
                test_file.close();
                max_frames = i;
            } else {
                break; // 找到最大值
            }
            
            // 每检查10个文件喂一次狗
            if (i % 10 == 0) {
                yield();
            }
        }
    } else {
        // 没找到常见值，从头开始线性查找
        for (uint8_t i = 1; i <= 100; i++) {
            char path[128];
            snprintf(path, sizeof(path), "/birds/%d/%d.bin", bird_id, i);
            File test_file = SD.open(path);
            if (test_file) {
                test_file.close();
                max_frames = i;
            } else if (max_frames > 0) {
                break; // 找到缺口，停止查找
            }
            
            // 每检查10个文件喂一次狗
            if (i % 10 == 0) {
                yield();
            }
        }
    }
    
    return max_frames;
}

} // namespace Utils
} // namespace BirdWatching
