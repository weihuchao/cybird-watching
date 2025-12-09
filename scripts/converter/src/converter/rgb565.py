"""
RGB565图片转换器
将PNG、JPG、JPEG等格式图片转换为RGB565格式
"""

from PIL import Image
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import struct


class RGB565Converter:
    """RGB565格式转换器"""

    @staticmethod
    def rgb_to_rgb565(r: int, g: int, b: int) -> int:
        """
        将RGB值转换为标准RGB565格式

        Args:
            r: 红色分量 (0-255)
            g: 绿色分量 (0-255)
            b: 蓝色分量 (0-255)

        Returns:
            标准RGB565格式的16位颜色值
        """
        # 将8位颜色转换为5位或6位
        r5 = (r >> 3) & 0x1F    # 红色5位
        g6 = (g >> 2) & 0x3F    # 绿色6位
        b5 = (b >> 3) & 0x1F    # 蓝色5位

        # 组合为标准RGB565格式 (RRRRRGGGGGGBBBBB)
        return (r5 << 11) | (g6 << 5) | b5

    @staticmethod
    def convert_image_to_rgb565(image_path: Path, output_path: Path,
                               max_size: Optional[Tuple[int, int]] = None) -> bool:
        """
        将图片转换为RGB565格式并保存为LVGL 7.9.1兼容的二进制文件

        Args:
            image_path: 输入图片路径
            output_path: 输出文件路径
            max_size: 最大尺寸 (width, height)，如果图片超过此尺寸则会等比缩放

        Returns:
            转换是否成功
        """
        try:
            # 打开图片
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # 调整尺寸如果指定了最大尺寸
                if max_size:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # 获取图片尺寸
                width, height = img.size

                # 转换为numpy数组
                pixels = np.array(img)

                # 创建RGB565数据数组
                rgb565_data = []

                for y in range(height):
                    for x in range(width):
                        r, g, b = pixels[y, x]
                        
                        # 重要：确保转换为Python int，避免numpy.uint8溢出问题
                        r = int(r)
                        g = int(g)
                        b = int(b)
                        
                        rgb565 = RGB565Converter.rgb_to_rgb565(r, g, b)
                        rgb565_data.append(rgb565)

                # 写入LVGL 9.x兼容的二进制文件
                with open(output_path, 'wb') as f:
                    # LVGL 9.x图像头部
                    # cf (color format): LV_COLOR_FORMAT_RGB565 = 0x12 (18) for RGB565
                    LV_COLOR_FORMAT_RGB565 = 0x12
                    magic = 0x37  # LVGL 9.x magic number '7' (LVGL_VERSION_MAJOR = 9 -> '7')
                    header_cf = (magic << 24) | (LV_COLOR_FORMAT_RGB565)  # 32-bit header

                    # 写入LVGL 9.x图像头部 - 参考lv_bin_decoder.c期望的格式
                    f.write(struct.pack('<I', header_cf))  # 4字节: magic + cf
                    f.write(struct.pack('<I', 0))  # 4字节: flags (32-bit)
                    f.write(struct.pack('<HH', width, height))  # 4字节: width + height
                    f.write(struct.pack('<I', 0))  # 4字节: stride (calculated automatically)
                    f.write(struct.pack('<I', 0))  # 4字节: reserved_2
                    data_size = len(rgb565_data) * 2  # RGB565每像素2字节
                    f.write(struct.pack('<I', data_size))  # 4字节: data_size
                    
                    # 写入RGB565像素数据
                    for pixel in rgb565_data:
                        f.write(struct.pack('<H', pixel))

                return True

        except Exception as e:
            print(f"转换图片 {image_path} 时出错: {e}")
            return False

    @staticmethod
    def convert_image_to_c_array(image_path: Path, output_path: Path,
                                array_name: Optional[str] = None,
                                max_size: Optional[Tuple[int, int]] = None) -> bool:
        """
        将图片转换为RGB565格式的C数组

        Args:
            image_path: 输入图片路径
            output_path: 输出C文件路径
            array_name: 数组名称，如果为None则使用文件名
            max_size: 最大尺寸 (width, height)，如果图片超过此尺寸则会等比缩放

        Returns:
            转换是否成功
        """
        try:
            # 打开图片
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # 调整尺寸如果指定了最大尺寸
                if max_size:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # 获取图片尺寸
                width, height = img.size

                # 转换为numpy数组
                pixels = np.array(img)

                # 生成数组名称
                if array_name is None:
                    array_name = image_path.stem.replace('-', '_').replace(' ', '_')

                # 生成C数组内容
                c_content = []
                c_content.append(f"// RGB565 Image Data")
                c_content.append(f"// Generated from: {image_path.name}")
                c_content.append(f"// Size: {width}x{height}")
                c_content.append(f"")
                c_content.append(f"#include <stdint.h>")
                c_content.append(f"")
                c_content.append(f"// Image dimensions")
                c_content.append(f"const uint16_t {array_name}_width = {width};")
                c_content.append(f"const uint16_t {array_name}_height = {height};")
                c_content.append(f"")
                c_content.append(f"// RGB565 pixel data")
                c_content.append(f"const uint16_t {array_name}_data[] = {{")

                # 转换像素数据
                pixel_data = []
                for y in range(height):
                    row_data = []
                    for x in range(width):
                        r, g, b = pixels[y, x]
                        rgb565 = RGB565Converter.rgb_to_rgb565(r, g, b)
                        row_data.append(f"0x{rgb565:04X}")
                    pixel_data.append("    " + ", ".join(row_data))

                c_content.append(",\n".join(pixel_data))
                c_content.append("};")

                # 写入C文件
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(c_content))

                return True

        except Exception as e:
            print(f"转换图片 {image_path} 为C数组时出错: {e}")
            return False

    @staticmethod
    def pack_frames_to_bundle(frame_files: list[Path], output_bundle: Path,
                              width: int = 120, height: int = 120) -> bool:
        """
        将多个帧文件打包为bundle.bin

        Bundle文件格式:
        - Bundle Header (64字节): magic, version, frame_count, 等元数据
        - Frame Index (N×12字节): 每帧的offset, size, checksum
        - Frame Data: 所有帧的LVGL 9.x格式数据

        Args:
            frame_files: 帧文件列表（按顺序，1.bin, 2.bin, ...）
            output_bundle: 输出bundle文件路径
            width: 帧宽度
            height: 帧高度

        Returns:
            转换是否成功
        """
        try:
            import zlib

            if not frame_files:
                print("错误: 没有提供帧文件")
                return False

            # 排序帧文件（按数字顺序）
            frame_files = sorted(frame_files, key=lambda p: int(p.stem) if p.stem.isdigit() else 0)

            frame_count = len(frame_files)
            print(f"开始打包 {frame_count} 帧到 {output_bundle}")

            # 常量定义
            MAGIC = 0x42495244  # "BIRD"
            VERSION = 1
            COLOR_FORMAT_RGB565 = 0x12
            HEADER_SIZE = 64
            INDEX_ENTRY_SIZE = 12
            INDEX_TABLE_SIZE = frame_count * INDEX_ENTRY_SIZE
            DATA_OFFSET = HEADER_SIZE + INDEX_TABLE_SIZE

            # 验证帧文件并收集信息
            print("验证帧文件...")
            frame_info_list = []
            for i, frame_file in enumerate(frame_files):
                if not frame_file.exists():
                    print(f"错误: 帧文件不存在: {frame_file}")
                    return False

                # 读取并验证LVGL 9.x头部
                with open(frame_file, 'rb') as f:
                    if f.seek(0, 2) < 32:  # 检查文件大小
                        print(f"错误: 帧文件太小: {frame_file}")
                        return False

                    f.seek(0)
                    header_cf_bytes = f.read(4)
                    if len(header_cf_bytes) != 4:
                        print(f"错误: 无法读取帧头部: {frame_file}")
                        return False

                    header_cf = struct.unpack('<I', header_cf_bytes)[0]
                    color_format = header_cf & 0xFF
                    magic = (header_cf >> 24) & 0xFF

                    if color_format != COLOR_FORMAT_RGB565 or magic != 0x37:
                        print(f"错误: 无效的LVGL 9.x格式: {frame_file} (cf=0x{color_format:02X}, magic=0x{magic:02X})")
                        return False

                frame_size = frame_file.stat().st_size
                frame_info_list.append({
                    'path': frame_file,
                    'size': frame_size,
                    'offset': DATA_OFFSET + sum(info['size'] for info in frame_info_list)
                })

            # 计算总文件大小
            total_data_size = sum(info['size'] for info in frame_info_list)
            total_size = DATA_OFFSET + total_data_size

            # 写入bundle文件
            print(f"写入bundle文件 (总大小: {total_size / 1024 / 1024:.2f} MB)...")
            with open(output_bundle, 'wb') as f:
                # 1. 写入Bundle Header (64字节)
                f.write(struct.pack('<I', MAGIC))                    # magic (4B)
                f.write(struct.pack('<H', VERSION))                  # version (2B)
                f.write(struct.pack('<H', frame_count))              # frame_count (2B)
                f.write(struct.pack('<H', width))                    # frame_width (2B)
                f.write(struct.pack('<H', height))                   # frame_height (2B)
                f.write(struct.pack('<I', frame_info_list[0]['size']))  # frame_size (4B, 假设所有帧相同)
                f.write(struct.pack('<I', HEADER_SIZE))              # index_offset (4B)
                f.write(struct.pack('<I', DATA_OFFSET))              # data_offset (4B)
                f.write(struct.pack('<I', total_size))               # total_size (4B)
                f.write(struct.pack('<B', COLOR_FORMAT_RGB565))      # color_format (1B)
                f.write(bytes(35))                                   # reserved (35B)

                # 2. 写入Frame Index表 (N×12字节)
                for frame_info in frame_info_list:
                    # 计算帧数据的CRC32校验
                    with open(frame_info['path'], 'rb') as frame_file:
                        frame_data = frame_file.read()
                        checksum = zlib.crc32(frame_data) & 0xFFFFFFFF

                    f.write(struct.pack('<I', frame_info['offset']))  # offset (4B)
                    f.write(struct.pack('<I', frame_info['size']))    # size (4B)
                    f.write(struct.pack('<I', checksum))              # checksum (4B)

                # 3. 写入所有帧数据
                print("写入帧数据...")
                for i, frame_info in enumerate(frame_info_list):
                    with open(frame_info['path'], 'rb') as frame_file:
                        frame_data = frame_file.read()
                        f.write(frame_data)

                    if (i + 1) % 10 == 0 or (i + 1) == frame_count:
                        print(f"  已写入 {i + 1}/{frame_count} 帧")

            print(f"✓ 成功打包 {frame_count} 帧")
            print(f"  输出文件: {output_bundle}")
            print(f"  文件大小: {total_size / 1024 / 1024:.2f} MB")
            return True

        except Exception as e:
            print(f"打包帧文件时出错: {e}")
            import traceback
            traceback.print_exc()
            return False