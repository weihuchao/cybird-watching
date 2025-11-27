#include "display.h"
#include <TFT_eSPI.h>
#include "log_manager.h"

/*
TFT pins should be set in path/to/Arduino/libraries/TFT_eSPI/User_Setups/Setup24_ST7789.h
*/
TFT_eSPI tft = TFT_eSPI();

static lv_disp_buf_t disp_buf;
static lv_color_t buf[LV_HOR_RES_MAX * 10];


void my_print(lv_log_level_t level, const char* file, uint32_t line, const char* fun, const char* dsc)
{
	// 使用日志系统重定向 LVGL 日志
	LogManager* logManager = LogManager::getInstance();
	if (logManager) {
		String message = String(file) + "@" + String(line) + " " + String(fun) + "->" + String(dsc);

		switch (level) {
			case LV_LOG_LEVEL_ERROR:
				logManager->error("LVGL", message);
				break;
			case LV_LOG_LEVEL_WARN:
				logManager->warn("LVGL", message);
				break;
			case LV_LOG_LEVEL_INFO:
				logManager->info("LVGL", message);
				break;
			case LV_LOG_LEVEL_TRACE:
			default:
				logManager->debug("LVGL", message);
				break;
		}
	} else {
		// 备用：直接输出到串口
		Serial.printf("%s@%d %s->%s\r\n", file, line, fun, dsc);
		Serial.flush();
	}
}


void my_disp_flush(lv_disp_drv_t* disp, const lv_area_t* area, lv_color_t* color_p)
{
	uint32_t w = (area->x2 - area->x1 + 1);
	uint32_t h = (area->y2 - area->y1 + 1);

	tft.startWrite();
	tft.setAddrWindow(area->x1, area->y1, w, h);
	tft.pushColors(&color_p->full, w * h, true);
	tft.endWrite();

	lv_disp_flush_ready(disp);
}


void Display::init()
{
	// Temporarily disable PWM backlight to avoid GPIO error
	// ledcSetup(LCD_BL_PWM_CHANNEL, 5000, 8);
	// ledcAttachPin(LCD_BL_PIN, LCD_BL_PWM_CHANNEL);
	pinMode(LCD_BL_PIN, OUTPUT);
	digitalWrite(LCD_BL_PIN, HIGH);

	lv_init();

	lv_log_register_print_cb(my_print); /* register print function for debugging */

	LOG_INFO("TFT", "Testing minimal TFT init...");

	// Try a minimal TFT initialization
	pinMode(2, OUTPUT); // DC pin
	digitalWrite(2, HIGH);

	LOG_INFO("TFT", "DC pin set, attempting tft.begin()...");
	tft.begin(); /* TFT init */
	LOG_INFO("TFT", "tft.begin() completed");

	tft.setRotation(4); /* mirror */
	LOG_INFO("TFT", "TFT rotation set");
	LOG_INFO("TFT", "TFT initialization successful");

	lv_disp_buf_init(&disp_buf, buf, NULL, LV_HOR_RES_MAX * 10);

	/*Initialize the display*/
	lv_disp_drv_t disp_drv;
	lv_disp_drv_init(&disp_drv);
	disp_drv.hor_res = 240;
	disp_drv.ver_res = 240;
	disp_drv.flush_cb = my_disp_flush;
	disp_drv.buffer = &disp_buf;
	lv_disp_drv_register(&disp_drv);
}

void Display::routine()
{
	lv_task_handler();
}

void Display::setBackLight(float duty)
{
	// Simple digital backlight control for now
	if (duty > 0.5) {
		digitalWrite(LCD_BL_PIN, HIGH);
	} else {
		digitalWrite(LCD_BL_PIN, LOW);
	}
}
