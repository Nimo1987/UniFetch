"""
配置管理模块

管理Cookie、代理、下载目录等配置
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict


# 默认配置目录
DEFAULT_CONFIG_DIR = Path.home() / ".unifetch"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
DEFAULT_DOWNLOAD_DIR = Path.cwd() / "downloads"


@dataclass
class PlatformCookie:
    """平台Cookie配置"""

    xiaohongshu: Optional[str] = None
    douyin: Optional[str] = None
    bilibili: Optional[str] = None
    weibo: Optional[str] = None
    instagram: Optional[str] = None
    youtube: Optional[str] = None
    twitter: Optional[str] = None

    def get_cookie(self, platform: str) -> Optional[str]:
        """获取指定平台的Cookie"""
        return getattr(self, platform.lower(), None)

    def set_cookie(self, platform: str, cookie: str):
        """设置指定平台的Cookie"""
        if hasattr(self, platform.lower()):
            setattr(self, platform.lower(), cookie)


@dataclass
class ProxyConfig:
    """代理配置"""

    enabled: bool = False
    http: Optional[str] = None
    https: Optional[str] = None
    socks5: Optional[str] = None
    fallback: Optional[str] = None  # fallback 代理（直连失败后使用，如 spider-proxy）

    def get_proxy_url(self) -> Optional[str]:
        """获取代理URL"""
        if not self.enabled:
            return None
        return self.socks5 or self.https or self.http


@dataclass
class DownloadConfig:
    """下载配置"""

    directory: str = str(DEFAULT_DOWNLOAD_DIR)
    quality: str = "best"  # best, worst, 720p, 1080p
    max_concurrent: int = 3
    timeout: int = 30
    retry_count: int = 3
    skip_existing: bool = True
    organize_by_platform: bool = True


@dataclass
class LLMConfig:
    """LLM分析配置"""

    enabled: bool = False
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.7


@dataclass
class AppConfig:
    """应用配置"""

    cookies: PlatformCookie = field(default_factory=PlatformCookie)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """从字典创建配置"""
        config = cls()
        if "cookies" in data:
            config.cookies = PlatformCookie(**data["cookies"])
        if "proxy" in data:
            config.proxy = ProxyConfig(**data["proxy"])
        if "download" in data:
            config.download = DownloadConfig(**data["download"])
        if "llm" in data:
            config.llm = LLMConfig(**data["llm"])
        return config


class ConfigManager:
    """
    配置管理器

    使用方式:
        # 创建配置管理器
        config_mgr = ConfigManager()

        # 加载配置
        config = config_mgr.load()

        # 修改配置
        config.cookies.xiaohongshu = "your_cookie"

        # 保存配置
        config_mgr.save(config)
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为 ~/.unifetch/config.json
        """
        self.config_path = config_path or DEFAULT_CONFIG_FILE
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppConfig:
        """
        加载配置

        Returns:
            AppConfig: 应用配置对象
        """
        if not self.config_path.exists():
            return AppConfig()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AppConfig.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return AppConfig()

    def save(self, config: AppConfig):
        """
        保存配置

        Args:
            config: 应用配置对象
        """
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

    def update_cookie(self, platform: str, cookie: str):
        """
        更新指定平台的Cookie

        Args:
            platform: 平台名称
            cookie: Cookie字符串
        """
        config = self.load()
        config.cookies.set_cookie(platform, cookie)
        self.save(config)

    def get_cookie(self, platform: str) -> Optional[str]:
        """
        获取指定平台的Cookie

        Args:
            platform: 平台名称

        Returns:
            Optional[str]: Cookie字符串
        """
        config = self.load()
        return config.cookies.get_cookie(platform)

    def update_proxy(self, proxy_url: str, enabled: bool = True):
        """
        更新代理配置

        Args:
            proxy_url: 代理URL
            enabled: 是否启用代理
        """
        config = self.load()
        config.proxy.enabled = enabled

        if proxy_url.startswith("socks5://"):
            config.proxy.socks5 = proxy_url
        elif proxy_url.startswith("https://"):
            config.proxy.https = proxy_url
        else:
            config.proxy.http = proxy_url

        self.save(config)

    def update_download_dir(self, directory: str):
        """
        更新下载目录

        Args:
            directory: 下载目录路径
        """
        config = self.load()
        config.download.directory = directory
        self.save(config)

    def get_download_dir(self) -> Path:
        """
        获取下载目录

        Returns:
            Path: 下载目录路径
        """
        config = self.load()
        download_dir = Path(config.download.directory)
        download_dir.mkdir(parents=True, exist_ok=True)
        return download_dir

    def reset(self):
        """重置配置为默认值"""
        self.save(AppConfig())

    def export_config(self, export_path: Path):
        """
        导出配置到指定文件

        Args:
            export_path: 导出文件路径
        """
        config = self.load()
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

    def import_config(self, import_path: Path):
        """
        从指定文件导入配置

        Args:
            import_path: 导入文件路径
        """
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        config = AppConfig.from_dict(data)
        self.save(config)


# 便捷函数
def get_config() -> AppConfig:
    """获取应用配置"""
    return ConfigManager().load()


def save_config(config: AppConfig):
    """保存应用配置"""
    ConfigManager().save(config)


def get_cookie(platform: str) -> Optional[str]:
    """获取指定平台的Cookie"""
    return ConfigManager().get_cookie(platform)


def set_cookie(platform: str, cookie: str):
    """设置指定平台的Cookie"""
    ConfigManager().update_cookie(platform, cookie)


def get_download_dir() -> Path:
    """获取下载目录"""
    return ConfigManager().get_download_dir()


# 环境变量支持
def load_from_env() -> AppConfig:
    """从环境变量加载配置"""
    config = AppConfig()

    # Cookie
    config.cookies.xiaohongshu = os.environ.get("XHS_COOKIE")
    config.cookies.douyin = os.environ.get("DOUYIN_COOKIE")
    config.cookies.bilibili = os.environ.get("BILIBILI_COOKIE")
    config.cookies.weibo = os.environ.get("WEIBO_COOKIE")
    config.cookies.instagram = os.environ.get("INSTAGRAM_COOKIE")
    config.cookies.youtube = os.environ.get("YOUTUBE_COOKIE")
    config.cookies.twitter = os.environ.get("TWITTER_COOKIE")

    # Proxy
    proxy_url = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")
    if proxy_url:
        config.proxy.enabled = True
        config.proxy.http = proxy_url
        config.proxy.https = proxy_url

    # Download
    download_dir = os.environ.get("DOWNLOAD_DIR")
    if download_dir:
        config.download.directory = download_dir

    # LLM
    llm_url = os.environ.get("LLM_API_URL")
    llm_key = os.environ.get("LLM_API_KEY")
    if llm_url:
        config.llm.enabled = True
        config.llm.api_url = llm_url
    if llm_key:
        config.llm.api_key = llm_key

    return config


def merge_configs(base: AppConfig, override: AppConfig) -> AppConfig:
    """
    合并配置，override覆盖base中的非None值

    Args:
        base: 基础配置
        override: 覆盖配置

    Returns:
        AppConfig: 合并后的配置
    """
    result = AppConfig.from_dict(base.to_dict())

    # 合并Cookie
    for field_name in vars(override.cookies):
        value = getattr(override.cookies, field_name)
        if value is not None:
            setattr(result.cookies, field_name, value)

    # 合并Proxy
    if override.proxy.http:
        result.proxy.http = override.proxy.http
    if override.proxy.https:
        result.proxy.https = override.proxy.https
    if override.proxy.socks5:
        result.proxy.socks5 = override.proxy.socks5

    # 合并Download
    if override.download.directory != DEFAULT_DOWNLOAD_DIR:
        result.download.directory = override.download.directory

    return result
