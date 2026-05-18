#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经济学实证论文自动化工作流 - 微状态机实现
支持 28 个微状态的精细状态管理，多项目切换

路径设计（支持插件全局安装）：
- PLUGIN_ROOT：插件安装目录（内置模板、脚本）
- WORKING_DIR：用户当前工作目录（论文项目创建于此）
- PAPERS_DIR：WORKING_DIR/papers（用户论文存放位置）
- CONFIG_DIR：WORKING_DIR/.config（当前项目配置）
"""

import json
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from memory import ConversationMemory, get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# 插件根目录（内置模板、脚本，只读）
PLUGIN_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PLUGIN_ROOT / "templates"
PAPER_TEMPLATES_DIR = TEMPLATES_DIR / "paper"

# 用户工作目录（论文项目创建于此）
WORKING_DIR = Path.cwd()
PAPERS_DIR = WORKING_DIR / "papers"
CONFIG_DIR = WORKING_DIR / ".config"
CURRENT_PROJECT_FILE = CONFIG_DIR / "current_project.json"

# ============================================================
# 微状态定义 (共 28 个)
# ============================================================
MICRO_STATES = [
    # ========== Stage 1: 选题研究 (11 个状态) ==========
    {
        "id": "topic-init",
        "stage": "topic",
        "name": "项目初始化与档位选择",
        "description": "项目创建完成，展示工作流全景和档位选择",
        "entry_prompt": "项目创建成功！\n\n项目结构已就绪，你的原始数据在 data/raw/ 目录。\n\n========================================\n实证论文标准工作流（必经三关）\n========================================\n\n  [1] 选题评审  -->  [2] 文献综述  -->  [3] 数据诊断  -->  实证  -->  论文\n       |                 |                  |\n  3档深度可选      3档深度可选        自动执行\n\n每一关都有三档深度可选，请选择：\n\n【第一关：选题评审】\n  轻量：确认研究问题 + 一句话创新点\n  标准：5W1H复盘 + 3个核心创新点梳理  (推荐)\n  深度：完整选题报告 + 边际贡献论证 + 研究假说\n\n【第二关：文献综述】\n  轻量：关键词检索20篇核心文献摘要\n  标准：50篇脉络梳理 + 理论框架图 + 文献表  (推荐)\n  深度：系统综述 + 文献计量 + 研究假说推演\n\n【第三关：数据质量诊断】(自动执行)\n  完整性/平衡性/缺失值/异常值检验\n  输出：数据质量报告 + 变量建议 + 补充数据搜索建议\n\n========================================\n\n请告诉我各环节选什么深度（格式如：轻量+标准+自动）\n或直接说标准配置，按 标准+标准+自动 开始。",
        "output_path": "topics/00_project_overview.md",
        "next_states": ["topic-review-light", "topic-review-standard", "topic-review-deep"],
        "requires_confirm": True,
    },
    {
        "id": "topic-review-light",
        "stage": "topic",
        "name": "轻量选题评审",
        "description": "快速确认研究问题和创新点",
        "entry_prompt": "【轻量选题评审】\n\n基于你提供的信息：\n- 研究问题：企业数字化转型对供应链韧性的影响\n\n请确认/补充：\n1. 这个研究问题是否需要调整？\n2. 一句话说明本文的核心创新点在哪里？\n3. 核心假说（H1）：数字化转型 ____（促进/抑制）供应链韧性",
        "output_path": "topics/01_quick_review.md",
        "next_states": ["literature-search-plan"],
        "requires_confirm": True,
    },
    {
        "id": "topic-review-standard",
        "stage": "topic",
        "name": "标准选题评审",
        "description": "5W1H复盘 + 创新点梳理",
        "entry_prompt": "【标准选题评审】\n\n让我们快速复盘选题的5个核心维度：\n\n[1] What：核心变量定义\n   - 数字化转型：你的测量方式是？\n   - 供应链韧性：你的测量方式是？\n\n[2] Why：为什么重要？\n   - 现实意义（政策/企业价值）：____\n   - 理论缺口：____\n\n[3] How：识别策略\n   - 基准模型：OLS/FE/DID？\n   - 内生性应对：工具变量/自然实验？\n\n[4] 创新点：3个核心边际贡献\n   - 创新1：____\n   - 创新2：____\n   - 创新3：____\n\n[5] 假说：待检验的3个假说\n   - H1（主效应）：____\n   - H2（异质性）：____\n   - H3（机制）：____",
        "output_path": "topics/01_5w1h_review.md",
        "next_states": ["literature-search-plan"],
        "requires_confirm": True,
    },
    {
        "id": "topic-review-deep",
        "stage": "topic",
        "name": "深度选题评审",
        "description": "完整选题报告 + 边际贡献论证",
        "entry_prompt": "【深度选题评审】\n\n将生成完整的选题分析报告，包括：\n1. 研究背景与问题提出\n2. 文献Gap的系统论证\n3. 理论框架图\n4. 研究假说推演（H1-H5）\n5. 边际贡献的三个维度\n\n请确认：是否按此标准开始深度选题评审？",
        "output_path": "topics/01_full_proposal.md",
        "next_states": ["literature-search-plan"],
        "requires_confirm": True,
    },
    {
        "id": "topic-5w1h-what",
        "stage": "topic",
        "name": "5W1H - What",
        "description": "核心经济现象与变量初步想法",
        "entry_prompt": "【What - 研究对象】\n核心经济现象/问题是什么？\n被解释变量 Y、核心解释变量 D 的初步想法是什么？",
        "output_path": "topics/01_5w1h_what.md",
        "next_states": ["topic-5w1h-why"],
        "requires_confirm": False,
    },
    {
        "id": "topic-5w1h-why",
        "stage": "topic",
        "name": "5W1H - Why",
        "description": "研究重要性与理论贡献",
        "entry_prompt": "【Why - 研究动机】\n为什么这个问题重要？\n理论贡献或政策含义何在？与既有文献的张力在哪里？",
        "output_path": "topics/01_5w1h_why.md",
        "next_states": ["topic-5w1h-who"],
        "requires_confirm": False,
    },
    {
        "id": "topic-5w1h-who",
        "stage": "topic",
        "name": "5W1H - Who",
        "description": "利益相关方与研究受众",
        "entry_prompt": "【Who - 利益相关方】\n利益相关方是谁（政策制定者、企业、劳动者、消费者）？\n研究结论对谁有意义？",
        "output_path": "topics/01_5w1h_who.md",
        "next_states": ["topic-5w1h-when"],
        "requires_confirm": False,
    },
    {
        "id": "topic-5w1h-when",
        "stage": "topic",
        "name": "5W1H - When",
        "description": "时间跨度与自然实验窗口",
        "entry_prompt": "【When - 时间维度】\n研究的时间跨度？\n是否有自然实验窗口？（政策冲击、制度变革、外部事件）",
        "output_path": "topics/01_5w1h_when.md",
        "next_states": ["topic-5w1h-where"],
        "requires_confirm": False,
    },
    {
        "id": "topic-5w1h-where",
        "stage": "topic",
        "name": "5W1H - Where",
        "description": "制度背景与地理范围",
        "entry_prompt": "【Where - 空间/制度维度】\n制度背景和地理范围（国别/区域/行业）？\n数据来源的可得性如何？",
        "output_path": "topics/01_5w1h_where.md",
        "next_states": ["topic-5w1h-how"],
        "requires_confirm": False,
    },
    {
        "id": "topic-5w1h-how",
        "stage": "topic",
        "name": "5W1H - How",
        "description": "识别策略初步思考",
        "entry_prompt": "【How - 识别策略】\n可能的识别策略（OLS/FE/DID/RDD/IV）？\n核心识别假设的初步思考？",
        "output_path": "topics/01_5w1h_how.md",
        "next_states": ["topic-5w1h-summary"],
        "requires_confirm": False,
    },
    {
        "id": "topic-5w1h-summary",
        "stage": "topic",
        "name": "5W1H 总结确认",
        "description": "汇总5W1H结果并请求用户确认",
        "entry_prompt": "【5W1H 推演完成】\n已完成 5W1H 框架分析，请查看推演摘要表。\n确认无误后继续，或提出需要调整的维度。",
        "output_path": "topics/01_5w1h_summary.md",
        "next_states": ["topic-gap-analysis"],
        "requires_confirm": True,
    },
    {
        "id": "topic-gap-analysis",
        "stage": "topic",
        "name": "研究空白分析",
        "description": "识别文献/方法/数据/政策/跨学科空白",
        "entry_prompt": "【研究空白分析】\n正在进行文献检索与空白识别...\n请确认识别出的研究空白类型和评分。",
        "output_path": "topics/02_gap_analysis.md",
        "next_states": ["topic-smart"],
        "requires_confirm": True,
    },
    {
        "id": "topic-smart",
        "stage": "topic",
        "name": "SMART 研究问题",
        "description": "精确化研究问题与假设",
        "entry_prompt": "【SMART 原则精确化】\n已生成候选研究问题，请确认：\n- 研究假设（H1, H2, ...）\n- 核心变量定义及预期符号\n- 识别策略论证",
        "output_path": "topics/03_research_question.md",
        "next_states": ["topic-proposal"],
        "requires_confirm": True,
    },
    {
        "id": "topic-proposal",
        "stage": "topic",
        "name": "选题分析报告",
        "description": "整合为完整研究方案",
        "entry_prompt": "【选题分析报告】\n已生成完整的选题分析报告，请审阅确认。\n确认后将进入文献综述阶段。",
        "output_path": "topics/00_research_proposal.md",
        "next_states": ["literature-search-plan"],
        "requires_confirm": True,
    },

    # ========== Stage 2: 文献综述 (6 个状态 - 3档深度) ==========
    {
        "id": "literature-search-plan",
        "stage": "literature",
        "name": "检索策略与深度选择",
        "description": "确定检索关键词和综述深度档位",
        "entry_prompt": "【文献检索策略】\n\n基于选题：「企业数字化转型对供应链韧性的影响」\n\n已生成核心检索关键词：\n  \"digital transformation\", \"supply chain resilience\",\n  \"数字化转型\", \"供应链韧性\", \"供应链稳健性\"\n\n请选择文献综述深度：\n\n[轻量版] (约20篇)\n- 核心文献摘要列表\n- 3篇经典文献精读笔记\n- 自动生成 .bib 文件\n\n[标准版] (约50篇)  <- 推荐\n- 文献脉络梳理（3-5个学派）\n- 理论框架图\n- 文献对比表\n- 研究缺口定位\n- 自动生成 .bib 文件\n\n[深度版] (约100篇)\n- 文献计量分析（作者/期刊/关键词共现）\n- 系统综述PRISMA规范\n- 完整的理论发展脉络\n- 研究假说的文献支撑论证",
        "output_path": "literature/00_search_plan.md",
        "next_states": ["literature-light", "literature-standard", "literature-deep"],
        "requires_confirm": True,
    },
    {
        "id": "literature-light",
        "stage": "literature",
        "name": "轻量文献综述",
        "description": "20篇核心文献检索 + 摘要",
        "entry_prompt": "【轻量文献检索执行中】\n正在检索 Google Scholar 和 arXiv...\n目标：20篇核心文献 + 摘要 + Bib文件",
        "output_path": "literature/01_light_summary.md",
        "next_states": ["data-diagnosis"],
        "requires_confirm": False,
    },
    {
        "id": "literature-standard",
        "stage": "literature",
        "name": "标准文献综述",
        "description": "50篇文献 + 脉络梳理 + 理论框架",
        "entry_prompt": "【标准文献检索执行中】\n正在检索和筛选50篇核心文献...\n\n后续步骤：\n1. 文献脉络梳理（3-5个研究流派）\n2. 理论框架图生成\n3. 文献对比表（作者/年份/方法/发现/不足）\n4. 研究缺口定位",
        "output_path": "literature/01_standard_synthesis.md",
        "next_states": ["data-diagnosis"],
        "requires_confirm": False,
    },
    {
        "id": "literature-deep",
        "stage": "literature",
        "name": "深度文献综述",
        "description": "100篇 + 文献计量 + 系统综述",
        "entry_prompt": "【深度文献检索执行中】\n正在进行系统文献检索...\n\n将生成：\n1. 文献计量分析（CiteSpace 风格）\n2. PRISMA流程图\n3. 完整的理论发展脉络\n4. 研究假说的文献支撑论证",
        "output_path": "literature/01_deep_synthesis.md",
        "next_states": ["data-diagnosis"],
        "requires_confirm": False,
    },
    {
        "id": "literature-screen",
        "stage": "literature",
        "name": "文献筛选与解读",
        "description": "筛选高相关文献，生成摘要",
        "entry_prompt": "【文献筛选与解读】\n已检索到 N 篇文献，正在进行相关性筛选和关键文献解读。\n请确认筛选出的核心文献列表。",
        "output_path": "literature/02_screened_papers.md",
        "next_states": ["literature-synthesize"],
        "requires_confirm": True,
    },
    {
        "id": "literature-synthesize",
        "stage": "literature",
        "name": "文献脉络梳理",
        "description": "构建文献发展脉络与理论框架",
        "entry_prompt": "【文献脉络梳理】\n正在构建文献发展脉络与理论框架图...\n请确认文献综述的整体结构。",
        "output_path": "literature/03_synthesis.md",
        "next_states": ["literature-write"],
        "requires_confirm": True,
    },
    {
        "id": "literature-write",
        "stage": "literature",
        "name": "综述撰写与Bib管理",
        "description": "完成文献综述撰写，生成.bib文件",
        "entry_prompt": "【文献综述撰写】\n正在生成文献综述正文并管理参考文献...",
        "output_path": "literature/04_review_final.md",
        "bib_path": "paper/erjref.bib",
        "next_states": ["data-diagnosis"],
        "requires_confirm": True,
    },

    # ========== Stage 3: 数据质量诊断与清洗 (5 个状态) ==========
    {
        "id": "data-diagnosis",
        "stage": "data",
        "name": "数据质量诊断",
        "description": "自动检查原始数据质量：完整性、平衡性、缺失值、异常值",
        "entry_prompt": "【数据质量诊断】\n正在扫描 data/raw/ 中的原始数据...\n\n自动检测项目：\n✅ 文件格式识别 (.dta/.csv/.xlsx)\n✅ 面板结构诊断 (N个体 × T时间)\n✅ 变量存在性检查 (Y/D/X/M是否都在数据中)\n✅ 缺失值统计与分布\n✅ 异常值检测 (3σ/IQR)\n✅ 变量描述性统计\n✅ 相关性矩阵初步分析\n\n诊断完成后将生成：数据质量报告 + 变量标准化建议 + 补充数据搜索建议",
        "output_path": "data/00_diagnosis_report.md",
        "next_states": ["data-plan"],
        "requires_confirm": False,
    },
    {
        "id": "data-plan",
        "stage": "data",
        "name": "数据清洗方案确认",
        "description": "基于诊断结果，确认清洗方案",
        "entry_prompt": "【数据清洗方案】\n基于数据诊断结果，已生成清洗方案：\n1. 缺失值处理：____\n2. 异常值处理：____\n3. 变量标准化：____\n4. 需要补充的数据：____\n\n请确认清洗方案，或提出调整意见。",
        "output_path": "data/01_clean_plan.md",
        "next_states": ["data-clean"],
        "requires_confirm": True,
    },
    {
        "id": "data-acquire",
        "stage": "data",
        "name": "补充数据获取",
        "description": "自动搜索/爬取缺失的数据",
        "entry_prompt": "【补充数据获取中】\n正在搜索/下载诊断中发现的缺失数据...",
        "output_path": "data/raw/",
        "next_states": ["data-clean"],
        "requires_confirm": False,
    },
    {
        "id": "data-clean",
        "stage": "data",
        "name": "数据清洗执行",
        "description": "缺失值处理、异常值处理、变量构造",
        "entry_prompt": "【数据清洗中】\n正在执行 Stata 数据清洗脚本...",
        "output_path": "data/scripts/01_clean.do",
        "next_states": ["data-validate"],
        "requires_confirm": False,
    },
    {
        "id": "data-validate",
        "stage": "data",
        "name": "清洗后数据验证",
        "description": "描述性统计、平衡性检验、清洗质量检查",
        "entry_prompt": "【数据验证】\n已生成清洗后数据的描述性统计表和平衡性检验。\n请确认数据质量，如无问题进入实证分析阶段。",
        "output_path": "data/clean/final_data.dta",
        "next_states": ["stata-model-spec"],
        "requires_confirm": True,
    },

    # ========== Stage 4: Stata实证 (3 个状态) ==========
    {
        "id": "stata-model-spec",
        "stage": "stata",
        "name": "模型设定",
        "description": "确定回归方程、变量选择、标准误设定",
        "entry_prompt": "【模型设定】\n请确认：\n- 基准回归方程设定\n- 核心变量 Y, D, X 的选择\n- 固定效应与标准误聚类方式",
        "output_path": "analysis/do-files/00_model_spec.md",
        "next_states": ["stata-baseline"],
        "requires_confirm": True,
    },
    {
        "id": "stata-baseline",
        "stage": "stata",
        "name": "基准回归",
        "description": "执行基准回归，生成T2核心表",
        "entry_prompt": "【基准回归执行中】\n正在运行 Stata 基准回归...",
        "output_path": "analysis/output/02_baseline_regression.tex",
        "next_states": ["stata-heterogeneity"],
        "requires_confirm": False,
        "decision_points": [
            {"condition": "核心变量显著且符号符合预期", "next": "stata-heterogeneity", "message": "✅ 基准结果支持假设，进入异质性分析"},
            {"condition": "核心变量显著但符号相反", "next": "stata-model-spec", "message": "⚠️ 符号与预期相反，建议重新检查变量定义或模型设定"},
            {"condition": "核心变量不显著", "next": "stata-model-spec", "message": "⚠️ 核心变量不显著，建议：换标准误聚类/加控制变量/检查样本"},
            {"condition": "中介效应全部不显著，跳过中介直接异质", "next": "stata-heterogeneity", "message": "ℹ️ 中介效应不成立，跳过直接进入异质性分析"},
        ],
    },
    {
        "id": "stata-heterogeneity",
        "stage": "stata",
        "name": "异质性分析",
        "description": "分样本回归、交互项分析",
        "entry_prompt": "【异质性分析】\n正在执行分样本回归和交互项分析...",
        "output_path": "analysis/output/03_heterogeneity.tex",
        "next_states": ["robustness-plan"],
        "requires_confirm": True,
    },

    # ========== Stage 5: 稳健性检验 (2 个状态) ==========
    {
        "id": "robustness-plan",
        "stage": "robustness",
        "name": "稳健性策略设计",
        "description": "确定稳健性检验组合",
        "entry_prompt": "【稳健性检验策略】\n已生成稳健性检验方案（替换变量、改变样本、安慰剂检验等）。\n请确认检验策略。",
        "output_path": "analysis/04_robustness_plan.md",
        "next_states": ["robustness-execute"],
        "requires_confirm": True,
    },
    {
        "id": "robustness-execute",
        "stage": "robustness",
        "name": "稳健性执行",
        "description": "执行所有稳健性检验",
        "entry_prompt": "【稳健性检验执行中】\n正在执行各项稳健性检验...",
        "output_path": "analysis/output/04_robustness.tex",
        "next_states": ["conclusion-verify"],
        "requires_confirm": False,
    },

    # ========== Stage 6: 结论验证 (2 个状态) ==========
    {
        "id": "conclusion-verify",
        "stage": "conclusion",
        "name": "结论验证",
        "description": "对比假设与实证结果",
        "entry_prompt": "【结论验证】\n已对比研究假设与实证结果。\n请确认核心结论的有效性。",
        "output_path": "analysis/05_conclusion_verification.md",
        "next_states": ["conclusion-discuss"],
        "requires_confirm": True,
    },
    {
        "id": "conclusion-discuss",
        "stage": "conclusion",
        "name": "讨论与机制",
        "description": "机制分析、政策含义、局限与展望",
        "entry_prompt": "【讨论与机制分析】\n正在生成机制分析和政策含义...",
        "output_path": "analysis/06_discussion.md",
        "next_states": ["paper-outline"],
        "requires_confirm": True,
    },

    # ========== Stage 7: LaTeX论文 (1 个状态 - 可进一步拆分) ==========
    {
        "id": "paper-outline",
        "stage": "paper",
        "name": "论文大纲确认",
        "description": "确定论文章节结构",
        "entry_prompt": "【论文大纲】\n已生成论文章节结构，请确认。",
        "output_path": "paper/outline.md",
        "next_states": ["paper-write"],
        "requires_confirm": True,
    },
    {
        "id": "paper-write",
        "stage": "paper",
        "name": "论文撰写与编译",
        "description": "生成LaTeX源码并编译PDF",
        "entry_prompt": "【论文撰写中】\n正在生成 LaTeX 论文源码...",
        "output_path": "paper/main.tex",
        "next_states": [],  # 终态
        "requires_confirm": True,
    },
]

# 粗粒度阶段映射
STAGE_GROUPS = {
    "topic": {"name": "选题评审", "states": [s["id"] for s in MICRO_STATES if s["stage"] == "topic"]},
    "literature": {"name": "文献综述", "states": [s["id"] for s in MICRO_STATES if s["stage"] == "literature"]},
    "data": {"name": "数据诊断与清洗", "states": [s["id"] for s in MICRO_STATES if s["stage"] == "data"]},
    "stata": {"name": "Stata实证回归", "states": [s["id"] for s in MICRO_STATES if s["stage"] == "stata"]},
    "robustness": {"name": "稳健性检验", "states": [s["id"] for s in MICRO_STATES if s["stage"] == "robustness"]},
    "conclusion": {"name": "验证结论", "states": [s["id"] for s in MICRO_STATES if s["stage"] == "conclusion"]},
    "paper": {"name": "LaTeX论文撰写", "states": [s["id"] for s in MICRO_STATES if s["stage"] == "paper"]},
}

AVAILABLE_TEMPLATES = {
    "economic-research": "《经济研究》",
    "qje": "《经济学季刊》",
    "aer": "美国经济评论 AER",
}


# ============================================================
# 状态机工具函数
# ============================================================
def get_state_by_id(state_id):
    """根据状态ID获取状态定义"""
    for state in MICRO_STATES:
        if state["id"] == state_id:
            return state
    return None


def get_project_config_path(project_name):
    """获取项目配置文件路径"""
    return get_project_path(project_name) / "project_config.json"


def load_project_config(project_name):
    """加载项目变量配置文件"""
    config_path = get_project_config_path(project_name)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_project_config(project_name, config):
    """保存项目变量配置文件"""
    config_path = get_project_config_path(project_name)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def build_context_summary(project_name, state):
    """从 state 构建分层上下文摘要（供 LLM 快速掌握项目状态）"""
    ctx = state.get("context_store", {})
    decisions = state.get("decisions", [])
    current_state_id = state.get("current_micro_state", MICRO_STATES[0]["id"])
    current_state = get_state_by_id(current_state_id)

    summary = {
        "project": project_name,
        "current_stage": current_state["stage"] if current_state else "unknown",
        "current_state_name": current_state["name"] if current_state else "unknown",
        "completed": [],
        "pending_decision": None,
        "last_updated": state.get("updated_at", ""),
    }

    # 汇总已完成的阶段
    for stage_id in ["topic", "literature", "data", "stata", "robustness", "conclusion", "paper"]:
        if ctx.get(stage_id):
            info = ctx[stage_id]
            entry = {"stage": stage_id, "name": STAGE_GROUPS.get(stage_id, {}).get("name", stage_id)}
            if stage_id == "topic":
                entry["summary"] = info.get("research_question", "")
            elif stage_id == "stata":
                sig = info.get("baseline_sig", "")
                entry["summary"] = f"β={info.get('baseline_coef','?')}{sig}, N={info.get('n_obs','?')}"
            elif stage_id == "paper":
                entry["summary"] = f"{info.get('word_count','?')}字 {info.get('sections_completed','?')}章"
            summary["completed"].append(entry)

    summary["recent_decisions"] = decisions[-5:] if decisions else []

    return summary


def build_stage_context_md(project_name, state, stage_id):
    """生成 Tier 3 阶段上下文 .md 文件"""
    ctx = state.get("context_store", {})
    stage_info = ctx.get(stage_id, {})
    current_state = get_state_by_id(state.get("current_micro_state"))

    stage_labels = {
        "topic": "选题研究",
        "literature": "文献综述",
        "data": "数据清洗",
        "stata": "Stata 实证",
        "robustness": "稳健性检验",
        "conclusion": "结论验证",
        "paper": "LaTeX 论文",
    }

    lines = [
        f"# {stage_labels.get(stage_id, stage_id)} 阶段上下文\n",
        f"## 输入（来自上游）",
    ]

    # 上游信息
    if stage_id in ["literature", "stata", "paper"] and ctx.get("topic"):
        t = ctx["topic"]
        lines.append(f"- 研究问题: {t.get('research_question', '未记录')}")
        lines.append(f"- Y={t.get('y_var','?')}, D={t.get('d_var','?')}, 识别策略: {t.get('identification','?')}")

    if stage_id in ["stata", "paper"] and ctx.get("literature"):
        lit = ctx["literature"]
        lines.append(f"- 核心文献: {lit.get('total_papers','?')}篇, 定位空白: {lit.get('research_gap','未记录')}")

    if stage_id == "paper" and ctx.get("stata"):
        s = ctx["stata"]
        lines.append(f"- 基准回归: β={s.get('baseline_coef','?')}(SE={s.get('baseline_se','?')}), sig={s.get('baseline_sig','?')}")

    lines.extend([
        f"\n## 当前状态: {current_state['name'] if current_state else '未知'}",
        f"\n## 待决策",
        f"- {current_state['entry_prompt'][:200] if current_state else '无'}",
        f"\n## 下游需要",
    ])

    if stage_id == "topic":
        lines.append("- research_question, variables, hypotheses")
        lines.append("- 传递给 literature: keywords")
        lines.append("- 传递给 stata: Y/D/X 变量名 + identification")
    elif stage_id in ["stata", "robustness"]:
        lines.append("- 输出路径: analysis/output/t[1-5]_*.tex")
        lines.append("- 需要表格: T1描述性, T2基准, T4稳健性, T5异质性")
    elif stage_id == "paper":
        lines.append("- 输出路径: paper/main.pdf")
        lines.append("- 需要引用: analysis/output/*.tex 中的表格")
        lines.append("- 需要引用: paper/erjref.bib 中的参考文献")

    return "\n".join(lines)


def get_state_index(state_id):
    """获取状态在状态列表中的索引"""
    for i, state in enumerate(MICRO_STATES):
        if state["id"] == state_id:
            return i
    return -1


def get_current_project():
    """获取当前激活的项目名称"""
    if not CURRENT_PROJECT_FILE.exists():
        return None
    with open(CURRENT_PROJECT_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("current_project")


def get_project_path(project_name):
    """获取项目路径"""
    return PAPERS_DIR / project_name


def get_state_file(project_name):
    """获取项目的状态文件路径"""
    return get_project_path(project_name) / "pipeline_state.json"


def load_state(project_name=None):
    """加载指定项目的状态，默认加载当前项目"""
    if project_name is None:
        project_name = get_current_project()
        if project_name is None:
            return None, None

    state_file = get_state_file(project_name)
    if state_file.exists():
        with open(state_file, encoding="utf-8") as f:
            raw = json.load(f)
        # 从旧版状态迁移（V1 -> V2 微状态迁移）
        if "current_micro_state" not in raw:
            raw["current_micro_state"] = MICRO_STATES[0]["id"]
        if "micro_state_history" not in raw:
            raw["micro_state_history"] = []
        if "stage_completed" not in raw:
            raw["stage_completed"] = []
        if "user_inputs" not in raw:
            raw["user_inputs"] = {}
        if "template" not in raw:
            raw["template"] = "economic-research"
        return project_name, raw

    default_state = {
        "current_micro_state": MICRO_STATES[0]["id"],
        "micro_state_history": [],
        "stage_completed": [],
        "user_inputs": {},
        "created_at": datetime.now().isoformat(),
        "project_name": project_name,
        "template": "economic-research",
        "context_store": {},
        "decisions": [],
    }
    return project_name, default_state


def save_state(project_name, state):
    """保存项目状态"""
    state["updated_at"] = datetime.now().isoformat()
    state_file = get_state_file(project_name)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def set_current_project(project_name, show_resume=True):
    """设置当前激活的项目"""
    project_path = get_project_path(project_name)
    if not project_path.exists():
        print(f"错误: 项目 '{project_name}' 不存在")
        return False

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CURRENT_PROJECT_FILE, "w", encoding="utf-8") as f:
        json.dump({"current_project": project_name}, f, ensure_ascii=False, indent=2)
    print(f"已切换到项目: {project_name}")

    if show_resume and MEMORY_AVAILABLE:
        mem = get_memory(project_name)
        print("\n" + "=" * 50)
        print(mem.generate_resume_message("medium"))
        print("=" * 50 + "\n")

    return True


# ============================================================
# 命令实现
# ============================================================
def cmd_list(_=None):
    """列出所有项目"""
    if not PAPERS_DIR.exists():
        print("暂无项目，使用 'python pipeline.py new <项目名>' 创建第一个项目")
        return

    current = get_current_project()
    projects = [p.name for p in PAPERS_DIR.iterdir() if p.is_dir()]

    if not projects:
        print("暂无项目")
        return

    print(f"共有 {len(projects)} 个项目:\n")
    for p in sorted(projects):
        marker = "*" if p == current else " "
        _, state = load_state(p)
        if state:
            current_state_id = state.get("current_micro_state", MICRO_STATES[0]["id"])
            current_state = get_state_by_id(current_state_id)
            state_name = current_state["name"] if current_state else "未知"
            stage_group = STAGE_GROUPS.get(current_state["stage"], {}).get("name", "") if current_state else ""
            print(f" {marker} {p:40s} -> {stage_group} / {state_name}")


def cmd_new(args):
    """创建新项目: python pipeline.py new <项目名>"""
    if len(args) < 3:
        print("用法: python pipeline.py new <项目名>")
        print("示例: python pipeline.py new minimum-wage-employment")
        return

    project_name = args[2]
    project_path = get_project_path(project_name)

    if project_path.exists():
        print(f"错误: 项目 '{project_name}' 已存在")
        return

    if not TEMPLATES_DIR.exists():
        print(f"错误: 模板目录不存在: {TEMPLATES_DIR}")
        return

    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"正在创建新项目: {project_name}...")
    shutil.copytree(TEMPLATES_DIR, project_path)

    _, state = load_state(project_name)
    save_state(project_name, state)

    if MEMORY_AVAILABLE:
        mem = get_memory(project_name)
        mem.add_system_message(f"新项目 '{project_name}' 创建成功，进入选题研究阶段")
        mem.set_context_summary(
            "新项目已创建，即将开始选题研究。我们将通过 5W1H 框架逐步明确研究问题。",
            MICRO_STATES[0]["entry_prompt"]
        )
        mem.save()

    set_current_project(project_name, show_resume=True)
    print(f"项目创建成功！路径: {project_path}")


def cmd_use(args):
    """切换当前项目: python pipeline.py use <项目名>"""
    if len(args) < 3:
        print("用法: python pipeline.py use <项目名>")
        print("使用 'python pipeline.py list' 查看所有项目")
        return

    project_name = args[2]
    set_current_project(project_name)


def cmd_status(_=None):
    """查看当前项目的微状态详情（含分层上下文摘要）"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目，使用 'python pipeline.py use <项目名>' 或 'python pipeline.py new <项目名>'")
        return

    current_state_id = state.get("current_micro_state", MICRO_STATES[0]["id"])
    current_state = get_state_by_id(current_state_id)

    if not current_state:
        print(f"错误: 未知状态 '{current_state_id}'")
        return

    current_idx = get_state_index(current_state_id)
    total = len(MICRO_STATES)
    progress = (current_idx + 1) / total * 100
    stage_name = STAGE_GROUPS.get(current_state["stage"], {}).get("name", current_state["stage"])

    # ---- Tier 1: 项目快照 ----
    print("=" * 60)
    print(f"📍 {project_name}: {stage_name} / {current_state['name']}")
    print(f"   进度: [{current_idx + 1}/{total}] {progress:.1f}%")

    # ---- 已完成阶段摘要 ----
    ctx = state.get("context_store", {})
    if ctx:
        print()
        print("已完成:")
        for stage_id in ["topic", "literature", "data", "stata", "robustness", "conclusion", "paper"]:
            info = ctx.get(stage_id)
            if info:
                sname = STAGE_GROUPS.get(stage_id, {}).get("name", stage_id)
                if stage_id == "topic":
                    print(f"  ✅ {sname}: {info.get('research_question', '')[:60]}")
                elif stage_id == "stata":
                    sig = info.get("baseline_sig", "")
                    print(f"  ✅ {sname}: β={info.get('baseline_coef','?')}{sig}")
                elif stage_id == "paper":
                    print(f"  ✅ {sname}: {info.get('word_count','?')}字")
                else:
                    print(f"  ✅ {sname}")

    # ---- 待决策 ----
    decisions = state.get("decisions", [])
    if decisions:
        print(f"\n📋 最近决策:")
        for d in decisions[-5:]:
            reason = d.get("reason", "")[:60]
            print(f"  {d.get('time','')[:16]} | {d.get('decision','')}")
            if reason:
                print(f"     → {reason}")

    # ---- 当前状态信息 ----
    print(f"\n📌 当前: {current_state['name']}")
    print(f"   输出: {current_state['output_path']}")

    next_states = current_state.get("next_states", [])
    if next_states:
        print(f"   下一步:")
        for ns_id in next_states:
            ns = get_state_by_id(ns_id)
            if ns:
                confirm = " [需确认]" if ns.get("requires_confirm") else ""
                print(f"     → {ns['name']}{confirm}")

    # ---- 分支决策点 ----
    decision_points = current_state.get("decision_points", [])
    if decision_points:
        print(f"   分支选项:")
        for dp in decision_points:
            print(f"     • {dp['condition']} → {dp['message'][:60]}")

    # ---- 最近历史 ----
    history = state.get("micro_state_history", [])
    if history:
        print(f"\n📜 最近转移:")
        for h in history[-3:]:
            action = h.get("reason", h.get("action", "推进"))
            print(f"  {h['time'][:19]} {h.get('from_name','?')} → {h.get('to_name','?')}")


