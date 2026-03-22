"""
URL路由器 - 识别平台并分发请求
"""

import re
from typing import Optional, Dict, List, Tuple
from ..models.content import Platform


# URL模式匹配规则 - 按照优先级排序（更具体的平台优先）
URL_PATTERNS: Dict[Platform, List[str]] = {
    # 金融数据（自定义协议）
    Platform.FINANCE: [
        r"^finance:",
    ],
    # 中国平台（优先匹配，避免被国际平台的域名匹配）
    Platform.XIAOHONGSHU: [
        r"(?:xiaohongshu\.com|xhslink\.com)",
    ],
    Platform.DOUYIN: [
        r"(?:douyin\.com|v\.douyin\.com)",
    ],
    Platform.BILIBILI: [
        r"(?:bilibili\.com|b23\.tv|bilibili\.tv)",
    ],
    Platform.WEIBO: [
        r"(?:weibo\.com|weibo\.cn|m\.weibo\.cn)",
    ],
    Platform.WEIXIN: [
        r"(?:mp\.weixin\.qq\.com)",
    ],
    # 国际平台
    Platform.YOUTUBE: [
        r"(?:youtube\.com|youtu\.be|youtube-nocookie\.com|m\.youtube\.com)",
    ],
    Platform.TWITTER: [
        r"(?:twitter\.com|x\.com|mobile\.twitter\.com)",
    ],
    Platform.FACEBOOK: [
        r"(?:facebook\.com|fb\.watch|fb\.com|m\.facebook\.com|web\.facebook\.com)",
    ],
    Platform.INSTAGRAM: [
        r"(?:instagram\.com|instagr\.am)",
    ],
    Platform.TIKTOK: [
        r"(?:tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com|m\.tiktok\.com)",
    ],
    Platform.REDDIT: [
        r"(?:reddit\.com|redd\.it|www\.reddit\.com)",
    ],
}

# 内容ID提取模式
ID_PATTERNS = {
    Platform.FINANCE: [
        (r"finance://(?:hk:|us:)?([A-Za-z0-9]+)", "stock"),
    ],
    Platform.YOUTUBE: [
        (r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})", "video"),
        (r"playlist\?list=([a-zA-Z0-9_-]+)", "playlist"),
        (r"@([a-zA-Z0-9_.-]+)", "user"),
    ],
    Platform.TWITTER: [
        (r"(?:status|tweet)/(\d+)", "tweet"),
        (r"(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/?$", "user"),
    ],
    Platform.FACEBOOK: [
        (r"(?:video\.php\?v=|videos/|watch/\?v=)(\d+)", "video"),
        (r"(?:photo\.php\?fbid=|photo/)(\d+)", "image"),
        (r"(?:permalink\.php\?story_fbid=|posts/)(\d+)", "post"),
    ],
    Platform.INSTAGRAM: [
        (r"/p/([a-zA-Z0-9_-]+)", "post"),
        (r"/reel/([a-zA-Z0-9_-]+)", "reel"),
        (r"/stories/([a-zA-Z0-9_.]+)/(\d+)", "story"),
        (r"/([a-zA-Z0-9_.]+)/?$", "user"),
    ],
    Platform.TIKTOK: [
        (r"/video/(\d+)", "video"),
        (r"/@([a-zA-Z0-9_.]+)/?$", "user"),
    ],
    Platform.XIAOHONGSHU: [
        (r"(?:explore|item)/([a-f0-9]+)", "note"),
        (r"user/profile/([a-f0-9]+)", "user"),
    ],
    Platform.DOUYIN: [
        (r"/video/(\d+)", "video"),
        (r"/user/([a-zA-Z0-9_-]+)", "user"),
    ],
    Platform.BILIBILI: [
        (r"/video/(BV[a-zA-Z0-9]+)", "video"),
        (r"/bangumi/play/([a-zA-Z0-9]+)", "bangumi"),
        (r"/space/(\d+)", "user"),
    ],
    Platform.WEIBO: [
        (r"/(\d+)/([a-zA-Z0-9]+)", "weibo"),
        (r"/u/(\d+)", "user"),
    ],
    Platform.WEIXIN: [
        (r"s/([a-zA-Z0-9_-]+)", "article"),
        (r"__biz=([^&]+)", "article"),
    ],
}


class URLRouter:
    """URL路由器"""

    @staticmethod
    def detect_platform(url: str) -> Platform:
        """
        检测URL所属平台

        Args:
            url: 社交媒体URL

        Returns:
            Platform: 平台枚举
        """
        url_lower = url.lower()

        for platform, patterns in URL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return platform

        return Platform.UNKNOWN

    @staticmethod
    def extract_id(url: str, platform: Platform) -> Tuple[Optional[str], Optional[str]]:
        """
        提取内容ID和类型

        Args:
            url: URL
            platform: 平台

        Returns:
            (content_id, content_type)
        """
        patterns = ID_PATTERNS.get(platform, [])

        for pattern, content_type in patterns:
            match = re.search(pattern, url)
            if match:
                # 返回第一个捕获组作为ID
                return match.group(1), content_type

        return None, None

    @staticmethod
    def parse(url: str) -> Dict:
        """
        解析URL，返回平台、ID、类型等信息

        Args:
            url: 社交媒体URL

        Returns:
            Dict: 解析结果
        """
        url = url.strip()
        platform = URLRouter.detect_platform(url)
        content_id, content_type = URLRouter.extract_id(url, platform)

        return {
            "url": url,
            "platform": platform,
            "content_id": content_id,
            "content_type": content_type,
            "supported": platform != Platform.UNKNOWN,
        }

    @staticmethod
    def is_supported(url: str) -> bool:
        """检查URL是否支持"""
        return URLRouter.detect_platform(url) != Platform.UNKNOWN

    @staticmethod
    def get_supported_platforms() -> List[str]:
        """获取支持的平台列表"""
        return [p.value for p in Platform if p != Platform.UNKNOWN]
