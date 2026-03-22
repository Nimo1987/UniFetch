"""
Handler基类 - 所有平台Handler的父类
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from ..models.content import (
    Content,
    Platform,
    ContentType,
    Author,
    MediaFile,
    FetchResult,
)


class BaseHandler(ABC):
    """
    平台处理器基类

    所有平台的Handler都需要继承这个类并实现抽象方法
    """

    def __init__(
        self,
        url: str,
        proxy: Optional[str] = None,
        cookie: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ):
        """
        初始化Handler

        Args:
            url: 内容URL
            proxy: 代理地址
            cookie: 平台Cookie
            output_dir: 下载目录
        """
        self.url = url
        self.proxy = proxy
        self.cookie = cookie
        self.output_dir = output_dir or Path("./downloads")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 解析结果缓存
        self._content: Optional[Content] = None

    @abstractmethod
    async def fetch(self) -> Content:
        """
        获取内容信息

        Returns:
            Content: 内容对象
        """
        pass

    @abstractmethod
    async def download(self, quality: str = "best") -> Path:
        """
        下载内容

        Args:
            quality: 下载质量 (best, worst, 720p, 1080p, etc.)

        Returns:
            Path: 下载文件路径
        """
        pass

    async def get_info(self) -> Content:
        """
        获取内容信息（如果已缓存则直接返回）

        Returns:
            Content: 内容对象
        """
        if self._content is None:
            self._content = await self.fetch()
        return self._content

    def create_content(
        self,
        content_type: ContentType,
        id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        author: Optional[Author] = None,
        media_files: list = None,
        cover_url: Optional[str] = None,
        likes: Optional[int] = None,
        comments_count: Optional[int] = None,
        shares: Optional[int] = None,
        views: Optional[int] = None,
        publish_time: Optional[datetime] = None,
        tags: list = None,
        raw_data: dict = None,
    ) -> Content:
        """
        创建Content对象的辅助方法
        """
        return Content(
            url=self.url,
            platform=self._get_platform(),
            content_type=content_type,
            id=id,
            title=title,
            description=description,
            author=author,
            media_files=media_files or [],
            cover_url=cover_url,
            likes=likes,
            comments_count=comments_count,
            shares=shares,
            views=views,
            publish_time=publish_time,
            fetch_time=datetime.now(),
            tags=tags or [],
            raw_data=raw_data or {},
        )

    @abstractmethod
    def _get_platform(self) -> Platform:
        """返回平台类型"""
        pass