def cmd_states(_=None):
    """列出所有微状态"""
    print(f"共 {len(MICRO_STATES)} 个微状态:\n")

    current_stage = None
    for i, state in enumerate(MICRO_STATES):
        if state["stage"] != current_stage:
            current_stage = state["stage"]
            stage_name = STAGE_GROUPS.get(current_stage, {}).get("name", current_stage)
            print(f"\n{'='*60}")
            print(f"  {stage_name} ({current_stage})")
            print(f"{'='*60}")

        confirm_marker = "[需确认]" if state.get("requires_confirm") else "[自动]"
        print(f"  [{i + 1:2d}] {confirm_marker:8s} {state['id']:30s} - {state['name']}")


def cmd_advance(args):
    """推进到下一状态: python pipeline.py advance [--skip-confirm] [--branch <索引>]"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    current_state_id = state.get("current_micro_state", MICRO_STATES[0]["id"])
    current_state = get_state_by_id(current_state_id)

    if not current_state:
        print(f"错误: 未知状态 '{current_state_id}'")
        return

    # 确定目标状态
    branch_idx = None
    for i, arg in enumerate(args):
        if arg == "--branch" and i + 1 < len(args):
            branch_idx = int(args[i + 1])
            break

    next_state_id = None
    reason = None

    if branch_idx is not None:
        # 用户指定了分支
        decision_points = current_state.get("decision_points", [])
        if 0 <= branch_idx < len(decision_points):
            dp = decision_points[branch_idx]
            next_state_id = dp.get("next")
            reason = dp.get("condition", "")
            if not next_state_id:
                print(f"错误: 分支 {branch_idx} 未定义 'next' 状态")
                return
        else:
            print(f"错误: 分支索引 {branch_idx} 超出范围 (0-{len(decision_points)-1})")
            return
    else:
        # 默认路径
        next_states = current_state.get("next_states", [])
        if not next_states:
            print("已到达最终状态")
            return
        if len(next_states) > 1:
            # 有多个默认路径，显示选项
            print(f"当前状态有多个后续路径:")
            for i, ns_id in enumerate(next_states):
                ns = get_state_by_id(ns_id)
                if ns:
                    print(f"  [{i}] {ns['name']}")
            print()
            # 也显示分支选项
            decision_points = current_state.get("decision_points", [])
            if decision_points:
                print(f"或根据决策点分支选择:")
                for i, dp in enumerate(decision_points):
                    print(f"  [--branch {i}] {dp['condition']} → {dp['message'][:50]}")
            return
        next_state_id = next_states[0]

    next_state = get_state_by_id(next_state_id)
    if not next_state:
        print(f"错误: 目标状态 '{next_state_id}' 不存在")
        return

    skip_confirm = "--skip-confirm" in args
    if current_state.get("requires_confirm") and not skip_confirm:
        print(f"[警告] 当前状态需要用户确认才能推进。")
        print(f"   请先完成 {current_state['name']} 的用户交互。")
        print(f"   如需强制跳过确认，使用: python pipeline.py advance --skip-confirm")
        return

    # 记录状态转移（含原因）
    transition = {
        "from": current_state_id,
        "to": next_state_id,
        "from_name": current_state["name"],
        "to_name": next_state["name"],
        "time": datetime.now().isoformat(),
        "action": "分支" if reason else "推进",
    }
    if reason:
        transition["reason"] = reason
    state["micro_state_history"].append(transition)

    state["current_micro_state"] = next_state_id

    # 阶段完成时自动保存上下文
    current_stage = current_state["stage"]
    next_stage = next_state["stage"]
    if current_stage != next_stage:
        if current_stage not in state.get("stage_completed", []):
            state.setdefault("stage_completed", []).append(current_stage)
            # 自动生成 Tier 3 上下文文件
            try:
                context_dir = get_project_path(project_name) / "context"
                context_dir.mkdir(exist_ok=True)
                stage_md = build_stage_context_md(project_name, state, next_stage)
                with open(context_dir / f"{next_stage}.md", "w", encoding="utf-8") as f:
                    f.write(stage_md)
            except:
                pass
            print(f"[完成] 已完成阶段: {STAGE_GROUPS.get(current_stage, {}).get('name', current_stage)}")

    save_state(project_name, state)
    print(f"[完成] 已推进到: {next_state['name']} ({next_state_id})")
    if reason:
        print(f"   分支原因: {reason}")
    print(f"   输出路径: {next_state['output_path']}")


def cmd_jump(args):
    """跳转到指定微状态: python pipeline.py jump <状态ID或编号>"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    if len(args) < 3:
        print("用法: python pipeline.py jump <状态ID或编号>")
        print("使用 'python pipeline.py states' 查看所有状态")
        return

    state_input = args[2]

    if state_input.isdigit():
        state_idx = int(state_input) - 1
        if 0 <= state_idx < len(MICRO_STATES):
            target_state = MICRO_STATES[state_idx]
        else:
            print(f"状态编号必须在 1-{len(MICRO_STATES)} 之间")
            return
    else:
        target_state = get_state_by_id(state_input)
        if not target_state:
            # 按阶段名搜索（如 "paper"、"latex"、"topic"）
            for s in MICRO_STATES:
                if s["stage"] == state_input or state_input in s.get("name", ""):
                    target_state = s
                    break
        if not target_state:
            print(f"未找到状态: {state_input}")
            print("使用 'python pipeline.py states' 查看所有可用状态")
            print("支持: 状态编号、状态ID、阶段名（如 topic/paper）")
            return

    old_state_id = state.get("current_micro_state", MICRO_STATES[0]["id"])
    old_state = get_state_by_id(old_state_id)

    state["micro_state_history"].append({
        "from": old_state_id,
        "to": target_state["id"],
        "from_name": old_state["name"] if old_state else "未知",
        "to_name": target_state["name"],
        "action": "跳转",
        "time": datetime.now().isoformat(),
    })

    state["current_micro_state"] = target_state["id"]
    save_state(project_name, state)
    print(f"[完成] 已跳转到: {target_state['name']} ({target_state['id']})")
    print(f"   所属阶段: {STAGE_GROUPS.get(target_state['stage'], {}).get('name', '')}")
    print(f"   输出路径: {target_state['output_path']}")


