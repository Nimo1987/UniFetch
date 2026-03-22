"""
国际平台Handler
- YouTube
- Twitter/X
- Facebook
- Instagram
- TikTok
"""

import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

import yt_dlp
import instaloader

from ..core.base_handler import BaseHandler
from ..models.content import Content, Platform, ContentType, Author, MediaFile


class YtDlpHandler(BaseHandler):
    """
    基于yt-dlp的通用Handler

    支持: YouTube, Twitter, Facebook, TikTok, Reddit等
    """

    def __init__(self, url: str, platform: Platform, **kwargs):
        super().__init__(url, **kwargs)
        self.platform = platform

    def _get_platform(self) -> Platform:
        return self.platform

    async def fetch(self) -> Content:
        """获取视频信息"""
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, self._extract_info)

        # 构建作者信息
        author = Author(
            id=info.get("uploader_id"),
            username=info.get("uploader"),
            nickname=info.get("uploader"),
        )

        # 构建媒体文件列表
        media_files = []
        for fmt in info.get("formats", []):
            if fmt.get("url"):
                media_files.append(
                    MediaFile(
                        url=fmt["url"],
                        type="video" if fmt.get("vcodec") != "none" else "audio",
                        quality=fmt.get("format_note"),
                        format=fmt.get("ext"),
                        width=fmt.get("width"),
                        height=fmt.get("height"),
                    )
                )

        # 判断内容类型
        content_type = ContentType.VIDEO
        if info.get("is_live"):
            content_type = ContentType.LIVE
        elif "/playlist" in self.url:
            content_type = ContentType.PLAYLIST

        self._content = self.create_content(
            content_type=content_type,
            id=info.get("id"),
            title=info.get("title"),
            description=info.get("description"),
            author=author,
            media_files=media_files,
            cover_url=info.get("thumbnail"),
            likes=info.get("like_count"),
            comments_count=info.get("comment_count"),
            views=info.get("view_count"),
            publish_time=self._parse_time(info.get("upload_date")),
            tags=info.get("tags", []),
            raw_data=info,
        )

        return self._content

    async def download(self, quality: str = "best") -> Path:
        """下载视频"""
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(
            None, lambda: self._download_video(quality)
        )
        return Path(filepath)

    def _extract_info(self) -> dict:
        """提取视频信息"""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "proxy": self.proxy,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(self.url, download=False)

    def _download_video(self, quality: str) -> str:
        """下载视频"""
        format_str = self._get_format_string(quality)

        ydl_opts = {
            "format": format_str,
            "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
            "proxy": self.proxy,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=True)
            return ydl.prepare_filename(info)

    def _get_format_string(self, quality: str) -> str:
        """根据质量设置返回格式字符串"""
        quality_map = {
            "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "worst": "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst",
            "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
            "4k": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]",
        }
        return quality_map.get(quality, quality_map["best"])

    def _parse_time(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析上传日期"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y%m%d")
        except (ValueError, TypeError):
            return None


class InstagramHandler(BaseHandler):
    """
    Instagram Handler - 基于 instaloader
    """

    def __init__(self, url: str, **kwargs):
        super().__init__(url, **kwargs)
        self.loader = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            max_connection_attempts=3,
        )

    def _get_platform(self) -> Platform:
        return Platform.INSTAGRAM

    async def fetch(self) -> Content:
        """获取Instagram内容"""
        loop = asyncio.get_event_loop()

        # 提取shortcode
        shortcode = self._extract_shortcode()
        if not shortcode:
            raise ValueError("无法提取Instagram shortcode")

        # 获取帖子信息
        post = await loop.run_in_executor(
            None,
            lambda: instaloader.Post.from_shortcode(self.loader.context, shortcode),
        )

        # 构建作者信息
        author = Author(
            username=post.owner_username,
            nickname=post.owner_username,
        )

        # 构建媒体文件
        media_files = []
        if post.is_video:
            media_files.append(
                MediaFile(
                    url=post.video_url,
                    type="video",
                    format="mp4",
                )
            )
        else:
            # 图片
            if post.typename == "GraphSidecar":
                # 图集
                for node in post.get_sidecar_nodes():
                    media_files.append(
                        MediaFile(
                            url=node.display_url,
                            type="image",
                            format="jpg",
                        )
                    )
            else:
                media_files.append(
                    MediaFile(
                        url=post.url,
                        type="image",
                        format="jpg",
                    )
                )

        # 判断内容类型
        content_type = ContentType.VIDEO if post.is_video else ContentType.IMAGE
        if post.typename == "GraphSidecar":
            content_type = ContentType.CAROUSEL

        self._content = self.create_content(
            content_type=content_type,
            id=shortcode,
            title=post.caption[:100] if post.caption else None,
            description=post.caption,
            author=author,
            media_files=media_files,
            cover_url=post.url if not post.is_video else None,
            likes=post.likes,
            comments_count=post.comments,
            publish_time=post.date,
            tags=self._extract_hashtags(post.caption),
            raw_data={"shortcode": shortcode, "typename": post.typename},
        )

        return self._content

    async def download(self, quality: str = "best") -> Path:
        """下载Instagram内容"""
        loop = asyncio.get_event_loop()

        shortcode = self._extract_shortcode()
        post = await loop.run_in_executor(
            None,
            lambda: instaloader.Post.from_shortcode(self.loader.context, shortcode),
        )

        # 下载到指定目录
        await loop.run_in_executor(
            None, lambda: self.loader.download_post(post, target=str(self.output_dir))
        )

        # 查找下载的文件
        files = list(self.output_dir.glob(f"*{shortcode}*"))
        return files[0] if files else self.output_dir

    def _extract_shortcode(self) -> Optional[str]:
        """从URL提取shortcode"""
        import re

        patterns = [
            r"instagram\.com/p/([A-Za-z0-9_-]+)",
            r"instagram\.com/reel/([A-Za-z0-9_-]+)",
            r"instagram\.com/tv/([A-Za-z0-9_-]+)",
            r"instagram\.com/stories/[a-zA-Z0-9_.]+/(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, self.url)
            if match:
                return match.group(1)
        return None

    def _extract_hashtags(self, text: Optional[str]) -> list:
        """提取话题标签"""
        if not text:
            return []
        import re

        return re.findall(r"#(\w+)", text)
