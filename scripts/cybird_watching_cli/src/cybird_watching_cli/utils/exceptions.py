"""
自定义异常类
"""


class CybirdCLIError(Exception):
    """基础异常类"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ConnectionError(CybirdCLIError):
    """连接相关异常"""
    pass


class CommandTimeoutError(CybirdCLIError):
    """命令超时异常"""
    pass


class ResponseParseError(CybirdCLIError):
    """响应解析异常"""
    pass


class DeviceNotFoundError(ConnectionError):
    """设备未找到异常"""
    pass


class PortAccessError(ConnectionError):
    """端口访问异常"""
    pass


class InvalidCommandError(CybirdCLIError):
    """无效命令异常"""
    pass


class ConfigurationError(CybirdCLIError):
    """配置错误异常"""
    pass