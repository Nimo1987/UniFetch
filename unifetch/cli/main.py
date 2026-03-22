"""
CLI入口

支持命令:
- download: 下载单个URL
- batch: 批量下载
- analyze: 分析内容
- config: 配置管理
- platforms: 显示支持的平台
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from .. import Downloader, URLRouter
from ..core.config import ConfigManager, AppConfig, get_config, save_config


console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    社交媒体统一下载工具

    支持: YouTube, Twitter, Facebook, Instagram, TikTok, Reddit,
          小红书, 抖音, B站, 微博
    """
    pass


# ==================== 下载命令 ====================


@cli.command()
@click.argument("url")
@click.option("--output", "-o", help="下载目录 (默认: ./downloads)")
@click.option("--proxy", "-p", help="代理地址")
@click.option(
    "--quality", "-q", default="best", help="下载质量 (best/worst/720p/1080p/4k)"
)
@click.option("--cookie", "-c", help="Cookie字符串")
@click.option("--info-only", "-i", is_flag=True, help="仅获取信息，不下载")
@click.option("--json-output", "-j", is_flag=True, help="输出JSON格式")
def download(
    url: str,
    output: Optional[str],
    proxy: Optional[str],
    quality: str,
    cookie: Optional[str],
    info_only: bool,
    json_output: bool,
):
    """下载社交媒体内容"""
    asyncio.run(_download(url, output, proxy, quality, cookie, info_only, json_output))


async def _download(
    url: str,
    output: Optional[str],
    proxy: Optional[str],
    quality: str,
    cookie: Optional[str],
    info_only: bool,
    json_output: bool,
):
    """下载的异步实现"""
    # 加载配置
    config = get_config()
    download_dir = output or config.download.directory
    proxy_url = proxy or config.proxy.get_proxy_url()

    # 获取Cookie
    cookies = {}
    if cookie:
        # 从URL检测平台
        parsed = URLRouter.parse(url)
        if parsed["platform"]:
            cookies[parsed["platform"].value] = cookie
    else:
        # 从配置加载Cookie
        cookies = {
            "xiaohongshu": config.cookies.xiaohongshu,
            "douyin": config.cookies.douyin,
            "bilibili": config.cookies.bilibili,
            "weibo": config.cookies.weibo,
            "instagram": config.cookies.instagram,
        }
        cookies = {k: v for k, v in cookies.items() if v}

    with console.status("[bold green]正在处理..."):
        dl = Downloader(
            output_dir=download_dir,
            proxy=proxy_url,
            cookies=cookies,
        )

        if info_only:
            result = await dl.fetch(url)
        else:
            result = await dl.download(url, quality)

    if result.success:
        if json_output:
            output_data = _content_to_dict(result.content)
            click.echo(json.dumps(output_data, ensure_ascii=False, indent=2))
        else:
            _display_content(result.content)
            console.print("[bold green]✅ 操作成功[/bold green]")
    else:
        console.print(f"[bold red]❌ 操作失败: {result.error}[/bold red]")
        sys.exit(1)


# ==================== 批量下载命令 ====================


@cli.command()
@click.argument("urls", nargs=-1, required=False)
@click.option(
    "--file", "-f", "url_file", type=click.Path(exists=True), help="URL列表文件"
)
@click.option("--output", "-o", help="下载目录")
@click.option("--proxy", "-p", help="代理地址")
@click.option("--quality", "-q", default="best", help="下载质量")
@click.option("--concurrent", "-n", default=3, help="并发数量")
def batch(
    urls: tuple,
    url_file: Optional[str],
    output: Optional[str],
    proxy: Optional[str],
    quality: str,
    concurrent: int,
):
    """批量下载社交媒体内容"""
    asyncio.run(_batch(urls, url_file, output, proxy, quality, concurrent))


async def _batch(
    urls: tuple,
    url_file: Optional[str],
    output: Optional[str],
    proxy: Optional[str],
    quality: str,
    concurrent: int,
):
    """批量下载的异步实现"""
    # 收集URL
    url_list = list(urls)
    if url_file:
        with open(url_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    url_list.append(line)

    if not url_list:
        console.print("[bold red]❌ 未提供任何URL[/bold red]")
        return

    # 加载配置
    config = get_config()
    download_dir = output or config.download.directory
    proxy_url = proxy or config.proxy.get_proxy_url()

    dl = Downloader(
        output_dir=download_dir,
        proxy=proxy_url,
    )

    # 进度显示
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]批量下载中...", total=len(url_list))

        results = []
        for url in url_list:
            progress.update(task, description=f"[cyan]下载: {url[:50]}...")
            result = await dl.download(url, quality)
            results.append((url, result))
            progress.advance(task)

        # 显示结果统计
        success_count = sum(1 for _, r in results if r.success)
        fail_count = len(results) - success_count

        console.print(
            f"\n[bold]下载完成:[/bold] 成功 {success_count}, 失败 {fail_count}"
        )

        # 显示失败的URL
        if fail_count > 0:
            console.print("\n[bold red]失败的URL:[/bold red]")
            for url, result in results:
                if not result.success:
                    console.print(f"  - {url}: {result.error}")


