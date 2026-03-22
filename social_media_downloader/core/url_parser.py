"""
URL解析器 - 自动识别社交媒体平台
"""

import re
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class Platform(Enum):
    """支持的平台枚举"""

    # 国际平台
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    REDDIT = "reddit"

    # 中国平台
    XIAOHONGSHU = "xiaohongshu"  # 小红书
    DOUYIN = "douyin"  # 抖音
    WEIBO = "weibo"  # 微博
    BILIBILI = "bilibili"  # B站
    WEIXIN = "weixin"  # 微信公众号

    # 金融数据
    FINANCE = "finance"

    # 未知
    UNKNOWN = "unknown"


# URL模式匹配规则
URL_PATTERNS = {
    # 国际平台
    Platform.YOUTUBE: [
        r"(?:youtube\.com|youtu\.be|youtube-nocookie\.com)",
    ],
    Platform.TWITTER: [
        r"(?:twitter\.com|x\.com|t\.co)",
    ],
    Platform.FACEBOOK: [
        r"(?:facebook\.com|fb\.watch|fb\.com)",
    ],
    Platform.INSTAGRAM: [
        r"(?:instagram\.com|instagr\.am)",
    ],
    Platform.TIKTOK: [
        r"(?:tiktok\.com|vm\.tiktok\.com)",
    ],
    Platform.REDDIT: [
        r"(?:reddit\.com|redd\.it)",
    ],
    # 中国平台
    Platform.XIAOHONGSHU: [
        r"(?:xiaohongshu\.com|xhslink\.com)",
    ],
    Platform.DOUYIN: [
        r"(?:douyin\.com|v\.douyin\.com)",
    ],
    Platform.WEIBO: [
        r"(?:weibo\.com|weibo\.cn|m\.weibo\.cn)",
    ],
    Platform.BILIBILI: [
        r"(?:bilibili\.com|b23\.tv)",
    ],
    Platform.WEIXIN: [
        r"(?:mp\.weixin\.qq\.com)",
    ],
}


@dataclass
class ParsedURL:
    """解析后的URL信息"""

    url: str
    platform: Platform
    video_id: Optional[str] = None
    user_id: Optional[str] = None
    content_type: Optional[str] = None  # video, image, article, etc.


class URLParser:
    """URL解析器"""

    @staticmethod
    def parse(url: str) -> ParsedURL:
        """
        解析URL，识别平台

        Args:
            url: 社交媒体URL

        Returns:
            ParsedURL: 解析结果
        """
        url = url.strip().lower()

        for platform, patterns in URL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url):
                    return ParsedURL(
                        url=url,
                        platform=platform,
                        video_id=URLParser._extract_id(url, platform),
                        content_type=URLParser._detect_content_type(url, platform),
                    )

        return ParsedURL(url=url, platform=Platform.UNKNOWN)

    @staticmethod
    def _extract_id(url: str, platform: Platform) -> Optional[str]:
        """提取内容ID"""
        patterns = {
            Platform.YOUTUBE: r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
            Platform.TWITTER: r"(?:status/|tweet/)(\d+)",
            Platform.TIKTOK: r"(?:video/)(\d+)",
            Platform.BILIBILI: r"(?:video/)(BV[a-zA-Z0-9]+)",
            Platform.XIAOHONGSHU: r"(?:explore/|item/)([a-zA-Z0-9]+)",
        }

        pattern = patterns.get(platform)
        if pattern:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _detect_content_type(url: str, platform: Platform) -> Optional[str]:
        """检测内容类型"""
        type_patterns = {
            "video": [r"/video/", r"/watch/", r"/reel/", r"/tv/"],
            "image": [r"/photo/", r"/image/", r"/picture/"],
            "article": [r"/article/", r"/post/"],
            "user": [r"/user/", r"/profile/", r"/@[\w]+/?$"],
            "playlist": [r"/playlist"],
            "story": [r"/stories/"],
        }

        for content_type, patterns in type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url):
                    return content_type
        return None

    @staticmethod
    def is_supported(url: str) -> bool:
        """检查URL是否支持"""
        parsed = URLParser.parse(url)
        return parsed.platform != Platform.UNKNOWN

    @staticmethod
    def get_supported_platforms() -> list:
        """获取支持的平台列表"""
        return [p.value for p in Platform if p != Platform.UNKNOWN]
