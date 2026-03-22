"""
FastAPI服务

提供REST API接口用于社交媒体内容下载和分析
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from ..downloader import Downloader
from ..core.router import URLRouter
from ..core.config import ConfigManager, get_config


# Pydantic模型
if FASTAPI_AVAILABLE:

    class URLRequest(BaseModel):
        """URL请求模型"""

        url: str = Field(..., description="社交媒体URL")
        quality: str = Field("best", description="下载质量")
        proxy: Optional[str] = Field(None, description="代理地址")
        cookie: Optional[str] = Field(None, description="Cookie字符串")

    class BatchRequest(BaseModel):
        """批量请求模型"""

        urls: List[str] = Field(..., description="URL列表")
        quality: str = Field("best", description="下载质量")
        proxy: Optional[str] = Field(None, description="代理地址")

    class ConfigRequest(BaseModel):
        """配置请求模型"""

        platform: str = Field(..., description="平台名称")
        cookie: str = Field(..., description="Cookie字符串")

    class ProxyRequest(BaseModel):
        """代理请求模型"""

        proxy_url: str = Field(..., description="代理URL")
        enabled: bool = Field(True, description="是否启用")

    class MediaFileResponse(BaseModel):
        """媒体文件响应"""

        url: str
        type: str
        format: Optional[str] = None
        quality: Optional[str] = None

    class AuthorResponse(BaseModel):
        """作者响应"""

        id: Optional[str] = None
        username: Optional[str] = None
        nickname: Optional[str] = None

    class ContentResponse(BaseModel):
        """内容响应"""

        url: str
        platform: str
        content_type: str
        id: Optional[str] = None
        title: Optional[str] = None
        description: Optional[str] = None
        author: Optional[AuthorResponse] = None
        media_files: List[MediaFileResponse] = []
        cover_url: Optional[str] = None
        likes: Optional[int] = None
        comments_count: Optional[int] = None
        shares: Optional[int] = None
        views: Optional[int] = None
        tags: List[str] = []

    class AnalysisResponse(BaseModel):
        """分析响应"""

        summary: str = ""
        sentiment: str = ""
        topics: List[str] = []
        keywords: List[str] = []
        category: str = ""

    class FetchResponse(BaseModel):
        """获取响应"""

        success: bool
        content: Optional[ContentResponse] = None
        analysis: Optional[AnalysisResponse] = None
        error: Optional[str] = None


def create_app() -> FastAPI:
    """
    创建FastAPI应用

    Returns:
        FastAPI: FastAPI应用实例
    """
    if not FASTAPI_AVAILABLE:
        raise ImportError("请安装fastapi: pip install fastapi uvicorn")

    app = FastAPI(
        title="社交媒体统一下载工具",
        description="支持YouTube、Twitter、Facebook、Instagram、TikTok、Reddit、小红书、抖音、B站、微博等平台的内容下载和分析",
        version="1.0.0",
    )

    @app.get("/")
    async def root():
        """根路径"""
        return {
            "name": "社交媒体统一下载工具",
            "version": "1.0.0",
            "platforms": URLRouter.get_supported_platforms(),
        }

    @app.post("/fetch", response_model=FetchResponse)
    async def fetch_url(request: URLRequest):
        """获取URL内容信息"""
        try:
            dl = _create_downloader(request.proxy)
            result = await dl.fetch(request.url)

            if result.success:
                return FetchResponse(
                    success=True,
                    content=_to_content_response(result.content),
                )
            else:
                return FetchResponse(success=False, error=result.error)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/download", response_model=FetchResponse)
    async def download_url(request: URLRequest):
        """下载URL内容"""
        try:
            dl = _create_downloader(request.proxy)
            result = await dl.download(request.url, request.quality)

            if result.success:
                return FetchResponse(
                    success=True,
                    content=_to_content_response(result.content),
                )
            else:
                return FetchResponse(success=False, error=result.error)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/analyze", response_model=FetchResponse)
    async def analyze_url(request: URLRequest):
        """分析URL内容"""
        try:
            dl = _create_downloader(request.proxy)
            result = await dl.analyze(request.url)

            if result.success:
                return FetchResponse(
                    success=True,
                    content=_to_content_response(result.content),
                    analysis=_to_analysis_response(result.analysis)
                    if result.analysis
                    else None,
                )
            else:
                return FetchResponse(success=False, error=result.error)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/batch/fetch")
    async def batch_fetch(request: BatchRequest):
        """批量获取URL内容"""
        try:
            dl = _create_downloader(request.proxy)
            results = await dl.batch_analyze(request.urls)

            responses = []
            for result in results:
                if result.success:
                    responses.append(
                        {
                            "url": result.content.url,
                            "success": True,
                            "content": _to_content_response(result.content),
                        }
                    )
                else:
                    responses.append(
                        {
                            "url": result.content.url if result.content else None,
                            "success": False,
                            "error": result.error,
                        }
                    )

            return {"results": responses}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/platforms")
    async def get_platforms():
        """获取支持的平台列表"""
        return {"platforms": URLRouter.get_supported_platforms()}

    @app.get("/check")
    async def check_url(url: str = Query(..., description="要检查的URL")):
        """检查URL是否支持"""
        parsed = URLRouter.parse(url)
        return {
            "url": url,
            "supported": parsed["supported"],
            "platform": parsed["platform"].value if parsed["platform"] else None,
            "content_id": parsed["content_id"],
            "content_type": parsed["content_type"],
        }

    @app.get("/config")
    async def get_config_api():
        """获取当前配置"""
        config = get_config()
        return {
            "cookies": {
                "xiaohongshu": bool(config.cookies.xiaohongshu),
                "douyin": bool(config.cookies.douyin),
                "bilibili": bool(config.cookies.bilibili),
                "weibo": bool(config.cookies.weibo),
                "instagram": bool(config.cookies.instagram),
            },
            "proxy": {
                "enabled": config.proxy.enabled,
                "url": config.proxy.get_proxy_url(),
            },
            "download": {
                "directory": config.download.directory,
                "quality": config.download.quality,
            },
        }

    @app.post("/config/cookie")
    async def set_cookie_api(request: ConfigRequest):
        """设置平台Cookie"""
        try:
            config_mgr = ConfigManager()
            config_mgr.update_cookie(request.platform, request.cookie)
            return {"success": True, "message": f"已设置 {request.platform} 的Cookie"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/config/proxy")
    async def set_proxy_api(request: ProxyRequest):
        """设置代理"""
        try:
            config_mgr = ConfigManager()
            config_mgr.update_proxy(request.proxy_url, request.enabled)
            return {"success": True, "message": f"已设置代理: {request.proxy_url}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


def _create_downloader(proxy: Optional[str] = None) -> Downloader:
    """创建下载器实例"""
    config = get_config()

    cookies = {}
    if config.cookies.xiaohongshu:
        cookies["xiaohongshu"] = config.cookies.xiaohongshu
    if config.cookies.douyin:
        cookies["douyin"] = config.cookies.douyin
    if config.cookies.bilibili:
        cookies["bilibili"] = config.cookies.bilibili
    if config.cookies.weibo:
        cookies["weibo"] = config.cookies.weibo
    if config.cookies.instagram:
        cookies["instagram"] = config.cookies.instagram

    return Downloader(
        output_dir=config.download.directory,
        proxy=proxy or config.proxy.get_proxy_url(),
        cookies=cookies,
    )


def _to_content_response(content) -> Optional[ContentResponse]:
    """转换为ContentResponse"""
    if not content:
        return None

    author = None
    if content.author:
        author = AuthorResponse(
            id=content.author.id,
            username=content.author.username,
            nickname=content.author.nickname,
        )

    media_files = [
        MediaFileResponse(
            url=m.url,
            type=m.type,
            format=m.format,
            quality=m.quality,
        )
        for m in content.media_files
    ]

    return ContentResponse(
        url=content.url,
        platform=content.platform.value if content.platform else "",
        content_type=content.content_type.value if content.content_type else "",
        id=content.id,
        title=content.title,
        description=content.description,
        author=author,
        media_files=media_files,
        cover_url=content.cover_url,
        likes=content.likes,
        comments_count=content.comments_count,
        shares=content.shares,
        views=content.views,
        tags=content.tags,
    )


def _to_analysis_response(analysis) -> Optional[AnalysisResponse]:
    """转换为AnalysisResponse"""
    if not analysis:
        return None

    return AnalysisResponse(
        summary=analysis.summary,
        sentiment=analysis.sentiment,
        topics=analysis.topics,
        keywords=analysis.keywords,
        category=analysis.category,
    )


# 如果直接运行此文件，启动服务器
if __name__ == "__main__":
    if not FASTAPI_AVAILABLE:
        print("请安装fastapi和uvicorn:")
        print("pip install fastapi uvicorn")
    else:
        import uvicorn

        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=8000)
