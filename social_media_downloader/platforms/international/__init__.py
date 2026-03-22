"""
国际平台下载器
基于 yt-dlp 和 instaloader
"""

from .youtube import YouTubeDownloader
from .twitter import TwitterDownloader
from .facebook import FacebookDownloader
from .instagram import InstagramDownloader
from .tiktok import TikTokDownloader

__all__ = [
    "YouTubeDownloader",
    "TwitterDownloader",
    "FacebookDownloader",
    "InstagramDownloader",
    "TikTokDownloader",
]
