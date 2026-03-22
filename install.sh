#!/bin/bash
# 社交媒体统一下载工具 - 安装脚本

set -e

echo "=========================================="
echo "  社交媒体统一下载工具 - 安装程序"
echo "=========================================="
echo ""

# 检查Python版本
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "检测到 Python 版本: $python_version"

if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo "✓ Python 版本满足要求 (>= 3.9)"
else
    echo "✗ 错误: 需要 Python 3.9 或更高版本"
    exit 1
fi

echo ""

# 安装依赖
echo "正在安装依赖..."
pip install -q yt-dlp instaloader httpx click rich pydantic akshare bilibili-api-python

echo ""
echo "正在安装 social-media-downloader..."
pip install -e . -q

echo ""
echo "=========================================="
echo "  安装完成！"
echo "=========================================="
echo ""
echo "使用方法："
echo ""
echo "  命令行："
echo "    social-downloader download \"URL\""
echo "    social-downloader platforms"
echo ""
echo "  Python："
echo "    from social_downloader import Downloader"
echo "    dl = Downloader()"
echo ""
echo "查看帮助："
echo "    social-downloader --help"
echo ""
