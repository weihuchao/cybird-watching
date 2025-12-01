#include "lvgl.h"
#include <stdio.h>
#include "gui_guider.h"


void setup_ui(lv_ui* ui)
{
	// 只初始化scenes界面，包含Bird Animation系统
	setup_screnes(ui);
	lv_scr_load(ui->scenes);
}
