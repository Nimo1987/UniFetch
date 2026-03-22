<div align="center">

# 🔗 UniFetch

**统一的社交媒体和金融数据下载工具**

一个支持中美主流社交平台和金融数据的统一下载工具

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/平台-12个-orange.svg)](#支持平台)

</div>

---

## 🚀 一键安装

复制以下命令，在你的 Agent 对话框中粘贴执行：

```
请帮我安装 UniFetch，执行以下命令：
pip install git+https://github.com/yourusername/UniFetch.git
```

或者本地安装：

```
cd /path/to/UniFetch && pip install -e .
```

---

## 📋 支持平台

### 社交媒体（11个平台）

| 类别 | 平台 | 状态 | 功能 |
|------|------|------|------|
| 🌏 **国际平台** | YouTube | ✅ | 视频、播放列表、频道 |
| | Twitter/X | ✅ | 推文、图片、视频 |
| | Facebook | ✅ | 视频、帖子 |
| | Instagram | ✅ | 帖子、Reels、图集 |
| | TikTok | ✅ | 短视频 |
| | Reddit | ✅ | 帖子、图片、视频 |
| 🇨🇳 **中国平台** | 小红书 | ✅ | 图文笔记、视频笔记 |
| | 抖音 | ✅ | 短视频（无水印） |
| | B站 | ✅ | 视频、番剧 |
| | 微博 | ✅ | 微博、图片、视频 |
| | 微信公众号 | ✅ | 文章内容抓取 |

### 金融数据（A股/港股/美股）

| 市场 | 数据类型 | 示例 |
|------|----------|------|
| 🇨🇳 **A股** | 公司信息、利润表、资产负债表、现金流量表、历史行情 | `finance://000001` |
| 🇭🇰 **港股** | 实时行情、历史行情、财务指标 | `finance://hk:00700` |
| 🇺🇸 **美股** | 实时行情、历史行情、财务数据 | `finance://us:AAPL` |

---

## ✨ 核心功能

### 1. 统一接口，一个函数搞定所有平台

```python
from unifetch import Downloader
import asyncio

async def main():
    dl = Downloader()
    
    # 同一个接口，支持所有平台
    await dl.download("https://www.youtube.com/watch?v=xxx")
    await dl.download("https://www.xiaohongshu.com/explore/xxx")
    await dl.download("https://mp.weixin.qq.com/s/xxx")
    await dl.download("finance://000001")

asyncio.run(main())
```

### 2. 自动识别平台

```python
from unifetch import URLRouter

result = URLRouter.parse("https://www.youtube.com/watch?v=xxx")
print(result)
# {'platform': 'youtube', 'content_id': 'xxx', 'supported': True}
```

### 3. 获取内容信息

```python
result = await dl.fetch("https://www.youtube.com/watch?v=xxx")
print(f"标题: {result.content.title}")
print(f"作者: {result.content.author.nickname}")
print(f"播放量: {result.content.views}")
```

### 4. 下载为不同格式

```python
# 微信公众号文章 - 下载为 Markdown
await dl.download("https://mp.weixin.qq.com/s/xxx")

# 金融数据 - 下载为 CSV
await dl.download("finance://000001?report=income")
```

---

## 🖥️ 命令行使用

### 基本命令

```bash
# 下载单个URL
unifetch download "https://www.youtube.com/watch?v=xxx"

# 批量下载
unifetch batch URL1 URL2 URL3

# 从文件批量下载
unifetch batch -f urls.txt

# 仅获取信息（不下载）
unifetch download --info-only "URL"

# 输出JSON格式
unifetch download --json-output "URL"
```

### 配置管理

```bash
# 查看当前配置
unifetch config show

# 设置代理
unifetch config set-proxy "socks5://127.0.0.1:1080"

# 设置下载目录
unifetch config set-download-dir "/path/to/downloads"

# 设置平台Cookie（部分平台需要）
unifetch config set-cookie xiaohongshu "your_cookie"
unifetch config set-cookie weibo "your_cookie"
```

### 其他命令

```bash
# 查看支持的平台
unifetch platforms

# 查看版本
unifetch --version
```

---

## 🌐 HTTP API 服务

### 启动服务

```bash
# 安装API依赖
pip install unifetch[api]

# 启动服务
python -m unifetch.api.server
```

### API端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/fetch` | 获取URL内容信息 |
| POST | `/download` | 下载URL内容 |
| POST | `/analyze` | 分析URL内容（需LLM） |
| GET | `/platforms` | 获取支持的平台列表 |
| GET | `/check?url=xxx` | 检查URL是否支持 |

---

## ⚙️ 配置说明

配置文件位置：`~/.unifetch/config.json`

```json
{
    "cookies": {
        "xiaohongshu": "小红书Cookie（获取高清图）",
        "weibo": "微博Cookie（完整内容）"
    },
    "proxy": {
        "enabled": true,
        "socks5": "socks5://127.0.0.1:1080"
    },
    "download": {
        "directory": "./downloads",
        "quality": "best"
    }
}
```

### 环境变量支持

```bash
# 代理
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"

# Cookie
export XHS_COOKIE="your_cookie"
export WEIBO_COOKIE="your_cookie"

# 下载目录
export DOWNLOAD_DIR="/path/to/downloads"
```

---

## 📝 使用注意事项

### 🔐 Cookie 使用

| 平台 | 是否必须 | 说明 |
|------|----------|------|
| 小红书 | 推荐 | 获取高清图片 |
| 微博 | 推荐 | 访问完整内容 |
| Instagram | 可选 | 访问部分帖子 |
| 其他平台 | 不需要 | - |

### 🌐 代理设置

以下平台在某些地区可能需要代理：
- YouTube、Twitter/X、Facebook、Instagram、TikTok、Reddit

### ⚠️ 法律合规

- **仅供学习研究**：请勿用于商业用途
- **遵守平台规则**：请遵守各平台的使用条款
- **尊重版权**：尊重内容创作者的知识产权
- **合理使用**：请勿进行大规模爬取

### 💡 常见问题

**Q: 下载失败怎么办？**

A: 
1. 检查网络连接
2. 尝试设置代理
3. 部分平台需要Cookie才能获取完整内容

**Q: 金融数据获取失败？**

A: 
1. 确保已安装 akshare：`pip install akshare`
2. 检查股票代码是否正确
3. 可能需要使用代理

**Q: 如何获取小红书Cookie？**

A: 
1. 登录小红书网页版
2. 打开浏览器开发者工具（F12）
3. 在 Network 标签中找到 Cookie
4. 复制完整的 Cookie 字符串

---

## 📦 开发相关

### 项目结构

```
unifetch/
├── __init__.py           # 包入口
├── downloader.py         # 统一下载器
├── core/                 # 核心模块
│   ├── router.py         # URL路由器
│   ├── base_handler.py   # Handler基类
│   └── config.py         # 配置管理
├── models/               # 数据模型
│   └── content.py        # Content等模型
├── china/                # 中国平台Handler
│   └── handlers.py       # 小红书、抖音、B站、微博、微信
├── international/        # 国际平台Handler
│   └── handlers.py       # YouTube、Instagram等
├── finance/              # 金融数据Handler
│   └── __init__.py       # A股、港股、美股
├── cli/                  # 命令行
│   └── main.py           # CLI入口
└── api/                  # HTTP API
    └── server.py         # FastAPI服务
```

### 本地开发

```bash
# 克隆项目
git clone https://github.com/yourusername/UniFetch.git
cd UniFetch

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[all]"

# 运行测试
python -c "from unifetch import URLRouter; print('OK')"
```

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

---

## 🙏 致谢

本项目参考并使用了以下优秀的开源项目，在此向原作者表示衷心的感谢：

### 视频下载

| 项目 | 作者 | 说明 |
|------|------|------|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | yt-dlp 团队 | YouTube、Twitter、Facebook、TikTok、Reddit 等国际平台下载 |
| [instaloader](https://github.com/instaloader/instaloader) | Alexander Graf | Instagram 内容下载 |
| [bilibili-api-python](https://github.com/Nemo2011/bilibili-api-python) | Nemo2011 | B站 API 封装 |

### 中国平台参考

| 项目 | Stars | 说明 |
|------|-------|------|
| [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) | 10k+ | 小红书下载器，提供 HTML 解析思路 |
| [douyin-downloader](https://github.com/johnserf-seed/douyin-downloader) | 6k+ | 抖音下载器，提供页面解析方案 |
| [weibo-crawler](https://github.com/dataabc/weibo-crawler) | 4k+ | 微博爬虫，提供 API 调用方式 |
| [wechat-article-exporter](https://github.com/nicoly/wechat-article-exporter) | - | 微信公众号文章导出 API |

### 金融数据

| 项目 | 说明 |
|------|------|
| [akshare](https://github.com/akfamily/akshare) | 开源金融数据接口库，提供 A股/港股/美股 数据 |

### 开发框架

| 项目 | 说明 |
|------|------|
| [Click](https://github.com/pallets/click) | 命令行界面框架 |
| [Rich](https://github.com/Textualize/rich) | 终端美化输出 |
| [HTTPX](https://github.com/encode/httpx) | 异步 HTTP 客户端 |
| [FastAPI](https://github.com/tiangolo/fastapi) | Web API 框架 |
| [Pydantic](https://github.com/pydantic/pydantic) | 数据验证 |

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

Made with ❤️ by UniFetch Contributors

</div>
