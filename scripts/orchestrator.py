#!/usr/bin/env python3
"""
编排器 (Orchestrator)

职责（不做业务逻辑）：
  1. 项目生命周期管理 — new/use/list/status
  2. 状态机核心 — advance/jump/undo
  3. 模块路由 — 用户意图 → 模块
  4. 上下文验证 — consume/provide 字段校验
  5. 状态持久化 — pipeline_state.json

不包含任何阶段业务逻辑（5W1H / 检索 / 回归等）。
"""

from __future__ import annotations
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from scripts.shared.state import (
    load as load_state,
    save as save_state,
    get_current_project,
    set_current_project,
    list_projects,
    get_project_path,
)
from scripts.shared.registry import ModuleRegistry, get_registry


# ── 路径 ──

PLUGIN_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PLUGIN_ROOT / "templates"
PAPERS_DIR = Path.cwd() / "papers"
CONFIG_DIR = Path.cwd() / ".config"


# ── 编排器 ──

class Orchestrator:
    """工作流编排器"""

    def __init__(self, registry: Optional[ModuleRegistry] = None):
        self.registry = registry or get_registry()

    # ── 项目 CRUD ──

    def new_project(self, name: str) -> dict:
        """创建新项目"""
        project_path = PAPERS_DIR / name
        if project_path.exists():
            return {"ok": False, "error": f"项目 '{name}' 已存在"}

        PAPERS_DIR.mkdir(parents=True, exist_ok=True)
        project_path.mkdir(parents=True, exist_ok=True)

        # 复制模板（如果有）
        if TEMPLATES_DIR.exists():
            for item in TEMPLATES_DIR.iterdir():
                if item.name.startswith("."):
                    continue
                dest = project_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

        # 初始化状态
        state = {
            "current_micro_state": "concept-init",
            "micro_state_history": [],
            "stage_completed": [],
            "context_store": {},
            "user_inputs": {},
            "template": "economic-research",
            "project_name": name,
            "created_at": datetime.now().isoformat(),
        }
        save_state(name, state, PAPERS_DIR)
        set_current_project(name, CONFIG_DIR)

        return {"ok": True, "project": name, "path": str(project_path)}

    def use_project(self, name: str) -> dict:
        """切换项目"""
        project_path = PAPERS_DIR / name
        if not project_path.exists():
            return {"ok": False, "error": f"项目 '{name}' 不存在"}
        set_current_project(name, CONFIG_DIR)
        return {"ok": True, "project": name}

    def list_projects(self) -> List[dict]:
        """列出所有项目"""
        projects = list_projects(PAPERS_DIR)
        current = get_current_project(CONFIG_DIR)
        result = []
        for p in projects:
            state = load_state(p, PAPERS_DIR)
            result.append({
                "name": p,
                "is_current": p == current,
                "current_state": state.get("current_micro_state", "concept-init"),
                "completed_stages": state.get("stage_completed", []),
            })
        return result

    def get_status(self, project_name: Optional[str] = None) -> dict:
        """获取项目状态摘要"""
        if project_name is None:
            project_name = get_current_project(CONFIG_DIR)
        if project_name is None:
            return {"ok": False, "error": "未选择项目"}

        state = load_state(project_name, PAPERS_DIR)
        current_state_id = state.get("current_micro_state", "concept-init")
        completed = state.get("stage_completed", [])
        ctx = state.get("context_store", {})

        # 找所属模块
        module_name = current_state_id.split("-")[0] if "-" in current_state_id else current_state_id
        module = self.registry.get(module_name)

        return {
            "ok": True,
            "project": project_name,
            "current_state": current_state_id,
            "module": module_name,
            "module_desc": module.description if module else "",
            "completed_stages": completed,
            "context_fields": list(ctx.keys()),
            "history_count": len(state.get("micro_state_history", [])),
        }

    # ── 状态转移 ──

    def advance(
        self,
        project_name: Optional[str] = None,
        target_state: Optional[str] = None,
    ) -> dict:
        """推进到下一状态

        Args:
          project_name: 项目名（默认当前项目）
          target_state: 目标状态 ID（默认由 LLM 根据上下文决定）

        Returns:
          转移结果
        """
        if project_name is None:
            project_name = get_current_project(CONFIG_DIR)
        if project_name is None:
            return {"ok": False, "error": "未选择项目"}

        state = load_state(project_name, PAPERS_DIR)
        current_state = state.get("current_micro_state", "concept-init")

        if target_state and target_state != current_state:
            # LLM 指定的目标状态
            next_state = target_state
        elif target_state == current_state:
            return {"ok": True, "message": "已在目标状态", "state": current_state}
        else:
            return {
                "ok": False,
                "error": "未指定目标状态。LLM 应根据上下文决定推进到哪个状态。",
                "current_state": current_state,
            }

        # 记录转移
        transition = {
            "from": current_state,
            "to": next_state,
            "time": datetime.now().isoformat(),
            "action": "推进",
        }
        history = state.setdefault("micro_state_history", [])
        history.append(transition)

        # 检查是否跨阶段
        from_module = current_state.split("-")[0] if "-" in current_state else current_state
        to_module = next_state.split("-")[0] if "-" in next_state else next_state
        if from_module != to_module:
            completed = state.setdefault("stage_completed", [])
            if from_module not in completed:
                completed.append(from_module)

        state["current_micro_state"] = next_state
        save_state(project_name, state, PAPERS_DIR)

        return {
            "ok": True,
            "from": current_state,
            "to": next_state,
            "message": f"已推进到: {next_state}",
        }

    def jump(self, project_name: Optional[str] = None, target_state: str = "") -> dict:
        """跳转到指定状态"""
        if project_name is None:
            project_name = get_current_project(CONFIG_DIR)
        if project_name is None:
            return {"ok": False, "error": "未选择项目"}

        state = load_state(project_name, PAPERS_DIR)
        current_state = state.get("current_micro_state", "concept-init")

        if not target_state:
            return {"ok": False, "error": "请指定目标状态"}

        # 校验目标状态是否存在
        module_name = target_state.split("-")[0] if "-" in target_state else target_state
        module = self.registry.get(module_name)
        if not module:
            return {"ok": False, "error": f"未知状态: {target_state}（未找到所属模块 '{module_name}'）"}

        transition = {
            "from": current_state,
            "to": target_state,
            "time": datetime.now().isoformat(),
            "action": "跳转",
        }
        state.setdefault("micro_state_history", []).append(transition)
        state["current_micro_state"] = target_state
        save_state(project_name, state, PAPERS_DIR)

        return {"ok": True, "from": current_state, "to": target_state}

    def undo(self, project_name: Optional[str] = None) -> dict:
        """回退到上一个状态"""
        if project_name is None:
            project_name = get_current_project(CONFIG_DIR)
        if project_name is None:
            return {"ok": False, "error": "未选择项目"}

        state = load_state(project_name, PAPERS_DIR)
        history = state.get("micro_state_history", [])
        if not history:
            return {"ok": False, "error": "没有可回退的历史记录"}

        last = history.pop()
        target_state = last["from"]
        state["current_micro_state"] = target_state
        state["micro_state_history"] = history
        save_state(project_name, state, PAPERS_DIR)

        return {
            "ok": True,
            "from": last["to"],
            "to": target_state,
            "message": f"⏪ 已回退到: {target_state}",
        }

    def reset(self, project_name: Optional[str] = None) -> dict:
        """重置项目到初始状态"""
        if project_name is None:
            project_name = get_current_project(CONFIG_DIR)
        if project_name is None:
            return {"ok": False, "error": "未选择项目"}

        state = load_state(project_name, PAPERS_DIR)
        state["current_micro_state"] = "concept-init"
        state["micro_state_history"] = []
        state["stage_completed"] = []
        state["context_store"] = {}
        save_state(project_name, state, PAPERS_DIR)

        return {"ok": True, "message": "项目已重置至初始状态"}

    # ── 模块路由 ──

    def get_available_modules(self) -> List[str]:
        """返回已注册的所有模块名称"""
        return list(self.registry.all.keys())

    def get_next_suggestions(self, project_name: Optional[str] = None) -> dict:
        """建议下一个可进入的模块（给 LLM 参考）"""
        if project_name is None:
            project_name = get_current_project(CONFIG_DIR)
        if project_name is None:
            return {"modules": self.get_available_modules()}

        state = load_state(project_name, PAPERS_DIR)
        completed = state.get("stage_completed", [])
        current_state = state.get("current_micro_state", "")
        current_module = current_state.split("-")[0] if "-" in current_state else current_state

        ctx = state.get("context_store", {})

        suggestions = []
        for name, contract in self.registry.all.items():
            if name == current_module:
                continue
            # 检查前置依赖是否满足
            missing = contract.validate_inputs(ctx)
            suggestions.append({
                "module": name,
                "description": contract.description,
                "ready": len(missing) == 0,
                "missing_fields": missing,
            })

        return {
            "current_module": current_module,
            "completed": completed,
            "suggestions": suggestions,
        }


