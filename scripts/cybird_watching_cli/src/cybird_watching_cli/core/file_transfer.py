"""
文件传输模块 - 通过串口上传/下载文件到SD卡
"""
import base64
import asyncio
from pathlib import Path
from typing import Optional
from .connection import SerialConnectionManager


class FileTransferError(Exception):
    """文件传输错误"""
    pass


class FileTransfer:
    """文件传输管理器"""

    def __init__(self, connection: SerialConnectionManager):
        self.connection = connection
        self.chunk_size = 768  # 768字节编码后1024字符

    async def upload_file(self, local_path: str, remote_path: str, 
                         progress_callback=None) -> bool:
        """
        上传文件到设备SD卡
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程SD卡路径
            progress_callback: 进度回调函数 (current, total) -> None
            
        Returns:
            bool: 上传是否成功
        """
        if not self.connection.is_connected:
            raise FileTransferError("设备未连接")

        local_file = Path(local_path)
        if not local_file.exists():
            raise FileTransferError(f"本地文件不存在: {local_path}")

        if not local_file.is_file():
            raise FileTransferError(f"不是一个文件: {local_path}")

        file_size = local_file.stat().st_size
        print(f"准备上传文件: {local_path}")
        print(f"目标路径: {remote_path}")
        print(f"文件大小: {file_size} 字节 ({file_size / 1024:.2f} KB)")

        # 发送上传命令
        command = f"file upload {remote_path}"
        await self.connection.send_command(command)

        # 等待READY信号
        ready_received = False
        timeout = asyncio.get_event_loop().time() + 10
        response_buffer = ""

        while asyncio.get_event_loop().time() < timeout:
            if self.connection.bytes_available() > 0:
                data = await self.connection.read_data()
                response_buffer += data.decode('utf-8', errors='ignore')
                
                # 按行处理
                lines = response_buffer.split('\n')
                response_buffer = lines[-1]  # 保留不完整的行
                
                for line in lines[:-1]:
                    line = line.strip()
                    if line and "READY" in line:
                        ready_received = True
                        print("设备已就绪，开始传输...")
                        break
                
                if ready_received:
                    break
            await asyncio.sleep(0.01)

        if not ready_received:
            raise FileTransferError("等待设备READY信号超时")

        # 发送文件大小
        await self.connection.send_command(f"FILE_SIZE:{file_size}")
        await asyncio.sleep(0.1)

        # 读取文件并编码发送
        try:
            with open(local_path, 'rb') as f:
                total_sent = 0
                
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break

                    # Base64编码
                    encoded = base64.b64encode(chunk).decode('ascii')
                    await self.connection.send_command(encoded)
                    
                    total_sent += len(chunk)
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(total_sent, file_size)
                    
                    # 显示进度
                    if total_sent % (self.chunk_size * 10) == 0 or total_sent == file_size:
                        percent = (total_sent / file_size) * 100
                        print(f"进度: {total_sent}/{file_size} 字节 ({percent:.1f}%)")
                    
                    # 短暂延迟避免缓冲区溢出
                    await asyncio.sleep(0.01)

                # 发送结束标记
                await self.connection.send_command("FILE_END")
                print("数据传输完成，等待设备确认...")

                # 等待成功确认
                success = False
                timeout = asyncio.get_event_loop().time() + 30
                response_buffer = ""

                while asyncio.get_event_loop().time() < timeout:
                    if self.connection.bytes_available() > 0:
                        data = await self.connection.read_data()
                        response_buffer += data.decode('utf-8', errors='ignore')
                        
                        # 按行处理
                        lines = response_buffer.split('\n')
                        response_buffer = lines[-1]
                        
                        for line in lines[:-1]:
                            line = line.strip()
                            if line:
                                print(f"设备响应: {line}")
                                if "SUCCESS" in line:
                                    success = True
                                    break
                                elif "ERROR" in line:
                                    raise FileTransferError(f"上传失败: {line}")
                        
                        if success:
                            break
                    await asyncio.sleep(0.1)

                if success:
                    print(f"✓ 文件上传成功!")
                    return True
                else:
                    raise FileTransferError("等待设备确认超时")

        except Exception as e:
            raise FileTransferError(f"文件上传失败: {str(e)}")

    async def download_file(self, remote_path: str, local_path: str,
                           progress_callback=None) -> bool:
        """
        从设备SD卡下载文件
        
        Args:
            remote_path: 远程SD卡路径
            local_path: 本地保存路径
            progress_callback: 进度回调函数 (current, total) -> None
            
        Returns:
            bool: 下载是否成功
        """
        if not self.connection.is_connected:
            raise FileTransferError("设备未连接")

        print(f"准备下载文件: {remote_path}")
        print(f"保存到: {local_path}")

        # 确保本地目录存在
        local_file = Path(local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)

        # 发送下载命令
        command = f"file download {remote_path}"
        await self.connection.send_command(command)

        # 等待FILE_START
        file_size = 0
        start_received = False
        timeout = asyncio.get_event_loop().time() + 10
        response_buffer = ""

        while asyncio.get_event_loop().time() < timeout:
            if self.connection.bytes_available() > 0:
                data = await self.connection.read_data()
                response_buffer += data.decode('utf-8', errors='ignore')
                
                # 按行处理
                lines = response_buffer.split('\n')
                response_buffer = lines[-1]
                
                for line in lines[:-1]:
                    line = line.strip()
                    if line and line.startswith("FILE_START:"):
                        parts = line.split(':')
                        if len(parts) >= 3:
                            file_size = int(parts[2])
                            start_received = True
                            print(f"文件大小: {file_size} 字节 ({file_size / 1024:.2f} KB)")
                            print("开始接收数据...")
                            break
                    elif line and "ERROR" in line:
                        raise FileTransferError(f"下载失败: {line}")
                
                if start_received:
                    break
            await asyncio.sleep(0.01)

        if not start_received:
            raise FileTransferError("等待FILE_START超时")

        # 接收并解码数据
        try:
            with open(local_path, 'wb') as f:
                total_received = 0
                timeout = asyncio.get_event_loop().time() + 120
                response_buffer = ""

                while asyncio.get_event_loop().time() < timeout:
                    if self.connection.bytes_available() > 0:
                        data = await self.connection.read_data()
                        response_buffer += data.decode('utf-8', errors='ignore')
                        
                        # 按行处理
                        lines = response_buffer.split('\n')
                        response_buffer = lines[-1]
                        
                        for line in lines[:-1]:
                            line = line.strip()
                            
                            if not line:
                                continue

                            if line == "FILE_END":
                                print("接收完成标记")
                                break

                            if line.startswith("PROGRESS:"):
                                # 进度信息，跳过
                                continue

                            if line.startswith("SUCCESS:"):
                                print(f"设备确认: {line}")
                                continue

                            # Base64数据
                            try:
                                decoded = base64.b64decode(line)
                                f.write(decoded)
                                total_received += len(decoded)
                                
                                # 调用进度回调
                                if progress_callback:
                                    progress_callback(total_received, file_size)
                                
                                # 显示进度
                                if total_received % (self.chunk_size * 10) == 0 or total_received == file_size:
                                    percent = (total_received / file_size) * 100 if file_size > 0 else 0
                                    print(f"进度: {total_received}/{file_size} 字节 ({percent:.1f}%)")
                                
                                # 重置超时
                                timeout = asyncio.get_event_loop().time() + 120
                                
                            except Exception as e:
                                print(f"警告: 解码数据失败: {e}")
                                continue

                    await asyncio.sleep(0.001)

                if total_received > 0:
                    print(f"✓ 文件下载成功! 总计 {total_received} 字节")
                    return True
                else:
                    raise FileTransferError("未接收到任何数据")

        except Exception as e:
            # 删除不完整的文件
            if Path(local_path).exists():
                Path(local_path).unlink()
            raise FileTransferError(f"文件下载失败: {str(e)}")

    async def delete_file(self, remote_path: str) -> bool:
        """
        删除设备SD卡上的文件
        
        Args:
            remote_path: 远程SD卡路径
            
        Returns:
            bool: 删除是否成功
        """
        if not self.connection.is_connected:
            raise FileTransferError("设备未连接")

        command = f"file delete {remote_path}"
        await self.connection.send_command(command)

        # 等待响应
        success = False
        timeout = asyncio.get_event_loop().time() + 5
        response_buffer = ""

        while asyncio.get_event_loop().time() < timeout:
            if self.connection.bytes_available() > 0:
                data = await self.connection.read_data()
                response_buffer += data.decode('utf-8', errors='ignore')
                
                # 按行处理
                lines = response_buffer.split('\n')
                response_buffer = lines[-1]
                
                for line in lines[:-1]:
                    line = line.strip()
                    if line:
                        print(f"设备响应: {line}")
                        if "SUCCESS" in line:
                            success = True
                            break
                        elif "ERROR" in line:
                            raise FileTransferError(f"删除失败: {line}")
                
                if success:
                    break
            await asyncio.sleep(0.01)

        return success

    async def get_file_info(self, remote_path: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            remote_path: 远程SD卡路径
            
        Returns:
            dict: 文件信息字典
        """
        if not self.connection.is_connected:
            raise FileTransferError("设备未连接")

        command = f"file info {remote_path}"
        await self.connection.send_command(command)

        # 等待响应并解析
        info = {}
        timeout = asyncio.get_event_loop().time() + 5
        response_buffer = ""
        all_lines = []

        while asyncio.get_event_loop().time() < timeout:
            if self.connection.bytes_available() > 0:
                data = await self.connection.read_data()
                response_buffer += data.decode('utf-8', errors='ignore')
                
                # 按行处理
                lines = response_buffer.split('\n')
                response_buffer = lines[-1]
                
                for line in lines[:-1]:
                    line = line.strip()
                    if line:
                        all_lines.append(line)
                        if "ERROR" in line:
                            raise FileTransferError(f"获取文件信息失败: {line}")
                        if "===" in line and len(all_lines) > 2:
                            # 结束标记
                            break
                
                if all_lines and "===" in all_lines[-1]:
                    break
            await asyncio.sleep(0.01)

        # 简单解析
        for line in all_lines:
            print(line)
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    info[key] = value

        return info if info else None
