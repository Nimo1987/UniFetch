"""
中国平台下载器
基于 XHS-Downloader, douyin-downloader, bilibili-api-python, weibo-crawler
"""

from .xhs import XHSDownloader
from .douyin import DouyinDownloader
from .weibo import WeiboDownloader
from .bilibili import BilibiliDownloader

__all__ = [
    "XHSDownloader",
    "DouyinDownloader",
    "WeiboDownloader",
    "BilibiliDownloader",
]
