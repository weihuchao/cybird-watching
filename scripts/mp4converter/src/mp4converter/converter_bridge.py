"""
与现有RGB565转换器的桥接模块

基于用户选择的完全独立工具设计，MP4转换器仅在最终步骤调用现有converter。
负责临时文件管理、subprocess调用、结果聚合和错误处理。
支持输出文件命名策略：视频名_帧序号.rgb565
"""

import os
import sys
import subprocess
import tempfile
import shutil
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from PIL import Image

# 获取converter目录的路径
# 从 mp4converter/src/mp4converter/converter_bridge.py 到 converter/src/converter/
CONVERTER_DIR = Path(__file__).parent.parent.parent.parent / "converter" / "src" / "converter"


@dataclass
class ConversionResult:
    """转换结果数据类"""
    success: bool
    rgb565_files: List[Path]
    temp_files: List[Path]
    error_message: Optional[str] = None
    conversion_time: Optional[float] = None
    frame_count: int = 0

    @property
    def has_rgb565_files(self) -> bool:
        """是否成功生成RGB565文件"""
        return len(self.rgb565_files) > 0


@dataclass
class RGB565Config:
    """RGB565转换配置"""
    format: str = 'binary'  # 'binary' 或 'c_array'
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    array_name: Optional[str] = None  # 用于C数组格式
    enabled: bool = True  # 是否启用RGB565转换，False则输出PNG
    pack_bundle: bool = False  # 是否打包为bundle.bin
    bundle_width: int = 120  # bundle帧宽度
    bundle_height: int = 120  # bundle帧高度

    def to_converter_args(self) -> List[str]:
        """转换为converter命令行参数

        Returns:
            List[str]: 命令行参数列表
        """
        if not self.enabled:
            return []

        args = []

        if self.max_width:
            args.extend(['--max-width', str(self.max_width)])

        if self.max_height:
            args.extend(['--max-height', str(self.max_height)])

        if self.format == 'c_array':
            args.extend(['--format', 'c_array'])
            if self.array_name:
                args.extend(['--array-name', self.array_name])

        return args


class ConverterBridgeError(Exception):
    """转换器桥接错误"""
    pass


class ConverterNotFoundError(Exception):
    """转换器未找到错误"""
    pass


