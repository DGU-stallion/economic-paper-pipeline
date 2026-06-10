#!/usr/bin/env python3
"""验证助手 (Verify) — 模块入口"""
from scripts.shared.contract import ModuleContract, FieldSpec

MODULE_CONTRACT = ModuleContract(
    name="verify",
    description="验证助手：稳健性检验套件（安慰剂/替换变量/子样本/换标准误）",
    consumes={
        "baseline": FieldSpec(type="dict", required=True, desc="基准回归结果", source="analyze"),
        "clean_data_path": FieldSpec(type="str", required=True, desc="清洗后数据路径", source="data"),
        "y_var": FieldSpec(type="str", required=True, desc="被解释变量", source="conceptualize"),
        "d_var": FieldSpec(type="str", required=True, desc="核心解释变量", source="conceptualize"),
    },
    provides={
        "robustness_results": FieldSpec(type="dict", required=True, desc="稳健性检验结果汇总"),
    },
    states=["verify-plan", "verify-execute"],
)
