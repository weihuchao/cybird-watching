"""
控制台界面模块
"""
from typing import Optional
import sys

try:
    from rich.console import Console
    from rich.text import Text
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

from ..config.settings import CybirdWatchingConfig
from ..core.command_executor import CommandResult


class OutputFormatter:
    """输出格式化器"""

    def __init__(self, enable_colors: bool = True):
        self.enable_colors = enable_colors and RICH_AVAILABLE
        self.console = Console() if self.enable_colors else None

    def format_success(self, message: str) -> str:
        """格式化成功消息"""
        if self.enable_colors:
            return f"[green]✓[/green] {message}"
        return f"✓ {message}"

    def format_error(self, message: str) -> str:
        """格式化错误消息"""
        if self.enable_colors:
            return f"[red]✗[/red] {message}"
        return f"✗ {message}"

    def format_warning(self, message: str) -> str:
        """格式化警告消息"""
        if self.enable_colors:
            return f"[yellow]⚠[/yellow] {message}"
        return f"⚠ {message}"

    def format_info(self, message: str) -> str:
        """格式化信息消息"""
        if self.enable_colors:
            return f"[blue]ℹ[/blue] {message}"
        return f"ℹ {message}"

    def format_command(self, command: str) -> str:
        """格式化命令显示"""
        if self.enable_colors:
            return f"[yellow]发送:[/yellow] {command}"
        return f"发送: {command}"

    def format_response(self, response: str) -> str:
        """格式化响应显示"""
        if self.enable_colors:
            return f"[cyan]响应:[/cyan]\n{response}"
        return f"响应:\n{response}"

    def print_colored(self, text: str, color: Optional[str] = None) -> None:
        """打印彩色文本"""
        if self.enable_colors and color:
            self.console.print(text, style=color)
        elif self.enable_colors:
            self.console.print(text)
        else:
            print(text)

    def print_success(self, message: str) -> None:
        """打印成功消息"""
        self.print_colored(self.format_success(message), "green")

    def print_error(self, message: str) -> None:
        """打印错误消息"""
        self.print_colored(self.format_error(message), "red")

    def print_warning(self, message: str) -> None:
        """打印警告消息"""
        self.print_colored(self.format_warning(message), "yellow")

    def print_info(self, message: str) -> None:
        """打印信息消息"""
        self.print_colored(self.format_info(message), "blue")

    def print_command_result(self, result: CommandResult) -> None:
        """打印命令执行结果"""
        if result.success:
            if result.response:
                self.print_colored(self.format_response(result.response))
            if result.execution_time > 0:
                self.print_info(f"执行时间: {result.execution_time:.2f}秒")
        else:
            self.print_error(result.error or "命令执行失败")


class ConsoleInterface:
    """控制台界面"""

    def __init__(self, config: CybirdWatchingConfig):
        self.config = config
        self.formatter = OutputFormatter(config.ui.enable_colors)
        self.console = Console() if RICH_AVAILABLE else None

    def show_welcome(self) -> None:
        """显示欢迎信息"""
        welcome_text = "CybirdWatching CLI - 跨平台命令行工具 v1.0"

        if self.console:
            panel = Panel(
                f"[bold green]{welcome_text}[/bold green]",
                title="欢迎使用",
                border_style="green"
            )
            self.console.print(panel)
        else:
            print(f"\n{welcome_text}")
            print("=" * len(welcome_text))

    def show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
=== CybirdWatching CLI 帮助 ===

设备命令 (发送到ESP32设备):
  log              - 显示最后20行日志
  log clear        - 清空日志文件
  log size         - 显示日志文件大小
  log lines N      - 显示最后N行日志 (1-500)
  log cat/export   - 显示完整日志文件内容
  status           - 显示系统状态
  clear            - 清除设备终端屏幕
  tree [path] [levels] - 显示SD卡目录树
  help             - 显示设备帮助

