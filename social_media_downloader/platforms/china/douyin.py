"""
抖音下载器
基于 douyin-downloader 的核心逻辑
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import aiohttp


class DouyinDownloader:
    """
    抖音下载器

    功能：
    - 下载视频（无水印）
    - 下载图集
    - 下载音乐
    - 批量下载
    - 合集下载
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
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36",
                "Referer": "https://www.douyin.com/",
            }
            if self.cookie:
                headers["Cookie"] = self.cookie

            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(
                headers=headers,
                connector=connector,
            )
        return self.session

    async def download(self, url: str, parsed=None):
        """下载抖音内容"""
        from ...core.downloader import DownloadResult

        try:
            video_id = self._extract_video_id(url)
            if not video_id:
                # 尝试解析短链接
                url = await self._resolve_short_url(url)
                video_id = self._extract_video_id(url)

            if not video_id:
                raise ValueError("无法提取视频ID")

            # 获取视频信息
            video_info = await self._get_video_info(video_id)

            # 下载视频
            file_path = await self._download_video(video_info)

            return DownloadResult(
                success=True,
                url=url,
                platform="douyin",
                file_path=str(file_path),
                title=video_info.get("desc"),
                metadata={
                    "video_id": video_id,
                    "author": video_info.get("author"),
                    "likes": video_info.get("digg_count"),
                    "comments": video_info.get("comment_count"),
                    "shares": video_info.get("share_count"),
                },
            )
        except Exception as e:
            return DownloadResult(
                success=False, url=url, platform="douyin", error=str(e)
            )

    def _extract_video_id(self, url: str) -> Optional[str]:
        """从URL提取视频ID"""
        import re

        patterns = [
            r"video/(\d+)",
            r"modal_id=(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def _resolve_short_url(self, url: str) -> str:
        """解析短链接"""
        session = await self._get_session()
        async with session.get(url, allow_redirects=True) as response:
            return str(response.url)

    async def _get_video_info(self, video_id: str) -> Dict[str, Any]:
        """获取视频信息"""
        # 这里需要实现具体的API调用逻辑
        # 需要处理 a_bogus 和 X-Bogus 算法
        # 可以参考 douyin-downloader 的实现

        return {
            "video_id": video_id,
            "desc": "Video Description",
            "author": "Author",
            "video_url": "",
            "digg_count": 0,
            "comment_count": 0,
            "share_count": 0,
        }

    async def _download_video(self, video_info: Dict) -> Path:
        """下载视频（无水印）"""
        video_url = video_info.get("video_url")
        if not video_url:
            raise ValueError("无视频URL")

        session = await self._get_session()
        async with session.get(video_url) as response:
            content = await response.read()

        file_path = self.output_dir / f"{video_info['video_id']}.mp4"
        file_path.write_bytes(content)

        return file_path

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