# ── CLI 入口 ──

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/orchestrator.py <命令> [参数]")
        print("命令: new, use, list, status, advance, jump, undo, reset")
        return

    orch = Orchestrator()
    cmd = sys.argv[1]

    if cmd == "new" and len(sys.argv) > 2:
        result = orch.new_project(sys.argv[2])
    elif cmd == "use" and len(sys.argv) > 2:
        result = orch.use_project(sys.argv[2])
    elif cmd == "list":
        projects = orch.list_projects()
        print(f"共 {len(projects)} 个项目:\n")
        for p in projects:
            marker = "*" if p["is_current"] else " "
            print(f" {marker} {p['name']:40s} -> {p['current_state']}")
        return
    elif cmd == "status":
        project = sys.argv[2] if len(sys.argv) > 2 else None
        result = orch.get_status(project)
    elif cmd == "advance":
        target = sys.argv[2] if len(sys.argv) > 2 else None
        result = orch.advance(target_state=target)
    elif cmd == "jump" and len(sys.argv) > 2:
        result = orch.jump(target_state=sys.argv[2])
    elif cmd == "undo":
        result = orch.undo()
    elif cmd == "reset":
        result = orch.reset()
    else:
        print(f"未知命令: {cmd}")
        return

    # 输出结果
    if result.get("ok"):
        if "message" in result:
            print(result["message"])
        elif "project" in result:
            print(f"✅ 项目: {result['project']}")
    else:
        print(f"❌ {result.get('error', '操作失败')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
