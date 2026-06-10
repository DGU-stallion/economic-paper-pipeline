#!/usr/bin/env python3
"""调研助手 (Research Assistant) — 模块入口"""

from scripts.shared.contract import ModuleContract, FieldSpec

MODULE_CONTRACT = ModuleContract(
    name="research",
    description="调研助手：从网络上搜索相关文献和数据源，只负责找不负责处理",

    # ── 输入（从概念助手或用户直接提供）──
    consumes={
        "research_question": FieldSpec(
            type="str", required=True,
            desc="一句话研究问题",
        ),
        "keywords": FieldSpec(
            type="list[str]", required=False,
            desc="搜索关键词（可选，未提供则从 research_question 自动生成）",
        ),
        "y_var": FieldSpec(
            type="str", required=False,
            desc="被解释变量名（辅助搜索用）",
        ),
        "d_var": FieldSpec(
            type="str", required=False,
            desc="核心解释变量名（辅助搜索用）",
        ),
        "time_window": FieldSpec(
            type="str", required=False,
            desc="时间窗口描述，如 '2010-2020'",
            source="conceptualize",
        ),
        "geographic_scope": FieldSpec(
            type="str", required=False,
            desc="地理范围，如 '中国 A 股上市公司'",
            source="conceptualize",
        ),
        "identification": FieldSpec(
            type="str", required=False,
            desc="识别策略，如 DID / RDD / IV（辅助搜索用）",
        ),
    },

    # ── 输出 ──
    provides={
        "candidate_papers": FieldSpec(
            type="list[dict]", required=True,
            desc="候选论文列表：[{title, authors, year, abstract, url, source}]",
        ),
        "data_sources": FieldSpec(
            type="list[dict]", required=False,
            desc="可用数据源：[{name, source_abstract, variables, time_coverage, access_method, url}]",
        ),
        "feasibility_verdict": FieldSpec(
            type="str", required=True,
            desc="可行性结论：'feasible' / 'needs_adjustment' / 'infeasible'",
        ),
    },
)
