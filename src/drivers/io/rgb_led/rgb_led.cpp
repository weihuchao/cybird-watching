#include "rgb_led.h"


void Pixel::init()
{
	FastLED.addLeds<WS2812, RGB_LED_PIN, GRB>(color_buffers, RGB_LED_NUM);
	// 初始化时默认关闭LED
	FastLED.setBrightness(0);
	// 设置默认颜色为黑色（关闭）
	for (int i = 0; i < RGB_LED_NUM; i++) {
		color_buffers[i] = CRGB(0, 0, 0);
	}
	FastLED.show();
}

Pixel& Pixel::setRGB(int id, int r, int g, int b)
{
	color_buffers[id] = CRGB(r, g, b);
	FastLED.show();

	return *this;
}

Pixel& Pixel::setBrightness(float duty)
{
	duty = constrain(duty, 0, 1);
	FastLED.setBrightness((uint8_t)(255 * duty));
	FastLED.show();

	return *this;
}
