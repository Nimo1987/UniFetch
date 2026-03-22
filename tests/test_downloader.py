"""Handler 分发测试"""

import pytest
from unittest.mock import patch, MagicMock

from unifetch import Downloader
from unifetch.models.content import Platform
from unifetch.international.handlers import YtDlpHandler, InstagramHandler
from unifetch.china.handlers import (
    XHSHandler,
    DouyinHandler,
    BilibiliHandler,
    WeiboHandler,
    WeixinHandler,
)


class TestDownloaderHandlerDispatch:
    """测试 Downloader 是否正确分发到对应 Handler"""

    def setup_method(self):
        self.dl = Downloader(output_dir="/tmp/unifetch_test")

    @pytest.mark.parametrize(
        "url,expected_cls,expected_platform",
        [
            ("https://www.youtube.com/watch?v=xxx", YtDlpHandler, Platform.YOUTUBE),
            ("https://twitter.com/user/status/123", YtDlpHandler, Platform.TWITTER),
            ("https://www.tiktok.com/@user/video/123", YtDlpHandler, Platform.TIKTOK),
            ("https://www.facebook.com/watch/?v=123", YtDlpHandler, Platform.FACEBOOK),
            ("https://www.reddit.com/r/test/abc", YtDlpHandler, Platform.REDDIT),
            ("https://www.instagram.com/p/ABC123/", InstagramHandler, Platform.INSTAGRAM),
            ("https://www.xiaohongshu.com/explore/abc", XHSHandler, Platform.XIAOHONGSHU),
            ("https://www.douyin.com/video/123", DouyinHandler, Platform.DOUYIN),
            ("https://www.bilibili.com/video/BV1xx", BilibiliHandler, Platform.BILIBILI),
            ("https://weibo.com/123/abc", WeiboHandler, Platform.WEIBO),
            ("https://mp.weixin.qq.com/s/abc", WeixinHandler, Platform.WEIXIN),
        ],
    )
    def test_handler_dispatch(self, url, expected_cls, expected_platform):
        handler = self.dl._get_handler(url)
        assert isinstance(handler, expected_cls)
        assert handler._get_platform() == expected_platform

    def test_unsupported_url_raises(self):
        with pytest.raises(ValueError, match="不支持的URL"):
            self.dl._get_handler("https://example.com/video")

    def test_handler_receives_proxy(self):
        dl = Downloader(output_dir="/tmp/test", proxy="socks5://127.0.0.1:1080")
        handler = dl._get_handler("https://www.youtube.com/watch?v=xxx")
        assert handler.proxy == "socks5://127.0.0.1:1080"

    def test_handler_receives_cookie(self):
        dl = Downloader(
            output_dir="/tmp/test",
            cookies={"xiaohongshu": "test_cookie_value"},
        )
        handler = dl._get_handler("https://www.xiaohongshu.com/explore/abc")
        assert handler.cookie == "test_cookie_value"

    def test_finance_lazy_load(self):
        """Finance Handler 懒加载：不安装 akshare 也不影响其他平台"""
        handler = self.dl._get_handler("https://www.youtube.com/watch?v=xxx")
        assert isinstance(handler, YtDlpHandler)

    def test_finance_handler_missing_akshare(self):
        """未安装 akshare 时获取 Finance Handler 应抛出 ImportError"""
        with patch.dict("sys.modules", {"akshare": None}):
            with pytest.raises(ImportError, match="akshare"):
                self.dl._get_handler("finance://000001")


class TestDownloaderPlatforms:
    """测试平台列表"""

    def test_get_supported_platforms(self):
        platforms = Downloader.get_supported_platforms()
        assert "youtube" in platforms
        assert "xiaohongshu" in platforms

    def test_is_supported(self):
        assert Downloader.is_supported("https://www.youtube.com/watch?v=xxx") is True
        assert Downloader.is_supported("https://unknown.com") is False
