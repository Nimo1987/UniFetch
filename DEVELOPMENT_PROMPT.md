# 社交媒体统一下载工具 - 开发提示词

## 复制以下内容到新的对话窗口

---

我正在开发一个社交媒体统一下载工具，项目位于 `/Users/gjq/Desktop/OpenCode/社交媒体统一下载插件/social_downloader/`

### 项目目标
构建一个通用的社交媒体下载工具，支持中美两国主流平台，提供统一的API接口和LLM内容分析功能。

### 当前状态
已完成项目框架，包括：
- ✅ URL路由器（自动识别平台）
- ✅ 统一数据模型（Content, AnalysisResult等）
- ✅ Handler基类（BaseHandler）
- ✅ LLM分析器框架
- ✅ CLI入口框架
- ✅ 各平台Handler框架

### 支持平台
| 平台 | 状态 | 实现方案 |
|------|------|----------|
| YouTube | ✅ 可用 | yt-dlp |
| Twitter/X | ✅ 可用 | yt-dlp |
| Facebook | ✅ 可用 | yt-dlp |
| TikTok | ✅ 可用 | yt-dlp |
| Reddit | ✅ 可用 | yt-dlp |
| B站 | ✅ 可用 | yt-dlp |
| Instagram | ⚠️ 需完善 | instaloader |
| 小红书 | ❌ 需实现 | 参考XHS-Downloader |
| 抖音 | ❌ 需实现 | 参考douyin-downloader |
| 微博 | ❌ 需实现 | 参考weibo-crawler |

### 参考项目（已克隆到/test_tools/）
- `/test_tools/XHS-Downloader/` - 小红书下载器（10k Stars）
- `/test_tools/douyin-downloader/` - 抖音下载器（6k Stars）
- `/test_tools/weibo-crawler/` - 微博爬虫（4k Stars）
- `/test_tools/Bili23-Downloader/` - B站下载器（3k Stars）
- `/test_tools/media_downloader/` - 综合下载器（架构参考）

### 核心依赖
```python
yt-dlp>=2026.3.0        # 国际平台通用
instaloader>=4.15.0     # Instagram专用
httpx[http2,socks]>=0.28.0  # 异步HTTP客户端
click>=8.0.0            # CLI框架
rich>=13.7.0            # 终端美化
```

### 需要完成的工作

#### 1. 完善小红书Handler（handlers/xiaohongshu.py）
参考 `/test_tools/XHS-Downloader/source/module/` 的实现：
- 实现笔记信息获取API
- 实现图片/视频下载链接提取
- 处理xs签名算法（如果需要）

核心API端点：
```
GET https://edith.xiaohongshu.com/api/sns/web/v1/feed
```

#### 2. 完善抖音Handler（handlers/douyin.py）
参考 `/test_tools/douyin-downloader/core/` 的实现：
- 实现视频信息获取
- 实现短链接解析
- 实现a_bogus签名算法（参考 `/test_tools/douyin-downloader/core/abogus.py`）

核心API端点：
```
GET https://www.douyin.com/aweme/v1/web/aweme/detail/
```

#### 3. 完善微博Handler（handlers/weibo.py）
参考 `/test_tools/weibo-crawler/weibo.py` 的实现：
- 实现微博内容获取
- 需要Cookie认证
- 实现图片/视频下载

核心API端点：
```
GET https://weibo.com/ajax/statuses/show?id={weibo_id}
```

#### 4. 完善Instagram Handler（handlers/instagram.py）
使用instaloader库，处理：
- 帖子（Post）
- Reels
- Stories
- 用户主页

#### 5. 实现配置管理
创建 `core/config.py`：
- Cookie管理
- 代理设置
- 下载目录配置
- LLM API配置

#### 6. 实现CLI完善
完善 `cli/main.py`：
- 添加配置命令
- 添加批量下载
- 添加进度显示

#### 7. 实现FastAPI服务
创建 `api/server.py`：
```python
@app.post("/analyze")
async def analyze_url(url: str):
    dl = Downloader()
    return await dl.analyze(url)

@app.post("/download")
async def download_url(url: str, quality: str = "best"):
    dl = Downloader()
    return await dl.download(url, quality)
```

#### 8. 添加测试用例
创建 `tests/` 目录：
- test_router.py - 测试URL解析
- test_handlers.py - 测试各平台Handler
- test_llm.py - 测试LLM分析

### 开发顺序建议
1. 先实现小红书Handler（最有价值的中国平台）
2. 实现配置管理（Cookie等）
3. 实际测试各平台下载
4. 完善抖音和微博Handler
5. 实现FastAPI服务
6. 添加测试用例
7. 编写README和开源准备

### 测试方法
```bash
cd /Users/gjq/Desktop/OpenCode/社交媒体统一下载插件

# 测试URL解析
python3 -c "
from social_downloader import URLRouter
print(URLRouter.parse('https://www.xiaohongshu.com/explore/abc123'))
"

# 测试B站下载（已验证可用）
yt-dlp --no-check-certificates -f "worst" "https://www.bilibili.com/video/BV1GJ411x7h7"
```

### LLM分析器配置
默认调用用户Agent系统内部LLM，需要实现：
```python
# 在llm_analyzer.py中添加
async def _call_internal_llm(self, prompt: str) -> str:
    # 调用系统内部LLM的实现
    pass
```

---

请帮我继续开发这个项目，优先完善各平台Handler的实际实现。

---
