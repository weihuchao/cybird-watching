#include <Arduino.h>
#include "log_manager.h"
#include "sd_card.h"
#include <vector>

// 静态成员初始化
LogManager* LogManager::instance = nullptr;

LogManager::LogManager() {
    sdCardAvailable = false;
    logFilePath = "/logs/holocubic.log";
    maxLogFileSize = 1024 * 1024; // 默认1MB
    currentLogLevel = LM_LOG_INFO;
    logOutputMode = OUTPUT_BOTH;
    lastFlushTime = 0;
}

LogManager* LogManager::getInstance() {
    if (instance == nullptr) {
        instance = new LogManager();
    }
    return instance;
}

bool LogManager::initialize(LogLevel level, LogOutput output) {
    currentLogLevel = level;
    logOutputMode = output;

    // 简化初始化：如果是只输出到串口，直接成功
    if (output == OUTPUT_SERIAL) {
        Serial.println("[LOG] LogManager initialized (serial only)");
        return true;
    }

    // 如果需要SD卡，稍后通过setLogOutput再尝试
    if (output == OUTPUT_SD_CARD || output == OUTPUT_BOTH) {
        Serial.println("[LOG] LogManager initialized (SD card support will be checked later)");
        sdCardAvailable = false; // 先设为false，等SD卡初始化完成后再检查
    }

    return true;
}

bool LogManager::createLogDirectory() {
    if (!sdCardAvailable) return false;

    // 检查并创建logs目录
    if (!SD.exists("/logs")) {
        if (!SD.mkdir("/logs")) {
            return false;
        }
    }

    return true;
}

void LogManager::checkLogRotation() {
    if (!sdCardAvailable) return;

    File logFile = SD.open(logFilePath, FILE_READ);
    if (logFile) {
        unsigned long size = logFile.size();
        logFile.close();

        // 如果文件超过最大大小，进行轮转
        if (size > maxLogFileSize) {
            // 删除旧的备份文件
            if (SD.exists(logFilePath + ".old")) {
                SD.remove(logFilePath + ".old");
            }

            // 将当前日志重命名为备份
            SD.rename(logFilePath, logFilePath + ".old");

            if (logOutputMode == OUTPUT_SERIAL || logOutputMode == OUTPUT_BOTH) {
                Serial.println("[LOG] Log rotated, old size: " + String(size) + " bytes");
            }
        }
    }
}

String LogManager::getTimestamp() {
    unsigned long currentTime = millis();
    unsigned long seconds = currentTime / 1000;
    unsigned long minutes = seconds / 60;
    unsigned long hours = minutes / 60;

    unsigned long millis_part = currentTime % 1000;
    unsigned long seconds_part = seconds % 60;
    unsigned long minutes_part = minutes % 60;
    unsigned long hours_part = hours % 24;

    char timestamp[32];
    sprintf(timestamp, "%02lu:%02lu:%02lu.%03lu",
            hours_part, minutes_part, seconds_part, millis_part);

    return String(timestamp);
}

void LogManager::writeToSDCard(const String& levelStr, const String& tag, const String& message) {
    if (!sdCardAvailable) return;

    checkLogRotation();

    File logFile = SD.open(logFilePath, FILE_APPEND);
    if (logFile) {
        String logLine = "[" + getTimestamp() + "] [" + levelStr + "] [" + tag + "] " + message + "\n";
        logFile.print(logLine);
        logFile.close();
    }
}

void LogManager::setLogLevel(LogLevel level) {
    currentLogLevel = level;
}

void LogManager::setLogOutput(LogOutput output) {
    logOutputMode = output;

    // 如果需要SD卡输出，重新尝试初始化SD卡
    if ((output == OUTPUT_SD_CARD || output == OUTPUT_BOTH) && !sdCardAvailable) {
        Serial.println("[LOG] Attempting to re-initialize SD card...");
        if (SD.begin()) {
            sdCardAvailable = true;
            if (createLogDirectory()) {
                Serial.println("[LOG] SD card re-initialization successful");
            } else {
                sdCardAvailable = false;
                Serial.println("[LOG] SD card re-initialization failed - cannot create log directory");
            }
        } else {
            Serial.println("[LOG] SD card re-initialization failed");
        }
    }
}

LogManager::LogOutput LogManager::getLogOutput() {
    return logOutputMode;
}

void LogManager::setLogFilePath(const String& path) {
    logFilePath = path;
}

void LogManager::setMaxLogFileSize(unsigned long size) {
    maxLogFileSize = size;
}

void LogManager::log(LogLevel level, const String& tag, const String& message) {
    if (level > currentLogLevel) return;

    String levelStr;
    switch (level) {
        case LM_LOG_FATAL: levelStr = "FATAL"; break;
        case LM_LOG_ERROR: levelStr = "ERROR"; break;
        case LM_LOG_WARN:  levelStr = "WARN";  break;
        case LM_LOG_INFO:  levelStr = "INFO";  break;
        case LM_LOG_DEBUG: levelStr = "DEBUG"; break;
        case LM_LOG_TRACE: levelStr = "TRACE"; break;
        default: levelStr = "UNKNOWN"; break;
    }

    // 输出到串口
    if (logOutputMode == OUTPUT_SERIAL || logOutputMode == OUTPUT_BOTH) {
        String logLine = "[" + levelStr + "] [" + tag + "] " + message;
        Serial.println(logLine);
    }

    // 输出到SD卡
    if ((logOutputMode == OUTPUT_SD_CARD || logOutputMode == OUTPUT_BOTH)) {
        writeToSDCard(levelStr, tag, message);
    }

    // 定期刷新缓冲区
    unsigned long currentTime = millis();
    if (currentTime - lastFlushTime > FLUSH_INTERVAL) {
        flush();
        lastFlushTime = currentTime;
    }
}

