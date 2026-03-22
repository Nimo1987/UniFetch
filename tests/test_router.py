"""URL 路由测试"""

import pytest
from unifetch.core.router import URLRouter
from unifetch.models.content import Platform


class TestURLRouterDetectPlatform:
    """平台检测测试"""

    @pytest.mark.parametrize(
        "url,expected",
        [
            # 国际平台
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", Platform.YOUTUBE),
            ("https://youtu.be/dQw4w9WgXcQ", Platform.YOUTUBE),
            ("https://twitter.com/user/status/123456789", Platform.TWITTER),
            ("https://x.com/user/status/123456789", Platform.TWITTER),
            ("https://www.facebook.com/watch/?v=123456789", Platform.FACEBOOK),
            ("https://www.instagram.com/p/ABC123/", Platform.INSTAGRAM),
            ("https://www.tiktok.com/@user/video/123456789", Platform.TIKTOK),
            ("https://www.reddit.com/r/python/comments/abc123/", Platform.REDDIT),
            # 中国平台
            ("https://www.xiaohongshu.com/explore/abc123", Platform.XIAOHONGSHU),
            ("https://xhslink.com/abc123", Platform.XIAOHONGSHU),
            ("https://www.douyin.com/video/123456789", Platform.DOUYIN),
            ("https://v.douyin.com/abc123", Platform.DOUYIN),
            ("https://www.bilibili.com/video/BV1xx411c7mD", Platform.BILIBILI),
            ("https://b23.tv/abc123", Platform.BILIBILI),
            ("https://weibo.com/123456789/abc123def", Platform.WEIBO),
            ("https://m.weibo.cn/detail/123456789", Platform.WEIBO),
            ("https://mp.weixin.qq.com/s/abc123", Platform.WEIXIN),
            # 金融
            ("finance://000001", Platform.FINANCE),
            ("finance://hk:00700", Platform.FINANCE),
            ("finance://us:AAPL", Platform.FINANCE),
        ],
    )
    def test_detect_platform(self, url, expected):
        assert URLRouter.detect_platform(url) == expected

    def test_unknown_platform(self):
        assert URLRouter.detect_platform("https://example.com/video") == Platform.UNKNOWN

    def test_case_insensitive(self):
        assert URLRouter.detect_platform("https://WWW.YOUTUBE.COM/watch?v=xxx") == Platform.YOUTUBE


class TestURLRouterExtractId:
    """内容 ID 提取测试"""

    def test_youtube_video_id(self):
        content_id, content_type = URLRouter.extract_id(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ", Platform.YOUTUBE
        )
        assert content_id == "dQw4w9WgXcQ"
        assert content_type == "video"

    def test_youtube_playlist(self):
        content_id, content_type = URLRouter.extract_id(
            "https://www.youtube.com/playlist?list=PLxxxxxxx", Platform.YOUTUBE
        )
        assert content_id == "PLxxxxxxx"
        assert content_type == "playlist"

    def test_bilibili_bvid(self):
        content_id, content_type = URLRouter.extract_id(
            "https://www.bilibili.com/video/BV1xx411c7mD", Platform.BILIBILI
        )
        assert content_id == "BV1xx411c7mD"
        assert content_type == "video"

    def test_xiaohongshu_note(self):
        content_id, content_type = URLRouter.extract_id(
            "https://www.xiaohongshu.com/explore/abc123def456", Platform.XIAOHONGSHU
        )
        assert content_id == "abc123def456"
        assert content_type == "note"

    def test_finance_cn(self):
        content_id, content_type = URLRouter.extract_id(
            "finance://000001", Platform.FINANCE
        )
        assert content_id == "000001"
        assert content_type == "stock"

    def test_finance_us(self):
        content_id, content_type = URLRouter.extract_id(
            "finance://us:AAPL", Platform.FINANCE
        )
        assert content_id == "AAPL"
        assert content_type == "stock"

    def test_no_id(self):
        content_id, content_type = URLRouter.extract_id(
            "https://www.youtube.com/", Platform.YOUTUBE
        )
        assert content_id is None


class TestURLRouterParse:
    """完整解析测试"""

    def test_parse_supported(self):
        result = URLRouter.parse("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result["platform"] == Platform.YOUTUBE
        assert result["content_id"] == "dQw4w9WgXcQ"
        assert result["supported"] is True

    def test_parse_unsupported(self):
        result = URLRouter.parse("https://example.com/page")
        assert result["platform"] == Platform.UNKNOWN
        assert result["supported"] is False

    def test_is_supported(self):
        assert URLRouter.is_supported("https://www.youtube.com/watch?v=xxx") is True
        assert URLRouter.is_supported("https://example.com") is False

    def test_get_supported_platforms(self):
        platforms = URLRouter.get_supported_platforms()
        assert "youtube" in platforms
        assert "xiaohongshu" in platforms
        assert "finance" in platforms
        assert "unknown" not in platforms
