#!/usr/bin/env python3
"""分析助手 (Analyze) — 模块入口"""
from scripts.shared.contract import ModuleContract, FieldSpec

MODULE_CONTRACT = ModuleContract(
    name="analyze",
    description="分析助手：从清洗后数据到回归表格（基准回归 + 异质性 + 中介效应）",
    consumes={
        "y_var": FieldSpec(type="str", required=True, desc="被解释变量名", source="conceptualize"),
        "d_var": FieldSpec(type="str", required=True, desc="核心解释变量名", source="conceptualize"),
        "identification": FieldSpec(type="str", required=True, desc="识别策略", source="conceptualize"),
        "control_vars": FieldSpec(type="list[str]", required=False, desc="控制变量", source="conceptualize"),
        "clean_data_path": FieldSpec(type="str", required=True, desc="清洗后数据路径", source="data"),
    },
    provides={
        "baseline": FieldSpec(type="dict", required=True, desc="基准回归结果（系数/SE/显著性）"),
        "heterogeneity": FieldSpec(type="dict", required=False, desc="异质性分析结果"),
        "mediation": FieldSpec(type="dict", required=False, desc="中介效应结果"),
    },
    states=["analyze-model-spec", "analyze-baseline", "analyze-heterogeneity"],
)