本地命令:
  help             - 显示此CLI帮助
  test             - 测试基本通信（无响应标记）
  quit, exit       - 退出程序
  reconnect        - 重新连接设备
  cls              - 清除此终端屏幕

示例:
  [ON] CybirdWatching> log          # 显示设备日志
  [ON] CybirdWatching> log cat      # 显示完整日志
  [ON] CybirdWatching> status       # 显示设备状态
  [ON] CybirdWatching> log lines 20 # 显示最后20行日志
  [ON] CybirdWatching> tree         # 显示SD卡目录树
  [ON] CybirdWatching> tree /config 2 # 显示config目录，2层深度
  [ON] CybirdWatching> test         # 测试通信
        """

        if self.console:
            panel = Panel(
                help_text.strip(),
                title="帮助信息",
                border_style="blue"
            )
            self.console.print(panel)
        else:
            print(help_text)

    def get_user_input(self, prompt: str) -> str:
        """获取用户输入"""
        if self.console:
            try:
                # Rich的Prompt不支持复杂的格式，所以使用普通输入
                user_input = input(prompt)
                return user_input.strip()
            except (EOFError, KeyboardInterrupt):
                return "quit"
        else:
            try:
                user_input = input(prompt)
                return user_input.strip()
            except (EOFError, KeyboardInterrupt):
                return "quit"

    def format_output(self, content: str, output_type: str = "response") -> str:
        """格式化输出内容"""
        if output_type == "command":
            return self.formatter.format_command(content)
        elif output_type == "response":
            return self.formatter.format_response(content)
        elif output_type == "success":
            return self.formatter.format_success(content)
        elif output_type == "error":
            return self.formatter.format_error(content)
        elif output_type == "warning":
            return self.formatter.format_warning(content)
        elif output_type == "info":
            return self.formatter.format_info(content)
        else:
            return content

    def show_connection_status(self, is_connected: bool, port: str) -> None:
        """显示连接状态"""
        status = "ON" if is_connected else "OFF"
        status_text = f"设备状态: {status}"

        if is_connected:
            status_text += f" (端口: {port})"

        if is_connected:
            self.formatter.print_success(status_text)
        else:
            self.formatter.print_error(status_text)

    def show_command_sent(self, command: str) -> None:
        """显示命令发送提示"""
        self.formatter.print_colored(self.formatter.format_command(command))

    def show_command_result(self, result: CommandResult) -> None:
        """显示命令执行结果"""
        self.formatter.print_command_result(result)

    def clear_screen(self) -> None:
        """清屏"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_error(self, message: str) -> None:
        """显示错误消息"""
        self.formatter.print_error(message)

    def show_info(self, message: str) -> None:
        """显示信息消息"""
        self.formatter.print_info(message)

    def show_warning(self, message: str) -> None:
        """显示警告消息"""
        self.formatter.print_warning(message)

    def get_prompt(self, is_connected: bool) -> str:
        """获取命令提示符"""
        status = "[ON]" if is_connected else "[OFF]"
        return self.config.ui.prompt_template.format(status=status)

    def show_device_info(self, device_info: dict) -> None:
        """显示设备信息"""
        if not self.console:
            print(f"设备信息: {device_info}")
            return

        table = Table(title="设备信息", box=box.ROUNDED)
        table.add_column("属性", style="cyan", no_wrap=True)
        table.add_column("值", style="white")

        table.add_row("端口", device_info.get('port', 'Unknown'))
        table.add_row("波特率", str(device_info.get('baudrate', 'Unknown')))
        table.add_row("连接状态", "已连接" if device_info.get('is_connected') else "未连接")
        table.add_row("端口开放", "是" if device_info.get('is_open') else "否")

        if device_info.get('is_open'):
            table.add_row("CD", str(device_info.get('cd', 'N/A')))
            table.add_row("DSR", str(device_info.get('dsr', 'N/A')))
            table.add_row("CTS", str(device_info.get('cts', 'N/A')))
            table.add_row("RI", str(device_info.get('ri', 'N/A')))

        self.console.print(table)