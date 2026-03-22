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

# 尝试导入FinanceHandler（可选依赖akshare）
try:
    from .finance import FinanceHandler

    FINANCE_AVAILABLE = True
except ImportError:
    FINANCE_AVAILABLE = False
    FinanceHandler = None


class Downloader:
    """
    统一下载器

    使用方式:
        dl = Downloader()
        result = await dl.analyze("https://www.youtube.com/watch?v=xxx")
        print(result.analysis.summary)
    """

    # Handler映射
    HANDLER_MAP = {
        Platform.YOUTUBE: lambda url, **kw: YtDlpHandler(url, Platform.YOUTUBE, **kw),
        Platform.TWITTER: lambda url, **kw: YtDlpHandler(url, Platform.TWITTER, **kw),
        Platform.FACEBOOK: lambda url, **kw: YtDlpHandler(url, Platform.FACEBOOK, **kw),
        Platform.TIKTOK: lambda url, **kw: YtDlpHandler(url, Platform.TIKTOK, **kw),
        Platform.REDDIT: lambda url, **kw: YtDlpHandler(url, Platform.REDDIT, **kw),
        Platform.INSTAGRAM: lambda url, **kw: InstagramHandler(url, **kw),
        Platform.XIAOHONGSHU: lambda url, **kw: XHSHandler(url, **kw),
        Platform.DOUYIN: lambda url, **kw: DouyinHandler(url, **kw),
        Platform.BILIBILI: lambda url, **kw: BilibiliHandler(url, **kw),
        Platform.WEIBO: lambda url, **kw: WeiboHandler(url, **kw),
        Platform.WEIXIN: lambda url, **kw: WeixinHandler(url, **kw),
        Platform.FINANCE: lambda url, **kw: (
            FinanceHandler(url, **kw)
            if FINANCE_AVAILABLE
            else (_ for _ in ()).throw(
                ImportError("请安装akshare: pip install akshare")
            )
        ),
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

    async def analyze(self, url: str) -> FetchResult:
        """
        分析URL内容（获取信息 + LLM分析）

        Args:
            url: 社交媒体URL

        Returns:
            FetchResult: 包含内容和分析结果
        """
        try:
            # 1. 获取Handler
            handler = self._get_handler(url)

            # 2. 获取内容信息
            content = await handler.fetch()

            # 3. LLM分析
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

            # 先获取信息
            content = await handler.fetch()

            # 下载
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

    def _get_handler(self, url: str) -> BaseHandler:
        """获取URL对应的Handler"""
        # 解析URL
        parsed = URLRouter.parse(url)

        if not parsed["supported"]:
            raise ValueError(f"不支持的URL: {url}")

        platform = parsed["platform"]

        # 获取Handler工厂
        handler_factory = self.HANDLER_MAP.get(platform)
        if not handler_factory:
            raise ValueError(f"未实现的平台Handler: {platform}")

        # 获取平台Cookie
        cookie = self.cookies.get(platform.value)

        # 创建Handler
        return handler_factory(
            url,
            proxy=self.proxy,
            cookie=cookie,
            output_dir=self.output_dir,
        )

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
