#!/usr/bin/env python3
"""web-access 集成层

检测 web-access 是否可用，提供调用接口和降级策略。
"""

from __future__ import annotations
import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional, List


# web-access 的可能安装路径
_WEB_ACCESS_PATHS = [
    Path.home() / ".claude" / "skills" / "web-access",
    Path.home() / ".claude" / "plugins" / "installed" / "web-access",
]


def detect() -> dict:
    """检测 web-access 是否可用，返回状态信息

    Returns:
      {"available": bool, "path": str|None, "cdp_available": bool, "message": str}
    """
    # 1. 找 web-access 目录
    wa_path = None
    for p in _WEB_ACCESS_PATHS:
        if p.exists() and (p / "SKILL.md").exists():
            wa_path = p
            break

    if not wa_path:
        return {
            "available": False,
            "path": None,
            "cdp_available": False,
            "message": "web-access 未安装。运行 npx skills add eze-is/web-access 安装。",
        }

    # 2. 检测 CDP Proxy 是否在运行
    cdp_available = False
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:3456/health"],
            capture_output=True, text=True, timeout=3,
        )
        if result.returncode == 0:
            cdp_available = True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # 3. 检测 Node.js
    node_available = shutil.which("node") is not None

    messages = []
    if node_available:
        messages.append("Node.js 已安装")
    else:
        messages.append("Node.js 未安装（CDP 模式需要 Node.js 22+）")

    if cdp_available:
        messages.append("CDP Proxy 运行中")
    else:
        messages.append("CDP Proxy 未启动，降级为 WebSearch/WebFetch")

    return {
        "available": True,
        "path": str(wa_path),
        "cdp_available": cdp_available,
        "message": " | ".join(messages),
    }


def start_cdp_proxy() -> bool:
    """尝试启动 CDP Proxy，返回是否启动成功"""
    status = detect()
    if not status["available"] or not status.get("path"):
        return False

    wa_path = Path(status["path"])
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


def get_installation_guide() -> str:
    """返回 web-access 安装说明"""
    return """\
web-access 未安装，建议安装以获得完整的浏览器自动化能力：

  npx skills add eze-is/web-access

安装后确保：
  1. 在 Chrome 地址栏打开 chrome://inspect/#remote-debugging
  2. 勾选 "Allow remote debugging for this browser instance"
  3. 重启浏览器

当前将以降级模式运行（仅 WebSearch + WebFetch），功能受限。"""
