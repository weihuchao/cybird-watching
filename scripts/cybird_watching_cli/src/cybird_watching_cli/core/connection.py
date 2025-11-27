"""
串口连接管理模块
"""
import asyncio
import serial
import serial.tools.list_ports
from typing import Optional, List
import time

from ..config.settings import SerialConnectionConfig
from ..utils.exceptions import ConnectionError, DeviceNotFoundError, PortAccessError, CommandTimeoutError


class SerialConnectionManager:
    """串口连接管理器 - 跨平台支持"""

    def __init__(self, config: SerialConnectionConfig):
        self.config = config
        self.port: Optional[serial.Serial] = None
        self.is_connected = False

    async def connect(self) -> bool:
        """异步连接串口设备"""
        try:
            if self.port and self.port.is_open:
                self.disconnect()

            # 检查端口是否可用
            if not self._is_port_available(self.config.port):
                available_ports = await self.list_available_ports()
                raise DeviceNotFoundError(
                    f"端口 {self.config.port} 不可用。可用端口: {', '.join(available_ports)}"
                )

            # 创建串口连接
            self.port = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                timeout=self.config.timeout,
                write_timeout=self.config.write_timeout
            )

            # 等待连接稳定
            await asyncio.sleep(0.1)

            if self.port.is_open:
                self.is_connected = True
                return True
            else:
                raise ConnectionError(f"无法打开端口 {self.config.port}")

        except serial.SerialException as e:
            self.is_connected = False
            raise PortAccessError(f"串口访问错误: {str(e)}")
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"连接失败: {str(e)}")

    def disconnect(self) -> None:
        """断开连接"""
        try:
            if self.port and self.port.is_open:
                self.port.close()
            self.is_connected = False
        except Exception as e:
            # 忽略断开连接时的异常
            print(f"断开连接时出现警告: {e}")

    def clear_buffers(self) -> None:
        """清空缓冲区"""
        if self.port and self.port.is_open:
            try:
                self.port.reset_input_buffer()
                self.port.reset_output_buffer()
            except Exception as e:
                print(f"清空缓冲区时出现警告: {e}")

    async def send_command(self, command: str) -> None:
        """发送命令到设备"""
        if not self.is_connected or not self.port or not self.port.is_open:
            raise ConnectionError("设备未连接")

        try:
            # 确保命令以正确的结尾发送
            if not command.endswith('\r\n'):
                command += '\r\n'

            # 清空输入缓冲区以避免读取旧数据
            self.clear_buffers()

            # 发送命令
            self.port.write(command.encode('utf-8'))
            self.port.flush()

        except serial.SerialTimeoutError:
            raise CommandTimeoutError("发送命令超时")
        except serial.SerialException as e:
            raise ConnectionError(f"串口通信错误: {str(e)}")
        except Exception as e:
            raise ConnectionError(f"发送命令失败: {str(e)}")

    async def read_data(self, size: int = 1024) -> bytes:
        """读取串口数据（优化版本）"""
        if not self.is_connected or not self.port or not self.port.is_open:
            raise ConnectionError("设备未连接")

        try:
            # 如果请求读取所有可用数据，直接使用in_waiting
            if size == -1 or size > self.port.in_waiting:
                size = self.port.in_waiting

            return self.port.read(size)
        except serial.SerialException as e:
            raise ConnectionError(f"读取数据错误: {str(e)}")

    def bytes_available(self) -> int:
        """检查可用字节数"""
        if self.port and self.port.is_open:
            return self.port.in_waiting
        return 0

    async def list_available_ports(self) -> List[str]:
        """列出可用串口"""
        try:
            ports = serial.tools.list_ports.comports()
            return [port.device for port in ports]
        except Exception as e:
            print(f"获取串口列表时出错: {e}")
            return []

    def _is_port_available(self, port: str) -> bool:
        """检查端口是否可用"""
        try:
            available_ports = serial.tools.list_ports.comports()
            return any(port == p.device for p in available_ports)
        except Exception:
            # 如果无法获取端口列表，假设端口可用
            return True

    async def wait_for_data(self, timeout_ms: int = 1000) -> bool:
        """等待数据到达"""
        if not self.is_connected or not self.port or not self.port.is_open:
            return False

        start_time = time.time()
        timeout_sec = timeout_ms / 1000.0

        while time.time() - start_time < timeout_sec:
            if self.bytes_available() > 0:
                return True
            await asyncio.sleep(0.01)  # 10ms检查间隔

        return False

    def get_connection_info(self) -> dict:
        """获取连接信息"""
        info = {
            'port': self.config.port,
            'baudrate': self.config.baudrate,
            'is_connected': self.is_connected,
            'is_open': False
        }

        if self.port:
            info['is_open'] = self.port.is_open
            if self.port.is_open:
                info.update({
                    'cd': self.port.cd,
                    'dsr': self.port.dsr,
                    'cts': self.port.cts,
                    'ri': self.port.ri
                })

        return info