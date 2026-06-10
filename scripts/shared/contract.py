#!/usr/bin/env python3
"""模块契约定义：每个模块通过 ModuleContract 声明 I/O 边界。"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FieldSpec:
    """一个 context 字段的定义"""
    type: str                          # "str" | "list[str]" | "dict"
    required: bool = True
    desc: str = ""
    source: Optional[str] = None       # 来自哪个模块（编排器推导用）


@dataclass
class ModuleContract:
    """模块契约

    每个模块通过 consumes / provides 声明它需要什么、产出什么。
    编排器据此推导上下游依赖，做门禁校验。
    """

    name: str
    description: str

    # 这个模块消费的 context 字段
    consumes: Dict[str, FieldSpec] = field(default_factory=dict)

    # 这个模块产出的 context 字段
    provides: Dict[str, FieldSpec] = field(default_factory=dict)

    # 涉及的状态（可选，编排器用）
    states: List[str] = field(default_factory=list)

    # 独立运行入口（可选）
    entry_points: Dict[str, str] = field(default_factory=dict)

    def validate_inputs(self, context: dict) -> List[str]:
        """检查 context 是否满足 consumes 要求，返回缺失字段列表"""
        missing = []
        for key, spec in self.consumes.items():
            if spec.required and (key not in context or context.get(key) is None):
                missing.append(key)
        return missing

    def extract_outputs(self, context: dict) -> dict:
        """从 context 中提取本模块产出的字段"""
        return {k: context[k] for k in self.provides if k in context}

    def check_readiness(self, context: dict) -> Dict[str, List[str]]:
        """完整就绪检查，返回 {ok: bool, missing: [], notes: []}"""
        missing = self.validate_inputs(context)
        return {
            "ok": len(missing) == 0,
            "missing": missing,
            "notes": [],
        }
