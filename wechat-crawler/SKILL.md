---
id: wechat-crawler
name: WeChat Article Crawler
version: 1.0.0
author: Jiaqi
description: 抓取微信公众号文章内容，提取正文并保存为 Markdown/HTML/JSON/TXT 格式。基于 wechat-article-exporter 公开 API，无需登录或密钥。
requires:
  - python: ">=3.9"
  - package: requests
compatible_with:
  - openclaw: ">=2026.2.0"
  - standalone: true
notes: |
  使用 wechat-article-exporter 公开 API。
  无需登录或密钥，直接抓取公众号文章。
  支持 markdown/html/json/txt 四种输出格式。
---

# 微信公众号文章抓取

抓取微信公众号文章正文，解决微信反爬导致的无法直接访问问题。

## 工作原理

使用 wechat-article-exporter 公开 API (`https://down.mptext.top/api/public/v1/download`) 获取文章完整内容。

## 使用方法

### 命令行

```bash
python3 scripts/wechat-crawler.py <文章链接> [格式]
```

**示例：**
```bash
# 抓取为 Markdown（默认）
python3 scripts/wechat-crawler.py "https://mp.weixin.qq.com/s/xxxxx"

# 抓取为 HTML
python3 scripts/wechat-crawler.py "https://mp.weixin.qq.com/s/xxxxx" html

# 抓取为纯文本
python3 scripts/wechat-crawler.py "https://mp.weixin.qq.com/s/xxxxx" txt
```

**支持格式：**
- `markdown` (默认) - 保留格式，适合阅读和分析
- `html` - 完整 HTML，保留图片和样式
- `json` - 结构化数据
- `txt` - 纯文本

### 在 Agent 中使用

当用户发送微信公众号链接时：

1. **提取链接** - 识别消息中的 `mp.weixin.qq.com` 链接
2. **调用脚本** - 使用 `exec` 运行 `wechat-crawler.py`
3. **处理结果** - 获取正文后进行分析、摘要或存储

**示例流程：**
```python
# 用户发送链接
url = "https://mp.weixin.qq.com/s/x9we1p7wkD7R30qDcTUlFg"

# 调用脚本抓取
exec: python3 skills/wechat-crawler/scripts/wechat-crawler.py "{url}"

# 读取结果并进行分析、摘要、存储到知识库等
```

## 输出内容

抓取结果包含：
- 文章标题
- 封面图
- 完整正文（带图片链接）
- 作者信息
- 原文链接

## 限制

- 依赖 wechat-article-exporter 公开服务的可用性
- 部分文章可能因微信风控无法抓取
- 图片链接为微信 CDN，长期可能失效

## 典型使用场景

1. **文章分析** - 抓取后分析核心观点
2. **知识库归档** - 保存到知识库供后续检索
3. **批量处理** - 配合 Cron 定时抓取特定公众号更新
4. **内容摘要** - 提取正文后生成 TL;DR
