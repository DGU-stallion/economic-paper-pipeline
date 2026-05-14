# 经济学实证论文自动化工作流

> **Economic Empirical Paper Pipeline** — 一套可复用的人机协作经济学实证论文自动化框架。

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue)](https://www.python.org/)
[![StataMP 18](https://img.shields.io/badge/StataMP-18-1f6f1f)](https://www.stata.com/)
[![LaTeX](https://img.shields.io/badge/LaTeX-XeLaTeX-008080)](https://www.overleaf.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 项目简介

本项目的目标是搭建一套**可复用的人机协作经济学实证论文工作流**，而非撰写某一篇特定论文。

每次使用本工作流，从选题到完稿，按以下阶段推进：**选题研究 → 文献综述 → 数据获取与清洗 → Stata 实证 → 稳健性检验 → 结论验证 → LaTeX 论文撰写**。框架本身持续迭代。

**核心原则**：技术操作全部自动执行，但任何涉及研究决策的节点均可请求用户介入。AI 负责执行、检索、编码、生成；用户负责方向判断、关键决策、最终审阅。

---

## 当前论文

### 数字经济发展对省际就业结构的影响——基于面板门槛模型的实证研究

| 维度 | 内容 |
|------|------|
| **研究问题** | 数字经济发展如何影响中国省际就业结构？是否存在非线性门槛效应？ |
| **方法** | 双向固定效应 + 面板门槛模型 (Hansen, 1999) |
| **数据** | 31 省份 × 2011–2023 年，403 观测值 |
| **核心发现** | 数字经济显著提升三产就业占比（M6: β=0.277, p=0.003）；效应呈区域异质性（中部 > 东部 > 西部） |
| **状态** | ✅ 全部 7 阶段完成，论文已撰写 |

详见 [`topics/00_research_proposal.md`](topics/00_research_proposal.md) | [`SESSION_HANDOVER.md`](SESSION_HANDOVER.md)

---

## 工作流总览

```
选题研究 → 文献综述 → 数据获取与清洗 → Stata实证 → 稳健性检验 → 结论验证 → LaTeX论文撰写
```

| 阶段 | 自动化程度 | 人机协作点 | 产出 |
|------|-----------|-----------|------|
| 1. 选题研究 | 半自动 | 与用户对话确认选题方向、研究问题 | `topics/` 选题分析报告 |
| 2. 文献综述 | 自动 + 反馈 | 自动检索，关键文献解读可请求用户确认 | `literature/` 文献综述 |
| 3. 数据获取与清洗 | 自动 | 数据源无法获取时反馈用户 | `data/clean/` 清洗后数据 |
| 4. Stata 实证 | 自动 | 模型设定、变量选择可请求用户确认 | `analysis/output/` 回归结果 |
| 5. 稳健性检验 | 自动 | 检验策略自动生成，结果异常时反馈用户 | `analysis/output/` 检验结果 |
| 6. 验证结论 | 自动 + 确认 | 自动对比假设与结果，需用户确认结论 | `analysis/` 验证报告 |
| 7. LaTeX 论文 | 自动 | 用户审阅和修改成稿 | `paper/` 论文源码 |

### Stage 1 子阶段

选题研究采用 5W1H → Gap Analysis → SMART 的结构化推演路径：

1. **1.1 5W1H 头脑风暴**：从 What/Why/Who/When/Where/How 六维收敛研究兴趣
2. **1.2 研究空白分析**：识别文献、方法、数据、政策、跨学科五类空白
3. **1.3 SMART 精确化**：将选题转化为可执行的精确研究问题
4. **1.4 整合报告**：输出完整研究方案

---

## 目录结构

```
.
├── topics/                      # 选题分析报告
│   ├── 00_research_proposal.md  # 研究方案总报告
│   ├── 01_5w1h.md              # 5W1H 头脑风暴记录
│   ├── 02_gap_analysis.md      # 研究空白分析
│   └── 03_research_question.md # SMART 研究问题
│
├── literature/                  # 文献综述
│   ├── literature_review.md    # 文献综述正文
│   └── references.bib         # 参考文献
│
├── data/
│   ├── raw/                    # 原始数据（只读）
│   ├── clean/                  # 清洗后数据（.dta 供 Stata 使用）
│   └── scripts/               # Python 数据获取与清洗脚本
│       ├── 01_fetch_data.py
│       ├── 01b_fetch_supplementary.py
│       ├── 01c_merge_manual_data.py
│       └── 02_clean_and_export.py
│
├── analysis/
│   ├── do-files/               # Stata .do 文件
│   │   ├── 00_setup.do        # 环境设置
│   │   ├── 00_check.do        # 数据完整性检查
│   │   ├── 00_install_pkgs.do # 安装 Stata 包
│   │   ├── 01_describe.do     # 描述性统计
│   │   ├── 02_baseline.do     # 基准回归（双向 FE）
│   │   ├── 03_threshold.do    # 面板门槛模型
│   │   ├── 04_robustness.do   # 稳健性检验
│   │   ├── 05_heterogeneity.do# 异质性分析
│   │   └── 99_coefplot_fix.do # 系数图修正
│   ├── logs/                  # Stata 运行日志
│   ├── output/                # 结果输出（表格 .tex、图形 .pdf）
│   ├── references/            # 实证规范文档
│   │   ├── 01_stata_packages.md
│   │   ├── 02_output_spec.md
│   │   ├── 03_diagnostics.md
│   │   └── 04_robustness.md
│   └── 05_conclusion_validation.md  # 结论验证报告
│
├── paper/                      # LaTeX 论文源码
│   ├── main.tex               # 主文件
│   ├── chinese-erj.cls        # 《经济研究》格式模板
│   ├── erjref.bib             # 参考文献库（22条，中英双语）
│   ├── sections/              # 论文章节
│   │   ├── 01_introduction.tex
│   │   ├── 02_literature.tex
│   │   ├── 03_model.tex
│   │   ├── 04_empirical_results.tex
│   │   ├── 05_robustness.tex
│   │   └── 06_conclusion.tex
│   ├── tables/                # 回归表格
│   ├── figures/               # 图表
│   └── image/                 # 模板相关图片
│
├── CLAUDE.md                   # 项目指令文档（AI 协作配置文件）
├── SESSION_HANDOVER.md         # 会话交接文档
├── pipeline.py                 # 工作流状态管理
└── pipeline_state.json         # 工作流状态文件
```

---

## 技术栈

| 工具 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.12+ | 数据获取、清洗、转换 |
| **StataMP** | 18 | 计量回归分析 |
| **LaTeX (XeLaTeX)** | — | 论文排版（Overleaf 编译） |
| **Overleaf** | — | 在线 LaTeX 编译与协作 |
| **MCP 协议** | — | AI 工具与本地软件的集成桥接 |

### Python 依赖

```txt
pandas, numpy, requests, beautifulsoup4, yfinance, openpyxl, statsmodels
```

### MCP 服务器

本项目通过 [MCP 协议](https://modelcontextprotocol.io/) 将 AI 与本地工具集成：

| 服务器 | 用途 |
|--------|------|
| [stata-mcp](https://github.com/SepineTam/stata-mcp) | 操作本地 StataMP 18 执行 .do 文件 |
| [paper-search-mcp](https://github.com/openags/paper-search-mcp) | 搜索 arXiv / PubMed / Google Scholar |
| [zotero-mcp](https://github.com/kujenga/zotero-mcp) | 连接 Zotero 文献管理 |

---

## 环境要求与配置

### 前置条件

- [Python](https://www.python.org/) 3.12+
- [StataMP 18](https://www.stata.com/)（安装于 `D:\Program Files\Stata\StataMP-64.exe`）
- [uv](https://docs.astral.sh/uv/)（Python 包管理器，用于运行 MCP 服务器）
- [Zotero](https://www.zotero.org/)（文献管理，可选）
- Overleaf 账号（论文编译）

### 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/<your-username>/economic-paper-pipeline.git
cd economic-paper-pipeline

# 2. 安装 Python 依赖
pip install pandas numpy requests beautifulsoup4 openpyxl statsmodels

# 3. 查看工作流状态
python pipeline.py status

# 4. 根据 CLAUDE.md 的 Stage 指引启动 AI 协作工作流
```

---

## 使用方法

### 工作流状态管理

```bash
python pipeline.py status      # 查看当前进度
python pipeline.py advance     # 推进到下一阶段
python pipeline.py history     # 查看已完成阶段记录
python pipeline.py reset       # 重置工作流（新项目时使用）
```

### 运行 Stata 分析

Stata .do 文件位于 `analysis/do-files/`，按编号顺序执行：

```bash
# 通过 stata-mcp 执行（在 AI 协作环境中自动完成）
01_describe.do      # 描述性统计
02_baseline.do      # 基准回归
03_threshold.do     # 面板门槛模型
04_robustness.do    # 稳健性检验
05_heterogeneity.do # 异质性分析
```

### 论文编译

论文使用 Overleaf 在线编译：

1. 将 `paper/` 目录全部内容上传至 Overleaf 项目
2. 设置编译器为 **XeLaTeX**（菜单 → Compiler → XeLaTeX）
3. 编译顺序：`XeLaTeX → biber → XeLaTeX → XeLaTeX`

---

## 核心实证发现

| 假设 | 内容 | 结果 |
|------|------|------|
| H₁ | 数字经济对就业规模有促进效应 | ⚠️ 无法检验（数据缺失） |
| **H₂** | **数字经济推动就业向三产转移** | **✅ 支持（β=0.277, p=0.003）** |
| H₃ | 人力资本门槛效应 | ⚠️ 无法检验（数据缺失） |
| H₄ | 城镇化门槛效应 | ⚠️ 部分支持（方向符合，统计效力不足） |
| H₅ | 区域异质性（中西部 > 东部） | ⚠️ 部分支持（中部显著，西部不显著） |

详细验证报告见 [`analysis/05_conclusion_validation.md`](analysis/05_conclusion_validation.md)。

### 关键稳健性发现

- 经 6 种模型规格（M1→M6）检验，核心系数方向稳定
- 5/6 项稳健性检验通过
- 数字经济综合指数的就业效应强于单纯的数字金融指数（广义数字化转型 > 狭义金融科技）

---

## 论文约束

本工作流产出的论文遵循以下规范：

| 约束 | 要求 |
|------|------|
| 字数 | 正文 8,000–12,000 字（中文） |
| 参考文献 | 必须同时包含中英文文献 |
| 时效性 | ≥50% 参考文献为近 5 年内发表（2021–2026） |
| 格式 | 参照《经济研究》期刊格式 (`chinese-erj.cls`) |

---

## 已知局限

1. **变量缺失**：7 个变量（就业规模、失业率、FDI、R&D 等）无法获取，核心假设 H₁ 和 H₃ 未检验
2. **内生性控制有限**：仅通过双向固定效应缓解，未使用工具变量
3. **门槛模型统计效力不足**：高城镇化组仅 3 省，Bootstrap 检验因 singleton cluster 失败
4. **中部异质性系数过大**（1.781），标准误也较大（0.707），需谨慎解读

---

## 可改进方向

- 获取缺失变量（就业规模、失业率、FDI、R&D 等）以检验 H₁ 和 H₃
- 使用 Bartik IV 或 shift-share 工具变量处理内生性
- 用地级市数据（N > 3000）重新估计门槛模型
- 利用"宽带中国"试点政策做 DID 自然实验

---

## 引用

如使用本工作流或框架，请引用：

```bibtex
@software{economic_paper_pipeline,
  title = {经济学实证论文自动化工作流 (Economic Empirical Paper Pipeline)},
  year = {2026},
  url = {https://github.com/<your-username>/economic-paper-pipeline}
}
```

---

## 许可

[MIT License](LICENSE)

---

## 致谢

- 模板：[EthanDeng/Chinese-ERJ](https://github.com/EthanDeng/Chinese-ERJ) — 《经济研究》LaTeX 模板
- Stata MCP：[SepineTam/stata-mcp](https://github.com/SepineTam/stata-mcp) — Stata 与 MCP 协议集成
- 实证规范参考：[Awesome-Agent-Skills-for-Empirical-Research](https://github.com/brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research)
