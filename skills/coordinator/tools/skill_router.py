#!/usr/bin/env python3
"""
Skill 协调器 - Skill 路由工具
负责：根据项目阶段和用户意图，决定激活哪个 Skill
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).parent.parent.parent

# 阶段 -> Skill 映射（与 skill.json 中一致）
STAGE_TO_SKILL = {
    "topic": "topic",
    "literature": "literature",
    "data": "stata",
    "stata": "stata",
    "robustness": "stata",
    "conclusion": "stata",
    "paper": "latex"
}

# 阶段前置需求检查清单
STAGE_REQUIREMENTS = {
    "topic": [],
    "literature": ["research_question", "keywords"],
    "data": ["research_question"],
    "stata": ["cleaned_dta_path", "y_var", "d_var"],
    "robustness": ["baseline_regression_done"],
    "conclusion": ["all_regressions_done"],
    "paper": ["all_tables_generated"]
}

# 用户意图关键词 -> 目标阶段/动作
INTENT_PATTERNS = {
    "create_new": {
        "keywords": ["创建新项目", "新开一篇", "写一篇关于", "start new", "new paper"],
        "action": "create_new",
        "target_stage": "topic"
    },
    "list_projects": {
        "keywords": ["列出我的论文", "看看所有项目", "有哪些项目", "list projects"],
        "action": "list_projects"
    },
    "switch_project": {
        "keywords": ["切换到", "我要写那篇", "switch to"],
        "action": "switch_project"
    },
    "show_status": {
        "keywords": ["当前什么状态", "进展到哪了", "看看进度", "status"],
        "action": "show_status"
    },
    "advance_stage": {
        "keywords": ["推进到下一阶段", "这个阶段完成了", "下一步", "完成了", "next stage"],
        "action": "advance_stage"
    },
    "jump_to_literature": {
        "keywords": ["已经有选题了", "直接做文献", "skip to literature"],
        "action": "jump_stage",
        "target_stage": "literature"
    },
    "jump_to_stata": {
        "keywords": ["数据都整理好了", "帮我跑回归", "skip to stata", "直接实证"],
        "action": "jump_stage",
        "target_stage": "stata"
    },
    "jump_to_paper": {
        "keywords": ["就差写论文了", "直接写论文", "skip to paper", "生成论文"],
        "action": "jump_stage",
        "target_stage": "paper"
    },
    "reset_project": {
        "keywords": ["重置这个项目", "从头开始", "reset"],
        "action": "reset_project"
    }
}


def parse_user_intent(user_message: str) -> Dict:
    """解析用户自然语言意图"""
    user_message_lower = user_message.lower()

    for intent_name, pattern in INTENT_PATTERNS.items():
        for keyword in pattern["keywords"]:
            if keyword.lower() in user_message_lower:
                return {
                    "intent": intent_name,
                    "action": pattern["action"],
                    "target_stage": pattern.get("target_stage"),
                    "confidence": 0.8
                }

    # 无法识别明确意图，需要追问
    return {
        "intent": "unknown",
        "action": "ask_clarification",
        "confidence": 0.0
    }


def get_current_skill_for_project(project_name: str) -> str:
    """根据项目状态获取当前应该激活的 Skill"""
    state_file = ROOT / "papers" / project_name / "pipeline_state.json"

    if not state_file.exists():
        return "topic"  # 新项目默认从选题开始

    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)

    # 如果有断点续传，从断点位置的 Skill 继续
    if state.get("resume_point"):
        return state["resume_point"]["skill"]

    # 根据阶段索引映射到 Skill
    stages = ["topic", "literature", "data", "stata", "robustness", "conclusion", "paper"]
    current_stage_idx = state.get("current_stage", 0)
    if current_stage_idx >= len(stages):
        return "latex"

    current_stage = stages[current_stage_idx]
    return STAGE_TO_SKILL[current_stage]


def check_jump_requirements(target_stage: str, context: Dict) -> tuple[bool, List[str]]:
    """检查跳转到目标阶段的前置条件是否满足"""
    requirements = STAGE_REQUIREMENTS.get(target_stage, [])
    missing = []

    for req in requirements:
        if req not in context or not context[req]:
            missing.append(req)

    return len(missing) == 0, missing


def get_skill_entry_prompt(skill_id: str) -> str:
    """获取 Skill 的入口提示词"""
    skill_path = ROOT / "skills" / skill_id
    prompt_file = skill_path / "prompts" / "entry.md"

    if prompt_file.exists():
        return prompt_file.read_text(encoding='utf-8')
    return ""


def cmd_parse_intent(user_message: str) -> None:
    """解析用户意图"""
    result = parse_user_intent(user_message)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_get_current_skill(project_name: str) -> None:
    """获取项目当前的 Skill"""
    skill = get_current_skill_for_project(project_name)
    print(skill)


def cmd_check_requirements(target_stage: str, context_json: str) -> None:
    """检查前置条件"""
    context = json.loads(context_json)
    satisfied, missing = check_jump_requirements(target_stage, context)
    result = {
        "satisfied": satisfied,
        "missing_requirements": missing
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python skill_router.py parse-intent '<用户消息>'")
        print("  python skill_router.py get-current-skill <项目名>")
        print("  python skill_router.py check-requirements <目标阶段> '<上下文JSON>'")
        return

    cmd = sys.argv[1]

    if cmd == "parse-intent":
        user_message = sys.argv[2]
        cmd_parse_intent(user_message)
    elif cmd == "get-current-skill":
        project_name = sys.argv[2]
        cmd_get_current_skill(project_name)
    elif cmd == "check-requirements":
        target_stage = sys.argv[2]
        context_json = sys.argv[3]
        cmd_check_requirements(target_stage, context_json)
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