def cmd_prompt(_=None):
    """显示当前状态的进入话术"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    current_state_id = state.get("current_micro_state", MICRO_STATES[0]["id"])
    current_state = get_state_by_id(current_state_id)

    if current_state:
        print(current_state["entry_prompt"])


def cmd_history(_=None):
    """查看状态转移历史"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    history = state.get("micro_state_history", [])
    if not history:
        print("暂无状态转移记录。")
        return

    print(f"状态转移历史 (共 {len(history)} 次):\n")
    for h in history:
        action = h.get("action", "推进")
        print(f"{h['time'][:19]}  [{action}] {h['from_name']} -> {h['to_name']}")


def cmd_reset(_=None):
    """重置当前项目到初始状态"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    state["current_micro_state"] = MICRO_STATES[0]["id"]
    state["micro_state_history"] = []
    state["stage_completed"] = []
    state["user_inputs"] = {}

    save_state(project_name, state)
    print("[完成] 工作流已重置至初始状态")


def cmd_graph(_=None):
    """显示状态转移图"""
    print("微状态机转移图:")
    print("=" * 80)

    for stage_id, stage_info in STAGE_GROUPS.items():
        print(f"\n[{stage_info['name']}]")
        for state_id in stage_info["states"]:
            s = get_state_by_id(state_id)
            if s:
                next_list = ", ".join(s.get("next_states", ["(终态)"]))
                confirm = " [需确认]" if s.get("requires_confirm") else ""
                print(f"  {s['name']} -> {next_list}{confirm}")

    print("\n" + "=" * 80)
    print("图例: 🔒 需要用户确认  |  🔓 可自动推进")


def cmd_templates(_=None):
    """列出所有可用的论文模板"""
    print("可用的论文模板:")
    for tid, name in AVAILABLE_TEMPLATES.items():
        print(f"  {tid:20s} -> {name}")

    if PAPER_TEMPLATES_DIR.exists():
        reserved_names = {"figures", "image", "images", "sections", "tables", "cls", "sty"}
        custom = [d.name for d in PAPER_TEMPLATES_DIR.iterdir()
                  if d.is_dir()
                  and d.name not in AVAILABLE_TEMPLATES
                  and d.name not in reserved_names]
        if custom:
            print("\n用户自定义模板:")
            for c in custom:
                print(f"  {c}")


def cmd_set_template(args):
    """设置当前项目的模板: python pipeline.py set-template <模板名>"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    if len(args) < 3:
        print("用法: python pipeline.py set-template <模板名>")
        print("使用 'python pipeline.py templates' 查看所有可用模板")
        return

    template = args[2]

    all_templates = set(AVAILABLE_TEMPLATES.keys())
    if PAPER_TEMPLATES_DIR.exists():
        for d in PAPER_TEMPLATES_DIR.iterdir():
            if d.is_dir():
                all_templates.add(d.name)

    if template not in all_templates:
        print(f"模板 '{template}' 不存在")
        print(f"可用模板: {', '.join(sorted(all_templates))}")
        return

    state["template"] = template
    save_state(project_name, state)
    print(f"已设置模板: {AVAILABLE_TEMPLATES.get(template, template)}")


