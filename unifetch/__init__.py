"""
UniFetch - 社交媒体统一下载工具

支持平台:
- 国际: YouTube, Twitter/X, Facebook, Instagram, TikTok, Reddit
- 中国: 小红书, 抖音, B站, 微博, 微信公众号
- 金融: A股, 港股, 美股

使用方式:
    from unifetch import Downloader

    dl = Downloader()
    result = await dl.analyze("https://www.youtube.com/watch?v=xxx")
    print(result.analysis.summary)

配置管理:
    from unifetch import ConfigManager, get_config, set_cookie

    # 设置Cookie
    set_cookie("xiaohongshu", "your_cookie_here")

    # 获取配置
    config = get_config()
    print(config.download.directory)
"""

__version__ = "1.0.0"

from .downloader import Downloader, analyze_url, download_url
from .core.router import URLRouter
from .core.config import (
    ConfigManager,
    AppConfig,
    get_config,
    save_config,
    set_cookie,
    get_cookie,
    get_download_dir,
)
from .models.content import (
    Content,
    AnalysisResult,
    FetchResult,
    Platform,
    ContentType,
    Author,
    MediaFile,
)

__all__ = [
    # 核心类
    "Downloader",
    "URLRouter",
    "ConfigManager",
    "AppConfig",
    # 便捷函数
    "analyze_url",
    "download_url",
    "get_config",
    "save_config",
    "set_cookie",
    "get_cookie",
    "get_download_dir",
    # 数据模型
    "Content",
    "AnalysisResult",
    "FetchResult",
    "Platform",
    "ContentType",
    "Author",
    "MediaFile",
]
