"""
微博下载器
基于 weibo-crawler 的核心逻辑
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from lxml import etree


class WeiboDownloader:
    """
    微博下载器

    功能：
    - 下载微博图片
    - 下载微博视频
    - 获取微博信息
    - 批量下载用户微博
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

    def _get_session(self) -> requests.Session:
        """获取HTTP会话"""
        if self.session is None:
            self.session = requests.Session()
            self.session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://weibo.com/",
                }
            )
            if self.cookie:
                self.session.headers["Cookie"] = self.cookie
            if self.proxy:
                self.session.proxies = {"http": self.proxy, "https": self.proxy}
        return self.session

    async def download(self, url: str, parsed=None):
        """下载微博内容"""
        from ...core.downloader import DownloadResult

        try:
            # 解析URL获取微博ID
            weibo_id = self._extract_weibo_id(url)
            if not weibo_id:
                raise ValueError("无法提取微博ID")

            # 获取微博信息
            weibo_info = self._get_weibo_info(weibo_id)

            # 下载媒体文件
            downloaded_files = []

            # 下载图片
            for i, pic_url in enumerate(weibo_info.get("pics", [])):
                file_path = self._download_image(pic_url, weibo_id, i)
                downloaded_files.append(file_path)

            # 下载视频
            if weibo_info.get("video_url"):
                file_path = self._download_video(weibo_info["video_url"], weibo_id)
                downloaded_files.append(file_path)

            return DownloadResult(
                success=True,
                url=url,
                platform="weibo",
                file_path=str(downloaded_files[0]) if downloaded_files else None,
                title=weibo_info.get("text", "")[:100],
                metadata={
                    "weibo_id": weibo_id,
                    "author": weibo_info.get("author"),
                    "reposts": weibo_info.get("reposts_count"),
                    "comments": weibo_info.get("comments_count"),
                    "likes": weibo_info.get("attitudes_count"),
                    "downloaded_files": [str(f) for f in downloaded_files],
                },
            )
        except Exception as e:
            return DownloadResult(
                success=False, url=url, platform="weibo", error=str(e)
            )

    def _extract_weibo_id(self, url: str) -> Optional[str]:
        """从URL提取微博ID"""
        import re

        patterns = [
            r"weibo\.com/\d+/([a-zA-Z0-9]+)",
            r"weibo\.com/\d+/(\d+)",
            r"m\.weibo\.cn/detail/(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _get_weibo_info(self, weibo_id: str) -> Dict[str, Any]:
        """获取微博信息"""
        session = self._get_session()

        # 这里需要实现具体的API调用逻辑
        # 可以参考 weibo-crawler 的实现

        return {
            "weibo_id": weibo_id,
            "text": "Weibo content",
            "author": "Author",
            "pics": [],
            "video_url": None,
            "reposts_count": 0,
            "comments_count": 0,
            "attitudes_count": 0,
        }

    def _download_image(self, url: str, weibo_id: str, index: int) -> Path:
        """下载图片"""
        session = self._get_session()
        response = session.get(url)

        file_path = self.output_dir / f"{weibo_id}_{index}.jpg"
        file_path.write_bytes(response.content)

        return file_path

    def _download_video(self, url: str, weibo_id: str) -> Path:
        """下载视频"""
        session = self._get_session()
        response = session.get(url, stream=True)

        file_path = self.output_dir / f"{weibo_id}.mp4"
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return file_path
