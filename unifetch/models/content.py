"""
统一数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class Platform(Enum):
    """支持的平台"""

    # 国际
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    REDDIT = "reddit"

    # 中国
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    BILIBILI = "bilibili"
    WEIBO = "weibo"
    WEIXIN = "weixin"

    # 金融
    FINANCE = "finance"

    UNKNOWN = "unknown"


class ContentType(Enum):
    """内容类型"""

    VIDEO = "video"
    IMAGE = "image"
    ARTICLE = "article"
    CAROUSEL = "carousel"  # 图集
    STORY = "story"
    REEL = "reel"
    LIVE = "live"
    USER_PROFILE = "user_profile"
    PLAYLIST = "playlist"
    COMMENT = "comment"
    UNKNOWN = "unknown"


@dataclass
class MediaFile:
    """媒体文件"""

    url: str
    type: str  # video, image, audio
    quality: Optional[str] = None  # 1080p, 720p, etc.
    format: Optional[str] = None  # mp4, jpg, mp3
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # 秒
    filesize: Optional[int] = None  # 字节


@dataclass
class Author:
    """作者信息"""

    id: Optional[str] = None
    username: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    followers: Optional[int] = None
    verified: bool = False
    bio: Optional[str] = None


@dataclass
class Content:
    """统一的内容模型"""

    # 基本信息
    url: str
    platform: Platform
    content_type: ContentType
    id: Optional[str] = None  # 平台内的内容ID

    # 标题和描述
    title: Optional[str] = None
    description: Optional[str] = None

    # 作者
    author: Optional[Author] = None

    # 媒体文件
    media_files: List[MediaFile] = field(default_factory=list)
    cover_url: Optional[str] = None

    # 统计数据
    likes: Optional[int] = None
    comments_count: Optional[int] = None
    shares: Optional[int] = None
    views: Optional[int] = None
    saves: Optional[int] = None

    # 时间
    publish_time: Optional[datetime] = None
    fetch_time: Optional[datetime] = None

    # 标签和话题
    tags: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)

    # 位置信息
    location: Optional[str] = None

    # 原始数据
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """LLM分析结果"""

    # 内容摘要
    summary: str = ""

    # 情感分析
    sentiment: str = ""  # positive, negative, neutral
    sentiment_score: float = 0.0

    # 话题和关键词
    topics: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    # 内容分析
    key_points: List[str] = field(default_factory=list)
    language: str = ""

    # 质量评估
    quality_score: float = 0.0  # 0-10
    content_rating: str = ""  # G, PG, etc.

    # 推荐
    recommendation: str = ""  # 推荐/不推荐
    recommendation_reason: str = ""

    # 分类
    category: str = ""  # 娱乐, 教育, 新闻, etc.
    subcategory: str = ""


@dataclass
class FetchResult:
    """获取结果"""

    success: bool
    content: Optional[Content] = None
    analysis: Optional[AnalysisResult] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