def detect_texlive():
    """检测是否安装了 TeX Live"""
    try:
        result = subprocess.run(
            ["xelatex", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def safe_clean_aux_files(paper_dir):
    """安全清理辅助文件，避免通配符误删源文件"""
    aux_extensions = [".aux", ".bbl", ".bcf", ".blg", ".log", ".out", ".toc", ".lof", ".lot", ".run.xml", ".synctex.gz"]
    for ext in aux_extensions:
        aux_file = paper_dir / f"main{ext}"
        if aux_file.exists():
            try:
                aux_file.unlink()
            except:
                pass


def run_latex_command(cmd, cwd, log_file, timeout=120):
    """安全运行LaTeX命令，输出到日志文件避免管道问题"""
    try:
        with open(log_file, "w", encoding="utf-8", errors="replace") as f:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                stdout=f,
                stderr=subprocess.STDOUT,
                timeout=timeout
            )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"[警告] 命令超时: {' '.join(cmd)}")
        return False
    except Exception as e:
        print(f"[警告] 运行出错: {e}")
        return False


def cmd_compile(_=None):
    """编译当前项目的 LaTeX 论文为 PDF"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    project_path = get_project_path(project_name)
    paper_dir = project_path / "paper"

    if not paper_dir.exists():
        print(f"论文目录不存在: {paper_dir}")
        return

    main_tex = paper_dir / "main.tex"
    if not main_tex.exists():
        print(f"未找到 main.tex: {main_tex}")
        return

    if not detect_texlive():
        print("未检测到 TeX Live 环境")
        print("请安装 TeX Live 后重试，或上传到 Overleaf 编译")
        return

    print(f"正在编译论文: {main_tex}")
    print("这可能需要几分钟时间...")

    # 编译前强制删除旧PDF（解决文件锁定问题）
    pdf_path = paper_dir / "main.pdf"
    if pdf_path.exists():
        try:
            pdf_path.unlink()
        except:
            print("[警告] 旧PDF文件被锁定，可能无法覆盖")

    log_file = paper_dir / "compile.log"

    # 编译流程：xelatex -> biber -> xelatex -> xelatex
    steps = [
        (["xelatex", "-interaction=nonstopmode", "main.tex"], "第1次 xelatex"),
        (["biber", "main"], "biber 参考文献"),
        (["xelatex", "-interaction=nonstopmode", "main.tex"], "第2次 xelatex"),
        (["xelatex", "-interaction=nonstopmode", "main.tex"], "第3次 xelatex"),
    ]

    success = True
    for cmd, desc in steps:
        print(f"  正在执行: {desc}...")
        if not run_latex_command(cmd, paper_dir, log_file):
            print(f"  ❌ {desc} 失败，详情见 {log_file}")
            success = False
            break
        print(f"  ✅ {desc} 完成")

    if success and pdf_path.exists():
        print(f"\n✅ 编译成功！PDF 已生成:")
        print(f"   {pdf_path}")
        # 显示文件大小
        size_mb = pdf_path.stat().st_size / 1024 / 1024
        print(f"   文件大小: {size_mb:.2f} MB")
    else:
        print(f"\n[警告] 编译失败，请检查日志: {log_file}")
        if log_file.exists():
            # 显示最后20行日志
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                last_lines = lines[-20:] if len(lines) > 20 else lines
                print("\n最后20行日志:")
                for line in last_lines:
                    print(f"  {line.rstrip()}")


def cmd_word_count(_=None):
    """统计各章节字数"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    project_path = get_project_path(project_name)
    paper_dir = project_path / "paper"
    sections_dir = paper_dir / "sections"

    if not sections_dir.exists():
        print(f"章节目录不存在: {sections_dir}")
        return

    print(f"章节字数统计 - {project_name}:\n")

    total_chars = 0
    total_words = 0

    section_files = sorted(sections_dir.glob("*.tex"))
    for sf in section_files:
        with open(sf, "r", encoding="utf-8") as f:
            content = f.read()

        # 移除 LaTeX 命令
        import re
        clean = re.sub(r'\\[a-zA-Z]+(\[[^\]]*\])?(\{[^\}]*\})?', '', content)
        clean = re.sub(r'%.*$', '', clean, flags=re.MULTILINE)
        clean = re.sub(r'\s+', ' ', clean)

        chars = len(clean.strip())
        words = len(clean.strip().split())

        total_chars += chars
        total_words += words

        marker = "⚠️" if chars < 500 else "✅" if chars > 2000 else "  "
        print(f"{marker} {sf.name:25s} | 字符: {chars:5d} | 词数: {words:5d}")

    print(f"\n{'总 计':25s} | 字符: {total_chars:5d} | 词数: {total_words:5d}")
    print(f"\n目标参考: 摘要 300-500 字, 引言 1500-2500 字, 结论 1000-1500 字")