# ==================== 分析命令 ====================


@cli.command()
@click.argument("url")
@click.option("--proxy", "-p", help="代理地址")
@click.option("--json-output", "-j", is_flag=True, help="输出JSON格式")
def analyze(url: str, proxy: Optional[str], json_output: bool):
    """分析社交媒体内容（获取信息 + LLM分析）"""
    asyncio.run(_analyze(url, proxy, json_output))


async def _analyze(url: str, proxy: Optional[str], json_output: bool):
    """分析的异步实现"""
    config = get_config()
    proxy_url = proxy or config.proxy.get_proxy_url()

    with console.status("[bold green]正在分析..."):
        dl = Downloader(proxy=proxy_url)
        result = await dl.analyze(url)

    if result.success:
        if json_output:
            output = {
                "content": _content_to_dict(result.content),
                "analysis": _analysis_to_dict(result.analysis)
                if result.analysis
                else None,
            }
            click.echo(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            _display_content(result.content)
            if result.analysis:
                _display_analysis(result.analysis)
    else:
        console.print(f"[bold red]❌ 分析失败: {result.error}[/bold red]")


# ==================== 配置命令 ====================


@cli.group()
def config():
    """配置管理"""
    pass


@config.command("show")
def config_show():
    """显示当前配置"""
    cfg = get_config()
    _display_config(cfg)


@config.command("set-cookie")
@click.argument("platform")
@click.argument("cookie")
def config_set_cookie(platform: str, cookie: str):
    """设置平台Cookie"""
    valid_platforms = [
        "xiaohongshu",
        "douyin",
        "bilibili",
        "weibo",
        "instagram",
        "youtube",
        "twitter",
    ]
    if platform.lower() not in valid_platforms:
        console.print(f"[bold red]❌ 无效的平台: {platform}[/bold red]")
        console.print(f"有效平台: {', '.join(valid_platforms)}")
        return

    config_mgr = ConfigManager()
    config_mgr.update_cookie(platform.lower(), cookie)
    console.print(f"[bold green]✅ 已设置 {platform} 的Cookie[/bold green]")


@config.command("set-proxy")
@click.argument("proxy_url")
def config_set_proxy(proxy_url: str):
    """设置代理地址"""
    config_mgr = ConfigManager()
    config_mgr.update_proxy(proxy_url)
    console.print(f"[bold green]✅ 已设置代理: {proxy_url}[/bold green]")


@config.command("set-download-dir")
@click.argument("directory")
def config_set_download_dir(directory: str):
    """设置下载目录"""
    config_mgr = ConfigManager()
    config_mgr.update_download_dir(directory)
    console.print(f"[bold green]✅ 已设置下载目录: {directory}[/bold green]")


@config.command("reset")
def config_reset():
    """重置配置"""
    if Confirm.ask("确定要重置所有配置吗？"):
        config_mgr = ConfigManager()
        config_mgr.reset()
        console.print("[bold green]✅ 配置已重置[/bold green]")


@config.command("export")
@click.argument("path")
def config_export(path: str):
    """导出配置到文件"""
    config_mgr = ConfigManager()
    config_mgr.export_config(Path(path))
    console.print(f"[bold green]✅ 配置已导出到: {path}[/bold green]")


@config.command("import")
@click.argument("path")
def config_import(path: str):
    """从文件导入配置"""
    config_mgr = ConfigManager()
    config_mgr.import_config(Path(path))
    console.print(f"[bold green]✅ 配置已从 {path} 导入[/bold green]")


# ==================== 平台命令 ====================


@cli.command()
def platforms():
    """显示支持的平台列表"""
    table = Table(title="支持的平台")
    table.add_column("平台", style="cyan")
    table.add_column("类型", style="green")
    table.add_column("说明", style="yellow")

    platform_info = [
        ("youtube", "国际", "使用 yt-dlp"),
        ("twitter", "国际", "使用 yt-dlp (X.com)"),
        ("facebook", "国际", "使用 yt-dlp"),
        ("instagram", "国际", "使用 instaloader"),
        ("tiktok", "国际", "使用 yt-dlp"),
        ("reddit", "国际", "使用 yt-dlp"),
        ("xiaohongshu", "中国", "HTML解析"),
        ("douyin", "中国", "HTML解析"),
        ("bilibili", "中国", "API调用"),
        ("weibo", "中国", "API调用"),
        ("weixin", "中国", "wechat-article-exporter API"),
        ("finance", "金融", "akshare (A股/港股/美股)"),
    ]

    for name, type_, desc in platform_info:
        table.add_row(name, type_, desc)

    console.print(table)


# ==================== 辅助函数 ====================


def _content_to_dict(content) -> dict:
    """将Content对象转换为字典"""
    if not content:
        return None

    return {
        "url": content.url,
        "platform": content.platform.value if content.platform else None,
        "content_type": content.content_type.value if content.content_type else None,
        "id": content.id,
        "title": content.title,
        "description": content.description,
        "author": {
            "id": content.author.id if content.author else None,
            "username": content.author.username if content.author else None,
            "nickname": content.author.nickname if content.author else None,
        }
        if content.author
        else None,
        "media_files": [
            {
                "url": m.url,
                "type": m.type,
                "format": m.format,
                "quality": m.quality,
            }
            for m in content.media_files
        ],
        "cover_url": content.cover_url,
        "likes": content.likes,
        "comments_count": content.comments_count,
        "shares": content.shares,
        "views": content.views,
        "saves": content.saves,
        "tags": content.tags,
        "publish_time": content.publish_time.isoformat()
        if content.publish_time
        else None,
    }


def _analysis_to_dict(analysis) -> dict:
    """将AnalysisResult对象转换为字典"""
    if not analysis:
        return None

    return {
        "summary": analysis.summary,
        "sentiment": analysis.sentiment,
        "sentiment_score": analysis.sentiment_score,
        "topics": analysis.topics,
        "keywords": analysis.keywords,
        "key_points": analysis.key_points,
        "language": analysis.language,
        "quality_score": analysis.quality_score,
        "content_rating": analysis.content_rating,
        "recommendation": analysis.recommendation,
        "recommendation_reason": analysis.recommendation_reason,
        "category": analysis.category,
        "subcategory": analysis.subcategory,
    }


def _display_content(content):
    """显示内容信息"""
    if not content:
        return

    panel = Panel(
        f"""[bold]平台:[/bold] {content.platform.value if content.platform else "-"}
[bold]类型:[/bold] {content.content_type.value if content.content_type else "-"}
[bold]ID:[/bold] {content.id or "-"}
[bold]标题:[/bold] {content.title or "无标题"}
[bold]作者:[/bold] {content.author.nickname if content.author else "未知"}
[bold]点赞:[/bold] {content.likes or "-"}
[bold]评论:[/bold] {content.comments_count or "-"}
[bold]转发:[/bold] {content.shares or "-"}
[bold]播放:[/bold] {content.views or "-"}
[bold]收藏:[/bold] {content.saves or "-"}
[bold]媒体:[/bold] {len(content.media_files)} 个文件
[bold]标签:[/bold] {", ".join(content.tags[:5]) if content.tags else "-"}
[bold]链接:[/bold] {content.url}""",
        title="📱 内容信息",
        border_style="cyan",
    )
    console.print(panel)


def _display_analysis(analysis):
    """显示分析结果"""
    if not analysis:
        return

    panel = Panel(
        f"""[bold]摘要:[/bold] {analysis.summary or "-"}
[bold]情感:[/bold] {analysis.sentiment or "-"} ({analysis.sentiment_score:.2f})
[bold]话题:[/bold] {", ".join(analysis.topics[:5]) if analysis.topics else "-"}
[bold]关键词:[/bold] {", ".join(analysis.keywords[:5]) if analysis.keywords else "-"}
[bold]分类:[/bold] {analysis.category or "-"} - {analysis.subcategory or "-"}
[bold]质量:[/bold] {analysis.quality_score:.1f}/10
[bold]推荐:[/bold] {analysis.recommendation or "-"}
[bold]理由:[/bold] {analysis.recommendation_reason or "-"}""",
        title="🤖 LLM分析",
        border_style="green",
    )
    console.print(panel)


def _display_config(config: AppConfig):
    """显示配置信息"""
    table = Table(title="当前配置")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="green")

    # Cookie
    table.add_row("Cookie - 小红书", _mask_value(config.cookies.xiaohongshu))
    table.add_row("Cookie - 抖音", _mask_value(config.cookies.douyin))
    table.add_row("Cookie - B站", _mask_value(config.cookies.bilibili))
    table.add_row("Cookie - 微博", _mask_value(config.cookies.weibo))
    table.add_row("Cookie - Instagram", _mask_value(config.cookies.instagram))

    # Proxy
    table.add_row("代理 - 启用", str(config.proxy.enabled))
    table.add_row("代理 - 地址", config.proxy.get_proxy_url() or "未设置")

    # Download
    table.add_row("下载 - 目录", config.download.directory)
    table.add_row("下载 - 质量", config.download.quality)
    table.add_row("下载 - 并发数", str(config.download.max_concurrent))

    # LLM
    table.add_row("LLM - 启用", str(config.llm.enabled))
    table.add_row("LLM - API URL", config.llm.api_url or "未设置")
    table.add_row("LLM - 模型", config.llm.model)

    console.print(table)


def _mask_value(value: Optional[str]) -> str:
    """掩码显示敏感值"""
    if not value:
        return "未设置"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def main():
    """CLI主入口"""
    cli()


if __name__ == "__main__":
    main()
