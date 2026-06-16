#!/usr/bin/env python3
"""
对话记忆持久化系统
支持多项目独立对话记忆，包含消息历史、对话状态、用户偏好、决策记录
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from scripts.shared.paths import PAPERS_DIR


class ConversationMemory:
    """对话记忆管理器"""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_path = PAPERS_DIR / project_name
        self.conversation_file = self.project_path / "conversation.json"
        self._data = self._load()

    def _load(self) -> Dict:
        """加载或初始化对话记忆"""
        if self.conversation_file.exists():
            with open(self.conversation_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return self._init_default()

    def _init_default(self) -> Dict:
        """初始化默认记忆结构"""
        now = datetime.now().isoformat()
        return {
            "version": "1.0",
            "project_name": self.project_name,
            "created_at": now,
            "updated_at": now,
            "current_state": {
                "stage": "topic",
                "substage": "5w1h",
                "step": "what",
                "last_interaction": now,
                "conversation_topic": "5W1H 头脑风暴 - What 维度"
            },
            "messages": [],
            "decisions": [],
            "preferences": {
                "output_format": "detailed",
                "interaction_style": "collaborative",
                "preferred_language": "zh-CN",
                "auto_advance": False,
                "table_format": "latex",
                # 论文格式偏好（进入 Stage 7 时询问）
                "paper_template": "economic-research",
                "paper_word_count": "",
                "paper_ref_style": "",
                "paper_lang_requirement": "",
                "paper_extra_requirements": "",
            },
            "context_summary": {
                "last_summary": "新项目已创建，即将开始选题研究。",
                "next_action": "开始 5W1H 头脑风暴的 What 维度讨论"
            }
        }

    def save(self):
        """保存对话记忆到文件"""
        self._data["updated_at"] = datetime.now().isoformat()
        self._data["current_state"]["last_interaction"] = datetime.now().isoformat()
        self.project_path.mkdir(parents=True, exist_ok=True)
        with open(self.conversation_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def add_message(self, role: str, content: str,
                    stage: Optional[str] = None,
                    substage: Optional[str] = None,
                    metadata: Optional[Dict] = None) -> str:
        """
        添加一条消息
        返回消息 ID
        """
        msg_id = str(uuid.uuid4())
        message = {
            "id": msg_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "stage": stage or self._data["current_state"]["stage"],
            "substage": substage or self._data["current_state"]["substage"],
            "metadata": metadata or {}
        }
        self._data["messages"].append(message)
        return msg_id

    def add_user_message(self, content: str, **kwargs) -> str:
        """添加用户消息"""
        return self.add_message("user", content, **kwargs)

    def add_agent_message(self, content: str, **kwargs) -> str:
        """添加 Agent 消息"""
        return self.add_message("agent", content, **kwargs)

    def add_system_message(self, content: str, **kwargs) -> str:
        """添加系统消息"""
        return self.add_message("system", content, **kwargs)

    def get_recent_messages(self, n: int = 10) -> List[Dict]:
        """获取最近 N 条消息"""
        return self._data["messages"][-n:]

    def get_messages_by_role(self, role: str) -> List[Dict]:
        """按角色获取消息"""
        return [m for m in self._data["messages"] if m["role"] == role]

    def get_messages_by_stage(self, stage: str, substage: Optional[str] = None) -> List[Dict]:
        """按阶段获取消息"""
        if substage:
            return [m for m in self._data["messages"]
                    if m["stage"] == stage and m["substage"] == substage]
        return [m for m in self._data["messages"] if m["stage"] == stage]

    def search_messages(self, keyword: str, case_sensitive: bool = False) -> List[Dict]:
        """按关键词搜索消息"""
        if case_sensitive:
            return [m for m in self._data["messages"] if keyword in m["content"]]
        return [m for m in self._data["messages"]
                if keyword.lower() in m["content"].lower()]

    def get_all_messages(self) -> List[Dict]:
        """获取所有消息"""
        return self._data["messages"]

    def clear_messages(self, keep_last: int = 0):
        """清空消息历史，可选择保留最后 N 条"""
        if keep_last > 0:
            self._data["messages"] = self._data["messages"][-keep_last:]
        else:
            self._data["messages"] = []

    def update_state(self, **kwargs):
        """更新对话状态"""
        for key, value in kwargs.items():
            if key in self._data["current_state"]:
                self._data["current_state"][key] = value

    def get_state(self) -> Dict:
        """获取当前对话状态"""
        return self._data["current_state"].copy()

    def add_decision(self, decision: str, category: str,
                     context: str = "", confirmed: bool = True) -> str:
        """
        记录一个决策
        返回决策 ID
        """
        decision_id = str(uuid.uuid4())
        self._data["decisions"].append({
            "id": decision_id,
            "decision": decision,
            "category": category,
            "confirmed": confirmed,
            "confirmed_at": datetime.now().isoformat() if confirmed else None,
            "context": context
        })
        return decision_id

    def get_decisions(self, category: Optional[str] = None,
                      confirmed_only: bool = False) -> List[Dict]:
        """获取决策记录"""
        decisions = self._data["decisions"]
        if category:
            decisions = [d for d in decisions if d["category"] == category]
        if confirmed_only:
            decisions = [d for d in decisions if d["confirmed"]]
        return decisions

    def confirm_decision(self, decision_id: str):
        """确认一个决策"""
        for d in self._data["decisions"]:
            if d["id"] == decision_id:
                d["confirmed"] = True
                d["confirmed_at"] = datetime.now().isoformat()
                break

    def update_preferences(self, **kwargs):
        """更新用户偏好"""
        for key, value in kwargs.items():
            if key in self._data["preferences"]:
                self._data["preferences"][key] = value

    def get_preferences(self) -> Dict:
        """获取用户偏好"""
        return self._data["preferences"].copy()

    def set_context_summary(self, summary: str, next_action: str):
        """设置上下文摘要"""
        self._data["context_summary"]["last_summary"] = summary
        self._data["context_summary"]["next_action"] = next_action

    def get_context_summary(self) -> Dict:
        """获取上下文摘要"""
        return self._data["context_summary"].copy()

    def generate_resume_message(self, detail_level: str = "medium") -> str:
        """
        生成对话恢复话术

        detail_level: brief|medium|detailed
        """
        state = self._data["current_state"]
        summary = self._data["context_summary"]
        decisions = self.get_decisions(confirmed_only=True)

        stage_names = {
            "topic": "选题研究",
            "literature": "文献综述",
            "data": "数据获取与清洗",
            "stata": "Stata实证回归",
            "robustness": "稳健性检验",
            "conclusion": "验证结论",
            "paper": "LaTeX论文撰写"
        }

        if detail_level == "brief":
            return (f"欢迎回来！我们上次聊到「{stage_names.get(state['stage'], state['stage'])}」阶段，"
                    f"继续吧！")

        base_msg = f"欢迎回到「{self.project_name}」项目！\n\n"

        if detail_level == "medium":
            base_msg += (f"上次我们聊到「{stage_names.get(state['stage'], state['stage'])}」阶段。\n"
                        f"{summary['last_summary']}\n\n"
                        f"接下来：{summary['next_action']}")
            return base_msg

        # detailed
        base_msg += f"当前阶段：{stage_names.get(state['stage'], state['stage'])}\n"
        base_msg += f"当前子阶段：{state.get('substage', 'N/A')}\n"
        base_msg += f"当前步骤：{state.get('step', 'N/A')}\n\n"
        base_msg += f"对话摘要：{summary['last_summary']}\n\n"

        if decisions:
            base_msg += "已确认的决策：\n"
            for d in decisions[-5:]:
                base_msg += f"  • {d['decision']}\n"
            base_msg += "\n"

        base_msg += f"下一步：{summary['next_action']}\n\n"
        base_msg += "准备好了吗？我们继续！"

        return base_msg

    def get_stats(self) -> Dict:
        """获取对话统计信息"""
        messages = self._data["messages"]
        return {
            "total_messages": len(messages),
            "user_messages": len([m for m in messages if m["role"] == "user"]),
            "agent_messages": len([m for m in messages if m["role"] == "agent"]),
            "system_messages": len([m for m in messages if m["role"] == "system"]),
            "total_decisions": len(self._data["decisions"]),
            "confirmed_decisions": len(self.get_decisions(confirmed_only=True)),
            "first_message": messages[0]["timestamp"] if messages else None,
            "last_message": messages[-1]["timestamp"] if messages else None
        }


def get_memory(project_name: str) -> ConversationMemory:
    """获取指定项目的对话记忆"""
    return ConversationMemory(project_name)


def get_current_project_memory() -> Optional[ConversationMemory]:
    """获取当前项目的对话记忆"""
    from scripts.shared.paths import CONFIG_DIR
    current_file = CONFIG_DIR / "current_project.json"
    if not current_file.exists():
        return None
    with open(current_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    project_name = data.get("current_project")
    if not project_name:
        return None
    return ConversationMemory(project_name)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python memory.py <project_name> [command]")
        print("命令:")
        print("  resume    - 显示恢复话术")
        print("  stats     - 显示统计信息")
        print("  messages  - 显示最近消息")
        print("  decisions - 显示决策记录")
        sys.exit(1)

    project_name = sys.argv[1]
    mem = ConversationMemory(project_name)

    cmd = sys.argv[2] if len(sys.argv) > 2 else "resume"

    if cmd == "resume":
        print(mem.generate_resume_message("detailed"))
    elif cmd == "stats":
        stats = mem.get_stats()
        print("对话统计:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    elif cmd == "messages":
        print("最近 10 条消息:")
        for msg in mem.get_recent_messages(10):
            print(f"  [{msg['role']}] {msg['content'][:60]}...")
    elif cmd == "decisions":
        print("已确认决策:")
        for d in mem.get_decisions(confirmed_only=True):
            print(f"  [{d['category']}] {d['decision']}")
