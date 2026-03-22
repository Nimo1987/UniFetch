# 社交媒体统一下载工具 - 功能说明文档

## 📋 项目概述

社交媒体统一下载工具是一个通用的内容获取平台，支持中美两国主流社交媒体和金融数据，提供统一的API接口、CLI命令行和LLM内容分析功能。

---

## 🌐 支持平台总览

| 类别 | 平台 | 状态 | 实现方案 |
|------|------|------|----------|
| **国际社交** | YouTube | ✅ | yt-dlp |
| | Twitter/X | ✅ | yt-dlp |
| | Facebook | ✅ | yt-dlp |
| | Instagram | ✅ | instaloader |
| | TikTok | ✅ | yt-dlp |
| | Reddit | ✅ | yt-dlp |
| **中国社交** | 小红书 | ✅ | HTML解析 |
| | 抖音 | ✅ | HTML解析 |
| | B站 | ✅ | bilibili-api |
| | 微博 | ✅ | API调用 |
| | 微信公众号 | ✅ | wechat-article-exporter API |
| **金融数据** | A股 | ✅ | akshare |
| | 港股 | ✅ | akshare |
| | 美股 | ✅ | akshare |

---

## 📱 社交媒体功能详解

### 1. YouTube

**支持内容类型：**
- 单个视频
- 播放列表
- 频道视频

**获取数据：**
```python
{
    "id": "视频ID",
    "title": "视频标题",
    "description": "视频描述",
    "author": {"id", "username", "nickname"},
    "duration": 180,  # 秒
    "views": 1000000,
    "likes": 50000,
    "comments_count": 2000,
    "publish_time": "2024-01-01",
    "tags": ["标签1", "标签2"],
    "media_files": [
        {"url": "视频流地址", "quality": "1080p", "format": "mp4"},
        {"url": "音频流地址", "format": "m4a"}
    ]
}
```

**使用示例：**
```python
from social_downloader import Downloader
import asyncio

async def main():
    dl = Downloader()
    
    # 获取视频信息
    result = await dl.fetch("https://www.youtube.com/watch?v=xxx")
    print(f"标题: {result.content.title}")
    print(f"播放量: {result.content.views}")
    
    # 下载视频
    result = await dl.download("https://www.youtube.com/watch?v=xxx", quality="1080p")

asyncio.run(main())
```

---

### 2. Twitter/X

**支持内容类型：**
- 推文（含图片/视频）
- 用户主页

**获取数据：**
```python
{
    "id": "推文ID",
    "content": "推文内容",
    "author": {"username", "nickname", "avatar"},
    "likes": 1000,
    "retweets": 500,
    "replies": 100,
    "media_files": [
        {"url": "图片/视频地址", "type": "image/video"}
    ]
}
```

---

### 3. Facebook

**支持内容类型：**
- 视频
- 帖子（含图片）
- 公开页面内容

---

### 4. Instagram

**支持内容类型：**
- 帖子（单图/多图/视频）
- Reels
- Stories（需登录）

**获取数据：**
```python
{
    "id": "shortcode",
    "caption": "帖子描述",
    "author": {"username", "nickname"},
    "likes": 5000,
    "comments_count": 200,
    "is_video": False,
    "media_files": [
        {"url": "图片地址", "type": "image"}
    ]
}
```

---

### 5. TikTok

**支持内容类型：**
- 短视频
- 用户主页

**获取数据：**
```python
{
    "id": "视频ID",
    "description": "视频描述",
    "author": {"username", "nickname"},
    "likes": 100000,
    "comments_count": 5000,
    "shares": 2000,
    "views": 1000000,
    "duration": 15,
    "media_files": [{"url": "视频地址", "format": "mp4"}]
}
```

---

### 6. Reddit

**支持内容类型：**
- 帖子（含图片/视频）
- 评论

---

### 7. 小红书

**支持内容类型：**
- 图文笔记
- 视频笔记
- 图集笔记

**实现方式：**
- 解析页面HTML中的 `window.__INITIAL_STATE__` 数据
- 提取笔记内容、作者信息、媒体文件

