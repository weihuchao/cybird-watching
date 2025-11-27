#include <Arduino.h>
#include "drivers/display/display.h"
#include "drivers/sensors/imu/imu.h"
#include "drivers/sensors/ambient/ambient.h"
#include "drivers/communication/network/network.h"
#include "drivers/storage/sd_card/sd_card.h"
#include "drivers/io/rgb_led/rgb_led.h"
#include "system/lvgl/ports/lv_port_indev.h"
#include "system/lvgl/ports/lv_port_fatfs.h"
#include "applications/gui/core/lv_cubic_gui.h"
#include "applications/gui/core/gui_guider.h"
#include "system/logging/log_manager.h"
#include "system/commands/serial_commands.h"

/*** Component objects ***/
Display screen;
IMU mpu;
Pixel rgb;
SdCard tf;
Network wifi;

lv_ui guider_ui;

void setup()
{
    // 初始化串口通信
    Serial.begin(115200);
    delay(1000); // 等待串口稳定

    // 立即输出标识，不依赖日志系统
    Serial.println("=== CybirdWatching Starting ===");
    Serial.println("*** NEW FIRMWARE v2.0 WITH SERIAL COMMANDS ***");
    Serial.println("This should be visible if new firmware is running!");
    delay(1000);

    // 初始化日志系统 - 先只用串口输出，等SD卡初始化完成后再启用SD卡
    LogManager* logManager = LogManager::getInstance();
    logManager->initialize(LogManager::LM_LOG_INFO, LogManager::OUTPUT_SERIAL);

    LOG_INFO("MAIN", "=== CybirdWatching Starting ===");
    LOG_INFO("MAIN", "*** NEW FIRMWARE v2.0 WITH SERIAL COMMANDS ***");
    delay(1000);
    LOG_INFO("MAIN", "Serial communication OK");

    // 初始化串口命令系统
    SerialCommands* serialCommands = SerialCommands::getInstance();
    serialCommands->initialize();

    /*** Init screen ***/
    LOG_INFO("MAIN", "Initializing screen...");
    screen.init();
    LOG_INFO("MAIN", "Screen initialized");

    LOG_INFO("MAIN", "Setting backlight...");
    screen.setBackLight(0.2);
    LOG_INFO("MAIN", "Backlight set");

    /*** Init IMU as input device ***/
    LOG_INFO("MAIN", "Initializing LVGL input device...");
    lv_port_indev_init();
    LOG_INFO("MAIN", "LVGL input device initialized");

    LOG_INFO("MAIN", "Initializing MPU...");
    mpu.init();
    LOG_INFO("MAIN", "MPU initialized");

    /*** Init on-board RGB ***/
    LOG_INFO("MAIN", "Initializing RGB LED...");
    rgb.init();
    LOG_INFO("MAIN", "RGB LED initialized");

    LOG_INFO("MAIN", "Setting RGB colors...");
    rgb.setBrightness(0.1).setRGB(0, 0, 122, 204).setRGB(1, 0, 122, 204);
    LOG_INFO("MAIN", "RGB colors set");

    /*** Init micro SD-Card ***/
    LOG_INFO("MAIN", "Initializing SD card...");
    tf.init();
    LOG_INFO("MAIN", "SD card initialized");

    // 通知LogManager SD卡已初始化
    LOG_INFO("MAIN", "Re-initializing log manager with SD card support...");
    // Use SD card only to keep CLI responses clean
    // Use 'log cat' command to view full log when needed
    logManager->setLogOutput(LogManager::OUTPUT_SD_CARD);

    LOG_INFO("MAIN", "Initializing LVGL file system...");
    lv_fs_if_init();
    LOG_INFO("MAIN", "LVGL file system initialized");

    LOG_INFO("MAIN", "Reading WiFi configuration...");
    String ssid = tf.readFileLine("/wifi.txt", 1);        // line-1 for WiFi ssid
    String password = tf.readFileLine("/wifi.txt", 2);    // line-2 for WiFi password
    LOG_INFO("MAIN", "WiFi configuration read");

    /*** Inflate GUI objects ***/
    LOG_INFO("MAIN", "Creating GUI...");
    lv_holo_cubic_gui();
    LOG_INFO("MAIN", "GUI created");
//    setup_ui(&guider_ui);

    LOG_INFO("MAIN", "Setup completed, entering loop...");
}

int frame_id = 0;
char buf[100];
unsigned long lastHeartbeat = 0;

void loop()
{
    // run this as often as possible
    screen.routine();

    // 200 means update IMU data every 200ms
    mpu.update(200);

    // 处理串口命令
    SerialCommands::getInstance()->handleInput();

    //Serial.println("hello");
//    int len = sprintf(buf, "S:/Scenes/Holo3D/frame%03d.bin", frame_id++);
//    buf[len] = 0;
//    lv_img_set_src(guider_ui.scenes_canvas, buf);
//    Serial.println(buf);
//
//    if (frame_id == 138) frame_id = 0;

    //delay(10);
}