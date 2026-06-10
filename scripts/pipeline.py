#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline.py — 后向兼容入口

所有功能委托给 orchestrator.py + modules/。
保留作为老接口的兼容层，新功能通过 orchestrator 或 modules 直接访问。
"""

from __future__ import annotations
import sys
import json
from pathlib import Path

# 将项目根目录加入 sys.path，确保模块导入正确
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.shared.registry import get_registry, reset_registry
from scripts.shared.state import (
    load as load_state,
    save as save_state,
    get_current_project,
    set_current_project,
    list_projects,
    get_project_path,
)
from scripts.orchestrator import Orchestrator

# ── 注册所有模块 ──
def _init_registry():
    reset_registry()
    reg = get_registry()
    for mod_name in [
        "conceptualize", "research", "literature", "data",
        "analyze", "verify", "write", "format",
    ]:
        mod = __import__(f"scripts.modules.{mod_name}", fromlist=["MODULE_CONTRACT"])
        reg.register(mod.MODULE_CONTRACT)
    return reg

_registry = _init_registry()
_orch = Orchestrator(_registry)


# ── 兼容函数 ──

def cmd_list(args=None):
    projects = _orch.list_projects()
    current = get_current_project()
    print(f"共有 {len(projects)} 个项目:\n")
    for p in projects:
        marker = "*" if p.get("is_current") else " "
        print(f" {marker} {p['name']:40s} -> {p['current_state']}")


def cmd_new(args):
    if len(args) < 3:
        print("用法: python pipeline.py new <项目名>")
        return
    result = _orch.new_project(args[2])
    if result["ok"]:
        print(f"✅ 项目 '{result['project']}' 创建成功")
    else:
        print(f"❌ {result['error']}")


def cmd_use(args):
    if len(args) < 3:
        print("用法: python pipeline.py use <项目名>")
        return
    result = _orch.use_project(args[2])
    if result["ok"]:
        print(f"✅ 已切换到项目 '{result['project']}'")
    else:
        print(f"❌ {result['error']}")


def cmd_status(args=None):
    name = args[2] if len(args) > 2 else None
    result = _orch.get_status(name)
    if not result["ok"]:
        print(result["error"])
        return
    print(f"📍 {result['project']}")
    print(f"   当前状态: {result['current_state']}")
    print(f"   所属模块: {result['module']}")
    print(f"   已完成阶段: {result['completed_stages']}")


def cmd_advance(args):
    target = args[2] if len(args) > 2 else None
    result = _orch.advance(target_state=target)
    if result["ok"]:
        print(result.get("message", "已推进"))
    else:
        print(f"❌ {result['error']}")


def cmd_jump(args):
    if len(args) < 3:
        print("用法: python pipeline.py jump <状态ID>")
        return
    result = _orch.jump(target_state=args[2])
    if result["ok"]:
        print(f"✅ 已跳转到 {result['to']}")
    else:
        print(f"❌ {result['error']}")


def cmd_undo(args=None):
    result = _orch.undo()
    if result["ok"]:
        print(result.get("message", "已回退"))
    else:
        print(f"❌ {result['error']}")


def cmd_reset(args=None):
    result = _orch.reset()
    if result["ok"]:
        print(result["message"])
    else:
        print(f"❌ {result['error']}")


def cmd_prompt(args=None):
    """显示当前状态的入口话术"""
    project_name = get_current_project()
    if not project_name:
        print("未选择项目")
        return
    state = load_state(project_name)
    current = state.get("current_micro_state", "concept-init")
    module_name = current.split("-")[0] if "-" in current else current
    mod = _registry.get(module_name)
    if mod:
        print(f"当前状态: {current}")
        print(f"模块: {mod.description}")
    else:
        print(f"当前状态: {current}")


def cmd_graph(args=None):
    """显示模块依赖图"""
    print("模块依赖图 (8 模块):\n")
    for name, contract in _registry.all.items():
        down = _registry.get_downstream(name)
        up = _registry.get_upstream(name)
        parts = [f"  {name}"]
        if up:
            parts.append(f"    ← 上游: {', '.join(up)}")
        if down:
            parts.append(f"    → 下游: {', '.join(down)}")
        parts.append(f"    📝 {contract.description}")
        print("\n".join(parts))
        print()

    order = _registry.get_stage_order()
    print(f"执行顺序: {' → '.join(order)}")
    print(f"校验: {'✅ 无警告' if not _registry.validate_all() else '⚠️ 有警告'}")


def cmd_states(args=None):
    """列出所有模块的状态（简化版）"""
    print("可用模块:\n")
    for name, contract in sorted(_registry.all.items()):
        states = ", ".join(contract.states) if contract.states else "(无子状态)"
        print(f"  {name:15s} | {states}")


_COMMANDS = {
    "list": cmd_list,
    "new": cmd_new,
    "use": cmd_use,
    "status": cmd_status,
    "advance": cmd_advance,
    "jump": cmd_jump,
    "undo": cmd_undo,
    "reset": cmd_reset,
    "prompt": cmd_prompt,
    "graph": cmd_graph,
    "states": cmd_states,
    "help": lambda _: print("可用命令: " + ", ".join(sorted(_COMMANDS.keys()))),
}


def main():
    if len(sys.argv) < 2:
        cmd_status()
        return

    cmd = sys.argv[1]
    if cmd in _COMMANDS:
        _COMMANDS[cmd](sys.argv)
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: " + ", ".join(sorted(_COMMANDS.keys())))
        sys.exit(1)


if __name__ == "__main__":
    main()
