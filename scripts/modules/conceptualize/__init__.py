#!/usr/bin/env python3
"""概念助手 (Conceptualize) — 模块入口"""

from scripts.shared.contract import ModuleContract, FieldSpec

MODULE_CONTRACT = ModuleContract(
    name="conceptualize",
    description="概念助手：从模糊的研究想法出发，通过 5W1H 引导产出完整研究方案",

    consumes={},  # 概念助手是所有模块的起点，不依赖其他模块

    provides={
        "research_question": FieldSpec(
            type="str", required=True,
            desc="一句话研究问题",
        ),
        "y_var": FieldSpec(
            type="str", required=True,
            desc="被解释变量名",
        ),
        "d_var": FieldSpec(
            type="str", required=True,
            desc="核心解释变量名",
        ),
        "identification": FieldSpec(
            type="str", required=True,
            desc="识别策略（FE/DID/IV/RDD 等）",
        ),
        "hypotheses": FieldSpec(
            type="list[str]", required=True,
            desc="待检验假设列表",
        ),
        "control_vars": FieldSpec(
            type="list[str]", required=False,
            desc="控制变量列表",
        ),
        "keywords": FieldSpec(
            type="list[str]", required=False,
            desc="搜索关键词（自动生成，供调研助手使用）",
        ),
        "time_window": FieldSpec(
            type="str", required=False,
            desc="时间窗口，如 '2010-2020'",
        ),
        "geographic_scope": FieldSpec(
            type="str", required=False,
            desc="地理范围，如 '中国 A 股上市公司'",
        ),
    },

    states=[
        "concept-init",
        "concept-5w1h",
        "concept-gap",
        "concept-smart",
        "concept-proposal",
    ],

    entry_points={
        "new": "开始一个新的概念化对话",
        "quick": "快速输入已有想法，直接输出方案",
    },
)
