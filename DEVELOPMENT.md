# 社交媒体统一下载工具 - 开发文档

## 📋 项目概述

### 目标
构建一个通用的社交媒体下载工具，支持中美两国主流平台，提供统一的API接口和LLM内容分析功能。

### 核心功能
1. **URL自动识别** - 根据URL判断平台
2. **统一下载接口** - 一个接口支持所有平台
3. **LLM内容分析** - 自动分析内容摘要、情感、话题等
4. **CLI和API** - 提供命令行和HTTP API两种使用方式

### 支持平台

| 平台 | 类型 | 当前状态 | 实现方案 |
|------|------|----------|----------|
| YouTube | 国际 | ✅ 可用 | yt-dlp |
| Twitter/X | 国际 | ✅ 可用 | yt-dlp |
| Facebook | 国际 | ✅ 可用 | yt-dlp |
| TikTok | 国际 | ✅ 可用 | yt-dlp |
| Reddit | 国际 | ✅ 可用 | yt-dlp |
| Instagram | 国际 | ✅ 可用 | instaloader |
| 小红书 | 中国 | ✅ 已实现 | HTML解析 |
| 抖音 | 中国 | ✅ 已实现 | HTML解析 |
| B站 | 中国 | ✅ 可用 | bilibili-api + HTTP |
| 微博 | 中国 | ✅ 已实现 | API调用 |

---

## 🏗️ 架构设计

### 目录结构

```
social_downloader/
├── __init__.py              # 包入口，导出主要类
├── downloader.py            # 统一下载器主类
├── requirements.txt         # 依赖列表
│
├── core/
│   ├── __init__.py
│   ├── router.py            # URL路由器（平台识别）
│   ├── base_handler.py      # Handler基类（抽象类）
│   ├── config.py            # 配置管理
│   └── llm_analyzer.py      # LLM分析器
│
├── models/
│   ├── __init__.py
│   └── content.py           # 数据模型（Content, AnalysisResult等）
│
├── china/
│   ├── __init__.py
│   └── handlers.py          # 中国平台Handler（小红书、抖音、B站、微博）
│
├── international/
│   ├── __init__.py
│   └── handlers.py          # 国际平台Handler（YouTube、Twitter等）
│
├── handlers/
│   └── __init__.py          # 预留的独立Handler目录
│
├── cli/
│   ├── __init__.py
│   └── main.py              # CLI入口
│
├── api/
│   ├── __init__.py
│   └── server.py            # FastAPI服务
│
└── utils/
    └── __init__.py          # 工具函数
```

### 核心流程

```
用户输入URL
    ↓
URLRouter.detect_platform(url)
    ↓
返回 Platform 枚举
    ↓
根据 Platform 创建对应 Handler
    ↓
Handler.fetch() 获取内容信息
    ↓
LLMAnalyzer.analyze(content) 分析内容
    ↓
返回 FetchResult(content + analysis)
```

### 数据模型

```python
# Platform - 平台枚举
class Platform(Enum):
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    BILIBILI = "bilibili"
    WEIBO = "weibo"
    # ...

# Content - 内容模型
@dataclass
class Content:
    url: str                          # 原始URL
    platform: Platform                # 平台
    content_type: ContentType         # 类型(video/image/article)
    id: Optional[str]                 # 内容ID
    title: Optional[str]              # 标题
    description: Optional[str]        # 描述
    author: Optional[Author]          # 作者
    media_files: List[MediaFile]      # 媒体文件列表
    likes: Optional[int]              # 点赞数
    comments_count: Optional[int]     # 评论数
    views: Optional[int]              # 播放数
    tags: List[str]                   # 标签
    raw_data: Dict[str, Any]          # 原始数据

# FetchResult - 获取结果
@dataclass
class FetchResult:
    success: bool
    content: Optional[Content]
    analysis: Optional[AnalysisResult]
    error: Optional[str]
```

---

## 🔧 各模块详解

### 1. URL路由器 (core/router.py)

**职责**: 识别URL所属平台

**实现要点**:
```python
# URL模式匹配规则
URL_PATTERNS = {
    Platform.YOUTUBE: [r"(?:youtube\.com|youtu\.be)"],
    Platform.TWITTER: [r"(?:twitter\.com|x\.com)"],
    Platform.FACEBOOK: [r"(?:facebook\.com|fb\.watch)"],
    Platform.INSTAGRAM: [r"(?:instagram\.com)"],
    Platform.TIKTOK: [r"(?:tiktok\.com|vm\.tiktok\.com)"],
    Platform.XIAOHONGSHU: [r"(?:xiaohongshu\.com|xhslink\.com)"],
    Platform.DOUYIN: [r"(?:douyin\.com|v\.douyin\.com)"],
    Platform.BILIBILI: [r"(?:bilibili\.com|b23\.tv)"],
    Platform.WEIBO: [r"(?:weibo\.com|weibo\.cn)"],
}

# 使用正则匹配
def detect_platform(url: str) -> Platform:
    for platform, patterns in URL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url.lower()):
                return platform
    return Platform.UNKNOWN
```

