#!/usr/bin/env python3
"""
微信公众号文章抓取工具
使用 wechat-article-exporter 公开 API 获取文章正文
"""

import sys
import urllib.parse
import urllib.request
import ssl
import json

API_BASE = "https://down.mptext.top/api/public/v1/download"

def fetch_article(url, output_format="markdown"):
    """抓取微信公众号文章
    
    Args:
        url: 微信公众号文章链接
        output_format: 输出格式 (markdown/html/json/txt)
    
    Returns:
        文章内容或错误信息
    """
    # 编码 URL
    encoded_url = urllib.parse.quote(url, safe='')
    api_url = f"{API_BASE}?url={encoded_url}&format={output_format}"
    
    # 创建请求
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    req = urllib.request.Request(api_url, headers=headers)
    
    # 忽略 SSL 验证（如果需要）
    context = ssl._create_unverified_context()
    
    try:
        with urllib.request.urlopen(req, context=context, timeout=30) as response:
            content = response.read().decode('utf-8')
            return content
    except urllib.error.HTTPError as e:
        return f"Error: HTTP {e.code} - {e.reason}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    if len(sys.argv) < 2:
        print("Usage: wechat-crawler <wechat_article_url> [format]")
        print("  format: markdown (default), html, json, txt")
        sys.exit(1)
    
    url = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "markdown"
    
    result = fetch_article(url, output_format)
    print(result)

if __name__ == "__main__":
    main()
