#!/usr/bin/env python3
"""论文助手 (Write) — 模块入口"""
from scripts.shared.contract import ModuleContract, FieldSpec

MODULE_CONTRACT = ModuleContract(
    name="write",
    description="论文助手：从回归表格和文献综述生成完整 LaTeX 论文",
    consumes={
        "research_question": FieldSpec(type="str", required=True, desc="研究问题", source="conceptualize"),
        "baseline": FieldSpec(type="dict", required=False, desc="基准回归结果", source="analyze"),
        "heterogeneity": FieldSpec(type="dict", required=False, desc="异质性分析", source="analyze"),
        "literature_review_path": FieldSpec(type="str", required=False, desc="文献综述路径", source="literature"),
        "bib_path": FieldSpec(type="str", required=False, desc="参考文献路径", source="literature"),
        "robustness_results": FieldSpec(type="dict", required=False, desc="稳健性检验结果", source="verify"),
    },
    provides={
        "tex_path": FieldSpec(type="str", required=True, desc="生成的 LaTeX 主文件路径"),
    },
    states=["write-outline", "write-sections", "write-qc"],
)