void LogManager::debug(const String& tag, const String& message) {
    log(LM_LOG_DEBUG, tag, message);
}

void LogManager::info(const String& tag, const String& message) {
    log(LM_LOG_INFO, tag, message);
}

void LogManager::warn(const String& tag, const String& message) {
    log(LM_LOG_WARN, tag, message);
}

void LogManager::error(const String& tag, const String& message) {
    log(LM_LOG_ERROR, tag, message);
}

void LogManager::fatal(const String& tag, const String& message) {
    log(LM_LOG_FATAL, tag, message);
}

void LogManager::logToSDOnly(LogLevel level, const String& tag, const String& message) {
    if (level > currentLogLevel) return;

    // Only output to SD card, not to serial port
    if (logOutputMode == OUTPUT_SD_CARD || logOutputMode == OUTPUT_BOTH) {
        String levelStr;
        switch (level) {
            case LM_LOG_FATAL: levelStr = "FATAL"; break;
            case LM_LOG_ERROR: levelStr = "ERROR"; break;
            case LM_LOG_WARN:  levelStr = "WARN";  break;
            case LM_LOG_INFO:  levelStr = "INFO";  break;
            case LM_LOG_DEBUG: levelStr = "DEBUG"; break;
            case LM_LOG_TRACE: levelStr = "TRACE"; break;
            default: levelStr = "UNKNOWN"; break;
        }

        writeToSDCard(levelStr, tag, message);

        // Update flush timer
        unsigned long currentTime = millis();
        if (currentTime - lastFlushTime > FLUSH_INTERVAL) {
            flush();
            lastFlushTime = currentTime;
        }
    }
}

void LogManager::flush() {
    // 刷新串口缓冲区
    Serial.flush();

    // SD卡文件操作已经自动刷新，不需要额外处理
}

void LogManager::clearLogFile() {
    if (sdCardAvailable && SD.exists(logFilePath)) {
        SD.remove(logFilePath);
        info("LOG", "Log file cleared");
    }
}

String LogManager::getLogContent(int maxLines) {
    String content = "";
    if (!sdCardAvailable || !SD.exists(logFilePath)) {
        content = "No log file available\n";
        return content;
    }

    // 限制最大行数以避免内存问题
    const int safeMaxLines = min(maxLines, 500);

    File logFile = SD.open(logFilePath, FILE_READ);
    if (!logFile) {
        content = "Failed to open log file\n";
        return content;
    }

    unsigned long fileSize = logFile.size();
    if (fileSize == 0) {
        logFile.close();
        content = "Log file is empty\n";
        return content;
    }

    // 使用简单的环形缓冲区，限制大小
    const int bufferSize = safeMaxLines + 10;
    String lineBuffer[bufferSize]; // 栈分配，避免动态内存
    int lineIndex = 0;
    int totalLines = 0;
    bool bufferFilled = false;

    // 逐行读取文件
    logFile.seek(0);
    while (logFile.available()) {
        String line = logFile.readStringUntil('\n');
        if (line.length() > 0) {
            // 限制行长度避免内存问题
            if (line.length() > 512) {
                line = line.substring(0, 512) + "...";
            }

            lineBuffer[lineIndex] = line;
            lineIndex = (lineIndex + 1) % bufferSize;
            totalLines++;

            if (!bufferFilled && lineIndex == 0) {
                bufferFilled = true;
            }
        }
    }
    logFile.close();

    // 计算实际要显示的行数
    int linesToShow = min(totalLines, safeMaxLines);
    int startIndex = (bufferFilled) ?
                    ((lineIndex - linesToShow + bufferSize) % bufferSize) :
                    0;

    // 构建结果
    content = "=== Last " + String(linesToShow) + " lines (of " + String(totalLines) + " total) ===\n";

    for (int i = 0; i < linesToShow; i++) {
        int idx = (startIndex + i) % bufferSize;
        if (lineBuffer[idx].length() > 0) {
            content += lineBuffer[idx] + "\n";
        }
    }

    if (content.length() == 0) {
        content = "Log file is empty or unreadable\n";
    }

    return content;
}

unsigned long LogManager::getLogFileSize() {
    if (!sdCardAvailable || !SD.exists(logFilePath)) {
        return 0;
    }

    File logFile = SD.open(logFilePath, FILE_READ);
    if (logFile) {
        unsigned long size = logFile.size();
        logFile.close();
        return size;
    }

    return 0;
}

bool LogManager::isSDCardAvailable() const {
    return sdCardAvailable;
}

void LogManager::shutdown() {
    flush();
}

LogManager::~LogManager() {
    shutdown();
}