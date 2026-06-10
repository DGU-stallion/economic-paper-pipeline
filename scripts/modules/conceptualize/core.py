#!/usr/bin/env python3
"""概念助手核心逻辑

流程:
  [5W1H 逐维引导] → [Gap 分析] → [SMART 精确化] → [假说推演] → [研究方案]

    5W1H:
    1. What   — 核心经济现象? Y/D 初步想法?
    2. Why    — 为什么重要? 理论贡献?
    3. Who    — 结论对谁有价值?
    4. When   — 时间跨度? 自然实验窗口?
    5. Where  — 地理范围? 制度背景?
    6. How    — 识别策略? (OLS/FE/DID/IV/RDD)

LLM 在对话中驱动 5W1H 过程，core.py 提供：
  - entry_prompts（对话引导话术）
  - 产出文件写入
  - 研究方案模板
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional


# ── 5W1H 维度定义 ──

DIMENSIONS = [
    {
        "id": "what",
        "name": "What — 研究对象",
        "prompt": """\
【What】核心经济现象
核心经济现象是什么？被解释变量 Y 和核心解释变量 D 的初步想法？""",
    },
    {
        "id": "why",
        "name": "Why — 研究动机",
        "prompt": """\
【Why】研究动机
为什么这个问题重要？理论贡献或政策含义何在？与既有文献的张力在哪里？""",
    },
    {
        "id": "who",
        "name": "Who — 利益相关方",
        "prompt": """\
【Who】利益相关方
这个研究结论对谁最有价值？（政策制定者、企业、劳动者、消费者）""",
    },
    {
        "id": "when",
        "name": "When — 时间维度",
        "prompt": """\
【When】时间维度
研究的时间跨度？是否有自然实验窗口？（政策冲击、制度变革、外部事件）""",
    },
    {
        "id": "where",
        "name": "Where — 空间/制度维度",
        "prompt": """\
【Where】空间/制度维度
制度背景和地理范围（国别/区域/行业）？数据来源的可得性如何？""",
    },
    {
        "id": "how",
        "name": "How — 识别策略",
        "prompt": """\
【How】识别策略
可能的识别策略（OLS/FE/DID/RDD/IV）？核心识别假设的初步思考？""",
    },
]


# ── 入口 ──

def run(
    initial_idea: str = "",
    project_dir: Optional[Path] = None,
) -> dict:
    """启动概念化流程

    初始化 context 结构，LLM 在对话中驱动 5W1H 流程，
    完成后调用 commit_proposal() 写入产出文件。

    Args:
      initial_idea: 用户初始的一句话想法
      project_dir: 项目路径（可选）

    Returns:
      初始化的 context 更新字典
    """
    if project_dir:
        topics_dir = project_dir / "topics"
        topics_dir.mkdir(parents=True, exist_ok=True)

    return {
        "research_question": initial_idea,
        "y_var": "",
        "d_var": "",
        "identification": "",
        "hypotheses": [],
        "control_vars": [],
        "keywords": [],
    }


def commit_proposal(
    result: dict,
    project_dir: Path,
):
    """将概念化结果写入产出文件

    Args:
      result: LLM 填充好的结果字段
      project_dir: 项目路径
    """
    now = datetime.now().isoformat(timespec="minutes")
    topics_dir = project_dir / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)

    research_question = result.get("research_question", "")
    y_var = result.get("y_var", "")
    d_var = result.get("d_var", "")
    identification = result.get("identification", "")
    hypotheses = result.get("hypotheses", [])
    control_vars = result.get("control_vars", [])
    keywords = result.get("keywords", [])

    # ── 研究方案 ──
    hypotheses_text = ""
    for i, h in enumerate(hypotheses, 1):
        hypotheses_text += f"{i}. {h}\n"

    controls_text = ", ".join(control_vars) if control_vars else "（待定）"
    keywords_text = ", ".join(keywords) if keywords else "（待生成）"

    proposal = f"""\
# 研究方案

生成时间: {now}

## 研究问题

{research_question}

## 核心变量

- **Y（被解释变量）**: {y_var}
- **D（核心解释变量）**: {d_var}
- **控制变量**: {controls_text}

## 识别策略

{identification}

## 研究假设

{hypotheses_text}
## 搜索关键词

{keywords_text}
---
*由概念助手 (Conceptualize) 自动生成*
"""
    proposal_file = topics_dir / "00_research_proposal.md"
    proposal_file.write_text(proposal, encoding="utf-8")


# ── 对话话术 ──

ENTRY_PROMPT = """\
你好，我是概念助手。我会通过 5W1H 框架帮你逐步梳理研究问题。

我们逐维度来，一次只讨论一个问题。

---

**你想研究什么？**（告诉我一个句子或几个关键词就行）

比如：
- "最低工资对就业的影响"
- "企业数字化转型对供应链韧性的影响"
- "某个我不确定但觉得有趣的经济现象"
"""
