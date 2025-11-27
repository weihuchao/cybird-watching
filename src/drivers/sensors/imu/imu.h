#ifndef IMU_H
#define IMU_H


#include <I2Cdev.h>
#include <MPU6050.h>
#include "lv_port_indev.h"

#define IMU_I2C_SDA 32
#define IMU_I2C_SCL 33

// 手势类型定义
enum GestureType {
    GESTURE_NONE = 0,
    GESTURE_FORWARD_TILT,    // 向前倾斜 - 触发小鸟
    GESTURE_BACKWARD_TILT,   // 向后倾斜 - 显示统计
    GESTURE_SHAKE,           // 摇动 - 随机触发
    GESTURE_DOUBLE_TILT      // 双向倾斜 - 重置统计
};

extern int32_t encoder_diff;
extern lv_indev_state_t encoder_state;

class IMU
{
private:
	MPU6050 imu;
	int flag;
	int16_t ax, ay, az;
	int16_t gx, gy, gz;

	long  last_update_time;
	static bool initialized;

	// 手势检测相关变量
	long last_gesture_time;
	int shake_counter;
	bool was_forward_tilt;
	bool was_backward_tilt;
	int consecutive_tilt_count;

public:
	void init();

	void update(int interval);

	int16_t getAccelX();
	int16_t getAccelY();
	int16_t getAccelZ();

	int16_t getGyroX();
	int16_t getGyroY();
	int16_t getGyroZ();

	// 手势检测方法
	GestureType detectGesture();

private:
	// 手势检测辅助方法
	bool isShaking();
	bool isForwardTilt();
	bool isBackwardTilt();
	void resetGestureState();

};

#endif