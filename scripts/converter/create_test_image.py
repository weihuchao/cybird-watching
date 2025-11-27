#!/usr/bin/env python3
"""创建测试图片脚本"""

from PIL import Image, ImageDraw
import os

def create_test_images():
    """创建多个测试图片"""

    # 确保输出目录存在
    os.makedirs('test_input', exist_ok=True)

    # 创建不同尺寸和颜色的测试图片

    # 1. 红色渐变图片
    img1 = Image.new('RGB', (64, 64), color='black')
    draw1 = ImageDraw.Draw(img1)
    for x in range(64):
        color = (x * 4, 0, 0)  # 红色渐变
        draw1.rectangle([x, 0, x, 63], fill=color)
    img1.save('test_input/red_gradient.png')

    # 2. 绿色渐变图片
    img2 = Image.new('RGB', (32, 32), color='black')
    draw2 = ImageDraw.Draw(img2)
    for y in range(32):
        color = (0, y * 8, 0)  # 绿色渐变
        draw2.rectangle([0, y, 31, y], fill=color)
    img2.save('test_input/green_gradient.jpg')

    # 3. 蓝色渐变图片
    img3 = Image.new('RGB', (128, 64), color='black')
    draw3 = ImageDraw.Draw(img3)
    for x in range(128):
        for y in range(64):
            r = 0
            g = 0
            b = (x + y) * 2 % 256
            if b > 255:
                b = 255
            draw3.point([x, y], fill=(r, g, b))
    img3.save('test_input/blue_gradient.jpeg')

    # 4. 彩色条纹图片
    img4 = Image.new('RGB', (64, 32), color='black')
    draw4 = ImageDraw.Draw(img4)
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    for i, color in enumerate(colors):
        draw4.rectangle([i * 10, 0, (i + 1) * 10 - 1, 31], fill=color)
    img4.save('test_input/color_stripes.png')

    print("测试图片已创建:")
    print("- red_gradient.png (64x64)")
    print("- green_gradient.jpg (32x32)")
    print("- blue_gradient.jpeg (128x64)")
    print("- color_stripes.png (64x32)")

if __name__ == '__main__':
    create_test_images()