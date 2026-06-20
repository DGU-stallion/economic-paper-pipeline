#!/usr/bin/env python3
"""Tavily 搜索集成层

Tavily 是专为 AI Agent 设计的搜索 API，提供结构化搜索结果。
优先级：项目中最高优先级搜索后端。

使用方式：
  1. 注册 https://tavily.com 获取 API Key
  2. export TAVILY_API_KEY=your_key_here
  3. pip install tavily

检测流程：
  detect() → 检查 TAVILY_API_KEY 环境变量 + tavily 包是否可导入
"""

from __future__ import annotations
import os
from typing import Optional


def detect() -> dict:
    """检测 Tavily 是否可用

    Returns:
      {"available": bool, "message": str, "key_set": bool, "package_installed": bool}
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    key_set = bool(api_key)

    package_installed = False
    try:
        import tavily  # noqa: F401
        package_installed = True
    except ImportError:
        pass

    if key_set and package_installed:
        return {
            "available": True,
            "key_set": True,
            "package_installed": True,
            "message": "Tavily ✅",
        }
    elif not key_set:
        return {
            "available": False,
            "key_set": False,
            "package_installed": package_installed,
            "message": "TAVILY_API_KEY 未设置。注册 https://tavily.com 获取密钥",
        }
    else:
        return {
            "available": False,
            "key_set": True,
            "package_installed": False,
            "message": "tavily 包未安装。运行: pip install tavily",
        }


def search(query: str, search_depth: str = "basic", max_results: int = 8) -> list[dict]:
    """执行 Tavily 搜索

    Args:
      query: 搜索关键词
      search_depth: "basic" (快) 或 "advanced" (全面)
      max_results: 返回结果数

    Returns:
      [{"title": str, "url": str, "content": str, "score": float}, ...]

    Raises:
      ImportError: tavily 包未安装
      ValueError: TAVILY_API_KEY 未设置
      Exception: API 调用失败
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        raise ValueError("TAVILY_API_KEY 未设置。注册 https://tavily.com 获取密钥")

    try:
        from tavily import TavilyClient
    except ImportError:
        raise ImportError("tavily 包未安装。运行: pip install tavily")

    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        search_depth=search_depth,
        max_results=max_results,
    )
    return response.get("results", [])


def get_installation_guide() -> str:
    """返回 Tavily 安装配置说明"""
    return """\
Tavily 搜索集成

1. 注册账号: https://tavily.com
2. 获取 API Key (免费额度通常 1000 次/月)
3. 设置环境变量:
   export TAVILY_API_KEY="your-api-key-here"
4. 安装 Python 包:
   pip install tavily

验证是否配置成功:
   python -c "import os; print('✅' if os.environ.get('TAVILY_API_KEY') else '❌ 未设置')"
"""
