"""
配置管理模块
"""
from dataclasses import dataclass, field
from typing import Optional
import yaml
from pathlib import Path


@dataclass
class SerialConnectionConfig:
    """串口连接配置"""
    port: str = "COM3"
    baudrate: int = 115200
    timeout: float = 3.0
    write_timeout: float = 3.0


@dataclass
class ResponseHandlingConfig:
    """响应处理配置"""
    response_start_marker: str = "<<<RESPONSE_START>>>"
    response_end_marker: str = "<<<RESPONSE_END>>>"
    command_timeout_ms: int = 6000
    response_wait_ms: int = 300
    data_read_interval_ms: int = 50
    no_data_timeout_ms: int = 800


@dataclass
class UIConfig:
    """用户界面配置"""
    enable_colors: bool = True
    prompt_template: str = "{status} CybirdWatching> "


@dataclass
class CybirdWatchingConfig:
    """主配置类"""
    serial: SerialConnectionConfig = field(default_factory=SerialConnectionConfig)
    response: ResponseHandlingConfig = field(default_factory=ResponseHandlingConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    log_level: str = "INFO"

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'CybirdWatchingConfig':
        """从字典创建配置对象"""
        serial_config = SerialConnectionConfig(**config_dict.get('serial', {}))
        response_config = ResponseHandlingConfig(**config_dict.get('response', {}))
        ui_config = UIConfig(**config_dict.get('ui', {}))

        return cls(
            serial=serial_config,
            response=response_config,
            ui=ui_config,
            log_level=config_dict.get('log_level', 'INFO')
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'serial': {
                'port': self.serial.port,
                'baudrate': self.serial.baudrate,
                'timeout': self.serial.timeout,
                'write_timeout': self.serial.write_timeout
            },
            'response': {
                'response_start_marker': self.response.response_start_marker,
                'response_end_marker': self.response.response_end_marker,
                'command_timeout_ms': self.response.command_timeout_ms,
                'response_wait_ms': self.response.response_wait_ms,
                'data_read_interval_ms': self.response.data_read_interval_ms,
                'no_data_timeout_ms': self.response.no_data_timeout_ms
            },
            'ui': {
                'enable_colors': self.ui.enable_colors,
                'prompt_template': self.ui.prompt_template
            },
            'log_level': self.log_level
        }


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            # 相对于当前脚本的config目录
            self.config_dir = Path(__file__).parent.parent.parent.parent / "config"
        else:
            self.config_dir = config_dir

        self.default_config_path = self.config_dir / "default.yaml"
        self.user_config_path = self.config_dir / "user.yaml"

    def load_config(self) -> CybirdWatchingConfig:
        """加载配置文件"""
        default_config = self._load_yaml(self.default_config_path)
        user_config = self._load_yaml(self.user_config_path)

        # 合并配置，用户配置覆盖默认配置
        merged_config = self._merge_configs(default_config, user_config)
        return CybirdWatchingConfig.from_dict(merged_config)

    def save_default_config(self, config: CybirdWatchingConfig) -> None:
        """保存默认配置到文件"""
        config_dict = config.to_dict()
        self._save_yaml(self.default_config_path, config_dict)

    def _load_yaml(self, file_path: Path) -> dict:
        """加载YAML文件"""
        if not file_path.exists():
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"警告: 无法加载配置文件 {file_path}: {e}")
            return {}

    def _save_yaml(self, file_path: Path, data: dict) -> None:
        """保存数据到YAML文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"错误: 无法保存配置文件 {file_path}: {e}")

    def _merge_configs(self, default: dict, user: dict) -> dict:
        """合并配置，用户配置覆盖默认配置"""
        merged = default.copy()

        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged