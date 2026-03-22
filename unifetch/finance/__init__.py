"""
金融数据Handler
- A股
- 港股
- 美股
"""

import asyncio
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    import akshare as ak

    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False

from ..core.base_handler import BaseHandler
from ..models.content import Content, Platform, ContentType, Author, MediaFile


class FinanceHandler(BaseHandler):
    """
    金融数据Handler

    支持A股、港股、美股的财务数据获取
    基于akshare库实现

    URL格式:
    - A股: finance://000001 或 finance://000001?report=income
    - 港股: finance://hk:00700
    - 美股: finance://us:AAPL
    """

    def __init__(self, url: str, **kwargs):
        super().__init__(url, **kwargs)
        if not AKSHARE_AVAILABLE:
            raise ImportError("请安装akshare: pip install akshare")

        # 解析URL
        self.stock_info = self._parse_url(url)

    def _get_platform(self) -> Platform:
        return Platform.FINANCE

    def _parse_url(self, url: str) -> Dict[str, Any]:
        """解析金融URL"""
        # 移除 finance:// 前缀
        path = url.replace("finance://", "").replace("finance:", "")

        # 解析查询参数
        report_type = "info"  # 默认获取公司信息
        if "?" in path:
            path, query = path.split("?", 1)
            params = dict(p.split("=") for p in query.split("&") if "=" in p)
            report_type = params.get("report", "info")

        # 判断市场
        if path.startswith("hk:"):
            market = "hk"
            symbol = path[3:]
        elif path.startswith("us:"):
            market = "us"
            symbol = path[3:].upper()
        else:
            market = "cn"
            symbol = path

        return {
            "market": market,
            "symbol": symbol,
            "report_type": report_type,
        }

    async def fetch(self) -> Content:
        """获取金融数据"""
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self._fetch_data)

        market = self.stock_info["market"]
        symbol = self.stock_info["symbol"]

        # 构建内容
        self._content = self.create_content(
            content_type=ContentType.ARTICLE,
            id=symbol,
            title=data.get("name", symbol),
            description=data.get("description", ""),
            author=Author(nickname=data.get("source", "akshare")),
            tags=[market.upper(), data.get("industry", "")],
            raw_data=data,
        )

        return self._content

    async def download(self, quality: str = "best") -> Path:
        """下载金融数据（保存为CSV/JSON）"""
        content = await self.get_info()
        data = content.raw_data

        market = self.stock_info["market"]
        symbol = self.stock_info["symbol"]
        report_type = self.stock_info["report_type"]

        # 保存为CSV
        if "dataframe" in data:
            import pandas as pd

            df = data["dataframe"]
            filename = f"{market}_{symbol}_{report_type}.csv"
            filepath = self.output_dir / filename
            df.to_csv(filepath, index=False, encoding="utf-8-sig")
            return filepath

        # 保存为JSON
        import json

        filename = f"{market}_{symbol}_{report_type}.json"
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return filepath

    def _fetch_data(self) -> Dict[str, Any]:
        """获取数据（同步）"""
        market = self.stock_info["market"]
        symbol = self.stock_info["symbol"]
        report_type = self.stock_info["report_type"]

        if market == "cn":
            return self._fetch_cn_data(symbol, report_type)
        elif market == "hk":
            return self._fetch_hk_data(symbol, report_type)
        elif market == "us":
            return self._fetch_us_data(symbol, report_type)
        else:
            raise ValueError(f"不支持的市场: {market}")

    def _fetch_cn_data(self, symbol: str, report_type: str) -> Dict[str, Any]:
        """获取A股数据"""
        data = {
            "market": "A股",
            "symbol": symbol,
            "source": "东方财富/akshare",
        }

        try:
            if report_type == "info":
                # 公司基本信息
                df = ak.stock_individual_info_em(symbol=symbol)
                info_dict = dict(zip(df["item"], df["value"]))
                data.update(
                    {
                        "name": info_dict.get("股票简称", symbol),
                        "code": info_dict.get("股票代码", symbol),
                        "industry": info_dict.get("行业", ""),
                        "total_shares": info_dict.get("总股本", ""),
                        "market_cap": info_dict.get("总市值", ""),
                        "listing_date": info_dict.get("上市时间", ""),
                        "dataframe": df,
                    }
                )

            elif report_type == "income":
                # 利润表
                df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
                data.update(
                    {
                        "name": f"{symbol}利润表",
                        "report_type": "利润表",
                        "dataframe": df,
                        "description": f"获取{symbol}的利润表数据",
                    }
                )

            elif report_type == "balance":
                # 资产负债表
                df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
                data.update(
                    {
                        "name": f"{symbol}资产负债表",
                        "report_type": "资产负债表",
                        "dataframe": df,
                        "description": f"获取{symbol}的资产负债表数据",
                    }
                )

            elif report_type == "cashflow":
                # 现金流量表
                df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
                data.update(
                    {
                        "name": f"{symbol}现金流量表",
                        "report_type": "现金流量表",
                        "dataframe": df,
                        "description": f"获取{symbol}的现金流量表数据",
                    }
                )

            elif report_type == "history":
                # 历史行情
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
                data.update(
                    {
                        "name": f"{symbol}历史行情",
                        "report_type": "历史行情",
                        "dataframe": df,
                        "description": f"获取{symbol}的历史K线数据",
                    }
                )

            else:
                raise ValueError(f"不支持的报告类型: {report_type}")

        except Exception as e:
            data["error"] = str(e)
            data["description"] = f"获取数据失败: {e}"

        return data

    def _fetch_hk_data(self, symbol: str, report_type: str) -> Dict[str, Any]:
        """获取港股数据"""
        data = {
            "market": "港股",
            "symbol": symbol,
            "source": "akshare",
        }

        try:
            if report_type == "info":
                # 港股实时行情
                df = ak.stock_hk_spot_em()
                stock_data = df[df["代码"] == symbol]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    data.update(
                        {
                            "name": row.get("名称", symbol),
                            "price": row.get("最新价", ""),
                            "change_pct": row.get("涨跌幅", ""),
                            "market_cap": row.get("市值", ""),
                        }
                    )
                data["dataframe"] = stock_data

            elif report_type == "history":
                # 历史行情
                df = ak.stock_hk_hist(symbol=symbol, period="daily", adjust="qfq")
                data.update(
                    {
                        "name": f"{symbol}港股历史行情",
                        "dataframe": df,
                    }
                )

            elif report_type == "financial":
                # 财务指标
                df = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol)
                data.update(
                    {
                        "name": f"{symbol}港股财务指标",
                        "dataframe": df,
                    }
                )

            else:
                raise ValueError(f"不支持的报告类型: {report_type}")

        except Exception as e:
            data["error"] = str(e)

        return data

    def _fetch_us_data(self, symbol: str, report_type: str) -> Dict[str, Any]:
        """获取美股数据"""
        data = {
            "market": "美股",
            "symbol": symbol,
            "source": "akshare",
        }

        try:
            if report_type == "info":
                # 美股实时行情
                df = ak.stock_us_spot_em()
                stock_data = df[df["代码"] == symbol]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    data.update(
                        {
                            "name": row.get("名称", symbol),
                            "price": row.get("最新价", ""),
                            "market_cap": row.get("市值", ""),
                        }
                    )
                data["dataframe"] = stock_data

            elif report_type == "history":
                # 历史行情
                df = ak.stock_us_hist(symbol=symbol, period="daily", adjust="qfq")
                data.update(
                    {
                        "name": f"{symbol}美股历史行情",
                        "dataframe": df,
                    }
                )

            elif report_type == "financial":
                # 财务数据
                df = ak.stock_financial_us_report_em(symbol=symbol)
                data.update(
                    {
                        "name": f"{symbol}美股财务数据",
                        "dataframe": df,
                    }
                )

            else:
                raise ValueError(f"不支持的报告类型: {report_type}")

        except Exception as e:
            data["error"] = str(e)

        return data
