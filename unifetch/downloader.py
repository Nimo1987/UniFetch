"""
统一下载器 - 主入口
"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from .core.router import URLRouter
from .core.base_handler import BaseHandler
from .core.llm_analyzer import LLMAnalyzer, LLMConfig
from .models.content import Platform, Content, AnalysisResult, FetchResult

# 导入所有Handler
from .international.handlers import YtDlpHandler, InstagramHandler
from .china.handlers import (
    XHSHandler,
    DouyinHandler,
    BilibiliHandler,
    WeiboHandler,
    WeixinHandler,
)


class Downloader:
    """
    统一下载器

    使用方式:
        dl = Downloader()
        result = await dl.analyze("https://www.youtube.com/watch?v=xxx")
        print(result.analysis.summary)
    """

    # Handler映射 — 使用 (handler_class, *args) 形式，避免 lambda hack
    _HANDLER_REGISTRY = {
        Platform.YOUTUBE: (YtDlpHandler, Platform.YOUTUBE),
        Platform.TWITTER: (YtDlpHandler, Platform.TWITTER),
        Platform.FACEBOOK: (YtDlpHandler, Platform.FACEBOOK),
        Platform.TIKTOK: (YtDlpHandler, Platform.TIKTOK),
        Platform.REDDIT: (YtDlpHandler, Platform.REDDIT),
        Platform.INSTAGRAM: (InstagramHandler,),
        Platform.XIAOHONGSHU: (XHSHandler,),
        Platform.DOUYIN: (DouyinHandler,),
        Platform.BILIBILI: (BilibiliHandler,),
        Platform.WEIBO: (WeiboHandler,),
        Platform.WEIXIN: (WeixinHandler,),
        # Finance 懒加载：不在 import 时要求 akshare
        Platform.FINANCE: None,
    }

    def __init__(
        self,
        output_dir: str = "./downloads",
        proxy: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        """
        初始化下载器

        Args:
            output_dir: 下载目录
            proxy: 代理地址
            cookies: 各平台的Cookie
            llm_config: LLM配置
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.proxy = proxy
        self.cookies = cookies or {}
        self.analyzer = LLMAnalyzer(llm_config)

    def _get_handler(self, url: str) -> BaseHandler:
        """获取URL对应的Handler"""
        parsed = URLRouter.parse(url)

        if not parsed["supported"]:
            raise ValueError(f"不支持的URL: {url}")

        platform = parsed["platform"]

        if platform == Platform.FINANCE:
            return self._build_finance_handler(url)

        entry = self._HANDLER_REGISTRY.get(platform)
        if entry is None:
            raise ValueError(f"未实现的平台Handler: {platform}")

        handler_cls = entry[0]
        extra_args = entry[1:]
        cookie = self.cookies.get(platform.value)

        return handler_cls(
            url,
            *extra_args,
            proxy=self.proxy,
            cookie=cookie,
            output_dir=self.output_dir,
        )

    def _build_finance_handler(self, url: str):
        """懒加载 FinanceHandler，仅在使用时要求 akshare"""
        try:
            from .finance import FinanceHandler
        except ImportError:
            raise ImportError("请安装akshare: pip install akshare")

        return FinanceHandler(
            url,
            proxy=self.proxy,
            output_dir=self.output_dir,
        )

    async def analyze(self, url: str) -> FetchResult:
        """
        分析URL内容（获取信息 + LLM分析）

        Args:
            url: 社交媒体URL

        Returns:
            FetchResult: 包含内容和分析结果
        """
        try:
            handler = self._get_handler(url)
            content = await handler.fetch()
            analysis = await self.analyzer.analyze(content)

            return FetchResult(
                success=True,
                content=content,
                analysis=analysis,
            )
        except Exception as e:
            return FetchResult(
                success=False,
                error=str(e),
            )

    async def fetch(self, url: str) -> FetchResult:
        """
        仅获取内容信息（不分析）

        Args:
            url: 社交媒体URL

        Returns:
            FetchResult: 包含内容信息
        """
        try:
            handler = self._get_handler(url)
            content = await handler.fetch()

            return FetchResult(
                success=True,
                content=content,
            )
        except Exception as e:
            return FetchResult(
                success=False,
                error=str(e),
            )

    async def download(self, url: str, quality: str = "best") -> FetchResult:
        """
        下载内容

        Args:
            url: 社交媒体URL
            quality: 下载质量

        Returns:
            FetchResult: 包含下载文件路径
        """
        try:
            handler = self._get_handler(url)
            content = await handler.fetch()
            filepath = await handler.download(quality)

            return FetchResult(
                success=True,
                content=content,
            )
        except Exception as e:
            return FetchResult(
                success=False,
                error=str(e),
            )

    async def batch_analyze(self, urls: list) -> list:
        """
        批量分析

        Args:
            urls: URL列表

        Returns:
            List[FetchResult]: 结果列表
        """
        tasks = [self.analyze(url) for url in urls]
        return await asyncio.gather(*tasks)

    @staticmethod
    def get_supported_platforms() -> list:
        """获取支持的平台列表"""
        return URLRouter.get_supported_platforms()

    @staticmethod
    def is_supported(url: str) -> bool:
        """检查URL是否支持"""
        return URLRouter.is_supported(url)


# 便捷函数
async def analyze_url(url: str, **kwargs) -> FetchResult:
    """分析URL的便捷函数"""
    dl = Downloader(**kwargs)
    return await dl.analyze(url)


async def download_url(url: str, **kwargs) -> FetchResult:
    """下载URL的便捷函数"""
    dl = Downloader(**kwargs)
    return await dl.download(url)
