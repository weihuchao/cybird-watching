"""
命令执行器模块
"""
import asyncio
from dataclasses import dataclass
from typing import Optional

from ..config.settings import CybirdWatchingConfig
from .connection import SerialConnectionManager
from .response_handler import CommandResponseHandler, ParsedResponse
from ..utils.exceptions import ConnectionError, CommandTimeoutError, InvalidCommandError


@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    response: str
    raw_response: str
    error: Optional[str] = None
    execution_time: float = 0.0


class CommandExecutor:
    """命令执行器"""

    def __init__(self,
                 connection: SerialConnectionManager,
                 response_handler: CommandResponseHandler,
                 config: CybirdWatchingConfig):
        self.connection = connection
        self.response_handler = response_handler
        self.config = config

    async def execute_device_command(self, command: str) -> CommandResult:
        """执行设备命令"""
        import time
        start_time = time.time()

        try:
            if not self.connection.is_connected:
                raise ConnectionError("设备未连接")

            # 发送命令
            await self.connection.send_command(command)

            # 等待响应处理
            await asyncio.sleep(self.config.response.response_wait_ms / 1000.0)

            # 读取响应
            response = await self.response_handler.read_response(self.connection)

            execution_time = time.time() - start_time
            return CommandResult(
                success=True,
                response=response,
                raw_response=response,  # 这里raw_response和response相同，因为read_response已经处理了
                execution_time=execution_time
            )

        except ConnectionError as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                response="",
                raw_response="",
                error=str(e),
                execution_time=execution_time
            )
        except CommandTimeoutError as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                response="",
                raw_response="",
                error=f"命令执行超时: {str(e)}",
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                response="",
                raw_response="",
                error=f"命令执行失败: {str(e)}",
                execution_time=execution_time
            )

    async def execute_test_command(self) -> CommandResult:
        """执行测试命令 - 不需要响应标记的简单ping"""
        import time
        start_time = time.time()

        try:
            if not self.connection.is_connected:
                raise ConnectionError("设备未连接")

            # 发送简单的help命令进行测试
            await self.connection.send_command("help")

            # 等待响应
            await asyncio.sleep(1.0)  # 等待1秒

            # 读取所有可用数据（不期望有响应标记）
            raw_data = ""
            read_attempts = 0
            max_attempts = 20

            while read_attempts < max_attempts:
                if self.connection.bytes_available() > 0:
                    data = await self.connection.read_data(1024)
                    try:
                        new_data = data.decode('utf-8', errors='ignore')
                        raw_data += new_data
                    except UnicodeDecodeError:
                        pass
                else:
                    break
                await asyncio.sleep(0.05)
                read_attempts += 1

            execution_time = time.time() - start_time

            if raw_data.strip():
                return CommandResult(
                    success=True,
                    response=raw_data.strip(),
                    raw_response=raw_data,
                    execution_time=execution_time
                )
            else:
                return CommandResult(
                    success=False,
                    response="",
                    raw_response="",
                    error="测试模式：未接收到任何数据，固件可能未处理命令",
                    execution_time=execution_time
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                response="",
                raw_response="",
                error=f"测试命令执行失败: {str(e)}",
                execution_time=execution_time
            )

    def format_command(self, command: str) -> str:
        """格式化命令字符串"""
        command = command.strip()

        # 处理特殊命令别名
        if command.lower() in ['dh', 'device-help']:
            return 'help'

        return command

    def validate_command(self, command: str) -> bool:
        """验证命令是否有效"""
        if not command or not command.strip():
            return False

        # 设备命令列表
        device_commands = [
            'help', 'log', 'status', 'clear', 'tree', 'bird'
        ]

        formatted_command = self.format_command(command)
        command_word = formatted_command.split(' ')[0].lower()

        return command_word in device_commands

    async def execute_command_with_validation(self, command: str) -> CommandResult:
        """执行带验证的命令"""
        # 验证命令
        if not self.validate_command(command):
            return CommandResult(
                success=False,
                response="",
                raw_response="",
                error=f"无效命令: {command}"
            )

        # 格式化命令
        formatted_command = self.format_command(command)

        # 特殊处理测试命令
        if command.lower() == 'test':
            return await self.execute_test_command()

        # 执行设备命令
        return await self.execute_device_command(formatted_command)

    async def send_raw_command(self, command: str) -> CommandResult:
        """发送原始命令（不进行验证）"""
        import time
        start_time = time.time()

        try:
            if not self.connection.is_connected:
                raise ConnectionError("设备未连接")

            await self.connection.send_command(command)

            # 读取响应（带标记验证）
            parsed_response = await self.response_handler.read_with_markers(
                self.connection, require_markers=True
            )

            execution_time = time.time() - start_time

            return CommandResult(
                success=parsed_response.success,
                response=parsed_response.content,
                raw_response=parsed_response.raw_data,
                error=parsed_response.error,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                response="",
                raw_response="",
                error=f"原始命令执行失败: {str(e)}",
                execution_time=execution_time
            )

    def get_supported_commands(self) -> list:
        """获取支持的命令列表"""
        return [
            'help - 显示可用命令',
            'log [clear|size|lines N|cat|help] - 日志文件操作',
            'status - 显示系统状态',
            'clear - 清除终端屏幕',
            'tree [path] [levels] - 显示SD卡目录树',
            'bird trigger - 手动触发小鸟动画',
            'bird stats - 显示观鸟统计信息',
            'bird reset - 重置观鸟统计数据',
            'bird list - 显示可用小鸟列表',
            'test - 测试基本通信（无响应标记）'
        ]

    def parse_log_subcommand(self, command: str) -> tuple:
        """解析log子命令"""
        parts = command.strip().split()
        if len(parts) == 1:
            return 'log', ''  # 默认显示最后20行
        elif len(parts) == 2:
            return 'log', parts[1]
        else:
            return 'log', ' '.join(parts[1:])

    def parse_bird_subcommand(self, command: str) -> tuple:
        """解析bird子命令"""
        parts = command.strip().split()
        if len(parts) == 1:
            return 'bird', 'help'  # 默认显示bird帮助
        elif len(parts) == 2:
            return 'bird', parts[1]
        else:
            return 'bird', ' '.join(parts[1:])