**获取数据：**
```python
{
    "id": "笔记ID",
    "title": "笔记标题",
    "description": "笔记内容",
    "author": {"user_id", "nickname", "avatar"},
    "likes": 5000,
    "comments_count": 300,
    "saves": 1000,
    "tags": ["标签1", "标签2"],
    "media_files": [
        {"url": "图片/视频地址", "type": "image/video"}
    ]
}
```

**使用示例：**
```python
dl = Downloader()
result = await dl.download("https://www.xiaohongshu.com/explore/xxx")
# 下载图片/视频到本地
```

---

### 8. 抖音

**支持内容类型：**
- 短视频

**实现方式：**
- 解析页面HTML中的 `RENDER_DATA` 数据
- 支持短链接解析（v.douyin.com）

**获取数据：**
```python
{
    "id": "视频ID",
    "description": "视频描述",
    "author": {"uid", "unique_id", "nickname", "avatar"},
    "likes": 100000,
    "comments_count": 5000,
    "shares": 2000,
    "views": 5000000,
    "tags": ["话题标签"],
    "media_files": [{"url": "无水印视频地址", "format": "mp4"}]
}
```

---

### 9. B站（Bilibili）

**支持内容类型：**
- 普通视频
- 番剧/影视

**实现方式：**
- 优先使用 `bilibili-api-python`
- 回退到直接HTTP API调用
- 支持ffmpeg合并视频+音频

**获取数据：**
```python
{
    "id": "BV号",
    "title": "视频标题",
    "description": "视频简介",
    "author": {"mid", "name", "face"},
    "likes": 50000,
    "coins": 10000,
    "favorites": 20000,
    "views": 1000000,
    "duration": 600,
    "tags": ["标签"],
    "media_files": [
        {"url": "视频流", "type": "video", "quality": "1080p"},
        {"url": "音频流", "type": "audio"}
    ]
}
```

---

### 10. 微博

**支持内容类型：**
- 普通微博（文字/图片）
- 视频微博
- 长文章

**实现方式：**
- 支持移动端API
- 支持桌面端Ajax API
- Cookie认证（可选）

**获取数据：**
```python
{
    "id": "微博ID",
    "text": "微博内容",
    "author": {"id", "screen_name", "avatar", "verified"},
    "likes": 5000,
    "comments_count": 1000,
    "reposts_count": 2000,
    "pics": [{"url": "图片地址"}],
    "video_url": "视频地址",
    "created_at": "发布时间"
}
```

---

### 11. 微信公众号

**支持内容类型：**
- 公众号文章

**实现方式：**
- 使用 `wechat-article-exporter` 公开API
- 无需登录或密钥
- 支持Markdown/HTML/JSON/TXT格式输出

**获取数据：**
```python
{
    "id": "文章ID",
    "title": "文章标题",
    "description": "文章摘要",
    "author": {"nickname": "作者名"},
    "cover_url": "封面图地址",
    "content": "文章正文(HTML)",
    "markdown": "Markdown格式正文",
    "images": ["图片地址列表"]
}
```

**使用示例：**
```python
dl = Downloader()

# 获取文章内容
result = await dl.fetch("https://mp.weixin.qq.com/s/xxx")
print(f"标题: {result.content.title}")

# 下载为Markdown
result = await dl.download("https://mp.weixin.qq.com/s/xxx")
# 保存为 xxx.md 文件
```

---

## 💰 金融数据功能详解

### 功能概述

基于 `akshare` 库实现，支持A股、港股、美股的财务数据获取。**已验证可用。**

### URL格式

| 市场 | URL格式 | 示例 |
|------|---------|------|
| A股 | `finance://{股票代码}` | `finance://000001` (平安银行) |
| A股-财报 | `finance://{股票代码}?report={类型}` | `finance://000001?report=income` |
| 港股 | `finance://hk:{股票代码}` | `finance://hk:00700` (腾讯) |
| 美股 | `finance://us:{股票代码}` | `finance://us:AAPL` (苹果) |

### 报告类型

| report参数 | 说明 | 适用市场 |
|------------|------|----------|
| `info` | 公司基本信息（默认） | A股/港股/美股 |
| `income` | 利润表 | A股 |
| `balance` | 资产负债表 | A股 |
| `cashflow` | 现金流量表 | A股 |
| `history` | 历史行情K线 | A股/港股/美股 |
| `financial` | 财务指标 | 港股/美股 |

### 已验证支持的数据类型

#### A股

| 数据类型 | 说明 | report参数 |
|----------|------|------------|
| 公司信息 | 股票代码、名称、行业、市值、上市时间等 | `info` |
| 历史行情 | K线数据（日/周/月） | `history` |
| 利润表 | 营业收入、净利润等 | `income` |
| 资产负债表 | 总资产、总负债等 | `balance` |
| 现金流量表 | 经营/投资/筹资现金流 | `cashflow` |

#### 港股

| 数据类型 | 说明 | report参数 |
|----------|------|------------|
| 实时行情 | 股价、涨跌幅、成交量、市值 | `info` |
| 历史行情 | K线数据 | `history` |
| 财务指标 | ROE、PE、PB等 | `financial` |

#### 美股

| 数据类型 | 说明 | report参数 |
|----------|------|------------|
| 实时行情 | 股价、市值 | `info` |
| 历史行情 | K线数据 | `history` |
| 财务数据 | 收入、利润、资产负债 | `financial` |

#### 美股

| 数据类型 | 说明 |
|----------|------|
| 实时行情 | 股价、市值 |
| 历史行情 | K线数据 |
| 财务数据 | 收入、利润、资产负债 |

### 使用示例

```python
from social_downloader import Downloader
import asyncio

async def main():
    dl = Downloader()
    
    # ===== A股数据 =====
    
    # 获取A股公司信息
    result = await dl.fetch("finance://000001")  # 平安银行
    print(f"公司: {result.content.title}")
    print(f"行业: {result.content.raw_data.get('industry')}")
    print(f"市值: {result.content.raw_data.get('market_cap')}")
    
    # 获取利润表
    result = await dl.fetch("finance://000001?report=income")
    df = result.content.raw_data.get('dataframe')  # pandas DataFrame
    print(df.head())
    
    # 获取资产负债表
    result = await dl.fetch("finance://600519?report=balance")  # 贵州茅台
    
    # 获取现金流量表
    result = await dl.fetch("finance://000858?report=cashflow")  # 五粮液
    
    # 获取历史行情
    result = await dl.fetch("finance://000001?report=history")
    
    # 下载数据为CSV
    result = await dl.download("finance://000001?report=income")
    print(f"保存到: {result.content.id}.csv")
    
    # ===== 港股数据 =====
    
    # 获取腾讯控股信息
    result = await dl.fetch("finance://hk:00700")
    print(f"公司: {result.content.title}")
    
    # 获取港股历史行情
    result = await dl.fetch("finance://hk:00700?report=history")
    
    # ===== 美股数据 =====
    
    # 获取苹果公司信息
    result = await dl.fetch("finance://us:AAPL")
    print(f"公司: {result.content.title}")
    
    # 获取美股历史行情
    result = await dl.fetch("finance://us:AAPL?report=history")

asyncio.run(main())
```

### CLI使用

```bash
# 获取A股公司信息
social-downloader download "finance://000001"

# 获取利润表
social-downloader download "finance://000001?report=income"

# 获取港股信息
social-downloader download "finance://hk:00700"

# 获取美股信息
social-downloader download "finance://us:AAPL"
```

### 数据来源

- **东方财富** - A股行情、财务数据
- **新浪财经** - 港股、美股数据
- **同花顺** - 财务分析指标

---

## 🔧 核心功能

### 1. URL自动识别

```python
from social_downloader import URLRouter

# 自动识别平台
result = URLRouter.parse("https://www.youtube.com/watch?v=xxx")
# result = {
#     "url": "https://www.youtube.com/watch?v=xxx",
#     "platform": Platform.YOUTUBE,
#     "content_id": "xxx",
#     "content_type": "video",
#     "supported": True
# }
```

### 2. 统一下载接口

```python
from social_downloader import Downloader
import asyncio

async def download_any(url: str):
    dl = Downloader(output_dir="./downloads")
    
    # 同一接口支持所有平台
    result = await dl.download(url, quality="best")
    
    if result.success:
        print(f"下载成功: {result.content.title}")
    else:
        print(f"下载失败: {result.error}")

# 使用
asyncio.run(download_any("https://www.youtube.com/watch?v=xxx"))
asyncio.run(download_any("https://www.xiaohongshu.com/explore/xxx"))
asyncio.run(download_any("https://mp.weixin.qq.com/s/xxx"))
```

### 3. 内容分析（LLM）

```python
async def analyze_content(url: str):
    dl = Downloader()
    result = await dl.analyze(url)
    
    if result.success:
        print(f"摘要: {result.analysis.summary}")
        print(f"情感: {result.analysis.sentiment}")
        print(f"话题: {result.analysis.topics}")
        print(f"关键词: {result.analysis.keywords}")
        print(f"分类: {result.analysis.category}")
```

### 4. 批量处理

```python
async def batch_download(urls: list):
    dl = Downloader()
    results = await dl.batch_analyze(urls)
    
    for result in results:
        if result.success:
            print(f"✓ {result.content.title}")
        else:
            print(f"✗ {result.error}")
```

---

## 🖥️ 命令行界面 (CLI)

### 基本命令

```bash
# 下载单个URL
social-downloader download "https://www.youtube.com/watch?v=xxx"

# 批量下载
social-downloader batch URL1 URL2 URL3

# 从文件批量下载
social-downloader batch -f urls.txt

# 仅获取信息（不下载）
social-downloader download --info-only "URL"

# 分析内容
social-downloader analyze "URL"

# 输出JSON格式
social-downloader download --json-output "URL"
```

### 配置管理

```bash
# 查看当前配置
social-downloader config show

# 设置Cookie
social-downloader config set-cookie xiaohongshu "your_cookie"
social-downloader config set-cookie weibo "your_cookie"

# 设置代理
social-downloader config set-proxy "socks5://127.0.0.1:1080"

# 设置下载目录
social-downloader config set-download-dir "/path/to/downloads"

# 导出/导入配置
social-downloader config export config.json
social-downloader config import config.json
```

### 其他命令

```bash
# 查看支持的平台
social-downloader platforms

# 检查URL是否支持
social-downloader check "URL"

# 查看版本
social-downloader --version
```

---

## 🌐 HTTP API 服务

### 启动服务

```bash
python -m social_downloader.api.server
# 或
uvicorn social_downloader.api.server:app --host 0.0.0.0 --port 8000
```

### API端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务信息 |
| POST | `/fetch` | 获取URL内容信息 |
| POST | `/download` | 下载URL内容 |
| POST | `/analyze` | 分析URL内容 |
| POST | `/batch/fetch` | 批量获取 |
| GET | `/platforms` | 支持的平台列表 |
| GET | `/check?url=xxx` | 检查URL支持 |
| GET | `/config` | 获取配置 |
| POST | `/config/cookie` | 设置Cookie |
| POST | `/config/proxy` | 设置代理 |

### API使用示例

```python
import httpx
import asyncio

async def use_api():
    async with httpx.AsyncClient() as client:
        # 获取内容信息
        response = await client.post("http://localhost:8000/fetch", json={
            "url": "https://www.youtube.com/watch?v=xxx"
        })
        data = response.json()
        print(data["content"]["title"])
        
        # 下载内容
        response = await client.post("http://localhost:8000/download", json={
            "url": "https://www.xiaohongshu.com/explore/xxx",
            "quality": "best"
        })

asyncio.run(use_api())
```

---

## ⚙️ 配置文件

配置文件位置：`~/.social_downloader/config.json`

```json
{
    "cookies": {
        "xiaohongshu": "cookie_string",
        "douyin": "cookie_string",
        "bilibili": "cookie_string",
        "weibo": "cookie_string",
        "instagram": "cookie_string"
    },
    "proxy": {
        "enabled": true,
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890",
        "socks5": "socks5://127.0.0.1:1080"
    },
    "download": {
        "directory": "./downloads",
        "quality": "best",
        "max_concurrent": 3,
        "timeout": 30,
        "retry_count": 3,
        "skip_existing": true,
        "organize_by_platform": true
    },
    "llm": {
        "enabled": false,
        "api_url": "https://api.openai.com/v1",
        "api_key": "sk-xxx",
        "model": "gpt-3.5-turbo"
    }
}
```

