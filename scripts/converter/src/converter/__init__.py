"""
图片转RGB565转换器主程序
"""

import click
from pathlib import Path
from typing import Tuple, Optional

from .batch_processor import BatchProcessor


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """图片转RGB565转换器 - 将PNG、JPG、JPEG图片转换为RGB565格式"""
    pass


@cli.command()
@click.argument('source', type=click.Path(exists=True, path_type=Path))
@click.argument('output', type=click.Path(path_type=Path))
@click.option('--max-width', type=int, default=None, help='最大宽度 (像素)')
@click.option('--max-height', type=int, default=None, help='最大高度 (像素)')
@click.option('--format', 'output_format',
              type=click.Choice(['binary', 'c_array']),
              default='binary',
              help='输出格式 (binary 或 c_array)')
@click.option('--workers', type=int, default=4, help='并行处理线程数')
def convert(source: Path, output: Path, max_width: Optional[int],
           max_height: Optional[int], output_format: str, workers: int):
    """
    批量转换图片文件

    SOURCE: 源目录路径
    OUTPUT: 输出目录路径
    """

    # 确定最大尺寸
    max_size = None
    if max_width and max_height:
        max_size = (max_width, max_height)
    elif max_width:
        max_size = (max_width, 999999)  # 很大的高度值
    elif max_height:
        max_size = (999999, max_height)  # 很大的宽度值

    # 创建输出目录
    output.mkdir(parents=True, exist_ok=True)

    # 创建批量处理器
    processor = BatchProcessor(max_workers=workers)

    click.echo(f"开始批量转换:")
    click.echo(f"  源目录: {source}")
    click.echo(f"  输出目录: {output}")
    click.echo(f"  输出格式: {output_format}")
    if max_size:
        click.echo(f"  最大尺寸: {max_size[0]}x{max_size[1]}")
    click.echo(f"  并行线程数: {workers}")
    click.echo()

    # 执行批量转换
    success, failed = processor.batch_convert(
        source, output, max_size, output_format
    )

    if failed == 0:
        click.echo(f"[SUCCESS] 转换完成! 成功处理 {success} 个文件")
    else:
        click.echo(f"[WARNING] 转换完成，但有 {failed} 个文件失败")


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.argument('output_file', type=click.Path(path_type=Path))
@click.option('--max-width', type=int, default=None, help='最大宽度 (像素)')
@click.option('--max-height', type=int, default=None, help='最大高度 (像素)')
@click.option('--array-name', type=str, default=None, help='C数组名称')
@click.option('--format', 'output_format',
              type=click.Choice(['binary', 'c_array']),
              default='binary',
              help='输出格式 (binary 或 c_array)')
def single(input_file: Path, output_file: Path, max_width: Optional[int],
          max_height: Optional[int], array_name: Optional[str], output_format: str):
    """
    转换单个图片文件

    INPUT_FILE: 输入图片文件路径
    OUTPUT_FILE: 输出文件路径
    """

    # 确定最大尺寸
    max_size = None
    if max_width and max_height:
        max_size = (max_width, max_height)
    elif max_width:
        max_size = (max_width, 999999)
    elif max_height:
        max_size = (999999, max_height)

    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)

    click.echo(f"转换单个文件:")
    click.echo(f"  输入文件: {input_file}")
    click.echo(f"  输出文件: {output_file}")
    click.echo(f"  输出格式: {output_format}")
    if max_size:
        click.echo(f"  最大尺寸: {max_size[0]}x{max_size[1]}")
    if array_name:
        click.echo(f"  C数组名称: {array_name}")

    # 执行转换
    processor = BatchProcessor()

    if output_format == 'c_array':
        success = processor.convert_single_to_c_array(
            input_file, output_file, array_name, max_size
        )
    else:
        success = processor.convert_single_file(
            input_file, output_file, max_size
        )

    if success:
        click.echo("[SUCCESS] 转换成功!")
    else:
        click.echo("[ERROR] 转换失败!")


def main():
    """主入口函数"""
    cli()
