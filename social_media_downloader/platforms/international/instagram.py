"""
Instagram下载器 - 基于 instaloader
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import instaloader


class InstagramDownloader:
    """Instagram下载器"""

    def __init__(
        self,
        output_dir: Path,
        proxy: Optional[str] = None,
        quality: str = "best",
    ):
        self.output_dir = output_dir
        self.proxy = proxy
        self.quality = quality
        self.loader = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern="",
            max_connection_attempts=3,
        )

    async def download(self, url: str, parsed=None):
        """下载Instagram内容"""
        from ...core.downloader import DownloadResult

        try:
            # 提取shortcode
            shortcode = self._extract_shortcode(url)
            if not shortcode:
                raise ValueError("无法提取Instagram shortcode")

            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

            # 下载到临时目录
            temp_dir = self.output_dir / "temp"
            temp_dir.mkdir(exist_ok=True)

            self.loader.download_post(post, target=str(temp_dir))

            # 找到下载的文件
            downloaded_files = list(temp_dir.glob(f"*{shortcode}*"))
            file_path = str(downloaded_files[0]) if downloaded_files else None

            return DownloadResult(
                success=True,
                url=url,
                platform="instagram",
                file_path=file_path,
                title=post.caption[:100] if post.caption else None,
                metadata={
                    "shortcode": shortcode,
                    "likes": post.likes,
                    "comments": post.comments,
                    "is_video": post.is_video,
                    "date": str(post.date),
                    "owner": post.owner_username,
                },
            )
        except Exception as e:
            return DownloadResult(
                success=False, url=url, platform="instagram", error=str(e)
            )

    def _extract_shortcode(self, url: str) -> Optional[str]:
        """从URL提取shortcode"""
        import re

        patterns = [
            r"instagram\.com/p/([A-Za-z0-9_-]+)",
            r"instagram\.com/reel/([A-Za-z0-9_-]+)",
            r"instagram\.com/tv/([A-Za-z0-9_-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def download_profile(self, username: str, max_posts: int = 50):
        """下载用户主页的所有帖子"""
        from ...core.downloader import DownloadResult

        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)

            posts = []
            for i, post in enumerate(profile.get_posts()):
                if i >= max_posts:
                    break
                self.loader.download_post(post, target=str(self.output_dir / username))
                posts.append(post.shortcode)

            return DownloadResult(
                success=True,
                url=f"https://instagram.com/{username}",
                platform="instagram",
                metadata={
                    "username": username,
                    "downloaded_posts": len(posts),
                    "post_shortcodes": posts,
                },
            )
        except Exception as e:
            return DownloadResult(
                success=False,
                url=f"https://instagram.com/{username}",
                platform="instagram",
                error=str(e),
            )
