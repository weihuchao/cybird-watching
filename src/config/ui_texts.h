#ifndef UI_TEXTS_H
#define UI_TEXTS_H

#include <Arduino.h>

/**
 * UI文本配置
 * 所有需要在屏幕UI上展示的文本集中在这里管理
 * 注意：不包括日志输出和串口调试信息
 */
namespace UITexts {

// ============================================
// 启动界面文本
// ============================================
namespace SplashView {
    constexpr const char* COPYRIGHT = "Copyright (c) 2025 Huchao";
}

} // namespace UITexts

#endif // UI_TEXTS_H
