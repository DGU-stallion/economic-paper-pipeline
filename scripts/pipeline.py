#!/usr/bin/env python3
"""
经济学实证论文自动化工作流 - 微状态机实现
支持 28 个微状态的精细状态管理，多项目切换
"""

import json
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from memory import ConversationMemory, get_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

ROOT = Path(__file__).parent.parent
CURRENT_PROJECT_FILE = ROOT / "config" / "current_project.json"
PAPERS_DIR = ROOT / "papers"
TEMPLATES_DIR = ROOT / "templates"
PAPER_TEMPLATES_DIR = TEMPLATES_DIR / "paper"

# ============================================================
# 微状态定义 (共 28 个)
# ============================================================
MICRO_STATES = [
    # ========== Stage 1: 选题研究 (11 个状态) ==========
    {
        "id": "topic-init",
        "stage": "topic",
        "name": "选题初始化",
        "description": "开始新的选题研究",
        "entry_prompt": "欢迎开始经济学实证论文工作流！让我们从选题开始。\n请简要描述你感兴趣的研究方向或经济现象。",
        "output_path": "topics/00_init.md",
        "next_states": ["topic-5w1h-what"],
        "requires_confirm": False,
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

    # ========== Stage 2: 文献综述 (5 个状态) ==========
    {
        "id": "literature-search-plan",
        "stage": "literature",
        "name": "检索策略设计",
        "description": "确定关键词、数据库、时间范围",
        "entry_prompt": "【文献检索策略】\n基于选题分析报告，已生成检索关键词列表。\n请确认检索策略（关键词、数据库、时间范围）。",
        "output_path": "literature/01_search_plan.md",
        "next_states": ["literature-search-execute"],
        "requires_confirm": True,
    },
    {
        "id": "literature-search-execute",
        "stage": "literature",
        "name": "文献检索执行",
        "description": "执行检索，获取文献列表",
        "entry_prompt": "【执行文献检索】\n正在检索学术文献...",
        "output_path": "literature/02_search_results.json",
        "next_states": ["literature-screen"],
        "requires_confirm": False,
    },
    {
        "id": "literature-screen",
        "stage": "literature",
        "name": "文献筛选与解读",
        "description": "筛选高相关文献，生成摘要",
        "entry_prompt": "【文献筛选与解读】\n已检索到 N 篇文献，正在进行相关性筛选和关键文献解读。\n请确认筛选出的核心文献列表。",
        "output_path": "literature/03_screened_papers.md",
        "next_states": ["literature-synthesize"],
        "requires_confirm": True,
    },
    {
        "id": "literature-synthesize",
        "stage": "literature",
        "name": "文献脉络梳理",
        "description": "构建文献发展脉络与理论框架",
        "entry_prompt": "【文献脉络梳理】\n正在构建文献发展脉络与理论框架图...\n请确认文献综述的整体结构。",
        "output_path": "literature/04_synthesis.md",
        "next_states": ["literature-write"],
        "requires_confirm": True,
    },
    {
        "id": "literature-write",
        "stage": "literature",
        "name": "综述撰写与Bib管理",
        "description": "完成文献综述撰写，生成.bib文件",
        "entry_prompt": "【文献综述撰写】\n正在生成文献综述正文并管理参考文献...",
        "output_path": "literature/05_review_final.md",
        "bib_path": "paper/erjref.bib",
        "next_states": ["data-plan"],
        "requires_confirm": True,
    },

    # ========== Stage 3: 数据获取与清洗 (4 个状态) ==========
    {
        "id": "data-plan",
        "stage": "data",
        "name": "数据方案设计",
        "description": "确定数据源、变量定义、数据结构",
        "entry_prompt": "【数据获取方案】\n基于研究问题，已生成数据需求清单。\n请确认数据源、变量定义和数据获取计划。",
        "output_path": "data/01_data_plan.md",
        "next_states": ["data-acquire"],
        "requires_confirm": True,
    },
    {
        "id": "data-acquire",
        "stage": "data",
        "name": "数据获取",
        "description": "爬取/下载/导入原始数据",
        "entry_prompt": "【数据获取中】\n正在获取原始数据...",
        "output_path": "data/raw/",
        "next_states": ["data-clean"],
        "requires_confirm": False,
    },
    {
        "id": "data-clean",
        "stage": "data",
        "name": "数据清洗",
        "description": "缺失值处理、异常值处理、变量构造",
        "entry_prompt": "【数据清洗中】\n正在执行数据清洗脚本...",
        "output_path": "data/scripts/",
        "next_states": ["data-validate"],
        "requires_confirm": False,
    },
    {
        "id": "data-validate",
        "stage": "data",
        "name": "数据验证",
        "description": "描述性统计、数据质量检查",
        "entry_prompt": "【数据验证】\n已生成描述性统计表。\n请确认数据质量，如无问题继续到实证分析阶段。",
        "output_path": "data/clean/",
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
    "topic": {"name": "选题研究", "states": [s["id"] for s in MICRO_STATES if s["stage"] == "topic"]},
    "literature": {"name": "文献综述", "states": [s["id"] for s in MICRO_STATES if s["stage"] == "literature"]},
    "data": {"name": "数据获取与清洗", "states": [s["id"] for s in MICRO_STATES if s["stage"] == "data"]},
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
    """查看当前项目的微状态详情"""
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

    print(f"[项目] {project_name}")
    print(f"[当前阶段] {stage_name}")
    print(f"[微状态] [{current_idx + 1}/{total}] {current_state['name']}")
    print(f"[进度] {progress:.1f}%")
    print(f"[输出路径] {current_state['output_path']}")
    print()
    print(f"[进入话术]:")
    print(f"   {current_state['entry_prompt']}")
    print()

    next_states = current_state.get("next_states", [])
    if next_states:
        print(f"[下一状态]:")
        for ns_id in next_states:
            ns = get_state_by_id(ns_id)
            if ns:
                confirm_marker = "[需确认]" if ns.get("requires_confirm") else "[自动]"
                print(f"   {confirm_marker} {ns['name']} ({ns['id']})")
    else:
        print("[完成] 已到达最终状态！")

    history = state.get("micro_state_history", [])
    if history:
        print(f"\n[最近状态转移]:")
        for h in history[-5:]:
            print(f"  {h['time'][:16]} | {h['from']} -> {h['to']}")

    print(f"\n[阶段完成情况]:")
    completed_stages = state.get("stage_completed", [])
    for stage_id, stage_info in STAGE_GROUPS.items():
        marker = "[X]" if stage_id in completed_stages else "[ ]"
        states_count = len(stage_info["states"])
        print(f"  {marker} {stage_info['name']} ({states_count} 个微状态)")


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
    """推进到下一状态: python pipeline.py advance [--skip-confirm]"""
    project_name, state = load_state()
    if project_name is None:
        print("未选择项目")
        return

    current_state_id = state.get("current_micro_state", MICRO_STATES[0]["id"])
    current_state = get_state_by_id(current_state_id)

    if not current_state:
        print(f"错误: 未知状态 '{current_state_id}'")
        return

    next_states = current_state.get("next_states", [])
    if not next_states:
        print("已到达最终状态，无法继续推进")
        return

    if len(next_states) > 1:
        print(f"当前状态有多个后续路径，请使用 'python pipeline.py jump <状态ID>' 选择:")
        for ns_id in next_states:
            ns = get_state_by_id(ns_id)
            if ns:
                print(f"  - {ns['id']}: {ns['name']}")
        return

    next_state_id = next_states[0]
    next_state = get_state_by_id(next_state_id)

    skip_confirm = "--skip-confirm" in args
    if current_state.get("requires_confirm") and not skip_confirm:
        print(f"[警告] 当前状态需要用户确认才能推进。")
        print(f"   请先完成 {current_state['name']} 的用户交互。")
        print(f"   如需强制跳过确认，使用: python pipeline.py advance --skip-confirm")
        return

    state["micro_state_history"].append({
        "from": current_state_id,
        "to": next_state_id,
        "from_name": current_state["name"],
        "to_name": next_state["name"],
        "time": datetime.now().isoformat(),
    })

    state["current_micro_state"] = next_state_id

    current_stage = current_state["stage"]
    next_stage = next_state["stage"]
    if current_stage != next_stage and current_stage not in state.get("stage_completed", []):
        state.setdefault("stage_completed", []).append(current_stage)
        print(f"[完成] 已完成阶段: {STAGE_GROUPS[current_stage]['name']}")

    save_state(project_name, state)
    print(f"[完成] 已推进到: {next_state['name']} ({next_state_id})")
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

    try:
        subprocess.run(["xelatex", "-interaction=nonstopmode", "main.tex"], cwd=paper_dir, capture_output=True, timeout=120)
        subprocess.run(["biber", "main"], cwd=paper_dir, capture_output=True, timeout=60)
        subprocess.run(["xelatex", "-interaction=nonstopmode", "main.tex"], cwd=paper_dir, capture_output=True, timeout=120)
        subprocess.run(["xelatex", "-interaction=nonstopmode", "main.tex"], cwd=paper_dir, capture_output=True, timeout=120)

        pdf_path = paper_dir / "main.pdf"
        if pdf_path.exists():
            print(f"✅ 编译成功！PDF 已生成:")
            print(f"   {pdf_path}")
        else:
            print("[警告] 编译未生成 PDF 文件，请检查日志")
    except subprocess.TimeoutExpired:
        print("[错误] 编译超时")
    except Exception as e:
        print(f"[错误] 编译出错: {e}")


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
        "prompt": cmd_prompt,
        "history": cmd_history,
        "reset": cmd_reset,
        "graph": cmd_graph,
        "templates": cmd_templates,
        "set-template": cmd_set_template,
        "compile": cmd_compile,
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
        print("用法: python pipeline.py <list|new|use|states|status|advance|jump|prompt|history|reset|graph|templates|set-template|compile|input|resume|memory-stats|chat|decisions>")
        sys.exit(1)


if __name__ == "__main__":
    main()
