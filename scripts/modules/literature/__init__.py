#!/usr/bin/env python3
"""文献助手 (Literature) — 模块入口"""
from scripts.shared.contract import ModuleContract, FieldSpec

MODULE_CONTRACT = ModuleContract(
    name="literature",
    description="文献助手：从候选论文列表中筛选、梳理脉络、撰写综述、生成 .bib",
    consumes={
        "candidate_papers": FieldSpec(
            type="list[dict]", required=True,
            desc="候选论文列表（来自调研助手）",
            source="research",
        ),
        "research_question": FieldSpec(
            type="str", required=True,
            desc="研究问题，用于定位文献空白",
            source="conceptualize",
        ),
    },
    provides={
        "literature_review_path": FieldSpec(
            type="str", required=True,
            desc="文献综述文件路径",
        ),
        "bib_path": FieldSpec(
            type="str", required=True,
            desc="参考文献 .bib 文件路径",
        ),
        "research_gap": FieldSpec(
            type="str", required=True,
            desc="识别的文献空白",
        ),
        "total_papers": FieldSpec(
            type="int", required=False,
            desc="综述涵盖的论文总数",
        ),
    },
    states=[
        "literature-screen",
        "literature-synthesize",
        "literature-write",
    ],
)
