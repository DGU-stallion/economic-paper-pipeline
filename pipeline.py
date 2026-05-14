#!/usr/bin/env python3
"""
经济学实证论文自动化工作流 - 状态管理工具
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PIPELINE_STATE_FILE = Path(__file__).parent / "pipeline_state.json"

STAGES = [
    {"id": "topic", "name": "选题研究", "emoji": "topic"},
    {"id": "literature", "name": "文献综述", "emoji": "literature"},
    {"id": "data", "name": "数据获取与清洗", "emoji": "data"},
    {"id": "stata", "name": "Stata实证回归", "emoji": "stata"},
    {"id": "robustness", "name": "稳健性检验", "emoji": "robustness"},
    {"id": "conclusion", "name": "验证结论", "emoji": "conclusion"},
    {"id": "paper", "name": "LaTeX论文撰写", "emoji": "paper"},
]


def load_state():
    if PIPELINE_STATE_FILE.exists():
        with open(PIPELINE_STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"current_stage": 0, "history": [], "created_at": datetime.now().isoformat()}


def save_state(state):
    state["updated_at"] = datetime.now().isoformat()
    with open(PIPELINE_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def cmd_status(state):
    total = len(STAGES)
    current = state["current_stage"]
    print(f"当前阶段: [{current + 1}/{total}] {STAGES[current]['name']}")
    print()
    for i, stage in enumerate(STAGES):
        prefix = ">>" if i == current else "  "
        done = "v" if i < current else (" " if i > current else ">")
        print(f" {prefix} [{done}] {stage['name']}")

    if state["history"]:
        print(f"\n最近记录:")
        for h in state["history"][-3:]:
            print(f"  {h['time'][:16]} | {h['stage']}: {h['action']}")


def cmd_advance(state):
    current = state["current_stage"]
    if current >= len(STAGES) - 1:
        print("所有阶段已完成！如需重新开始请使用: python pipeline.py reset")
        return

    stage_name = STAGES[current]["name"]
    state["history"].append({
        "stage": stage_name,
        "action": "完成",
        "time": datetime.now().isoformat(),
    })
    state["current_stage"] = current + 1
    save_state(state)
    print(f"已推进至下一阶段: {STAGES[current + 1]['name']}")


def cmd_history(state):
    if not state["history"]:
        print("暂无历史记录。")
        return
    for h in state["history"]:
        print(f"{h['time'][:19]}  [{h['stage']}] {h['action']}")


def cmd_reset(state):
    stage_name = STAGES[state["current_stage"]]["name"]
    state["history"].append({
        "stage": stage_name,
        "action": "重置",
        "time": datetime.now().isoformat(),
    })
    state["current_stage"] = 0
    save_state(state)
    print("工作流已重置至第一阶段: 选题研究")


def main():
    state = load_state()

    if len(sys.argv) < 2:
        cmd_status(state)
        return

    cmd = sys.argv[1]
    if cmd == "status":
        cmd_status(state)
    elif cmd == "advance":
        cmd_advance(state)
    elif cmd == "history":
        cmd_history(state)
    elif cmd == "reset":
        cmd_reset(state)
    else:
        print(f"未知命令: {cmd}")
        print("用法: python pipeline.py [status|advance|history|reset]")
        sys.exit(1)


if __name__ == "__main__":
    main()
