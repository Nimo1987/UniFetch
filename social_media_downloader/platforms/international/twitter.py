"""
Twitter/X下载器 - 基于 yt-dlp
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import yt_dlp


class TwitterDownloader:
    """Twitter/X下载器"""

    def __init__(
        self,
        output_dir: Path,
        proxy: Optional[str] = None,
        quality: str = "best",
    ):
        self.output_dir = output_dir
        self.proxy = proxy
        self.quality = quality

    async def download(self, url: str, parsed=None):
        """下载Twitter视频"""
        from ...core.downloader import DownloadResult

        try:
            ydl_opts = {
                "format": "best",
                "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
                "proxy": self.proxy,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                return DownloadResult(
                    success=True,
                    url=url,
                    platform="twitter",
                    file_path=ydl.prepare_filename(info),
                    title=info.get("title"),
                    metadata={
                        "uploader": info.get("uploader"),
                        "like_count": info.get("like_count"),
                        "repost_count": info.get("repost_count"),
                    },
                )
        except Exception as e:
            return DownloadResult(
                success=False, url=url, platform="twitter", error=str(e)
            )


class FacebookDownloader:
    """Facebook下载器 - 基于 yt-dlp"""

    def __init__(
        self,
        output_dir: Path,
        proxy: Optional[str] = None,
        quality: str = "best",
    ):
        self.output_dir = output_dir
        self.proxy = proxy
        self.quality = quality

    async def download(self, url: str, parsed=None):
        """下载Facebook视频"""
        from ...core.downloader import DownloadResult

        try:
            ydl_opts = {
                "format": "best",
                "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
                "proxy": self.proxy,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                return DownloadResult(
                    success=True,
                    url=url,
                    platform="facebook",
                    file_path=ydl.prepare_filename(info),
                    title=info.get("title"),
                    metadata={
                        "uploader": info.get("uploader"),
                        "view_count": info.get("view_count"),
                    },
                )
        except Exception as e:
            return DownloadResult(
                success=False, url=url, platform="facebook", error=str(e)
            )


class TikTokDownloader:
    """TikTok下载器 - 基于 yt-dlp"""

    def __init__(
        self,
        output_dir: Path,
        proxy: Optional[str] = None,
        quality: str = "best",
    ):
        self.output_dir = output_dir
        self.proxy = proxy
        self.quality = quality

    async def download(self, url: str, parsed=None):
        """下载TikTok视频"""
        from ...core.downloader import DownloadResult

        try:
            ydl_opts = {
                "format": "best",
                "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
                "proxy": self.proxy,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                return DownloadResult(
                    success=True,
                    url=url,
                    platform="tiktok",
                    file_path=ydl.prepare_filename(info),
                    title=info.get("title"),
                    metadata={
                        "uploader": info.get("uploader"),
                        "view_count": info.get("view_count"),
                        "like_count": info.get("like_count"),
                    },
                )
        except Exception as e:
            return DownloadResult(
                success=False, url=url, platform="tiktok", error=str(e)
            )
