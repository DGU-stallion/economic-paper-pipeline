#!/usr/bin/env python3
"""
Skill 协调器 - 上下文管理工具
负责：项目上下文的读取、更新、持久化
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).parent.parent.parent


class SkillContextManager:
    """Skill 上下文管理器"""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_path = ROOT / "papers" / project_name
        self.state_file = self.project_path / "pipeline_state.json"

    def load_state(self) -> Dict[str, Any]:
        """加载项目状态（含上下文）"""
        if not self.state_file.exists():
            return {
                "current_stage": 0,
                "current_skill": "skill-topic",
                "history": [],
                "context_store": {},
                "resume_point": None
            }

        with open(self.state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        # 确保有 context_store
        if "context_store" not in state:
            state["context_store"] = {}

        return state

    def save_state(self, state: Dict[str, Any]) -> None:
        """保存项目状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def update_skill_output(self, skill_id: str, output_data: Dict[str, Any]) -> None:
        """更新某个 Skill 的输出到上下文"""
        state = self.load_state()
        state["context_store"][skill_id] = output_data
        self.save_state(state)

    def get_skill_input(self, skill_id: str) -> Dict[str, Any]:
        """获取某个 Skill 的输入上下文（前序所有 Skill 的输出合并）"""
        state = self.load_state()
        context_store = state.get("context_store", {})

        # Skill 执行顺序决定依赖关系
        skill_order = ["skill-topic", "skill-literature", "skill-stata", "skill-latex"]
        skill_index = skill_order.index(skill_id)

        # 收集所有前序 Skill 的输出
        merged_context = {
            "project_name": self.project_name,
            "project_path": str(self.project_path),
            "entry_point": "resume" if state.get("resume_point") else "new"
        }

        # 合并前序 Skill 输出
        for prev_skill in skill_order[:skill_index]:
            if prev_skill in context_store:
                prev_context = context_store[prev_skill]
                # 特殊处理：提取关键数据
                if prev_skill == "skill-topic" and "research_proposal" in prev_context:
                    merged_context["topic_context"] = prev_context["research_proposal"]
                elif prev_skill == "skill-literature" and "literature_summary" in prev_context:
                    merged_context["literature_context"] = prev_context

        # 特殊：skill-latex 需要所有前序
        if skill_id == "skill-latex":
            if "skill-topic" in context_store:
                merged_context["topic_context"] = context_store["skill-topic"].get("research_proposal", {})
            if "skill-literature" in context_store:
                merged_context["literature_context"] = context_store["skill-literature"]
            if "skill-stata" in context_store:
                merged_context["stata_context"] = context_store["skill-stata"]

        return merged_context

    def set_resume_point(self, skill_id: str, step: str, partial_data: Dict = None) -> None:
        """设置断点续传位置"""
        state = self.load_state()
        state["resume_point"] = {
            "skill": skill_id,
            "step": step,
            "partial_data": partial_data or {}
        }
        self.save_state(state)

    def clear_resume_point(self) -> None:
        """清除断点续传标记"""
        state = self.load_state()
        state["resume_point"] = None
        self.save_state(state)

    def add_history(self, action: str, detail: str = "") -> None:
        """添加历史记录"""
        state = self.load_state()
        if "history" not in state:
            state["history"] = []

        from datetime import datetime
        state["history"].append({
            "time": datetime.now().isoformat(),
            "skill": state.get("current_skill", "unknown"),
            "action": action,
            "detail": detail
        })
        self.save_state(state)


def cmd_get_input(project_name: str, skill_id: str) -> None:
    """获取 Skill 输入上下文"""
    mgr = SkillContextManager(project_name)
    context = mgr.get_skill_input(skill_id)
    print(json.dumps(context, ensure_ascii=False, indent=2))


def cmd_save_output(project_name: str, skill_id: str, output_json: str) -> None:
    """保存 Skill 输出"""
    mgr = SkillContextManager(project_name)
    output_data = json.loads(output_json)
    mgr.update_skill_output(skill_id, output_data)
    mgr.add_history(f"{skill_id} 完成")
    print(f"已保存 {skill_id} 输出")


def cmd_set_resume(project_name: str, skill_id: str, step: str) -> None:
    """设置断点"""
    mgr = SkillContextManager(project_name)
    mgr.set_resume_point(skill_id, step)
    print(f"已设置断点: {skill_id} @ {step}")


def main():
    if len(sys.argv) < 3:
        print("用法:")
        print("  python context_manager.py get-input <项目名> <skill_id>")
        print("  python context_manager.py save-output <项目名> <skill_id> <output_json>")
        print("  python context_manager.py set-resume <项目名> <skill_id> <step>")
        return

    cmd = sys.argv[1]
    project_name = sys.argv[2]

    if cmd == "get-input":
        skill_id = sys.argv[3]
        cmd_get_input(project_name, skill_id)
    elif cmd == "save-output":
        skill_id = sys.argv[3]
        output_json = sys.argv[4]
        cmd_save_output(project_name, skill_id, output_json)
    elif cmd == "set-resume":
        skill_id = sys.argv[3]
        step = sys.argv[4]
        cmd_set_resume(project_name, skill_id, step)
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
