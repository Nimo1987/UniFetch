"""
LLM分析器 - 使用大语言模型分析内容
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

import httpx

from ..models.content import Content, AnalysisResult


@dataclass
class LLMConfig:
    """LLM配置"""

    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    max_tokens: int = 1000
    temperature: float = 0.3


class LLMAnalyzer:
    """
    LLM分析器

    使用大语言模型分析社交媒体内容
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        初始化分析器

        Args:
            config: LLM配置，如果不提供则从环境变量读取
        """
        self.config = config or LLMConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )

    async def analyze(self, content: Content) -> AnalysisResult:
        """
        分析内容

        Args:
            content: 内容对象

        Returns:
            AnalysisResult: 分析结果
        """
        # 构建提示词
        prompt = self._build_prompt(content)

        # 调用LLM
        response = await self._call_llm(prompt)

        # 解析结果
        return self._parse_response(response, content)

    def _build_prompt(self, content: Content) -> str:
        """构建分析提示词"""
        # 收集内容信息
        title = content.title or "无标题"
        description = content.description or "无描述"
        platform = content.platform.value
        content_type = content.content_type.value

        # 统计信息
        stats = []
        if content.likes is not None:
            stats.append(f"点赞: {content.likes}")
        if content.comments_count is not None:
            stats.append(f"评论: {content.comments_count}")
        if content.shares is not None:
            stats.append(f"分享: {content.shares}")
        if content.views is not None:
            stats.append(f"播放: {content.views}")
        stats_str = ", ".join(stats) if stats else "无统计信息"

        # 作者信息
        author_str = "未知"
        if content.author:
            author_str = content.author.nickname or content.author.username or "未知"

        # 标签
        tags_str = ", ".join(content.tags[:10]) if content.tags else "无标签"

        prompt = f"""请分析以下社交媒体内容，并以JSON格式返回分析结果。

## 内容信息
- 平台: {platform}
- 类型: {content_type}
- 作者: {author_str}
- 标题: {title}
- 描述: {description[:500]}
- 统计: {stats_str}
- 标签: {tags_str}

## 请分析以下内容并返回JSON格式结果

{{
    "summary": "内容摘要（50-100字）",
    "sentiment": "情感倾向（positive/negative/neutral）",
    "sentiment_score": "情感分数（0-1，越接近1越积极）",
    "topics": ["主要话题列表"],
    "keywords": ["关键词列表（5-10个）"],
    "key_points": ["关键信息点（3-5个）"],
    "language": "内容语言（zh/en/ja/ko等）",
    "quality_score": "内容质量评分（0-10）",
    "content_rating": "内容分级（G/PG/PG-13/R）",
    "recommendation": "推荐意见（推荐/不推荐/一般）",
    "recommendation_reason": "推荐理由",
    "category": "内容分类（娱乐/教育/新闻/生活/科技/其他）",
    "subcategory": "子分类"
}}

请直接返回JSON，不要添加其他说明文字。"""

        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        if not self.config.api_key:
            # 如果没有配置API Key，返回默认分析
            return self._get_default_analysis()

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的内容分析师，擅长分析社交媒体内容。",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0,
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

    def _get_default_analysis(self) -> str:
        """返回默认分析结果"""
        return """{
    "summary": "需要配置LLM API Key才能进行内容分析",
    "sentiment": "neutral",
    "sentiment_score": 0.5,
    "topics": [],
    "keywords": [],
    "key_points": [],
    "language": "unknown",
    "quality_score": 5.0,
    "content_rating": "G",
    "recommendation": "一般",
    "recommendation_reason": "未进行深度分析",
    "category": "其他",
    "subcategory": "未分类"
}"""

    def _parse_response(self, response: str, content: Content) -> AnalysisResult:
        """解析LLM响应"""
        import json
        import re

        try:
            # 尝试提取JSON
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            return AnalysisResult(
                summary=data.get("summary", ""),
                sentiment=data.get("sentiment", "neutral"),
                sentiment_score=float(data.get("sentiment_score", 0.5)),
                topics=data.get("topics", []),
                keywords=data.get("keywords", []),
                key_points=data.get("key_points", []),
                language=data.get("language", ""),
                quality_score=float(data.get("quality_score", 5.0)),
                content_rating=data.get("content_rating", ""),
                recommendation=data.get("recommendation", ""),
                recommendation_reason=data.get("recommendation_reason", ""),
                category=data.get("category", ""),
                subcategory=data.get("subcategory", ""),
            )
        except Exception as e:
            # 解析失败，返回基本结果
            return AnalysisResult(
                summary=f"分析失败: {str(e)}",
                sentiment="neutral",
            )
