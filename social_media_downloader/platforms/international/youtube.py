"""
YouTube下载器 - 基于 yt-dlp
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import yt_dlp


class YouTubeDownloader:
    """YouTube下载器"""

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
        """下载YouTube视频"""
        from ...core.downloader import DownloadResult

        try:
            ydl_opts = {
                "format": self._get_format(),
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
                    platform="youtube",
                    file_path=ydl.prepare_filename(info),
                    title=info.get("title"),
                    metadata={
                        "duration": info.get("duration"),
                        "view_count": info.get("view_count"),
                        "like_count": info.get("like_count"),
                        "uploader": info.get("uploader"),
                    },
                )
        except Exception as e:
            return DownloadResult(
                success=False, url=url, platform="youtube", error=str(e)
            )

    async def get_info(self, url: str) -> Dict[str, Any]:
        """获取视频信息"""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "proxy": self.proxy,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title"),
                "duration": info.get("duration"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "description": info.get("description"),
                "upload_date": info.get("upload_date"),
                "uploader": info.get("uploader"),
                "formats": [
                    {
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "resolution": f.get("resolution"),
                        "filesize": f.get("filesize"),
                    }
                    for f in info.get("formats", [])
                ],
            }

    def _get_format(self) -> str:
        """根据质量设置返回格式字符串"""
        quality_map = {
            "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "worst": "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst",
            "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
            "4k": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160][ext=mp4]",
        }
        return quality_map.get(self.quality, quality_map["best"])