class ConverterBridge:
    """转换器桥接

    基于用户选择的完全独立工具设计：
    - MP4转换器完全独立，仅在最终步骤调用现有converter
    - 临时文件管理和自动清理
    - 通过subprocess调用现有转换器
    - 结果聚合和错误处理
    """

    def __init__(self, converter_path: Optional[Path] = None,
                 temp_dir: Optional[Path] = None,
                 keep_temp_files: bool = False):
        """初始化转换器桥接

        Args:
            converter_path: converter目录路径，None则自动检测
            temp_dir: 临时目录路径，None则使用系统默认
            keep_temp_files: 是否保留临时文件（用于调试）
        """
        self.converter_path = converter_path or CONVERTER_DIR
        self.temp_dir = temp_dir
        self.keep_temp_files = keep_temp_files
        self.temp_files_created: List[Path] = []

        # 验证converter路径
        self._validate_converter_path()

    def _validate_converter_path(self) -> None:
        """验证converter路径是否有效"""
        if not self.converter_path.exists():
            raise ConverterNotFoundError(f"Converter目录不存在: {self.converter_path}")

        # 检查是否存在converter模块
        converter_init = self.converter_path / "__init__.py"
        if not converter_init.exists():
            raise ConverterNotFoundError(f"Converter模块不存在: {converter_init}")

        # 检查是否存在pyproject.toml（在converter根目录）
        converter_pyproject = self.converter_path.parent.parent / "pyproject.toml"
        if not converter_pyproject.exists():
            raise ConverterNotFoundError(f"Converter配置文件不存在: {converter_pyproject}")

    def _create_temp_dir(self) -> Path:
        """创建临时目录"""
        if self.temp_dir:
            temp_path = self.temp_dir
            temp_path.mkdir(exist_ok=True)
        else:
            temp_path = Path(tempfile.mkdtemp(prefix="mp4converter_"))

        self.temp_files_created.append(temp_path)
        return temp_path

    def _cleanup_temp_files(self) -> None:
        """清理临时文件"""
        if self.keep_temp_files:
            print(f"保留临时文件用于调试: {[str(f) for f in self.temp_files_created]}")
            return

        for temp_file in self.temp_files_created:
            try:
                if temp_file.is_file():
                    temp_file.unlink()
                elif temp_file.is_dir():
                    shutil.rmtree(temp_file)
            except Exception as e:
                print(f"警告: 清理临时文件失败 {temp_file}: {e}")

    def save_frames_as_temp(self, frames: List[Image.Image],
                           video_name: str,
                           start_index: int = 0) -> List[Path]:
        """将帧保存为临时PNG文件

        Args:
            frames: 帧列表
            video_name: 视频名称（用于文件命名）
            start_index: 起始帧索引

        Returns:
            List[Path]: 临时文件路径列表
        """
        try:
            temp_dir = self._create_temp_dir()
            temp_files = []

            # 确保视频名称有效（移除特殊字符）
            safe_video_name = "".join(c for c in video_name if c.isalnum() or c in ('-', '_')).rstrip()

            for i, frame in enumerate(frames):
                frame_index = start_index + i

                # 使用简洁的数字命名，避免converter保留前缀
                frame_number = i + 1
                filename = f"{frame_number}.png"
                temp_path = temp_dir / filename

                # 确保为RGB格式
                if frame.mode != 'RGB':
                    frame = frame.convert('RGB')

                # 保存为PNG格式
                frame.save(temp_path, 'PNG', optimize=True)
                temp_files.append(temp_path)

            return temp_files

        except Exception as e:
            raise ConverterBridgeError(f"保存临时文件失败: {e}")

    def call_existing_converter(self, input_dir: Path, output_dir: Path,
                               config: RGB565Config) -> ConversionResult:
        """调用现有的converter进行批量转换

        Args:
            input_dir: 输入目录（包含PNG文件）
            output_dir: 输出目录
            config: RGB565转换配置

        Returns:
            ConversionResult: 转换结果
        """
        try:
            start_time = time.time()

            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)

            # 构建converter命令
            cmd = [
                "uv", "run", "converter", "convert",
                str(input_dir), str(output_dir)
            ]

            # 添加转换配置参数
            cmd.extend(config.to_converter_args())

            print(f"执行转换命令: {' '.join(cmd)}")

            # 执行转换
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.converter_path.parent),
                    capture_output=True,
                    text=True,
                    encoding='utf-8',  # 明确指定UTF-8编码
                    errors='replace',  # 遇到无法解码的字符用替换字符
                    timeout=300  # 5分钟超时
                )
            except subprocess.TimeoutExpired:
                raise ConverterBridgeError("转换超时（5分钟）")

            conversion_time = time.time() - start_time

            # 收集输出的RGB565文件
            rgb565_files = []
            if result.returncode == 0:
                # 查找输出目录中的RGB565文件
                for pattern in ["*.bin", "*.c", "*.h"]:
                    rgb565_files.extend(output_dir.glob(pattern))

                # 过滤掉临时文件
                rgb565_files = [f for f in rgb565_files if not f.name.startswith('.')]

            # 分析转换结果
            if result.returncode != 0:
                # 安全地处理可能为None的stderr和stdout
                error_msg = (result.stderr.strip() if result.stderr else "") or \
                           (result.stdout.strip() if result.stdout else "") or \
                           "转换失败，未知错误"
                return ConversionResult(
                    success=False,
                    rgb565_files=[],
                    temp_files=[input_dir, output_dir],
                    error_message=error_msg,
                    conversion_time=conversion_time
                )

            if not rgb565_files:
                return ConversionResult(
                    success=False,
                    rgb565_files=[],
                    temp_files=[input_dir, output_dir],
                    error_message="转换完成但未生成RGB565文件",
                    conversion_time=conversion_time
                )

            return ConversionResult(
                success=True,
                rgb565_files=rgb565_files,
                temp_files=[input_dir, output_dir],
                conversion_time=conversion_time,
                frame_count=len(rgb565_files)
            )

        except Exception as e:
            if isinstance(e, ConverterBridgeError):
                raise
            raise ConverterBridgeError(f"调用converter失败: {e}")

    def convert_frames_to_output(self, frames: List[Image.Image],
                                video_name: str,
                                output_dir: Path,
                                config: Optional[RGB565Config] = None) -> ConversionResult:
        """将帧转换为输出格式（RGB565或PNG）

        Args:
            frames: 处理后的帧列表
            video_name: 视频名称
            output_dir: 输出目录
            config: RGB565转换配置

        Returns:
            ConversionResult: 转换结果
        """
        if config is None:
            config = RGB565Config()

        try:
            if config.enabled:
                # 转换为RGB565格式（.bin文件）
                return self.convert_frames_to_rgb565(frames, video_name, output_dir, config)
            else:
                # 直接保存为PNG文件
                return self.save_frames_as_png(frames, video_name, output_dir)

        except Exception as e:
            if isinstance(e, ConverterBridgeError):
                raise
            raise ConverterBridgeError(f"转换帧失败: {e}")

    def convert_frames_to_rgb565(self, frames: List[Image.Image],
                                video_name: str,
                                output_dir: Path,
                                config: Optional[RGB565Config] = None) -> ConversionResult:
        """将帧转换为RGB565格式

        完整的转换流程：
        1. MP4转换器完成帧提取和图像处理
        2. 保存处理后的帧为临时PNG文件
        3. 如果pack_bundle=True: 直接转换并打包为bundle.bin
        4. 否则: 转换为单独的.bin文件
        5. 清理临时文件
        6. 返回最终文件列表

        Args:
            frames: 处理后的帧列表
            video_name: 视频名称
            output_dir: 输出目录
            config: RGB565转换配置

        Returns:
            ConversionResult: 转换结果
        """
        if config is None:
            config = RGB565Config()

        temp_input_dir = None
        temp_bin_dir = None
        try:
            # 1. 保存帧为临时PNG文件
            temp_files = self.save_frames_as_temp(frames, video_name)
            temp_input_dir = temp_files[0].parent if temp_files else self._create_temp_dir()

            if not temp_files:
                raise ConverterBridgeError("没有成功保存的临时文件")

            print(f"保存了 {len(temp_files)} 个临时帧文件到: {temp_input_dir}")

            # 2. 根据是否需要打包选择不同的流程
            if config.pack_bundle:
                # 打包模式：先转换到临时目录，再打包到输出目录
                temp_bin_dir = self._create_temp_dir()

                # 转换PNG到临时.bin目录
                result = self.call_existing_converter(temp_input_dir, temp_bin_dir, config)
                if not result.success:
                    return result

                # 打包到最终输出目录
                print(f"\n打包为bundle格式...")
                bundle_path = output_dir / "bundle.bin"
                bundle_result = self.pack_to_bundle_direct(temp_bin_dir, bundle_path, config)

                # 记录临时bin目录用于清理
                if temp_bin_dir not in self.temp_files_created:
                    self.temp_files_created.append(temp_bin_dir)

                result = bundle_result
            else:
                # 普通模式：直接转换到输出目录
                result = self.call_existing_converter(temp_input_dir, output_dir, config)

            # 记录临时文件用于清理
            if temp_input_dir not in self.temp_files_created:
                self.temp_files_created.append(temp_input_dir)

            return result

        except Exception as e:
            if isinstance(e, ConverterBridgeError):
                raise
            raise ConverterBridgeError(f"转换帧到RGB565失败: {e}")

        finally:
            # 清理临时文件
            if not self.keep_temp_files:
                self._cleanup_temp_files()

    def save_frames_as_png(self, frames: List[Image.Image],
                          video_name: str,
                          output_dir: Path) -> ConversionResult:
        """将帧直接保存为PNG文件

        Args:
            frames: 帧列表
            video_name: 视频名称
            output_dir: 输出目录

        Returns:
            ConversionResult: 转换结果
        """
        try:
            start_time = time.time()

            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)

            output_files = []
            safe_video_name = "".join(c for c in video_name if c.isalnum() or c in ('-', '_')).rstrip()

            for i, frame in enumerate(frames):
                # 使用从1开始递增的数字命名，无前缀
                frame_number = i + 1
                filename = f"{frame_number}.png"
                output_path = output_dir / filename

                # 如果图像是RGBA格式（有透明通道），直接保存
                # 如果是RGB格式，保持原样
                # 这样可以保留抠图处理后的透明通道
                if frame.mode == 'RGB':
                    # 对于RGB图像，转换为RGBA以支持透明（如果有透明需求）
                    frame_rgba = Image.new('RGBA', frame.size, (0, 0, 0, 0))
                    frame_rgba.paste(frame)
                    frame_to_save = frame_rgba
                else:
                    # 已经是RGBA或其它支持透明的格式
                    frame_to_save = frame

                # 保存为PNG格式，保留透明通道
                frame_to_save.save(output_path, 'PNG', optimize=True)
                output_files.append(output_path)

            conversion_time = time.time() - start_time

            print(f"保存了 {len(output_files)} 个PNG文件到: {output_dir}")

            return ConversionResult(
                success=True,
                rgb565_files=output_files,  # 复用这个字段存储PNG文件
                temp_files=[],
                conversion_time=conversion_time,
                frame_count=len(output_files)
            )

        except Exception as e:
            raise ConverterBridgeError(f"保存PNG文件失败: {e}")

    def get_output_filename_pattern(self, video_name: str) -> str:
        """获取输出文件名模式

        基于用户选择的输出文件命名策略：
        文件格式: `视频名_帧序号.rgb565`
        示例: `myvideo_0001.rgb565`, `myvideo_0002.rgb565`

        Args:
            video_name: 视频名称

        Returns:
            str: 文件名模式
        """
        # 确保视频名称有效
        safe_video_name = "".join(c for c in video_name if c.isalnum() or c in ('-', '_')).rstrip()
        return f"{safe_video_name}_%04d.rgb565"

    @staticmethod
    def create_rgb565_config(format: str = 'binary',
                           max_width: Optional[int] = None,
                           max_height: Optional[int] = None,
                           array_name: Optional[str] = None) -> RGB565Config:
        """创建RGB565转换配置

        Args:
            format: 输出格式 ('binary' 或 'c_array')
            max_width: 最大宽度
            max_height: 最大高度
            array_name: C数组名称

        Returns:
            RGB565Config: 转换配置
        """
        return RGB565Config(
            format=format,
            max_width=max_width,
            max_height=max_height,
            array_name=array_name
        )

    def pack_to_bundle(self, frames_dir: Path, config: RGB565Config) -> ConversionResult:
        """将目录中的帧文件打包为bundle.bin

        Args:
            frames_dir: 包含.bin帧文件的目录
            config: RGB565配置（包含bundle尺寸信息）

        Returns:
            ConversionResult: 打包结果
        """
        try:
            start_time = time.time()

            bundle_path = frames_dir / "bundle.bin"

            # 构建pack命令
            cmd = [
                "uv", "run", "converter", "pack",
                str(frames_dir),
                str(bundle_path),
                "--width", str(config.bundle_width),
                "--height", str(config.bundle_height)
            ]

            print(f"执行打包命令: {' '.join(cmd)}")

            # 执行打包
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.converter_path.parent),
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=300  # 5分钟超时
                )
            except subprocess.TimeoutExpired:
                raise ConverterBridgeError("打包超时（5分钟）")

            conversion_time = time.time() - start_time

            if result.returncode != 0:
                error_msg = (result.stderr.strip() if result.stderr else "") or \
                           (result.stdout.strip() if result.stdout else "") or \
                           "打包失败，未知错误"
                return ConversionResult(
                    success=False,
                    rgb565_files=[],
                    temp_files=[frames_dir],
                    error_message=error_msg,
                    conversion_time=conversion_time
                )

            if not bundle_path.exists():
                return ConversionResult(
                    success=False,
                    rgb565_files=[],
                    temp_files=[frames_dir],
                    error_message="打包完成但未生成bundle文件",
                    conversion_time=conversion_time
                )

            # 打包成功，删除单独的.bin文件（保留bundle.bin）
            for bin_file in frames_dir.glob("*.bin"):
                if bin_file.name != "bundle.bin" and bin_file.stem.isdigit():
                    bin_file.unlink()
                    print(f"删除临时文件: {bin_file.name}")

            return ConversionResult(
                success=True,
                rgb565_files=[bundle_path],
                temp_files=[frames_dir],
                conversion_time=conversion_time,
                frame_count=1  # bundle算作1个文件
            )

        except Exception as e:
            if isinstance(e, ConverterBridgeError):
                raise
            raise ConverterBridgeError(f"打包bundle失败: {e}")

    def pack_to_bundle_direct(self, frames_dir: Path, output_bundle: Path,
                             config: RGB565Config) -> ConversionResult:
        """将帧文件直接打包到指定路径的bundle.bin

        Args:
            frames_dir: 包含.bin帧文件的临时目录
            output_bundle: 输出bundle文件的完整路径
            config: RGB565配置（包含bundle尺寸信息）

        Returns:
            ConversionResult: 打包结果
        """
        try:
            start_time = time.time()

            # 确保输出目录存在
            output_bundle.parent.mkdir(parents=True, exist_ok=True)

            # 构建pack命令
            cmd = [
                "uv", "run", "converter", "pack",
                str(frames_dir),
                str(output_bundle),
                "--width", str(config.bundle_width),
                "--height", str(config.bundle_height)
            ]

            print(f"执行打包命令: {' '.join(cmd)}")

            # 执行打包
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.converter_path.parent),
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=300  # 5分钟超时
                )
            except subprocess.TimeoutExpired:
                raise ConverterBridgeError("打包超时（5分钟）")

            conversion_time = time.time() - start_time

            if result.returncode != 0:
                error_msg = (result.stderr.strip() if result.stderr else "") or \
                           (result.stdout.strip() if result.stdout else "") or \
                           "打包失败，未知错误"
                return ConversionResult(
                    success=False,
                    rgb565_files=[],
                    temp_files=[frames_dir],
                    error_message=error_msg,
                    conversion_time=conversion_time
                )

            if not output_bundle.exists():
                return ConversionResult(
                    success=False,
                    rgb565_files=[],
                    temp_files=[frames_dir],
                    error_message="打包完成但未生成bundle文件",
                    conversion_time=conversion_time
                )

            print(f"✓ 成功打包到: {output_bundle}")
            print(f"  文件大小: {output_bundle.stat().st_size / 1024 / 1024:.2f} MB")

            return ConversionResult(
                success=True,
                rgb565_files=[output_bundle],
                temp_files=[frames_dir],
                conversion_time=conversion_time,
                frame_count=1  # bundle算作1个文件
            )

        except Exception as e:
            if isinstance(e, ConverterBridgeError):
                raise
            raise ConverterBridgeError(f"打包bundle失败: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._cleanup_temp_files()