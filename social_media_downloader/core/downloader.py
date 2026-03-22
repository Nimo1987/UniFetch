"""
核心下载器 - 统一下载接口
"""

import asyncio
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

from .url_parser import URLParser, Platform, ParsedURL


@dataclass
class DownloadResult:
    """下载结果"""

    success: bool
    url: str
    platform: str
    file_path: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Downloader:
    """
    统一下载器

    支持平台：
    - 国际：YouTube, Twitter, Facebook, Instagram, TikTok, Reddit
    - 中国：小红书, 抖音, 微博, B站, 微信公众号
    - 金融：股票、期货、基金等数据
    """

    def __init__(
        self,
        output_dir: str = "./downloads",
        proxy: Optional[str] = None,
        cookie: Optional[Dict[str, str]] = None,
        quality: str = "best",
    ):
        """
        初始化下载器

        Args:
            output_dir: 下载目录
            proxy: 代理地址
            cookie: 各平台的Cookie
            quality: 视频质量 (best, worst, 720p, 1080p, etc.)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.proxy = proxy
        self.cookie = cookie or {}
        self.quality = quality
        self._platform_downloaders = {}

    async def download(self, url: str) -> DownloadResult:
        """
        下载内容（自动识别平台）

        Args:
            url: 社交媒体URL

        Returns:
            DownloadResult: 下载结果
        """
        parsed = URLParser.parse(url)

        if parsed.platform == Platform.UNKNOWN:
            return DownloadResult(
                success=False, url=url, platform="unknown", error=f"不支持的URL: {url}"
            )

        try:
            downloader = self._get_downloader(parsed.platform)
            result = await downloader.download(url, parsed)
            return result
        except Exception as e:
            return DownloadResult(
                success=False, url=url, platform=parsed.platform.value, error=str(e)
            )

    async def download_batch(self, urls: List[str]) -> List[DownloadResult]:
        """
        批量下载

        Args:
            urls: URL列表

        Returns:
            List[DownloadResult]: 下载结果列表
        """
        tasks = [self.download(url) for url in urls]
        return await asyncio.gather(*tasks)

    def _get_downloader(self, platform: Platform):
        """获取平台对应的下载器"""
        if platform not in self._platform_downloaders:
            self._platform_downloaders[platform] = self._create_downloader(platform)
        return self._platform_downloaders[platform]

    def _create_downloader(self, platform: Platform):
        """创建平台下载器"""
        from ..platforms.international import (
            YouTubeDownloader,
            TwitterDownloader,
            FacebookDownloader,
            InstagramDownloader,
            TikTokDownloader,
        )
        from ..platforms.china import (
            XHSDownloader,
            DouyinDownloader,
            WeiboDownloader,
            BilibiliDownloader,
        )

        downloaders = {
            # 国际平台
            Platform.YOUTUBE: YouTubeDownloader,
            Platform.TWITTER: TwitterDownloader,
            Platform.FACEBOOK: FacebookDownloader,
            Platform.INSTAGRAM: InstagramDownloader,
            Platform.TIKTOK: TikTokDownloader,
            # 中国平台
            Platform.XIAOHONGSHU: XHSDownloader,
            Platform.DOUYIN: DouyinDownloader,
            Platform.WEIBO: WeiboDownloader,
            Platform.BILIBILI: BilibiliDownloader,
        }

        downloader_class = downloaders.get(platform)
        if downloader_class:
            return downloader_class(
                output_dir=self.output_dir,
                proxy=self.proxy,
                quality=self.quality,
            )
        raise ValueError(f"未实现的平台下载器: {platform}")

    def get_info(self, url: str) -> Dict[str, Any]:
        """
        获取URL信息（不下载）

        Args:
            url: 社交媒体URL

        Returns:
            Dict: 内容信息
        """
        parsed = URLParser.parse(url)
        return {
            "url": url,
            "platform": parsed.platform.value,
            "video_id": parsed.video_id,
            "content_type": parsed.content_type,
            "supported": parsed.platform != Platform.UNKNOWN,
        }