def parse_bib_keys(bib_file):
    """解析.bib文件，提取所有引用键名"""
    if not bib_file.exists():
        return {}

    import re
    keys = {}
    with open(bib_file, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # 匹配 @article{key, 格式
    pattern = r'@\w+\{([^,]+),'
    for match in re.finditer(pattern, content):
        key = match.group(1).strip()
        keys[key.lower()] = key  # 小写映射到原始键名

    return keys


def guess_cite_key(author_part, year_part, bib_keys):
    """根据作者和年份猜测bib键名"""
    # 作者部分可能是 "Wu et al." 或 "Wu and Zhang"
    first_author = author_part.split()[0].lower()

    # 尝试常见的命名模式
    candidates = [
        f"{first_author}{year_part}",
        f"{first_author}{year_part[2:]}",
        f"{first_author}_{year_part}",
    ]

    for cand in candidates:
        if cand in bib_keys:
            return bib_keys[cand]

    return None


def cmd_cite_fix(_=None):
    """自动将纯文本引用转换为\\cite命令"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    project_path = get_project_path(project_name)
    paper_dir = project_path / "paper"
    sections_dir = paper_dir / "sections"
    bib_file = paper_dir / "erjref.bib"

    if not sections_dir.exists():
        print(f"章节目录不存在: {sections_dir}")
        return

    bib_keys = parse_bib_keys(bib_file)
    print(f"从 .bib 文件中找到 {len(bib_keys)} 个引用键\n")

    import re

    # 匹配 (Wu et al., 2025) 或 (Wu and Zhang, 2025) 格式的引用
    # 排除已经是 \cite{...} 内部的内容
    pattern = r'\(([^)]+?,\s*\d{4})\)'

    total_found = 0
    total_fixed = 0

    section_files = sorted(sections_dir.glob("*.tex"))
    for sf in section_files:
        with open(sf, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        fixes_in_file = 0

        for match in re.finditer(pattern, content):
            full_match = match.group(0)
            inner = match.group(1)

            # 跳过已经在\cite命令中的内容
            prev_pos = max(0, match.start() - 20)
            prev_text = content[prev_pos:match.start()]
            if "\\cite" in prev_text:
                continue

            # 解析作者和年份
            parts = inner.rsplit(',', 1)
            if len(parts) != 2:
                continue
            author_part = parts[0].strip()
            year_part = parts[1].strip()

            cite_key = guess_cite_key(author_part, year_part, bib_keys)
            if cite_key:
                new_cite = f"\\cite{{{cite_key}}}"
                content = content.replace(full_match, new_cite)
                fixes_in_file += 1
                print(f"  ✅ {full_match:40s} -> {new_cite}")

        if fixes_in_file > 0:
            with open(sf, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"{sf.name}: 修复 {fixes_in_file} 处引用\n")
            total_fixed += fixes_in_file

    print(f"\n总计: 修复 {total_fixed} 处纯文本引用")
    if bib_keys:
        print(f"提示: .bib 文件中还有 {len(bib_keys)} 个引用键可用于匹配")


def cmd_gen_do(args):
    """从模板生成Stata do-file"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    if len(args) < 3:
        print("用法: python pipeline.py gen-do <clean|mediation|baseline>")
        print("  clean    - 数据清洗do-file (内置缩尾、类型转换)")
        print("  mediation - 中介效应do-file (内置Sobel检验)")
        print("  baseline - 基准回归do-file")
        return

    template_type = args[2]
    project_path = get_project_path(project_name)
    templates_dir = PLUGIN_ROOT / "templates"

    template_map = {
        "clean": ("data/scripts/01_clean_template.do", "data/scripts/01_clean.do"),
        "mediation": ("analysis/do-files/02_mediation_template.do", "analysis/do-files/02_mediation.do"),
        "baseline": ("analysis/do-files/01_baseline.do", "analysis/do-files/01_baseline.do"),
    }

    if template_type not in template_map:
        print(f"未知模板类型: {template_type}")
        return

    template_rel, output_rel = template_map[template_type]
    template_path = templates_dir / template_rel
    output_path = project_path / output_rel

    if not template_path.exists():
        print(f"模板文件不存在: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 优先从 project_config.json 读取变量映射
    config = load_project_config(project_name)
    variables = config.get("variables", {}) if config else {}

    # 占位符替换映射
    def get_var(role, default=""):
        return variables.get(role, {}).get("varname", default)

    def get_label(role, default=""):
        label = variables.get(role, {}).get("label", default)
        if isinstance(label, list):
            return " ".join(label)
        if isinstance(label, str):
            return label
        return str(label) if label else default

    def get_var_list(role, default=""):
        """获取控制变量列表，将list/str统一转为空格分隔字符串"""
        val = variables.get(role, {}).get("varname", default)
        if isinstance(val, list):
            return " ".join(val)
        if isinstance(val, str) and val:
            return val
        return default if isinstance(default, str) else " ".join(default) if isinstance(default, list) else str(default)

    replacements = {
        # 新占位符系统 (优先)
        "{{PROJECT_PATH}}": str(project_path).replace("\\", "/"),
        "{{Y_VARNAME}}": get_var("Y", args[3] if len(args) > 3 else "y"),
        "{{Y_LABEL}}": get_label("Y", ""),
        "{{D_VARNAME}}": get_var("D", args[4] if len(args) > 4 else "x"),
        "{{D_LABEL}}": get_label("D", ""),
        "{{X_VARNAMES}}": get_var_list("X", "size lev roa"),
        "{{X_LABELS}}": get_label("X", ""),
        "{{M1_VARNAME}}": get_var("M1", ""),
        "{{M2_VARNAME}}": get_var("M2", ""),
        "{{M3_VARNAME}}": get_var("M3", ""),
        "{{ID_VARNAME}}": get_var("ID", "id"),
        "{{YEAR_VARNAME}}": get_var("YEAR", "year"),
        "{{CLUSTER_VAR}}": config.get("model", {}).get("cluster_level", "id") if config else "id",
        "{{SAMPLE_START}}": str(config.get("data", {}).get("sample_start", 2015)) if config else "2015",
        "{{SAMPLE_END}}": str(config.get("data", {}).get("sample_end", 2024)) if config else "2024",
        "{{CONTROL_VARS}}": get_var_list("X", "size lev roa"),
        "{{MEDIATOR_VARS}}": get_var_list("M", ""),

        # 旧占位符系统 (向后兼容)
        "{PROJECT_PATH}": str(project_path).replace("\\", "/"),
        "{DATA_FILENAME}": args[3] if len(args) > 3 else "data.xlsx",
        "{WINSOR_VARS}": " ".join(args[4:]) if len(args) > 4 else "",
        "{ID_VAR}": get_var("ID", "id"),
        "{YEAR_VAR}": get_var("YEAR", "year"),
        "{OUTCOME_VAR}": get_var("Y", "y"),
        "{TREATMENT_VAR}": get_var("D", "x"),
        "{MEDIATOR_VARS}": " ".join(filter(None, [get_var("M1",""), get_var("M2",""), get_var("M3","")])) or "m1 m2 m3",
        "{CONTROL_VARS}": get_var_list("X", "size lev roa"),
    }

    for key, value in replacements.items():
        content = content.replace(key, value)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ do-file 已生成: {output_path}")
    # 检查是否有未替换的占位符
    import re
    remaining = set(re.findall(r'\{\{[A-Z_]+\}\}', content))
    if remaining:
        print(f"⚠️  未替换的占位符: {remaining}")
        print(f"   请运行 'pipeline.py init-config' 初始化项目配置，或修改后手动替换")
    else:
        print(f"   所有占位符已替换完成")


def cmd_run_stata(args):
    """批量运行Stata do-file并自动解析结果"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    if len(args) < 3:
        print("用法: python pipeline.py run-stata <do-file-name>")
        print("  all - 运行所有do-file (01_clean -> 02_baseline -> 03_mediation -> 04_heterogeneity)")
        print("  01_baseline - 仅运行基准回归")
        print("  02_mediation - 仅运行中介效应")
        print("  03_heterogeneity - 仅运行异质性分析")
        return

    do_name = args[2]
    project_path = get_project_path(project_name)
    do_dir = project_path / "analysis" / "do-files"
    log_dir = project_path / "analysis" / "logs"
    log_dir.mkdir(exist_ok=True)

    # 定义运行顺序
    do_sequence = {
        "01_clean": "数据清洗",
        "01_baseline": "基准回归",
        "02_mediation": "中介效应",
        "03_heterogeneity": "异质性分析",
        "04_robustness": "稳健性检验",
    }

    if do_name == "all":
        do_files = [k for k in do_sequence.keys() if (do_dir / f"{k}.do").exists()]
    else:
        # 自动补全扩展名
        if not do_name.endswith(".do"):
            do_name = do_name + ".do"
        do_files = [do_name.replace(".do", "")] if (do_dir / do_name).exists() else []

    if not do_files:
        print(f"❌ 未找到可运行的do-file: {do_name}")
        return

    print(f"=== 开始运行 {len(do_files)} 个do-file ===\n")

    import subprocess

    for do in do_files:
        do_file = do_dir / f"{do}.do"
        log_file = log_dir / f"{do}.log"
        description = do_sequence.get(do, do)

        print(f"▶️  正在运行: {description} ({do}.do)")

        try:
            # 运行Stata (需要Stata在PATH中，或者提供完整路径)
            result = subprocess.run(
                ["stata-se", "-do", str(do_file)],
                cwd=str(do_dir),
                capture_output=True,
                text=True,
                timeout=300
            )

            # 保存日志
            with open(log_file, "w", encoding="utf-8", errors="replace") as f:
                f.write(result.stdout)
                if result.stderr:
                    f.write("\n=== STDERR ===\n")
                    f.write(result.stderr)

            # 简单的结果解析
            if result.returncode == 0:
                print(f"   ✅ 完成，日志: {log_file.name}")

                # 自动解读关键结果
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                # 查找显著的系数
                import re
                sig_matches = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s+([0-9]+\.[0-9]+)\s+([0-9]+\.[0-9]+).*?(\*{1,3})', content)
                if sig_matches:
                    print(f"   📊 发现 {len(sig_matches)} 个显著系数:")
                    for var, coef, se, stars in sig_matches[:3]:
                        print(f"      {var}: {coef}{stars}")
            else:
                print(f"   ❌ 运行失败，返回码: {result.returncode}")
                print(f"   查看日志: {log_file}")

        except FileNotFoundError:
            print("   ⚠️  未找到Stata命令，请确保Stata在PATH中")
            print("   或手动在Stata中运行: do " + str(do_file))
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  运行超时 (> 5分钟)")
        except Exception as e:
            print(f"   ❌ 运行出错: {e}")

        print()

    print(f"=== 全部运行完成 ===")
    print(f"日志目录: {log_dir}")


def cmd_set_context(args):
    """写入上下文存储: python pipeline.py set-context <stage> <key> <value>"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    if len(args) < 4:
        print("用法: python pipeline.py set-context <stage> <key> <value>")
        print("示例: python pipeline.py set-context topic y_var employment")
        return

    stage = args[2]
    key = args[3]
    value = " ".join(args[4:]) if len(args) > 4 else ""

    ctx = state.setdefault("context_store", {})
    ctx.setdefault(stage, {})[key] = value

    save_state(project_name, state)
    print(f"已写入: context_store.{stage}.{key} = {value}")


def cmd_get_context(args):
    """读取上下文存储: python pipeline.py get-context [stage]"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    ctx = state.get("context_store", {})
    stage = args[2] if len(args) > 2 else None

    if stage:
        data = ctx.get(stage, {})
        if not data:
            print(f"context_store.{stage} 为空")
        else:
            print(f"=== context_store.{stage} ===")
            for k, v in data.items():
                print(f"  {k}: {v}")
    else:
        summary = build_context_summary(project_name, state)
        print(json.dumps(summary, ensure_ascii=False, indent=2))


def cmd_init_config(args):
    """初始化项目配置文件: python pipeline.py init-config"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    ctx = state.get("context_store", {}).get("topic", {})
    if not ctx:
        print("⚠️  未找到 Topic 阶段产出，请先完成选题研究")
        return

    # 规范化control_vars: 字符串 → 列表
    raw_x = ctx.get("control_vars", [])
    if isinstance(raw_x, str):
        raw_x = [v.strip() for v in raw_x.split() if v.strip()]
    raw_x_labels = ctx.get("control_labels", [])
    if isinstance(raw_x_labels, str):
        raw_x_labels = [l.strip() for l in raw_x_labels.split() if l.strip()]

    config = {
        "project_name": project_name,
        "created_at": state.get("created_at", ""),
        "template": state.get("template", "economic-research"),
        "variables": {
            "Y":   {"varname": ctx.get("y_var", "y"),   "label": ctx.get("y_label", "被解释变量")},
            "D":   {"varname": ctx.get("d_var", "x"),   "label": ctx.get("d_label", "核心解释变量")},
            "X":   {"varname": raw_x, "label": raw_x_labels},
            "M1":  {"varname": ctx.get("m1_var", ""),   "label": ctx.get("m1_label", "")},
            "M2":  {"varname": ctx.get("m2_var", ""),   "label": ctx.get("m2_label", "")},
            "M3":  {"varname": ctx.get("m3_var", ""),   "label": ctx.get("m3_label", "")},
            "ID":  {"varname": ctx.get("id_var", "id"), "label": "个体标识"},
            "YEAR":{"varname": ctx.get("year_var", "year"), "label": "年份"},
        },
        "data": {
            "raw_path": ctx.get("raw_data_path", "data/raw/"),
            "clean_path": "data/clean/panel_clean.dta",
            "sample_start": ctx.get("sample_start", 2015),
            "sample_end": ctx.get("sample_end", 2024),
        },
        "model": {
            "identification": ctx.get("identification", "FE"),
            "fe_individual": ctx.get("fe_indiv", "id"),
            "fe_time": "year",
            "cluster_level": ctx.get("cluster_var", "id"),
        },
    }

    save_project_config(project_name, config)

    # 也写入 context_store
    ctx_store = state.setdefault("context_store", {})
    ctx_store["topic"] = {
        "research_question": ctx.get("research_question", ""),
        "y_var": ctx.get("y_var", ""),
        "d_var": ctx.get("d_var", ""),
        "control_vars": ctx.get("control_vars", []),
        "identification": ctx.get("identification", ""),
        "hypotheses": ctx.get("hypotheses", []),
    }

    save_state(project_name, state)
    print(f"✅ project_config.json 已生成")
    print(f"   路径: {get_project_config_path(project_name)}")
    print(f"   变量: Y={config['variables']['Y']['varname']}, D={config['variables']['D']['varname']}")


def cmd_undo(args):
    """回退到上一个状态: python pipeline.py undo"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    history = state.get("micro_state_history", [])
    if not history:
        print("没有可回退的历史记录")
        return

    last = history.pop()
    old_state_id = state["current_micro_state"]
    target_state_id = last["from"]
    target_state = get_state_by_id(target_state_id)
    old_state = get_state_by_id(old_state_id)

    state["current_micro_state"] = target_state_id
    state["micro_state_history"] = history

    save_state(project_name, state)

    print(f"⏪ 已回退: {old_state['name'] if old_state else old_state_id}")
    print(f"   → {target_state['name'] if target_state else target_state_id}")
    print()
    print(f"📋 当前状态:")
    cmd_status([])


def cmd_context_stage(args):
    """生成或显示阶段上下文文件: python pipeline.py context-stage [stage_id]"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    current_state = get_state_by_id(state.get("current_micro_state"))
    stage_id = args[2] if len(args) > 2 else current_state["stage"] if current_state else "topic"

    md = build_stage_context_md(project_name, state, stage_id)

    context_dir = get_project_path(project_name) / "context"
    context_dir.mkdir(exist_ok=True)

    context_file = context_dir / f"{stage_id}.md"
    with open(context_file, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"✅ 阶段上下文已生成: {context_file}")
    print()
    print(md)


def cmd_check_data(args):
    """检查数据和变量一致性"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    project_path = get_project_path(project_name)
    data_dir = project_path / "data" / "clean"
    do_dir = project_path / "analysis" / "do-files"

    print(f"=== 数据一致性检查 ===\n")

    issues = []

    # 检查数据文件是否存在
    data_file = data_dir / "panel_clean.dta"
    if not data_file.exists():
        issues.append(("❌", f"清洗后数据不存在: {data_file}"))
    else:
        issues.append(("✅", "清洗后数据存在"))

    # 检查所有do-file的路径引用
    for do_file in do_dir.glob("*.do"):
        with open(do_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # 只检查use语句和esttab语句中的硬编码路径（全局宏中的根路径除外）
        import re
        hardcoded_paths = re.findall(r'(use|esttab.*using)\s+"[A-Z]:/', content)
        if hardcoded_paths and "$DATA" not in content[:100] and "$OUTPUT" not in content[:100]:
            issues.append(("⚠️", f"{do_file.name} 可能包含硬编码路径"))

        # 代码中出现的reghdfe（排除注释）
        code_lines = [l for l in content.split("\n") if not l.strip().startswith("*")]
        code_content = "\n".join(code_lines)
        if "reghdfe" in code_content:
            issues.append(("⚠️", f"{do_file.name} 使用了reghdfe (需要ssc安装)"))
        if "winsor" in code_content:
            issues.append(("⚠️", f"{do_file.name} 使用了winsor外部包"))
        if "ssc install" in content:
            issues.append(("ℹ️", f"{do_file.name} 包含ssc安装命令"))

    print(f"检查结果 (共 {len(issues)} 项):\n")
    for status, msg in issues:
        print(f"  {status} {msg}")

    print()
    if any(s == "❌" for s, _ in issues):
        print("❌ 发现严重问题，请修复后继续")
    elif any(s == "⚠️" for s, _ in issues):
        print("⚠️  发现警告，不影响运行但建议优化")
    else:
        print("✅ 所有检查通过！")


def cmd_run_all(_=None):
    """一键运行完整实证流程：清洗 → 基准 → 中介 → 异质性 → 稳健性 → 编译论文"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    project_path = get_project_path(project_name)

    print("=" * 60)
    print("  🚀 经济学实证论文 - 一键全流程自动化")
    print("=" * 60)
    print(f"  项目: {project_name}")
    print(f"  路径: {project_path}")
    print()

    steps = [
        ("1/6", "数据清洗与描述性统计", "01_clean.do", "data/scripts"),
        ("2/6", "基准回归分析 (M1-M6)", "01_baseline.do", "analysis/do-files"),
        ("3/6", "中介效应检验 (Sobel)", "02_mediation.do", "analysis/do-files"),
        ("4/6", "异质性分析 (分组+交互)", "03_heterogeneity.do", "analysis/do-files"),
        ("5/6", "稳健性检验", "04_robustness.do", "analysis/do-files"),
        ("6/6", "LaTeX论文编译", "compile", "latex"),
    ]

    results = []
    start_time = datetime.now()

    for step_num, step_name, do_file, subdir in steps:
        print(f"[{step_num}] {step_name}")
        print("-" * 60)

        step_start = datetime.now()

        if subdir == "latex":
            # 编译LaTeX
            try:
                cmd_compile([])
                success = True
                msg = "✅ 编译完成"
            except Exception as e:
                success = False
                msg = f"❌ 编译失败: {e}"
        else:
            # 运行Stata do-file
            do_path = project_path / subdir / do_file
            if not do_path.exists():
                msg = f"⏭️  跳过: {do_file} 不存在"
                success = False
                print(msg)
            else:
                msg = f"✅ 准备好运行: {do_path}"
                success = True
                print(msg)
                print("   (Stata自动运行功能需要Stata在PATH中)")
                print("   请手动在Stata中运行: do " + str(do_path).replace("\\", "/"))

        results.append((step_name, success, msg))
        step_time = (datetime.now() - step_start).total_seconds()
        print(f"   耗时: {step_time:.1f}秒")
        print()

    # 总结
    total_time = (datetime.now() - start_time).total_seconds()
    print("=" * 60)
    print("  📊 全流程执行总结")
    print("=" * 60)

    success_count = sum(1 for _, s, _ in results if s)
    total_count = len(results)

    for step_name, success, msg in results:
        status = "✅" if success else "⚠️"
        print(f"  {status} {step_name}: {msg}")

    print()
    print(f"  总计: {success_count}/{total_count} 步骤完成")
    print(f"  总耗时: {total_time:.1f}秒")
    print()
    print("  💡 下一步: 查看 analysis/output/ 中的表格文件")
    print("            然后在 LaTeX 中引用并撰写结果")


def cmd_input(args):
    """记录用户输入: python pipeline.py input <key> <value>"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    if len(args) < 4:
        print("用法: python pipeline.py input <key> <value>")
        print("示例: python pipeline.py input research_topic \"最低工资与就业\"")
        return

    key = args[2]
    value = args[3]

    state.setdefault("user_inputs", {})[key] = {
        "value": value,
        "time": datetime.now().isoformat(),
        "state": state.get("current_micro_state"),
    }
    save_state(project_name, state)
    print(f"[完成] 已记录输入: {key} = {value}")


def cmd_resume(_=None):
    """显示对话恢复话术"""
    if not MEMORY_AVAILABLE:
        print("记忆模块不可用")
        return

    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    mem = get_memory(project_name)
    print("\n" + "=" * 50)
    print(mem.generate_resume_message("detailed"))
    print("=" * 50 + "\n")


def cmd_memory_stats(_=None):
    """显示对话统计信息"""
    if not MEMORY_AVAILABLE:
        print("记忆模块不可用")
        return

    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    mem = get_memory(project_name)
    stats = mem.get_stats()
    print(f"对话统计 - {project_name}:\n")
    for k, v in stats.items():
        print(f"  {k:20s}: {v}")


def cmd_chat_history(args):
    """显示对话历史"""
    if not MEMORY_AVAILABLE:
        print("记忆模块不可用")
        return

    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    n = int(args[2]) if len(args) > 2 and args[2].isdigit() else 20
    mem = get_memory(project_name)
    messages = mem.get_recent_messages(n)

    print(f"最近 {len(messages)} 条对话记录:\n")
    for msg in messages:
        role_icon = {"user": "👤", "agent": "🤖", "system": "⚙️"}.get(msg["role"], "❓")
        timestamp = msg["timestamp"][:16]
        print(f"{role_icon} [{timestamp}] {msg['role']}:")
        print(f"   {msg['content']}")
        print()


def cmd_list_decisions(_=None):
    """显示已确认的决策"""
    if not MEMORY_AVAILABLE:
        print("记忆模块不可用")
        return

    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    mem = get_memory(project_name)
    decisions = mem.get_decisions(confirmed_only=True)

    if not decisions:
        print("暂无已确认的决策")
        return

    print(f"已确认决策 ({len(decisions)} 条):\n")
    for d in decisions:
        print(f"  [{d['category']}] {d['decision']}")
        if d.get("context"):
            print(f"     背景: {d['context']}")
        print()


def main():
    PAPERS_DIR.mkdir(exist_ok=True)

    if len(sys.argv) < 2:
        cmd_status()
        return

    cmd = sys.argv[1]
    commands = {
        "list": cmd_list,
        "new": cmd_new,
        "use": cmd_use,
        "status": cmd_status,
        "states": cmd_states,
        "advance": cmd_advance,
        "jump": cmd_jump,
        "undo": cmd_undo,
        "prompt": cmd_prompt,
        "history": cmd_history,
        "reset": cmd_reset,
        "graph": cmd_graph,
        "templates": cmd_templates,
        "set-template": cmd_set_template,
        "compile": cmd_compile,
        "wc": cmd_word_count,
        "word-count": cmd_word_count,
        "cite-fix": cmd_cite_fix,
        "gen-do": cmd_gen_do,
        "run-stata": cmd_run_stata,
        "run-all": cmd_run_all,
        "check-data": cmd_check_data,
        "init-config": cmd_init_config,
        "set-context": cmd_set_context,
        "get-context": cmd_get_context,
        "context-stage": cmd_context_stage,
        "input": cmd_input,
        "resume": cmd_resume,
        "memory-stats": cmd_memory_stats,
        "chat": cmd_chat_history,
        "decisions": cmd_list_decisions,
    }

    if cmd in commands:
        commands[cmd](sys.argv)
    else:
        print(f"未知命令: {cmd}")
        print("可用命令:")
        print("  项目管理: list, new <name>, use <name>, status, history, reset, undo")
        print("  状态控制: states, advance, jump <state>, prompt, graph")
        print("  上下文:   init-config, set-context, get-context, context-stage")
        print("  论文工具: compile, wc/word-count, cite-fix")
        print("  Stata工具: gen-do <type>, run-stata <do-file|all>, check-data, run-all")
        print("  模板设置: templates, set-template <name>")
        print("  对话记忆: input, resume, memory-stats, chat, decisions")
        sys.exit(1)


if __name__ == "__main__":
    main()
