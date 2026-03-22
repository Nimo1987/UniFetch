"""
小红书下载器
基于 XHS-Downloader 的核心逻辑
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import httpx


class XHSDownloader:
    """
    小红书下载器

    功能：
    - 下载图文笔记
    - 下载视频笔记
    - 获取笔记信息
    - 批量下载
    """

    def __init__(
        self,
        output_dir: Path,
        proxy: Optional[str] = None,
        quality: str = "best",
        cookie: Optional[str] = None,
    ):
        self.output_dir = output_dir
        self.proxy = proxy
        self.quality = quality
        self.cookie = cookie
        self.client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self.client is None or self.client.is_closed:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.xiaohongshu.com/",
            }
            if self.cookie:
                headers["Cookie"] = self.cookie

            self.client = httpx.AsyncClient(
                headers=headers,
                proxy=self.proxy,
                follow_redirects=True,
                timeout=30.0,
            )
        return self.client

    async def download(self, url: str, parsed=None):
        """下载小红书内容"""
        from ...core.downloader import DownloadResult

        try:
            note_id = self._extract_note_id(url)
            if not note_id:
                raise ValueError("无法提取笔记ID")

            # 获取笔记信息
            note_info = await self._get_note_info(note_id)

            # 下载媒体文件
            downloaded_files = []
            if note_info.get("type") == "video":
                file_path = await self._download_video(note_info)
                downloaded_files.append(file_path)
            else:
                for i, image_url in enumerate(note_info.get("images", [])):
                    file_path = await self._download_image(image_url, note_id, i)
                    downloaded_files.append(file_path)

            return DownloadResult(
                success=True,
                url=url,
                platform="xiaohongshu",
                file_path=str(downloaded_files[0]) if downloaded_files else None,
                title=note_info.get("title"),
                metadata={
                    "note_id": note_id,
                    "type": note_info.get("type"),
                    "author": note_info.get("author"),
                    "likes": note_info.get("likes"),
                    "downloaded_files": [str(f) for f in downloaded_files],
                },
            )
        except Exception as e:
            return DownloadResult(
                success=False, url=url, platform="xiaohongshu", error=str(e)
            )

    def _extract_note_id(self, url: str) -> Optional[str]:
        """从URL提取笔记ID"""
        import re

        patterns = [
            r"explore/([a-f0-9]+)",
            r"item/([a-f0-9]+)",
            r"xhslink\.com/([A-Za-z0-9]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def _get_note_info(self, note_id: str) -> Dict[str, Any]:
        """获取笔记信息"""
        client = await self._get_client()

        # 这里需要实现具体的API调用逻辑
        # 可以参考 XHS-Downloader 的实现

        return {
            "note_id": note_id,
            "title": "Note Title",
            "type": "image",
            "images": [],
            "author": "Author",
            "likes": 0,
        }

    async def _download_video(self, note_info: Dict) -> Path:
        """下载视频"""
        video_url = note_info.get("video_url")
        if not video_url:
            raise ValueError("无视频URL")

        client = await self._get_client()
        response = await client.get(video_url)

        file_path = self.output_dir / f"{note_info['note_id']}.mp4"
        file_path.write_bytes(response.content)

        return file_path

    async def _download_image(self, image_url: str, note_id: str, index: int) -> Path:
        """下载图片"""
        client = await self._get_client()
        response = await client.get(image_url)

        file_path = self.output_dir / f"{note_id}_{index}.jpg"
        file_path.write_bytes(response.content)

        return file_path

    async def close(self):
        """关闭客户端"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
