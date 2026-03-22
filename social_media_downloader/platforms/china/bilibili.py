"""
B站下载器
基于 bilibili-api-python
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

from bilibili_api import video, Credential, HEADERS
import httpx


class BilibiliDownloader:
    """
    B站下载器

    功能：
    - 下载视频
    - 获取视频信息
    - 支持多种清晰度
    - 支持弹幕下载
    """

    def __init__(
        self,
        output_dir: Path,
        proxy: Optional[str] = None,
        quality: str = "best",
        credential: Optional[Credential] = None,
    ):
        self.output_dir = output_dir
        self.proxy = proxy
        self.quality = quality
        self.credential = credential or Credential()

    async def download(self, url: str, parsed=None):
        """下载B站视频"""
        from ...core.downloader import DownloadResult

        try:
            bvid = self._extract_bvid(url)
            if not bvid:
                raise ValueError("无法提取BV号")

            # 创建视频对象
            v = video.Video(bvid=bvid, credential=self.credential)

            # 获取视频信息
            info = await v.get_info()

            # 获取下载链接
            download_url = await self._get_download_url(v, info)

            # 下载视频
            file_path = await self._download_video(download_url, info)

            return DownloadResult(
                success=True,
                url=url,
                platform="bilibili",
                file_path=str(file_path),
                title=info.get("title"),
                metadata={
                    "bvid": bvid,
                    "aid": info.get("aid"),
                    "cid": info.get("cid"),
                    "duration": info.get("duration"),
                    "view": info.get("stat", {}).get("view"),
                    "like": info.get("stat", {}).get("like"),
                    "coin": info.get("stat", {}).get("coin"),
                    "owner": info.get("owner", {}).get("name"),
                },
            )
        except Exception as e:
            return DownloadResult(
                success=False, url=url, platform="bilibili", error=str(e)
            )

    def _extract_bvid(self, url: str) -> Optional[str]:
        """从URL提取BV号"""
        import re

        patterns = [
            r"video/(BV[a-zA-Z0-9]+)",
            r"b23\.tv/([a-zA-Z0-9]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def _get_download_url(self, v: video.Video, info: Dict) -> str:
        """获取下载链接"""
        # 获取播放信息
        play_url = await v.get_playurl()

        # 根据质量选择视频流
        quality_id = self._get_quality_id(info)

        for dash in play_url.get("dash", {}).get("video", []):
            if dash.get("id") == quality_id:
                return dash.get("baseUrl", dash.get("base_url"))

        # 如果找不到指定质量，返回最高质量
        return play_url["dash"]["video"][0]["baseUrl"]

    def _get_quality_id(self, info: Dict) -> int:
        """根据质量设置返回清晰度ID"""
        quality_map = {
            "best": 127,  # 8K
            "4k": 120,  # 4K
            "1080p": 80,  # 1080P
            "720p": 64,  # 720P
            "480p": 32,  # 480P
            "360p": 16,  # 360P
        }
        return quality_map.get(self.quality, 80)

    async def _download_video(self, url: str, info: Dict) -> Path:
        """下载视频"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=HEADERS)

            bvid = info.get("bvid", "video")
            file_path = self.output_dir / f"{bvid}.mp4"
            file_path.write_bytes(response.content)

        return file_path
