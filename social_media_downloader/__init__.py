# 社交媒体统一下载工具 - 核心模块
# 基于以下开源项目二次开发：
# - yt-dlp (国际平台通用)
# - instaloader (Instagram)
# - XHS-Downloader (小红书)
# - douyin-downloader (抖音)
# - bilibili-api-python (B站)
# - weibo-crawler (微博)
# - akshare (金融数据)

__version__ = "0.1.0"
__author__ = "Social Media Downloader Team"

from .core.downloader import Downloader
from .core.url_parser import URLParser

__all__ = ["Downloader", "URLParser"]
