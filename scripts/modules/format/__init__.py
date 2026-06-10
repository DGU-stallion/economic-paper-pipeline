#!/usr/bin/env python3
"""格式助手 (Format) — 模块入口"""
from scripts.shared.contract import ModuleContract, FieldSpec

MODULE_CONTRACT = ModuleContract(
    name="format",
    description="格式助手：编译 LaTeX 源码为 PDF，AI 痕迹检测",
    consumes={
        "tex_path": FieldSpec(type="str", required=True, desc="LaTeX 主文件路径", source="write"),
    },
    provides={
        "pdf_path": FieldSpec(type="str", required=True, desc="编译生成的 PDF 路径"),
    },
    states=["format-compile", "format-humanizer"],
)
