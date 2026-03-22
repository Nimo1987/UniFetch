"""
中国平台Handler
- 小红书 (XHS)
- 抖音 (Douyin)
- B站 (Bilibili)
- 微博 (Weibo)
"""

import asyncio
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlencode, urlparse, parse_qs

import httpx

try:
    from bilibili_api import video, Credential

    BILIBILI_AVAILABLE = True
except ImportError:
    BILIBILI_AVAILABLE = False

from ..core.base_handler import BaseHandler
from ..models.content import Content, Platform, ContentType, Author, MediaFile


class XHSHandler(BaseHandler):
    """
    小红书 Handler

    基于XHS-Downloader的核心逻辑，通过解析HTML获取笔记数据
    """

    # 小红书请求头
    HEADERS = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def _get_platform(self) -> Platform:
        return Platform.XIAOHONGSHU

    async def fetch(self) -> Content:
        """获取小红书内容"""
        note_id = self._extract_note_id()
        if not note_id:
            raise ValueError("无法提取小红书笔记ID")

        # 获取笔记信息
        note_info = await self._get_note_info(note_id)

        # 构建作者信息
        author_data = note_info.get("user", {})
        author = Author(
            id=author_data.get("user_id"),
            username=author_data.get("nickname"),
            nickname=author_data.get("nickname"),
            avatar=self.format_url(author_data.get("avatar", {}).get("url", "")),
        )

        # 构建媒体文件
        media_files = []
        note_type = note_info.get("type", "normal")

        if note_type == "video":
            # 视频笔记
            video_info = note_info.get("video", {})
            video_url = self._extract_video_url(video_info)
            if video_url:
                media_files.append(
                    MediaFile(
                        url=video_url,
                        type="video",
                        format="mp4",
                    )
                )
        else:
            # 图片笔记
            image_list = note_info.get("imageList", [])
            for img in image_list:
                img_url = self._extract_image_url(img)
                if img_url:
                    media_files.append(
                        MediaFile(
                            url=img_url,
                            type="image",
                            format="jpg",
                        )
                    )

        # 判断内容类型
        if note_type == "video":
            content_type = ContentType.VIDEO
        elif len(media_files) > 1:
            content_type = ContentType.CAROUSEL
        else:
            content_type = ContentType.IMAGE

        # 提取标签
        tags = []
        tag_list = note_info.get("tagList", [])
        for tag in tag_list:
            if isinstance(tag, dict):
                tags.append(tag.get("name", ""))
            elif isinstance(tag, str):
                tags.append(tag)

        # 互动数据
        interact_info = note_info.get("interactInfo", {})

        self._content = self.create_content(
            content_type=content_type,
            id=note_id,
            title=note_info.get("title", ""),
            description=note_info.get("desc", ""),
            author=author,
            media_files=media_files,
            cover_url=self._extract_image_url(note_info.get("cover", {}))
            or self.format_url(note_info.get("cover", {}).get("urlDefault", "")),
            likes=self._parse_count(interact_info.get("likedCount", "0")),
            comments_count=self._parse_count(interact_info.get("commentCount", "0")),
            shares=self._parse_count(interact_info.get("shareCount", "0")),
            saves=self._parse_count(interact_info.get("collectedCount", "0")),
            tags=tags,
            raw_data=note_info,
        )

        return self._content

    async def download(self, quality: str = "best") -> Path:
        """下载小红书内容"""
        content = await self.get_info()

        if not content.media_files:
            raise ValueError("无媒体文件可下载")

        downloaded_files = []
        headers = {**self.HEADERS, "Referer": "https://www.xiaohongshu.com/"}

        async with httpx.AsyncClient(follow_redirects=True) as client:
            for i, media in enumerate(content.media_files):
                response = await client.get(media.url, headers=headers)
                response.raise_for_status()

                ext = "mp4" if media.type == "video" else "jpg"
                if len(content.media_files) > 1:
                    filepath = self.output_dir / f"{content.id}_{i + 1}.{ext}"
                else:
                    filepath = self.output_dir / f"{content.id}.{ext}"

                filepath.write_bytes(response.content)
                downloaded_files.append(filepath)

        return downloaded_files[0] if downloaded_files else self.output_dir

    def _extract_note_id(self) -> Optional[str]:
        """提取笔记ID"""
        patterns = [
            r"explore/([a-f0-9]+)",
            r"item/([a-f0-9]+)",
            r"discovery/item/([a-f0-9]+)",
            r"xhslink\.com/([A-Za-z0-9]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, self.url)
            if match:
                return match.group(1)
        return None

    async def _get_note_info(self, note_id: str) -> Dict[str, Any]:
        """获取笔记信息 - 通过解析HTML"""
        # 构建笔记URL
        note_url = f"https://www.xiaohongshu.com/explore/{note_id}"

        headers = {**self.HEADERS}
        if self.cookie:
            headers["Cookie"] = self.cookie

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(note_url, headers=headers)
            response.raise_for_status()
            html = response.text

        # 从HTML中提取__INITIAL_STATE__
        note_info = self._extract_initial_state(html, note_id)

        if not note_info:
            raise ValueError(f"无法获取笔记数据: {note_id}")

        return note_info

    def _extract_initial_state(self, html: str, note_id: str) -> Dict[str, Any]:
        """从HTML中提取__INITIAL_STATE__数据"""
        # 查找window.__INITIAL_STATE__
        patterns = [
            r"window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>",
            r"window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;?\s*$",
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    state_str = match.group(1)
                    # 处理undefined替换为null
                    state_str = state_str.replace("undefined", "null")
                    state = json.loads(state_str)
                    return self._find_note_data(state, note_id)
                except json.JSONDecodeError:
                    continue

        # 尝试从JSON-LD或其他位置提取
        return self._extract_from_scripts(html, note_id)

    def _find_note_data(self, state: Dict, note_id: str) -> Dict[str, Any]:
        """从state中查找笔记数据"""

        # 递归查找笔记数据
        def search_dict(d: Dict, target_id: str) -> Optional[Dict]:
            if not isinstance(d, dict):
                return None

            # 检查当前字典是否包含笔记数据
            if d.get("noteId") == target_id or d.get("note_id") == target_id:
                return d

            # 检查note字段
            if "note" in d:
                note = d["note"]
                if isinstance(note, dict):
                    if (
                        note.get("noteId") == target_id
                        or note.get("note_id") == target_id
                    ):
                        return note
                    # note下可能还有noteDetailMap
                    if "noteDetailMap" in note:
                        detail = note["noteDetailMap"].get(target_id)
                        if detail:
                            return detail.get("note", detail)

            # 递归搜索
            for key, value in d.items():
                if isinstance(value, dict):
                    result = search_dict(value, target_id)
                    if result:
                        return result
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            result = search_dict(item, target_id)
                            if result:
                                return result

            return None

        result = search_dict(state, note_id)
        if result:
            return result

        # 尝试直接从顶层结构获取
        note_map = state.get("note", {}).get("noteDetailMap", {})
        if note_id in note_map:
            return note_map[note_id].get("note", note_map[note_id])

        return {}

    def _extract_from_scripts(self, html: str, note_id: str) -> Dict[str, Any]:
        """从script标签中提取数据"""
        # 查找包含笔记数据的script
        script_pattern = r"<script[^>]*>(.*?)</script>"
        scripts = re.findall(script_pattern, html, re.DOTALL)

        for script in scripts:
            if note_id in script and ("noteId" in script or "note_id" in script):
                try:
                    # 尝试提取JSON
                    json_match = re.search(r"(\{[\s\S]*\})", script)
                    if json_match:
                        data_str = json_match.group(1)
                        data_str = data_str.replace("undefined", "null")
                        return json.loads(data_str)
                except (json.JSONDecodeError, AttributeError):
                    continue

        return {}

    def _extract_image_url(self, img_data: Dict) -> Optional[str]:
        """提取图片URL"""
        if not img_data:
            return None

        # 尝试多种URL格式
        url = (
            img_data.get("urlDefault")
            or img_data.get("url")
            or img_data.get("imageList", [{}])[0].get("urlDefault", "")
        )

        return self.format_url(url)

    def _extract_video_url(self, video_data: Dict) -> Optional[str]:
        """提取视频URL"""
        if not video_data:
            return None

        # 尝试从consumer获取
        consumer = video_data.get("consumer", {})
        origin_key = consumer.get("originVideoKey")
        if origin_key:
            return f"https://sns-video-bd.xhscdn.com/{origin_key}"

        # 尝试从media获取
        media = video_data.get("media", {})
        stream = media.get("stream", {})
        h264_list = stream.get("h264", [])
        if h264_list:
            # 选择最高质量
            best = max(h264_list, key=lambda x: x.get("quality", 0))
            return best.get("masterUrl") or best.get("backupUrls", [None])[0]

        return None


    def _parse_count(self, count_str: str) -> int:
        """解析数量字符串（支持万、亿等单位）"""
        if not count_str:
            return 0

        count_str = str(count_str).strip()

        try:
            if "万" in count_str:
                return int(float(count_str.replace("万", "")) * 10000)
            elif "亿" in count_str:
                return int(float(count_str.replace("亿", "")) * 100000000)
            else:
                return int(count_str)
        except ValueError:
            return 0


class DouyinHandler(BaseHandler):
    """
    抖音 Handler

    基于douyin-downloader的核心逻辑，通过解析页面获取视频数据
    """

    # 抖音请求头
    HEADERS = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def _get_platform(self) -> Platform:
        return Platform.DOUYIN

    async def fetch(self) -> Content:
        """获取抖音内容"""
        # 解析短链接获取完整URL
        resolved_url = await self._resolve_short_url()

        # 提取视频ID
        video_id = self._extract_video_id(resolved_url)
        if not video_id:
            raise ValueError("无法提取抖音视频ID")

        # 获取视频信息
        video_info = await self._get_video_info(video_id, resolved_url)

        # 构建作者信息
        author_data = video_info.get("author", {})
        author = Author(
            id=author_data.get("uid"),
            username=author_data.get("unique_id") or author_data.get("short_id"),
            nickname=author_data.get("nickname"),
            avatar=author_data.get("avatar_thumb", {}).get("url_list", [None])[0],
        )

        # 构建媒体文件
        media_files = []
        video_data = video_info.get("video", {})
        play_addr = video_data.get("play_addr", {})
        url_list = play_addr.get("url_list", [])

        if url_list:
            # 使用第一个URL（通常是无水印版本）
            media_files.append(
                MediaFile(
                    url=url_list[0],
                    type="video",
                    format="mp4",
                    width=play_addr.get("width"),
                    height=play_addr.get("height"),
                )
            )

        # 提取标签
        tags = []
        text_extra = video_info.get("text_extra", [])
        for extra in text_extra:
            if extra.get("hashtag_name"):
                tags.append(extra["hashtag_name"])

        self._content = self.create_content(
            content_type=ContentType.VIDEO,
            id=video_id,
            title=video_info.get("desc", "")[:100],
            description=video_info.get("desc"),
            author=author,
            media_files=media_files,
            cover_url=video_data.get("cover", {}).get("url_list", [None])[0],
            likes=video_info.get("statistics", {}).get("digg_count"),
            comments_count=video_info.get("statistics", {}).get("comment_count"),
            shares=video_info.get("statistics", {}).get("share_count"),
            views=video_info.get("statistics", {}).get("play_count"),
            tags=tags,
            raw_data=video_info,
        )

        return self._content

    async def download(self, quality: str = "best") -> Path:
        """下载抖音视频"""
        content = await self.get_info()

        if not content.media_files:
            raise ValueError("无媒体文件可下载")

        headers = {
            **self.HEADERS,
            "Referer": "https://www.douyin.com/",
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(content.media_files[0].url, headers=headers)
            response.raise_for_status()
            filepath = self.output_dir / f"{content.id}.mp4"
            filepath.write_bytes(response.content)
            return filepath

    def _extract_video_id(self, url: str = None) -> Optional[str]:
        """提取视频ID"""
        target_url = url or self.url

        patterns = [
            r"video/(\d+)",
            r"modal_id=(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, target_url)
            if match:
                return match.group(1)
        return None

    async def _resolve_short_url(self) -> str:
        """解析短链接"""
        if "v.douyin.com" not in self.url:
            return self.url

        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            try:
                response = await client.get(self.url, headers=self.HEADERS)
                return str(response.url)
            except Exception:
                return self.url

    async def _get_video_info(self, video_id: str, url: str) -> Dict[str, Any]:
        """获取视频信息 - 通过解析HTML"""
        headers = {**self.HEADERS}
        if self.cookie:
            headers["Cookie"] = self.cookie

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text

        # 从HTML中提取视频数据
        video_info = self._extract_video_from_html(html, video_id)

        if not video_info:
            raise ValueError(f"无法获取视频数据: {video_id}")

        return video_info

    def _extract_video_from_html(self, html: str, video_id: str) -> Dict[str, Any]:
        """从HTML中提取视频数据"""
        # 尝试从RENDER_DATA提取
        render_data_match = re.search(
            r'<script id="RENDER_DATA" type="application/json">(.*?)</script>',
            html,
            re.DOTALL,
        )
        if render_data_match:
            try:
                from urllib.parse import unquote

                render_data = json.loads(unquote(render_data_match.group(1)))
                return self._find_video_in_render_data(render_data, video_id)
            except (json.JSONDecodeError, KeyError):
                pass

        # 尝试从__INITIAL_STATE__提取
        state_match = re.search(
            r"window\._SSR_HYDRATED_DATA\s*=\s*({.*?})\s*;?\s*</script>",
            html,
            re.DOTALL,
        )
        if state_match:
            try:
                state_str = state_match.group(1).replace("undefined", "null")
                state = json.loads(state_str)
                return self._find_video_in_state(state, video_id)
            except json.JSONDecodeError:
                pass

        # 尝试从其他script提取
        script_patterns = [
            r'"aweme_id"\s*:\s*"' + video_id + r'"[^}]*"video"\s*:\s*\{[^}]*\}',
            r"window\.__INITIAL_STATE__\s*=\s*\{[^}]*awemeId[^}]*\}",
        ]

        for pattern in script_patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    # 尝试提取更大的JSON块
                    json_match = re.search(
                        r'(\{[\s\S]*"aweme_id"\s*:\s*"' + video_id + r'"[\s\S]*\})',
                        html,
                    )
                    if json_match:
                        data_str = json_match.group(1)
                        # 处理JavaScript特殊值
                        data_str = re.sub(r":\s*undefined", ":null", data_str)
                        return json.loads(data_str)
                except (json.JSONDecodeError, AttributeError):
                    pass

        return {}

    def _find_video_in_render_data(self, data: Dict, video_id: str) -> Dict[str, Any]:
        """从RENDER_DATA中查找视频数据"""

        def search(d):
            if not isinstance(d, dict):
                return None

            # 检查当前字典是否包含视频数据
            if d.get("aweme_id") == video_id or d.get("awemeId") == video_id:
                return d

            # 递归搜索
            for value in d.values():
                if isinstance(value, dict):
                    result = search(value)
                    if result:
                        return result
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            result = search(item)
                            if result:
                                return result

            return None

        return search(data) or {}

    def _find_video_in_state(self, state: Dict, video_id: str) -> Dict[str, Any]:
        """从state中查找视频数据"""
        # 常见的路径
        paths = [
            ["odin", "videoData"],
            ["video", "videoData"],
            ["aweme", "detail"],
        ]

        for path in paths:
            current = state
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    current = None
                    break

            if current and isinstance(current, dict):
                if current.get("aweme_id") == video_id:
                    return current

        return self._find_video_in_render_data(state, video_id)


class BilibiliHandler(BaseHandler):
    """
    B站 Handler

    支持bilibili-api-python和直接API调用两种方式
    """

    # B站API端点
    API_BASE = "https://api.bilibili.com"
    HEADERS = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "origin": "https://www.bilibili.com",
        "referer": "https://www.bilibili.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def __init__(self, url: str, **kwargs):
        super().__init__(url, **kwargs)
        if BILIBILI_AVAILABLE:
            self.credential = Credential()
        else:
            self.credential = None

    def _get_platform(self) -> Platform:
        return Platform.BILIBILI

    async def fetch(self) -> Content:
        """获取B站视频信息"""
        bvid = self._extract_bvid()
        if not bvid:
            raise ValueError("无法提取BV号")

        # 尝试使用bilibili-api
        if BILIBILI_AVAILABLE and self.credential:
            try:
                return await self._fetch_with_api(bvid)
            except Exception as e:
                # 回退到直接API调用
                pass

        # 使用直接API调用
        return await self._fetch_with_http(bvid)

    async def _fetch_with_api(self, bvid: str) -> Content:
        """使用bilibili-api获取视频信息"""
        v = video.Video(bvid=bvid, credential=self.credential)
        info = await v.get_info()
        play_url = await v.get_playurl()

        # 构建作者信息
        owner = info.get("owner", {})
        author = Author(
            id=str(owner.get("mid")),
            username=owner.get("name"),
            nickname=owner.get("name"),
            avatar=owner.get("face"),
        )

        # 构建媒体文件
        media_files = self._extract_media_from_playurl(play_url)

        stat = info.get("stat", {})
        self._content = self.create_content(
            content_type=ContentType.VIDEO,
            id=bvid,
            title=info.get("title"),
            description=info.get("desc"),
            author=author,
            media_files=media_files,
            cover_url=info.get("pic"),
            likes=stat.get("like"),
            comments_count=stat.get("reply"),
            shares=stat.get("share"),
            views=stat.get("view"),
            publish_time=datetime.fromtimestamp(info.get("pubdate", 0)),
            tags=[t.get("tag_name", "") for t in info.get("tag", [])],
            raw_data=info,
        )
        return self._content

    async def _fetch_with_http(self, bvid: str) -> Content:
        """使用HTTP直接调用B站API"""
        headers = {**self.HEADERS}
        if self.cookie:
            headers["Cookie"] = self.cookie

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # 获取视频信息
            info_url = f"{self.API_BASE}/x/web-interface/view?bvid={bvid}"
            response = await client.get(info_url, headers=headers)
            data = response.json()

            if data.get("code") != 0:
                raise ValueError(f"获取视频信息失败: {data.get('message', '未知错误')}")

            info = data.get("data", {})
            aid = info.get("aid")

            # 获取播放链接
            play_url = await self._get_playurl(client, aid, bvid, headers)

            # 构建作者信息
            owner = info.get("owner", {})
            author = Author(
                id=str(owner.get("mid")),
                username=owner.get("name"),
                nickname=owner.get("name"),
                avatar=owner.get("face"),
            )

            # 构建媒体文件
            media_files = self._extract_media_from_playurl(play_url)

            stat = info.get("stat", {})
            self._content = self.create_content(
                content_type=ContentType.VIDEO,
                id=bvid,
                title=info.get("title"),
                description=info.get("desc"),
                author=author,
                media_files=media_files,
                cover_url=info.get("pic"),
                likes=stat.get("like"),
                comments_count=stat.get("reply"),
                shares=stat.get("share"),
                views=stat.get("view"),
                publish_time=datetime.fromtimestamp(info.get("pubdate", 0)),
                tags=[],
                raw_data=info,
            )
            return self._content

    async def _get_playurl(
        self, client: httpx.AsyncClient, aid: int, bvid: str, headers: Dict
    ) -> Dict:
        """获取播放链接"""
        params = {
            "bvid": bvid,
            "avid": aid,
            "qn": 64,  # 720p
            "fnval": 16,  # DASH格式
            "fourk": 1,
        }
        play_url = f"{self.API_BASE}/x/player/playurl"
        response = await client.get(play_url, params=params, headers=headers)
        data = response.json()
        return data.get("data", {})

    def _extract_media_from_playurl(self, play_url: Dict) -> List[MediaFile]:
        """从playurl中提取媒体文件"""
        media_files = []

        # DASH格式
        dash = play_url.get("dash", {})
        if dash:
            for video_dash in dash.get("video", []):
                media_files.append(
                    MediaFile(
                        url=video_dash.get("baseUrl", video_dash.get("base_url", "")),
                        type="video",
                        quality=str(video_dash.get("quality", "")),
                        format="mp4",
                        width=video_dash.get("width"),
                        height=video_dash.get("height"),
                    )
                )
            for audio_dash in dash.get("audio", []):
                media_files.append(
                    MediaFile(
                        url=audio_dash.get("baseUrl", audio_dash.get("base_url", "")),
                        type="audio",
                        format="m4a",
                    )
                )
        else:
            # 普通格式
            durl = play_url.get("durl", [])
            for item in durl:
                media_files.append(
                    MediaFile(
                        url=item.get("url", ""),
                        type="video",
                        format="flv" if item.get("url", "").endswith(".flv") else "mp4",
                    )
                )

        return media_files

    async def download(self, quality: str = "best") -> Path:
        """下载B站视频"""
        content = await self.get_info()

        # 获取视频流
        video_streams = [m for m in content.media_files if m.type == "video"]
        audio_streams = [m for m in content.media_files if m.type == "audio"]

        if not video_streams:
            raise ValueError("无视频流可下载")

        # 选择最高质量
        video_stream = video_streams[0]
        audio_stream = audio_streams[0] if audio_streams else None

        headers = {**self.HEADERS, "Referer": "https://www.bilibili.com/"}

        async with httpx.AsyncClient(follow_redirects=True) as client:
            # 下载视频
            response = await client.get(video_stream.url, headers=headers)
            response.raise_for_status()
            video_path = self.output_dir / f"{content.id}_video.m4s"
            video_path.write_bytes(response.content)

            # 下载音频
            if audio_stream:
                response = await client.get(audio_stream.url, headers=headers)
                response.raise_for_status()
                audio_path = self.output_dir / f"{content.id}_audio.m4s"
                audio_path.write_bytes(response.content)

                # 尝试使用ffmpeg合并
                output_path = self.output_dir / f"{content.id}.mp4"
                try:
                    import subprocess

                    subprocess.run(
                        [
                            "ffmpeg",
                            "-i",
                            str(video_path),
                            "-i",
                            str(audio_path),
                            "-c:v",
                            "copy",
                            "-c:a",
                            "copy",
                            str(output_path),
                            "-y",
                        ],
                        check=True,
                        capture_output=True,
                    )
                    # 删除临时文件
                    video_path.unlink(missing_ok=True)
                    audio_path.unlink(missing_ok=True)
                    return output_path
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # ffmpeg不可用，返回视频文件
                    return video_path

            return video_path

    def _extract_bvid(self) -> Optional[str]:
        """提取BV号"""
        patterns = [
            r"video/(BV[a-zA-Z0-9]+)",
            r"b23\.tv/[a-zA-Z0-9]+",
        ]
        for pattern in patterns:
            match = re.search(pattern, self.url)
            if match:
                bvid = match.group(1)
                # 如果是短链接，需要解析
                if bvid.startswith("b23.tv"):
                    return None  # 需要先解析短链接
                return bvid
        return None


class WeiboHandler(BaseHandler):
    """
    微博 Handler

    基于weibo-crawler的核心逻辑，支持通过API获取微博内容
    """

    # 微博API端点
    API_BASE = "https://m.weibo.cn/api"
    HEADERS = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://m.weibo.cn/",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "x-requested-with": "XMLHttpRequest",
    }

    def _get_platform(self) -> Platform:
        return Platform.WEIBO

    async def fetch(self) -> Content:
        """获取微博内容"""
        weibo_id = self._extract_weibo_id()
        if not weibo_id:
            raise ValueError("无法提取微博ID")

        # 获取微博信息
        weibo_info = await self._get_weibo_info(weibo_id)

        # 构建作者信息
        user_data = weibo_info.get("user", {})
        author = Author(
            id=str(user_data.get("id", "")),
            username=user_data.get("screen_name"),
            nickname=user_data.get("screen_name"),
            avatar=user_data.get("profile_image_url"),
            followers=user_data.get("followers_count"),
            verified=user_data.get("verified", False),
        )

        # 构建媒体文件
        media_files = self._extract_media(weibo_info)

        # 判断内容类型
        pics = weibo_info.get("pics", [])
        has_video = weibo_info.get("page_info", {}).get("type") == "video"

        if has_video:
            content_type = ContentType.VIDEO
        elif len(pics) > 1:
            content_type = ContentType.CAROUSEL
        elif len(pics) == 1:
            content_type = ContentType.IMAGE
        else:
            content_type = ContentType.ARTICLE

        # 提取标签
        tags = self._extract_tags(weibo_info.get("text", ""))

        self._content = self.create_content(
            content_type=content_type,
            id=weibo_id,
            title=weibo_info.get("text", "")[:100],
            description=self._clean_text(weibo_info.get("text", "")),
            author=author,
            media_files=media_files,
            cover_url=self._extract_cover(weibo_info),
            likes=weibo_info.get("attitudes_count", 0),
            comments_count=weibo_info.get("comments_count", 0),
            shares=weibo_info.get("reposts_count", 0),
            views=weibo_info.get("reads_count"),
            publish_time=self._parse_time(weibo_info.get("created_at")),
            tags=tags,
            raw_data=weibo_info,
        )

        return self._content

    async def download(self, quality: str = "best") -> Path:
        """下载微博内容"""
        content = await self.get_info()

        if not content.media_files:
            raise ValueError("无媒体文件可下载")

        headers = {**self.HEADERS, "Referer": "https://m.weibo.cn/"}
        downloaded_files = []

        async with httpx.AsyncClient(follow_redirects=True) as client:
            for i, media in enumerate(content.media_files):
                response = await client.get(media.url, headers=headers)
                response.raise_for_status()

                ext = "mp4" if media.type == "video" else "jpg"
                if len(content.media_files) > 1:
                    filepath = self.output_dir / f"{content.id}_{i + 1}.{ext}"
                else:
                    filepath = self.output_dir / f"{content.id}.{ext}"

                filepath.write_bytes(response.content)
                downloaded_files.append(filepath)

        return downloaded_files[0] if downloaded_files else self.output_dir

    def _extract_weibo_id(self) -> Optional[str]:
        """提取微博ID"""
        patterns = [
            r"weibo\.com/\d+/([a-zA-Z0-9]+)",
            r"weibo\.com/\d+/([a-zA-Z0-9]+)\?",
            r"m\.weibo\.cn/detail/(\d+)",
            r"m\.weibo\.cn/status/(\d+)",
            r"weibo\.com/(?:status|detail)/(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, self.url)
            if match:
                return match.group(1)
        return None

    async def _get_weibo_info(self, weibo_id: str) -> Dict[str, Any]:
        """获取微博信息"""
        headers = {**self.HEADERS}
        if self.cookie:
            # 处理Cookie，提取核心字段
            cookie_dict = self._parse_cookie(self.cookie)
            if cookie_dict:
                headers["Cookie"] = "; ".join(
                    [f"{k}={v}" for k, v in cookie_dict.items()]
                )

        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            # 首先尝试移动端API
            try:
                info = await self._fetch_mobile_api(client, weibo_id, headers)
                if info:
                    return info
            except Exception:
                pass

            # 回退到桌面端解析
            try:
                info = await self._fetch_desktop_page(client, weibo_id, headers)
                if info:
                    return info
            except Exception:
                pass

        raise ValueError(f"无法获取微博数据: {weibo_id}")

    async def _fetch_mobile_api(
        self, client: httpx.AsyncClient, weibo_id: str, headers: Dict
    ) -> Optional[Dict]:
        """通过移动端API获取微博"""
        # 先预热session
        await client.get("https://m.weibo.cn/", headers=headers)

        # 获取微博详情
        detail_url = f"https://m.weibo.cn/detail/{weibo_id}"
        response = await client.get(detail_url, headers=headers)
        html = response.text

        # 从HTML中提取JSON数据
        return self._extract_from_html(html, weibo_id)

    async def _fetch_desktop_page(
        self, client: httpx.AsyncClient, weibo_id: str, headers: Dict
    ) -> Optional[Dict]:
        """通过桌面端页面获取微博"""
        desktop_headers = {
            **headers,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "referer": "https://weibo.com/",
        }

        # 尝试使用Ajax API
        api_url = f"https://weibo.com/ajax/statuses/show?id={weibo_id}"
        response = await client.get(api_url, headers=desktop_headers)

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("id"):
                    return data
            except Exception:
                pass

        return None

    def _extract_from_html(self, html: str, weibo_id: str) -> Optional[Dict]:
        """从HTML中提取微博数据"""
        # 查找$render_data或类似的JSON数据
        patterns = [
            r"\$render_data\s*=\s*(\[.*?\])\s*\[0\]\s*\|\|\s*\{\}",
            r"var\s+\$render_data\s*=\s*(\[.*?\])\s*;",
            r'"status"\s*:\s*(\{[^}]*"id"\s*:\s*' + weibo_id + r"[^}]*\})",
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data_str = match.group(1)
                    # 处理JavaScript特殊值
                    data_str = re.sub(r":\s*undefined", ":null", data_str)
                    data_str = re.sub(r"//.*?\n", "\n", data_str)  # 移除注释
                    data = json.loads(data_str)

                    # 如果是数组格式
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                status = item.get("status", item)
                                if status.get("id") or status.get("bid"):
                                    return status
                    elif isinstance(data, dict):
                        return data
                except (json.JSONDecodeError, KeyError):
                    continue

        # 尝试从script标签中提取
        script_match = re.search(
            r"<script>.*?var\s+data\s*=\s*(\{.*?\});.*?</script>", html, re.DOTALL
        )
        if script_match:
            try:
                data_str = script_match.group(1).replace("undefined", "null")
                return json.loads(data_str)
            except json.JSONDecodeError:
                pass

        return None

    def _extract_media(self, weibo_info: Dict) -> List[MediaFile]:
        """提取媒体文件"""
        media_files = []

        # 提取图片
        pics = weibo_info.get("pics", [])
        for pic in pics:
            if not isinstance(pic, dict):
                continue

            # 跳过视频类型
            if pic.get("type") == "video":
                continue

            # 获取大图URL
            large = pic.get("large", {})
            url = large.get("url") if isinstance(large, dict) else pic.get("url", "")

            if url:
                # 确保URL格式正确
                url = self.format_url(url)
                media_files.append(
                    MediaFile(
                        url=url,
                        type="image",
                        format="jpg",
                    )
                )

        # 提取视频
        video_url = self._extract_video_url(weibo_info)
        if video_url:
            media_files.append(
                MediaFile(
                    url=video_url,
                    type="video",
                    format="mp4",
                )
            )

        return media_files

    def _extract_video_url(self, weibo_info: Dict) -> Optional[str]:
        """提取视频URL"""
        # 从page_info中提取
        page_info = weibo_info.get("page_info", {})
        if page_info.get("type") == "video":
            media_info = page_info.get("urls") or page_info.get("media_info")
            if media_info:
                # 尝试多种URL格式
                url = (
                    media_info.get("mp4_720p_mp4")
                    or media_info.get("mp4_hd_mp4")
                    or media_info.get("mp4_hd_url")
                    or media_info.get("mp4_sd_mp4")
                    or media_info.get("stream_url_hd")
                    or media_info.get("stream_url")
                )
                if url:
                    return self.format_url(url)

        # 从pics中提取视频
        pics = weibo_info.get("pics", [])
        for pic in pics:
            if isinstance(pic, dict) and pic.get("type") == "video":
                video_src = pic.get("videoSrc") or pic.get("video_src")
                if video_src:
                    return self.format_url(video_src)

        # 检查live_photo
        live_photo = weibo_info.get("live_photo", [])
        if live_photo and isinstance(live_photo, list):
            return self.format_url(live_photo[0])

        return None

    def _extract_cover(self, weibo_info: Dict) -> Optional[str]:
        """提取封面图"""
        # 从page_info中提取
        page_info = weibo_info.get("page_info", {})
        if page_info:
            page_pic = page_info.get("page_pic", {})
            if isinstance(page_pic, dict):
                return page_pic.get("url")
            elif isinstance(page_pic, str):
                return page_pic

        # 从pics中提取
        pics = weibo_info.get("pics", [])
        if pics and isinstance(pics[0], dict):
            large = pics[0].get("large", {})
            if isinstance(large, dict):
                return large.get("url")
            return pics[0].get("url")

        return None

    def _extract_tags(self, text: str) -> List[str]:
        """从文本中提取话题标签"""
        if not text:
            return []
        return re.findall(r"#([^#]+)#", text)

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        # 移除HTML标签
        text = re.sub(r"<[^>]+>", "", text)
        # 移除多余空白
        text = re.sub(r"\s+", " ", text).strip()
        return text


    def _parse_cookie(self, cookie_str: str) -> Dict[str, str]:
        """解析Cookie字符串"""
        if not cookie_str:
            return {}

        cookie_dict = {}
        for pair in cookie_str.split(";"):
            pair = pair.strip()
            if "=" in pair:
                key, value = pair.split("=", 1)
                cookie_dict[key.strip()] = value.strip()

        return cookie_dict

    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """解析时间"""
        if not time_str:
            return None

        formats = [
            "%a %b %d %H:%M:%S %z %Y",  # Wed Mar 15 10:30:00 +0800 2024
            "%Y-%m-%d %H:%M:%S",  # 2024-03-15 10:30:00
            "%Y-%m-%dT%H:%M:%S",  # 2024-03-15T10:30:00
            "%Y-%m-%d",  # 2024-03-15
        ]

        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue

        return None


class WeixinHandler(BaseHandler):
    """
    微信公众号 Handler

    基于 wechat-article-exporter 公开 API 获取文章内容
    无需登录或密钥，直接抓取公众号文章
    """

    # wechat-article-exporter API
    API_BASE = "https://down.mptext.top/api/public/v1/download"

    # 请求头
    HEADERS = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def _get_platform(self) -> Platform:
        return Platform.WEIXIN

    async def fetch(self) -> Content:
        """获取微信公众号文章内容"""
        # 验证URL
        if "mp.weixin.qq.com" not in self.url:
            raise ValueError("无效的微信公众号文章链接")

        # 获取文章信息
        article_info = await self._get_article_info()

        # 构建作者信息
        author = Author(
            nickname=article_info.get("author", ""),
        )

        # 提取文章中的图片
        media_files = self._extract_images(article_info)

        # 提取标签
        tags = self._extract_tags(article_info.get("content", ""))

        self._content = self.create_content(
            content_type=ContentType.ARTICLE,
            id=self._extract_article_id(),
            title=article_info.get("title", ""),
            description=article_info.get("description", ""),
            author=author,
            media_files=media_files,
            cover_url=article_info.get("cover_url"),
            tags=tags,
            raw_data=article_info,
        )

        return self._content

    async def download(self, quality: str = "best") -> Path:
        """下载微信公众号文章（保存为Markdown）"""
        content = await self.get_info()

        # 生成Markdown内容
        markdown_content = self._to_markdown(content)

        # 保存文件
        filename = self._sanitize_filename(content.title or "article")
        filepath = self.output_dir / f"{filename}.md"

        filepath.write_text(markdown_content, encoding="utf-8")

        # 下载封面图（如果有）
        if content.cover_url:
            try:
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.get(content.cover_url, headers=self.HEADERS)
                    if response.status_code == 200:
                        cover_path = self.output_dir / f"{filename}_cover.jpg"
                        cover_path.write_bytes(response.content)
            except Exception:
                pass

        return filepath

    async def _get_article_info(self) -> Dict[str, Any]:
        """通过API获取文章信息"""
        from urllib.parse import quote

        encoded_url = quote(self.url, safe="")
        api_url = f"{self.API_BASE}?url={encoded_url}&format=json"

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            response = await client.get(api_url, headers=self.HEADERS)

            if response.status_code != 200:
                raise ValueError(f"获取文章失败: HTTP {response.status_code}")

            try:
                data = response.json()
                return data
            except Exception:
                # 如果JSON解析失败，尝试获取markdown格式
                api_url = f"{self.API_BASE}?url={encoded_url}&format=markdown"
                response = await client.get(api_url, headers=self.HEADERS)
                return {
                    "title": "",
                    "content": response.text,
                    "author": "",
                    "cover_url": None,
                }

    def _extract_article_id(self) -> str:
        """从URL提取文章ID"""
        # 尝试提取 /s/ 后面的ID
        match = re.search(r"/s/([a-zA-Z0-9_-]+)", self.url)
        if match:
            return match.group(1)

        # 如果没有，使用URL的hash
        return str(hash(self.url) % 10000000000)

    def _extract_images(self, article_info: Dict) -> List[MediaFile]:
        """从文章内容中提取图片"""
        media_files = []
        content = article_info.get("content", "")

        # 从HTML内容中提取图片URL
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(img_pattern, content)

        for img_url in matches:
            if img_url.startswith("//"):
                img_url = f"https:{img_url}"
            media_files.append(
                MediaFile(
                    url=img_url,
                    type="image",
                    format="jpg",
                )
            )

        return media_files

    def _extract_tags(self, content: str) -> List[str]:
        """从内容中提取标签"""
        # 微信文章通常没有明确的标签，返回空列表
        return []

    def _to_markdown(self, content: Content) -> str:
        """将文章内容转换为Markdown格式"""
        lines = []

        # 标题
        if content.title:
            lines.append(f"# {content.title}")
            lines.append("")

        # 元信息
        if content.author and content.author.nickname:
            lines.append(f"**作者:** {content.author.nickname}")
        lines.append(f"**链接:** {content.url}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 正文内容（从raw_data获取）
        raw_content = content.raw_data.get("content", "")
        if raw_content:
            # 简单的HTML转Markdown
            md_content = self._html_to_markdown(raw_content)
            lines.append(md_content)
        else:
            # 尝试获取markdown格式
            lines.append(content.raw_data.get("markdown", ""))

        return "\n".join(lines)

    def _html_to_markdown(self, html: str) -> str:
        """简单的HTML转Markdown"""
        if not html:
            return ""

        # 替换常见的HTML标签
        text = html

        # 标题
        for i in range(6, 0, -1):
            text = re.sub(
                rf"<h{i}[^>]*>(.*?)</h{i}>",
                lambda m: f"\n{'#' * i} {m.group(1)}\n",
                text,
                flags=re.DOTALL,
            )

        # 段落
        text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", text, flags=re.DOTALL)

        # 换行
        text = re.sub(r"<br\s*/?>", "\n", text)

        # 粗体
        text = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", text, flags=re.DOTALL)

        # 斜体
        text = re.sub(r"<(em|i)[^>]*>(.*?)</\1>", r"*\2*", text, flags=re.DOTALL)

        # 链接
        text = re.sub(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            r"[\2](\1)",
            text,
            flags=re.DOTALL,
        )

        # 图片
        text = re.sub(
            r'<img[^>]+src=["\']([^"\']+)["\'][^>]*/?>',
            r"![](\1)",
            text,
        )

        # 列表
        text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1", text, flags=re.DOTALL)

        # 移除其他HTML标签
        text = re.sub(r"<[^>]+>", "", text)

        # 处理HTML实体
        text = text.replace("&nbsp;", " ")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        text = text.replace("&quot;", '"')

        # 清理多余空白
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        return text

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        # 移除非法字符
        filename = re.sub(r'[<>:"/\\|?*]', "", filename)
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename.strip() or "article"