### 环境变量支持

```bash
# Cookie
export XHS_COOKIE="your_cookie"
export DOUYIN_COOKIE="your_cookie"
export WEIBO_COOKIE="your_cookie"

# 代理
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"

# 下载目录
export DOWNLOAD_DIR="/path/to/downloads"

# LLM
export LLM_API_URL="https://api.openai.com/v1"
export LLM_API_KEY="sk-xxx"
```

---

## 📊 数据模型

### Content (内容)

```python
@dataclass
class Content:
    url: str                          # 原始URL
    platform: Platform                # 平台
    content_type: ContentType         # 类型
    id: Optional[str]                 # 内容ID
    title: Optional[str]              # 标题
    description: Optional[str]        # 描述
    author: Optional[Author]          # 作者
    media_files: List[MediaFile]      # 媒体文件列表
    cover_url: Optional[str]          # 封面图
    likes: Optional[int]              # 点赞数
    comments_count: Optional[int]     # 评论数
    shares: Optional[int]             # 转发/分享数
    views: Optional[int]              # 播放/阅读数
    saves: Optional[int]              # 收藏数
    tags: List[str]                   # 标签
    publish_time: Optional[datetime]  # 发布时间
    fetch_time: Optional[datetime]    # 获取时间
    raw_data: Dict[str, Any]          # 原始数据
```

### AnalysisResult (分析结果)

```python
@dataclass
class AnalysisResult:
    summary: str                      # 内容摘要
    sentiment: str                    # 情感 (positive/negative/neutral)
    sentiment_score: float            # 情感分数 (0-1)
    topics: List[str]                 # 话题
    keywords: List[str]               # 关键词
    key_points: List[str]             # 要点
    language: str                     # 语言
    quality_score: float              # 质量分数 (0-10)
    recommendation: str               # 推荐/不推荐
    category: str                     # 分类
    subcategory: str                  # 子分类
```

---

## 🔒 注意事项

### Cookie使用

部分平台需要Cookie才能获取完整内容：
- **小红书**: 获取高清图片
- **微博**: 访问完整内容
- **Instagram**: 访问部分帖子

### 代理设置

以下平台在某些地区可能需要代理：
- YouTube
- Twitter/X
- Facebook
- Instagram
- TikTok
- Reddit

### 法律合规

- 请遵守各平台的使用条款
- 仅用于个人学习和研究目的
- 不要进行大规模爬取或商业使用
- 尊重内容创作者的版权

---

## 📦 依赖说明

### 核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| yt-dlp | >=2026.3.0 | 国际平台视频下载 |
| instaloader | >=4.15.0 | Instagram专用 |
| bilibili-api-python | >=17.0.0 | B站API |
| httpx | >=0.28.0 | 异步HTTP客户端 |
| click | >=8.0.0 | CLI框架 |
| rich | >=13.7.0 | 终端美化 |
| pydantic | >=2.0.0 | 数据验证 |
| akshare | >=1.18.0 | 金融数据 |

### 可选依赖

| 包名 | 用途 |
|------|------|
| fastapi | HTTP API服务 |
| uvicorn | ASGI服务器 |
| openai | LLM分析 |
| ffmpeg | 视频合并（系统依赖） |

---

## 🚀 快速开始

### 安装

```bash
pip install social-downloader
```

### 基本使用

```python
from social_downloader import Downloader
import asyncio

async def main():
    dl = Downloader()
    
    # 下载任意平台内容
    url = input("请输入URL: ")
    result = await dl.download(url)
    
    if result.success:
        print(f"下载成功: {result.content.title}")
    else:
        print(f"下载失败: {result.error}")

asyncio.run(main())
```

### CLI使用

```bash
# 下载
social-downloader download "https://www.youtube.com/watch?v=xxx"

# 配置
social-downloader config set-proxy "socks5://127.0.0.1:1080"
```

---

## 📝 更新日志

### v1.0.0 (2024-03-22)

- ✅ 支持11个主流社交平台
- ✅ 统一API接口
- ✅ CLI命令行工具
- ✅ HTTP API服务
- ✅ 配置管理
- ✅ 金融数据支持（A股/港股/美股）
