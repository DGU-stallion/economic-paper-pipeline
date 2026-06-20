#!/usr/bin/env python3
"""搜索后端统一检测器

检测所有可用搜索后端的可用性，按优先级排序。

优先级：
  1. Tavily (API key + package)
  2. paper-search-mcp (学术论文搜索引擎)
  3. web-access CDP (浏览器自动化)
  4. WebSearch / WebFetch (LLM 工具级，始终可用)
  5. 手动引导 (兜底)
"""

from __future__ import annotations
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


# ── web-access 路径（旧检测用） ──
_WEB_ACCESS_PATHS = [
    Path.home() / ".claude" / "skills" / "web-access",
    Path.home() / ".claude" / "plugins" / "installed" / "web-access",
]


def detect_all() -> List[Dict]:
    """检测所有后端，按优先级返回可用列表

    Returns:
      [
        {"name": "tavily", "available": True, "type": "api", ...},
        {"name": "paper-search-mcp", "available": True, "type": "academic-mcp", ...},
        {"name": "cdp-proxy", "available": False, "type": "browser", ...},
        {"name": "websearch-webfetch", "available": True, "type": "tool-level", ...},
      ]
    """
    backends = []

    # 1. Tavily
    tavily_api_key = os.environ.get("TAVILY_API_KEY", "")
    if tavily_api_key:
        try:
            import tavily  # noqa: F401
            backends.append({
                "name": "tavily",
                "available": True,
                "type": "api",
                "priority": 1,
                "message": "Tavily API ✅",
            })
        except ImportError:
            backends.append({
                "name": "tavily",
                "available": False,
                "type": "api",
                "priority": 1,
                "message": "Tavily 包未安装: pip install tavily",
            })
    else:
        backends.append({
            "name": "tavily",
            "available": False,
            "type": "api",
            "priority": 1,
            "message": "TAVILY_API_KEY 未设置",
        })

    # 2. paper-search-mcp
    uv_available = shutil.which("uv") is not None
    paper_mcp_ok = False
    if uv_available:
        try:
            result = subprocess.run(
                ["uv", "run", "--with", "paper-search-mcp", "python", "-c",
                 "import paper_search_mcp; print('ok')"],
                capture_output=True, text=True, timeout=10,
            )
            paper_mcp_ok = result.returncode == 0 and "ok" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    if paper_mcp_ok:
        backends.append({
            "name": "paper-search-mcp",
            "available": True,
            "type": "academic-mcp",
            "priority": 2,
            "tools": ["search_arxiv", "search_google_scholar", "search_pubmed",
                      "search_biorxiv", "search_medrxiv"],
            "message": "paper-search-mcp ✅ (uv 可用)",
        })
    else:
        msg = "paper-search-mcp 不可用"
        if not uv_available:
            msg += "（需安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh）"
        backends.append({
            "name": "paper-search-mcp",
            "available": False,
            "type": "academic-mcp",
            "priority": 2,
            "message": msg,
        })

    # 3. web-access CDP
    wa_path = None
    for p in _WEB_ACCESS_PATHS:
        if p.exists() and (p / "SKILL.md").exists():
            wa_path = p
            break

    cdp_available = False
    if wa_path:
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:3456/health"],
                capture_output=True, text=True, timeout=3,
            )
            cdp_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    if cdp_available:
        backends.append({
            "name": "cdp-proxy",
            "available": True,
            "type": "browser",
            "priority": 3,
            "message": f"CDP Proxy ✅ ({wa_path})",
        })
    else:
        backends.append({
            "name": "cdp-proxy",
            "available": False,
            "type": "browser",
            "priority": 3,
            "message": "CDP Proxy 未启动（需安装 web-access + 启动 Chrome）",
        })

    # 4. WebSearch / WebFetch（始终可用，LLM 工具级别）
    backends.append({
        "name": "websearch-webfetch",
        "available": True,
        "type": "tool-level",
        "priority": 4,
        "message": "WebSearch + WebFetch ✅",
    })

    return backends


def get_primary(backends: Optional[List[Dict]] = None) -> Dict:
    """返回最高优先级的可用后端"""
    if backends is None:
        backends = detect_all()
    for b in sorted(backends, key=lambda x: x.get("priority", 99)):
        if b.get("available"):
            return b
    # 兜底：WebSearch/WebFetch 始终可用
    return {"name": "websearch-webfetch", "available": True, "type": "tool-level"}


def get_summary(backends: Optional[List[Dict]] = None) -> str:
    """返回可读的后端状态摘要（供 LLM 展示用）"""
    if backends is None:
        backends = detect_all()
    parts = []
    for b in sorted(backends, key=lambda x: x.get("priority", 99)):
        icon = "✅" if b.get("available") else "⚠️"
        parts.append(f"{icon} {b['name']}: {b.get('message', '')}")
    return " | ".join(parts)


def get_installation_guide() -> str:
    """返回可用后端的安装引导（当所有高级后端不可用时）"""
    return """\
可用搜索后端：

1. **Tavily** (首选): 注册 https://tavily.com 获取 API Key
   export TAVILY_API_KEY=你的key
   pip install tavily

2. **paper-search-mcp**: 用于学术论文搜索，需安装 uv
   curl -LsSf https://astral.sh/uv/install.sh | sh

3. **web-access CDP**: 浏览器自动化，用于需要渲染的页面
   npx skills add eze-is/web-access

当前以 WebSearch + WebFetch 降级运行，功能受限。
"""


# ── 向下兼容：保留原 detect() 接口 ──
def detect() -> dict:
    """兼容旧版 web_access.detect() 接口"""
    all_b = detect_all()
    tavily_b = next((b for b in all_b if b["name"] == "tavily"), {})
    paper_b = next((b for b in all_b if b["name"] == "paper-search-mcp"), {})
    cdp_b = next((b for b in all_b if b["name"] == "cdp-proxy"), {})

    available = any(b.get("available") for b in all_b if b["name"] != "websearch-webfetch")
    msg_parts = [b.get("message", "") for b in sorted(all_b, key=lambda x: x.get("priority", 99))]
    return {
        "available": available,
        "tavily_available": tavily_b.get("available", False),
        "paper_mcp_available": paper_b.get("available", False),
        "cdp_available": cdp_b.get("available", False),
        "message": " | ".join(msg_parts),
    }


def start_cdp_proxy() -> bool:
    """尝试启动 CDP Proxy（保留兼容）"""
    wa_path = None
    for p in _WEB_ACCESS_PATHS:
        if p.exists() and (p / "SKILL.md").exists():
            wa_path = p
            break
    if not wa_path:
        return False

    proxy_script = wa_path / "scripts" / "cdp-proxy.mjs"
    if not proxy_script.exists():
        return False

    try:
        subprocess.Popen(
            ["node", str(proxy_script)],
            cwd=str(wa_path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except FileNotFoundError:
        return False