### 2. Handler基类 (core/base_handler.py)

**职责**: 定义所有平台Handler的统一接口

**实现要点**:
```python
class BaseHandler(ABC):
    def __init__(self, url: str, proxy: str = None, cookie: str = None):
        self.url = url
        self.proxy = proxy
        self.cookie = cookie
    
    @abstractmethod
    async def fetch(self) -> Content:
        """获取内容信息"""
        pass
    
    @abstractmethod
    async def download(self, quality: str = "best") -> Path:
        """下载内容"""
        pass
```

### 3. 国际平台Handler

**通用方案**: 使用 yt-dlp

```python
class YtDlpHandler(BaseHandler):
    async def fetch(self) -> Content:
        ydl_opts = {'quiet': True, 'proxy': self.proxy}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)
            return self._parse_info(info)
    
    async def download(self, quality: str = "best") -> Path:
        ydl_opts = {'format': self._get_format(quality), 'outtmpl': '...'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])
            return Path(...)
```

**支持平台**: YouTube, Twitter, Facebook, TikTok, Reddit, B站

### 4. 中国平台Handler

#### 小红书 (handlers/xiaohongshu.py)

**参考项目**: XHS-Downloader (https://github.com/JoeanAmier/XHS-Downloader)

**实现要点**:
- 提取笔记ID: `https://www.xiaohongshu.com/explore/{note_id}`
- 调用小红书API获取笔记信息
- 处理图片/视频下载链接
- 可能需要处理xs签名算法

**核心代码参考**:
```python
# 从 XHS-Downloader/source/module/manager.py 学习
class XHSHandler(BaseHandler):
    async def fetch(self) -> Content:
        note_id = self._extract_note_id()
        # 调用小红书API
        api_url = f"https://edith.xiaohongshu.com/api/sns/web/v1/feed"
        # 需要生成签名参数
        headers = self._generate_headers()
        data = {"source_note_id": note_id}
        # ...
```

#### 抖音 (handlers/douyin.py)

**参考项目**: douyin-downloader (https://github.com/jiji262/douyin-downloader)

**实现要点**:
- 提取视频ID: `https://www.douyin.com/video/{aweme_id}`
- 处理短链接解析: `https://v.douyin.com/xxx`
- 实现a_bogus和X-Bogus签名算法
- 调用抖音API获取无水印视频

**核心代码参考**:
```python
# 从 douyin-downloader/core/ 学习
class DouyinHandler(BaseHandler):
    async def fetch(self) -> Content:
        video_id = self._extract_video_id()
        # 可能需要解析短链接
        if not video_id:
            url = await self._resolve_short_url()
            video_id = self._extract_id_from_url(url)
        # 调用抖音API
        # 需要处理签名算法
        # ...
```

#### B站 (handlers/bilibili.py)

**方案**: 使用 yt-dlp（已验证可用）

```python
class BilibiliHandler(BaseHandler):
    # 直接继承 YtDlpHandler 即可
    # yt-dlp 已经支持B站
    pass
```

#### 微博 (handlers/weibo.py)

**参考项目**: weibo-crawler (https://github.com/dataabc/weibo-crawler)

**实现要点**:
- 提取微博ID
- 需要Cookie认证
- 调用微博API获取内容
- 下载图片/视频

**核心代码参考**:
```python
# 从 weibo-crawler/weibo.py 学习
class WeiboHandler(BaseHandler):
    async def fetch(self) -> Content:
        weibo_id = self._extract_weibo_id()
        # 需要Cookie认证
        headers = {"Cookie": self.cookie}
        # 调用微博API
        # ...
```

#### Instagram (handlers/instagram.py)

**方案**: 使用 instaloader

```python
class InstagramHandler(BaseHandler):
    def __init__(self, url, **kwargs):
        super().__init__(url, **kwargs)
        self.loader = instaloader.Instaloader()
    
    async def fetch(self) -> Content:
        shortcode = self._extract_shortcode()
        post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
        return self._parse_post(post)
```

### 5. LLM分析器 (core/llm_analyzer.py)

**职责**: 调用LLM分析内容

**实现要点**:
```python
class LLMAnalyzer:
    async def analyze(self, content: Content) -> AnalysisResult:
        prompt = self._build_prompt(content)
        response = await self._call_llm(prompt)
        return self._parse_response(response)
    
    async def _call_llm(self, prompt: str) -> str:
        # 调用OpenAI API或内部LLM
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                json={"model": self.model, "messages": [...]}
            )
            return response.json()["choices"][0]["message"]["content"]
```

**LLM提示词模板**:
```
请分析以下社交媒体内容：

平台: {platform}
标题: {title}
描述: {description}
作者: {author}
统计: 点赞{likes}, 评论{comments}, 播放{views}
标签: {tags}

请以JSON格式返回分析结果：
{
    "summary": "内容摘要",
    "sentiment": "positive/negative/neutral",
    "topics": ["话题1", "话题2"],
    "keywords": ["关键词1", "关键词2"],
    "category": "分类",
    "recommendation": "推荐/不推荐"
}
```

---

## 📝 开发指南

### 环境准备

```bash
# Python 3.9+
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install yt-dlp instaloader httpx click rich pydantic

# 可选依赖
pip install akshare  # 金融数据
pip install openai   # LLM
```

### 开发流程

1. **先实现URL路由器** - 确保平台识别正确
2. **实现Handler基类** - 定义统一接口
3. **实现yt-dlp Handler** - 覆盖国际平台和B站
4. **实现Instagram Handler** - 使用instaloader
5. **实现中国平台Handler** - 参考已克隆项目
6. **实现LLM分析器** - 调用LLM API
7. **实现CLI** - 命令行入口
8. **测试各平台** - 实际下载测试

### 测试方法

```bash
# 测试URL解析
python -c "
from social_downloader import URLRouter
print(URLRouter.parse('https://www.youtube.com/watch?v=xxx'))
"

# 测试下载
python -m social_downloader.cli.main download "https://www.bilibili.com/video/BV1GJ411x7h7"

# 测试分析
python -m social_downloader.cli.main analyze "https://www.youtube.com/watch?v=xxx"
```

---

## ✅ 完成功能清单

### 已完成

- [x] URL路由器 - 自动识别平台
- [x] 统一数据模型 - Content, AnalysisResult等
- [x] Handler基类 - 定义统一接口
- [x] 国际平台Handler - 使用yt-dlp（YouTube、Twitter、Facebook、TikTok、Reddit）
- [x] Instagram Handler - 使用instaloader
- [x] 小红书Handler - HTML解析获取笔记数据
- [x] 抖音Handler - HTML解析获取视频数据
- [x] B站Handler - 支持bilibili-api和HTTP两种方式
- [x] 微博Handler - API调用获取微博内容
- [x] 配置管理 - Cookie、代理、下载目录配置
- [x] CLI命令行 - 支持download、batch、analyze、config等命令
- [x] FastAPI服务 - REST API接口

### 待完善

- [ ] LLM分析器 - 调用LLM分析内容
- [ ] 下载进度显示
- [ ] 断点续传
- [ ] 更完善的错误处理
- [ ] 单元测试
- [ ] GitHub Actions CI/CD
- [ ] PyPI发布
- [ ] Docker支持

---

## 🔗 参考资源

### 已克隆的参考项目

```
/test_tools/
├── XHS-Downloader/         # 小红书下载器（10k+ Stars）
├── douyin-downloader/      # 抖音下载器（6k+ Stars）
├── weibo-crawler/          # 微博爬虫（4k+ Stars）
├── Bili23-Downloader/      # B站下载器（3k+ Stars）
├── Spider_XHS/             # 小红书爬虫
├── TikTok-Content-Scraper/ # TikTok爬虫
├── fdown-api/              # Facebook下载
├── media_downloader/       # 综合下载器（架构参考）
└── social-media-downloader/# 综合下载器（CLI参考）
```

### 核心依赖

```
yt-dlp>=2026.3.0           # 国际平台通用
instaloader>=4.15.0        # Instagram专用
httpx>=0.28.0              # 异步HTTP客户端
click>=8.0.0               # CLI框架
rich>=13.7.0               # 终端美化
```

---

## 📄 开源准备

### 必备文件

- [ ] README.md - 使用说明
- [ ] LICENSE - MIT许可证
- [ ] requirements.txt - 依赖列表
- [ ] setup.py / pyproject.toml - 打包配置
- [ ] .github/workflows/ci.yml - CI/CD

### README结构

```markdown
# 社交媒体统一下载工具

支持平台：YouTube, Twitter, Facebook, Instagram, TikTok, 小红书, 抖音, B站, 微博

## 安装
pip install social-downloader

## 使用
### 命令行
social-downloader download "https://..."
social-downloader analyze "https://..."

### Python API
from social_downloader import Downloader
dl = Downloader()
result = await dl.analyze("https://...")

## 支持平台
| 平台 | 状态 |
|------|------|
| YouTube | ✅ |
| ... | ... |
```
