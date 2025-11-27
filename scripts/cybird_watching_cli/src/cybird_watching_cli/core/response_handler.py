"""
命令响应处理器模块
"""
import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from ..config.settings import ResponseHandlingConfig
from ..utils.exceptions import ResponseParseError, CommandTimeoutError
from .connection import SerialConnectionManager


@dataclass
class ParsedResponse:
    """解析后的响应"""
    success: bool
    content: str
    raw_data: str
    error: Optional[str] = None


class CommandResponseHandler:
    """命令响应处理器"""

    def __init__(self, config: ResponseHandlingConfig):
        self.config = config
        # 预编译标记查找，提升性能
        self.start_marker = config.response_start_marker
        self.end_marker = config.response_end_marker
        self.start_marker_len = len(self.start_marker)

    async def read_response(self, connection: SerialConnectionManager) -> str:
        """异步读取设备响应"""
        try:
            raw_response = ""
            start_time = time.time()
            timeout_sec = self.config.command_timeout_ms / 1000.0

            # 初始等待响应开始
            await asyncio.sleep(self.config.response_wait_ms / 1000.0)

            while (time.time() - start_time) < timeout_sec:
                # 一次性读取所有可用数据而不是固定大小
                if connection.bytes_available() > 0:
                    available_bytes = connection.bytes_available()
                    data = await connection.read_data(available_bytes)

                    try:
                        new_data = data.decode('utf-8', errors='ignore')
                    except UnicodeDecodeError:
                        continue

                    raw_response += new_data

                    # 使用预编译的标记进行查找，提升性能
                    start_pos = raw_response.find(self.start_marker)
                    if start_pos != -1:
                        end_pos = raw_response.find(self.end_marker, start_pos)
                        if end_pos != -1:
                            # 找到完整响应，立即返回
                            content_start = start_pos + self.start_marker_len
                            content = raw_response[content_start:end_pos]
                            return content.strip()

                # 减少等待时间，提高响应性
                await asyncio.sleep(0.01)  # 10ms而不是配置中的值

            # 超时处理
            if raw_response.strip():
                # 如果有原始数据但没有完整标记，返回警告
                return f"警告: 找不到完整的响应标记。\n接收到的原始数据: {self._format_raw_response(raw_response)}"
            else:
                raise CommandTimeoutError(f"命令执行超时 ({timeout_sec}秒)")

        except CommandTimeoutError:
            raise
        except Exception as e:
            raise ResponseParseError(f"响应解析错误: {str(e)}")

    def _extract_response_content(self, raw_response: str) -> str:
        """提取响应标记之间的内容（优化版本）"""
        try:
            # 使用预编译的标记
            start_pos = raw_response.find(self.start_marker)
            if start_pos == -1:
                raise ResponseParseError("找不到开始标记")

            end_pos = raw_response.find(self.end_marker, start_pos)
            if end_pos == -1:
                raise ResponseParseError("找不到结束标记")

            content_start = start_pos + self.start_marker_len
            content = raw_response[content_start:end_pos]
            return content.strip()

        except Exception as e:
            raise ResponseParseError(f"提取响应内容失败: {str(e)}")

    def _format_raw_response(self, raw_response: str) -> str:
        """格式化原始响应以便显示"""
        # 替换换行符以便在终端中显示
        formatted = raw_response.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
        # 限制长度避免输出过长
        if len(formatted) > 200:
            formatted = formatted[:200] + "...(截断)"
        return formatted

    def validate_response_markers(self, response: str) -> bool:
        """验证响应标记完整性"""
        has_start = self.config.response_start_marker in response
        has_end = self.config.response_end_marker in response
        return has_start and has_end

    async def read_with_markers(self, connection: SerialConnectionManager,
                               require_markers: bool = True) -> ParsedResponse:
        """读取响应并解析，支持标记验证"""
        try:
            # 等待响应开始
            if not await connection.wait_for_data(self.config.no_data_timeout_ms):
                return ParsedResponse(
                    success=False,
                    content="",
                    raw_data="",
                    error="无数据响应"
                )

            # 读取完整响应
            raw_response = ""
            start_time = time.time()
            timeout_sec = self.config.command_timeout_ms / 1000.0

            while (time.time() - start_time) < timeout_sec:
                if connection.bytes_available() > 0:
                    data = await connection.read_data(1024)
                    try:
                        new_data = data.decode('utf-8', errors='ignore')
                        raw_response += new_data
                    except UnicodeDecodeError:
                        continue

                    # 检查是否有结束标记
                    if self.config.response_end_marker in raw_response:
                        break

                await asyncio.sleep(self.config.data_read_interval_ms / 1000.0)

            # 验证响应
            if require_markers and not self.validate_response_markers(raw_response):
                return ParsedResponse(
                    success=False,
                    content=raw_response.strip(),
                    raw_data=raw_response,
                    error="响应标记不完整"
                )

            # 提取内容
            if self.validate_response_markers(raw_response):
                content = self._extract_response_content(raw_response)
                return ParsedResponse(
                    success=True,
                    content=content,
                    raw_data=raw_response
                )
            else:
                return ParsedResponse(
                    success=False,
                    content=raw_response.strip(),
                    raw_data=raw_response,
                    error="找不到响应标记"
                )

        except Exception as e:
            return ParsedResponse(
                success=False,
                content="",
                raw_data="",
                error=str(e)
            )

    def parse_command_output(self, output: str) -> ParsedResponse:
        """解析命令输出（同步版本，用于测试）"""
        try:
            if self.validate_response_markers(output):
                content = self._extract_response_content(output)
                return ParsedResponse(
                    success=True,
                    content=content,
                    raw_data=output
                )
            else:
                return ParsedResponse(
                    success=False,
                    content=output.strip(),
                    raw_data=output,
                    error="响应标记不完整"
                )
        except Exception as e:
            return ParsedResponse(
                success=False,
                content="",
                raw_data=output,
                error=str(e)
            )