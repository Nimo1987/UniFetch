# 社交媒体统一下载工具

一个整合中美主流社交媒体平台的统一下载工具。

## 支持平台

### 国际平台
- YouTube
- Twitter/X
- Facebook
- Instagram
- TikTok
- Reddit

### 中国平台
- 小红书 (XHS)
- 抖音 (Douyin)
- 微博 (Weibo)
- B站 (Bilibili)
- 微信公众号

### 金融数据
- 股票、期货、基金、债券、外汇、数字货币

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 命令行使用
python -m social_media_downloader "https://www.youtube.com/watch?v=xxx"

# 或使用URL自动识别
python -m social_media_downloader download "https://www.xiaohongshu.com/explore/xxx"
```

## 作为库使用

```python
from social_media_downloader import Downloader

dl = Downloader()
result = await dl.download("https://www.youtube.com/watch?v=xxx")
```
