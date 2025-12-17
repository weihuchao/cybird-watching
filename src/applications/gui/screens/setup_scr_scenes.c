/*
 * Copyright 2021 NXP
 * SPDX-License-Identifier: MIT
 */

#include "lvgl.h"
#include <stdio.h>
#include "gui_guider.h"
#include "Arduino.h"
#include "bird_animation_bridge.h"

void setup_screnes(lv_ui* ui)
{
	//Write codes scenes
	ui->scenes = lv_obj_create(NULL);

	//Write codes scenes_canvas
	ui->scenes_canvas = lv_image_create(ui->scenes);

	//Write style for scenes_canvas (LVGL 9.x中移除了LV_IMG_PART_MAIN)
	static lv_style_t style_scenes_canvas_main;
	lv_style_init(&style_scenes_canvas_main);

	// LVGL 9.x中样式API不再需要状态参数
	lv_style_set_bg_color(&style_scenes_canvas_main, lv_color_black());
	lv_style_set_bg_color(&style_scenes_canvas_main, lv_color_hex(0x888888));
	lv_style_set_bg_color(&style_scenes_canvas_main, lv_color_hex(0x666666));

	//Write style for scenes (LVGL 9.x中移除了LV_BTN_PART_MAIN，改为LV_PART_MAIN)
	lv_obj_add_style(ui->scenes, &style_scenes_canvas_main, LV_PART_MAIN);

	// 触发小鸟动画（通过BirdManager管理，避免多实例问题）
	bird_animation_load_image_to_canvas(ui->scenes_canvas, 1001, 0);

	// 设置对象位置和大小 - 覆盖整个屏幕
	lv_obj_set_size(ui->scenes_canvas, 240, 240); // 设置为全屏大小
	lv_obj_align(ui->scenes_canvas, LV_ALIGN_CENTER, 0, 0);

	// 确保对象可见
	lv_obj_clear_flag(ui->scenes_canvas, LV_OBJ_FLAG_HIDDEN);
}