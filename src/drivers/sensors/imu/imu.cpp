#include "imu.h"
#include "log_manager.h"

bool IMU::initialized = false;

void IMU::init()
{
	LOG_INFO("IMU", "Starting I2C...");
	Wire.begin(IMU_I2C_SDA, IMU_I2C_SCL);
	Wire.setClock(100000); // Reduce clock speed for more reliable communication

	LOG_INFO("IMU", "Scanning I2C bus...");
	byte error, address;
	int nDevices = 0;

	for(address = 1; address < 127; address++) {
		Wire.beginTransmission(address);
		error = Wire.endTransmission();

		if (error == 0) {
			LOG_INFO("IMU", "I2C device found at address 0x" + String(address, HEX));
			nDevices++;
		}
	}

	if (nDevices == 0) {
		LOG_ERROR("IMU", "No I2C devices found - MPU may not be connected");
		initialized = false;
		return;
	} else {
		LOG_INFO("IMU", "Found " + String(nDevices) + " I2C device(s)");
	}

	// MPU6050 was found at 0x68, try direct I2C communication
	LOG_INFO("IMU", "Testing direct I2C communication with MPU6050...");

	// Try to read WHO_AM_I register directly via I2C
	Wire.beginTransmission(0x68);
	Wire.write(0x75); // WHO_AM_I register
	Wire.endTransmission(false);

	Wire.requestFrom(0x68, 1);
	if (Wire.available()) {
		uint8_t whoami = Wire.read();
		Serial.printf("  MPU WHO_AM_I register: 0x%02X (expected: 0x68)\n", whoami);

		if (whoami == 0x68) {
			Serial.println("  MPU6050 communication OK, initializing manually...");

			// Wake up MPU6050 and configure it
			Serial.println("  Waking up MPU6050...");
			Wire.beginTransmission(0x68);
			Wire.write(0x6B); // PWR_MGMT_1 register
			Wire.write(0x00); // Wake up
			int result = Wire.endTransmission();
			Serial.printf("  Wake up result: %d\n", result);

			delay(100); // Wait for MPU to wake up

			// Configure accelerometer
			Serial.println("  Configuring accelerometer...");
			Wire.beginTransmission(0x68);
			Wire.write(0x1C); // ACCEL_CONFIG register
			Wire.write(0x00); // ±2g range
			result = Wire.endTransmission();
			Serial.printf("  Accelerometer config result: %d\n", result);

			Serial.println("  MPU6050 manual initialization complete");
			initialized = true;
		} else {
			Serial.printf("  Unexpected WHO_AM_I value: 0x%02X\n", whoami);
			initialized = false;
		}
	} else {
		Serial.println("  Failed to read WHO_AM_I register");
		initialized = false;
	}
}

void IMU::update(int interval)
{
	if (!initialized) {
		return; // Skip update if MPU is not initialized
	}
	Wire.beginTransmission(0x68);
	Wire.write(0x3B); // Start from ACCEL_XOUT_H
	int result = Wire.endTransmission(false);

	if (result != 0) {
		Serial.printf("  I2C transmission error: %d\n", result);
		return;
	}
	Wire.requestFrom(0x68, 6); // Read 6 bytes for accelerometer

	int bytes_received = Wire.available();

	if (bytes_received >= 6) {
		uint8_t data[6];
		for (int i = 0; i < 6; i++) {
			data[i] = Wire.read();
		}

		int16_t ax_raw = (data[0] << 8) | data[1];
		int16_t ay_raw = (data[2] << 8) | data[3];
		int16_t az_raw = (data[4] << 8) | data[5];

		ax = ax_raw;
		ay = ay_raw;
		az = az_raw;

		// Simple gyroscope read (optional for basic functionality)
		gx = 0;
		gy = 0;
		gz = 0;

		// Debug output for MPU data
		// Serial.printf("MPU: ay=%d, ax=%d, az=%d\n", ay, ax, az); // Commented out for cleaner output
	} else {
		Serial.printf("  Failed to read MPU data, only got %d bytes\n", bytes_received);
	}

	if (millis() - last_update_time > interval)
	{
		if (ay > 3000 && flag)
		{
			encoder_diff--;
			flag = 0;
			Serial.println("Gesture: Tilt forward - ENCODER--");
		}
		else if (ay < -3000 && flag)
		{
			encoder_diff++;
			flag = 0;
			Serial.println("Gesture: Tilt backward - ENCODER++");
		}
		else
		{
			flag = 1;
		}

		if (ax > 10000)
		{
			encoder_state = LV_INDEV_STATE_PR;
		}
		else
		{
			encoder_state = LV_INDEV_STATE_REL;
		}

		last_update_time = millis();
	}
}

int16_t IMU::getAccelX()
{
	return ax;
}

int16_t IMU::getAccelY()
{
	return ay;
}

int16_t IMU::getAccelZ()
{
	return az;
}

int16_t IMU::getGyroX()
{
	return gx;
}

int16_t IMU::getGyroY()
{
	return gy;
}

int16_t IMU::getGyroZ()
{
	return gz;
}
