#!/usr/bin/env python3
"""数据助手 (Data) — 模块入口"""
from scripts.shared.contract import ModuleContract, FieldSpec

MODULE_CONTRACT = ModuleContract(
    name="data",
    description="数据助手：原始数据清洗、变量构造、质量验证",
    consumes={
        "y_var": FieldSpec(type="str", required=True, desc="被解释变量名", source="conceptualize"),
        "d_var": FieldSpec(type="str", required=True, desc="核心解释变量名", source="conceptualize"),
        "control_vars": FieldSpec(type="list[str]", required=False, desc="控制变量列表", source="conceptualize"),
    },
    provides={
        "clean_data_path": FieldSpec(type="str", required=True, desc="清洗后数据文件路径"),
        "data_quality_report": FieldSpec(type="str", required=False, desc="数据质量报告路径"),
    },
    states=["data-diagnosis", "data-plan", "data-clean", "data-validate"],
)
