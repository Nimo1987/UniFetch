"""
HTTP 客户端封装 — 支持代理自动 fallback

当直接请求失败（403/429/超时）时，自动切换到代理模式重试。
兼容 spider-proxy（云函数代理）和标准 HTTP/SOCKS5 代理。
"""

import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import httpx


class ProxyClient:
    """
    带代理 fallback 的异步 HTTP 客户端

    使用方式:
        async with ProxyClient(proxy="socks5://127.0.0.1:1080") as client:
            resp = await client.get("https://example.com")

        # 自动 fallback（先直连，失败后走代理）
        async with ProxyClient(fallback_proxy="https://proxy.example.com") as client:
            resp = await client.get(url, headers=headers, fallback=True)
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        fallback_proxy: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        follow_redirects: bool = True,
        **client_kwargs,
    ):
        """
        Args:
            proxy: 主代理地址（始终使用）
            fallback_proxy: fallback 代理地址（仅在直连失败时使用）
            timeout: 请求超时（秒）
            max_retries: 最大重试次数
            follow_redirects: 是否跟随重定向
            **client_kwargs: 传递给 httpx.AsyncClient 的额外参数
        """
        self.proxy = proxy
        self.fallback_proxy = fallback_proxy
        self.timeout = timeout
        self.max_retries = max_retries
        self.follow_redirects = follow_redirects
        self.client_kwargs = client_kwargs

        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            proxy=self.proxy,
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
            **self.client_kwargs,
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, url: str, fallback: bool = False, **kwargs) -> httpx.Response:
        """
        GET 请求，支持 fallback

        Args:
            url: 目标 URL
            fallback: 是否启用代理 fallback（直连失败时自动切换）
            **kwargs: 传递给 httpx 的参数
        """
        if not fallback or not self.fallback_proxy:
            return await self._request("GET", url, **kwargs)

        return await self._request_with_fallback("GET", url, **kwargs)

    async def post(self, url: str, fallback: bool = False, **kwargs) -> httpx.Response:
        """POST 请求，支持 fallback"""
        if not fallback or not self.fallback_proxy:
            return await self._request("POST", url, **kwargs)

        return await self._request_with_fallback("POST", url, **kwargs)

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """执行请求"""
        for attempt in range(self.max_retries):
            try:
                resp = await self._client.request(method, url, **kwargs)
                return resp
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))

    async def _request_with_fallback(
        self, method: str, url: str, **kwargs
    ) -> httpx.Response:
        """先直连，失败后走代理 fallback"""
        # 第一次尝试：直连（或使用主代理）
        try:
            resp = await self._request(method, url, **kwargs)
            # 检查是否需要 fallback
            if not self._should_fallback(resp):
                return resp
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError):
            pass  # 继续 fallback

        # 第二次尝试：走 fallback 代理
        async with httpx.AsyncClient(
            proxy=self.fallback_proxy,
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
            **self.client_kwargs,
        ) as fallback_client:
            resp = await fallback_client.request(method, url, **kwargs)
            return resp

    @staticmethod
    def _should_fallback(resp: httpx.Response) -> bool:
        """判断是否需要触发 fallback"""
        return resp.status_code in (403, 429, 503)


def build_spider_proxy_url(function_url: str) -> str:
    """
    构建 spider-proxy（云函数代理）的代理 URL

    spider-proxy 原理：将请求转发到 Serverless 函数，
    用云函数的出口 IP 规避反爬。

    Args:
        function_url: 云函数外网地址

    Returns:
        httpx 可用的代理 URL（通过 Proxytourl header 传递真实 URL）
    """
    return function_url
