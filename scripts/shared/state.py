#!/usr/bin/env python3
"""状态管理：pipeline_state.json 的读写和迁移"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from scripts.shared.paths import PAPERS_DIR, CONFIG_DIR


DEFAULT_STATE = {
    "current_micro_state": "concept-init",
    "micro_state_history": [],
    "stage_completed": [],
    "context_store": {},
    "user_inputs": {},
    "decisions": [],
    "template": "economic-research",
}


def get_project_path(project_name: str, papers_dir: Optional[Path] = None) -> Path:
    """获取项目路径"""
    base = papers_dir or PAPERS_DIR
    return base / project_name


def get_state_file(project_name: str, papers_dir: Optional[Path] = None) -> Path:
    """获取项目的状态文件路径"""
    return get_project_path(project_name, papers_dir) / "pipeline_state.json"


def load(project_name: str, papers_dir: Optional[Path] = None):
    """加载项目状态，如果文件不存在则返回默认状态"""
    state_file = get_state_file(project_name, papers_dir)
    if state_file.exists():
        with open(state_file, encoding="utf-8") as f:
            raw = json.load(f)
        return _migrate(raw)
    return dict(DEFAULT_STATE, project_name=project_name, created_at=datetime.now().isoformat())


def _migrate(raw: dict) -> dict:
    """从旧版状态迁移（V1 -> V2 模块化状态）"""
    # V1 使用 state ID like "topic-5w1h-what"
    # V2 使用 module state like "concept-5w1h"
    if "current_micro_state" not in raw:
        raw["current_micro_state"] = "concept-init"
    if "micro_state_history" not in raw:
        raw["micro_state_history"] = []
    if "stage_completed" not in raw:
        raw["stage_completed"] = []
    if "context_store" not in raw:
        raw["context_store"] = {}
    if "user_inputs" not in raw:
        raw["user_inputs"] = {}
    if "template" not in raw:
        raw["template"] = "economic-research"
    return raw


def save(project_name: str, state: dict, papers_dir: Optional[Path] = None):
    """保存项目状态"""
    state["updated_at"] = datetime.now().isoformat()
    state_file = get_state_file(project_name, papers_dir)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_current_project(config_dir: Optional[Path] = None) -> Optional[str]:
    """获取当前激活的项目名称"""
    if config_dir is None:
        config_dir = CONFIG_DIR
    current_file = config_dir / "current_project.json"
    if not current_file.exists():
        return None
    with open(current_file, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("current_project")


def set_current_project(project_name: str, config_dir: Optional[Path] = None):
    """设置当前激活的项目"""
    if config_dir is None:
        config_dir = CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)
    current_file = config_dir / "current_project.json"
    with open(current_file, "w", encoding="utf-8") as f:
        json.dump({"current_project": project_name}, f, ensure_ascii=False, indent=2)


def list_projects(papers_dir: Optional[Path] = None) -> List[str]:
    """列出所有项目"""
    if papers_dir is None:
        papers_dir = PAPERS_DIR
    if not papers_dir.exists():
        return []
    return sorted([p.name for p in papers_dir.iterdir() if p.is_dir()])
