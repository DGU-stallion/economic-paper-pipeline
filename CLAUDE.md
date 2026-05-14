# 经济学实证论文自动化工作流 (Economic Paper Pipeline)

## 项目性质

本项目的目标是搭建一套**可复用的人机协作经济学实证论文工作流**，而非撰写某一篇特定论文。
每次使用本工作流，从选题到完稿，按以下阶段推进。框架本身持续迭代。

## 工作流总览

```
选题研究 → 文献综述 → 数据获取与清洗 → Stata实证 → 稳健性检验 → 结论验证 → LaTeX论文撰写
```

| 阶段 | 自动化程度 | 人机协作点 | 产出 |
|------|-----------|-----------|------|
| 1. 选题研究 | 半自动 | 必须与用户对话确认选题方向、研究问题 | `topics/` 选题分析报告 |
| 2. 文献综述 | 自动+反馈 | 自动检索，关键文献解读可请求用户确认 | `literature/` 文献综述 |
| 3. 数据获取与清洗 | 自动 | 数据源无法获取时反馈用户，数据清洗自动完成 | `data/clean/` 清洗后数据 |
| 4. Stata实证 | 自动 | 模型设定、变量选择可请求用户确认 | `analysis/output/` 回归结果 |
| 5. 稳健性检验 | 自动 | 检验策略自动生成，结果异常时反馈用户 | `analysis/output/` 检验结果 |
| 6. 验证结论 | 自动+确认 | 自动对比假设与结果，需用户确认结论 | `analysis/` 验证报告 |
| 7. LaTeX论文 | 自动 | 用户审阅和修改成稿 | `paper/` 论文源码 |

**关键原则**：技术操作全部自动执行，但任何涉及研究决策的节点都可以请求用户介入。

### Stage 1 选题研究——子阶段路由

选题研究分为 4 个连续子阶段，由 AI 引导用户完成从模糊兴趣到精确研究问题的结构化推演。

每个子阶段结束时，向用户呈现关键结论并请求确认，再推进到下一子阶段。

#### 1.1 5W1H 头脑风暴

使用 5W1H 框架将模糊研究兴趣收敛为结构化选题方向。AI 逐维引导用户回答：

| 维度 | 经济学适配问题 |
|------|--------------|
| **What** | 核心经济现象/问题是什么？被解释变量 Y、核心解释变量 D 初步想法？ |
| **Why** | 为什么重要？理论贡献或政策含义何在？与既有文献的张力在哪里？ |
| **Who** | 利益相关方是谁（政策制定者、企业、劳动者、消费者）？研究结论对谁有意义？ |
| **When** | 研究的时间跨度？是否有自然实验窗口？（政策冲击、制度变革、外部事件） |
| **Where** | 制度背景和地理范围（国别/区域/行业）？数据来源的可得性？ |
| **How** | 可能的识别策略（OLS/FE/DID/RDD/IV）？核心识别假设的初步思考？ |

AI 每次聚焦一个维度，基于前一个维度的答案自然过渡到下一个维度，最后以推演摘要表格收束。

产出：`topics/01_5w1h.md`（对话记录 + 结构化推演摘要表）

#### 1.2 研究空白分析 (Gap Analysis)

对 1.1 收敛出的选题方向进行系统评估，识别 5 类研究空白：

| 空白类型 | 经济学含义 | 识别方法 |
|---------|-----------|---------|
| **文献空白** | 某经济现象尚未被充分实证研究 | 检索 CNKI/Google Scholar，识别被引少但有潜力的方向 |
| **方法空白** | 现有识别策略存在局限 | 内生性未解决、测量误差、样本选择偏差、外部有效性不足 |
| **数据空白** | 新数据源带来的研究机会 | 新公开的微观调查数据、行政数据、卫星/遥感数据等 |
| **政策空白** | 新政策/制度变革的评估机会 | 近期出台政策（减税、社保改革、环境规制）尚未有严格因果推断 |
| **跨学科空白** | 经济学与其他领域的交叉 | 行为经济学+公共政策、劳动经济学+AI技术等 |

候选选题按三维度打分（1-5）：

| 维度 | 评估内容 |
|------|---------|
| **重要性** | 理论贡献潜力 / 政策含义强度 |
| **新颖性** | 区别于已有文献的程度 |
| **可行性** | 数据可获取性 / 识别策略可信度 / 预期时间成本 |

产出：`topics/02_gap_analysis.md`（含决策矩阵和推荐选题方向）

#### 1.3 研究问题精确化 (SMART 原则)

将选定方向转化为可执行的精确研究问题：

- **S (Specific)**: 明确研究总体、处理变量、结果变量、识别策略
  - 坏的例子："研究最低工资对就业的影响"
  - 好的例子："利用 2022 年各省最低工资上调的准自然实验，以 DID 方法估计最低工资标准提高对制造业企业用工数量的因果效应"
- **M (Measurable)**: 结果变量是否可量化？数据是否可得？预期效应方向和量级？
- **A (Achievable)**: 数据是否可在合理时间内获取和清洗？方法是否在能力范围内？
- **R (Relevant)**: 研究结果对学术界或政策制定者是否有价值？
- **T (Time-bound)**: 数据频率（年度/季度/月度）？研究周期预估？

同时明确：
- 研究假设（H₁, H₂, ...）
- 核心变量定义（被解释变量 Y、核心解释变量 D、控制变量 X）及预期符号
- 识别策略的初步论证与主要识别假设

产出：`topics/03_research_question.md`

#### 1.4 整合：选题分析报告

将前三步成果整合为完整的研究方案，结构如下：

```markdown
# 选题分析报告: [研究题目]

## 1. 研究动机与背景
## 2. 5W1H 推演摘要
## 3. 研究空白与定位
## 4. 研究问题与假设
## 5. 识别策略初案
## 6. 数据需求
## 7. 预期贡献
## 8. 下一步（Stage 2 文献检索策略）
```

产出：`topics/00_research_proposal.md`

---

## 目录约定

```
topics/             选题研究——分析报告、选题对话记录
literature/         文献综述——检索笔记、文献摘要、参考文献列表(.bib)
data/
  raw/              原始数据（只读，不修改）
  clean/            清洗后可用数据（.dta 格式供 Stata 使用）
  scripts/          Python 脚本（爬取、清洗、转换）
analysis/
  do-files/         Stata .do 文件（按阶段编号: 01_describe.do, 02_regression.do...）
  logs/             Stata 运行日志
  output/           结果输出（表格 .tex/.csv、图形 .pdf/.png）
paper/              论文源码（LaTeX 文件）
```

## 技术栈约定

### Python
- 版本: 3.12+
- 核心库: pandas, numpy, requests, beautifulsoup4, yfinance, openpyxl, statsmodels
- 数据清洗脚本放在 `data/scripts/`，以 `01_`, `02_` 前缀编号
- 脚本输出统一写入 `data/clean/`，最终导出为 `.dta` 格式供 Stata 读取

### Stata
- 版本: StataMP 18
- 通过 Stata MCP (stata-mcp) 执行 .do 文件
- .do 文件放在 `analysis/do-files/`，按执行顺序编号
- 所有回归结果输出到 `analysis/output/`，日志输出到 `analysis/logs/`
- .do 文件统一使用 UTF-8 编码
- **实证产出规范**：详见 `analysis/references/02_output_spec.md`
  - **T2 核心**: M1→M6 渐进控制回归表（6 列，从原始相关到完全设定）
  - 必须产出 5 表（T1-T5）+ 4 图（F1-F4）
- **诊断检验**：详见 `analysis/references/03_diagnostics.md`
- **稳健性检验**：详见 `analysis/references/04_robustness.md`
- **必需 Stata 包**：详见 `analysis/references/01_stata_packages.md`，首次使用时运行 `ssc install`

### LaTeX
- 语言: 中文
- 格式: 参照《经济研究》期刊格式要求
- 模板: `paper/chinese-erj.cls`（来自 [EthanDeng/Chinese-ERJ](https://github.com/EthanDeng/Chinese-ERJ)）
- 主文件: `paper/main.tex`，章节文件: `paper/sections/NN_*.tex`
- 参考文献: `paper/erjref.bib`
- 编译命令: `xelatex → biber → xelatex → xelatex`
- 本地 TeX Live 发行版编译

### 论文约束 (Paper Constraints)

论文撰写须遵守以下约束条件，适用于每次使用本工作流产出的论文：

1. **字数要求 (Word Count)**：全文正文字数（含摘要、正文、注释，不含参考文献、附录）控制在 8000~12000 字（中文）。
2. **参考文献双语要求 (Bilingual References)**：参考文献必须同时包含中文文献和英文文献，两类均需有一定数量。
3. **时效性要求 (Recency)**：参考文献中不少于 50% 应为近 5 年内发表（2021~2026 年），以保障文献的前沿性。

这些约束在工作流第 7 阶段（LaTeX 论文撰写）执行，但在第 2 阶段（文献综述）就应当开始考虑。

### 通用约定
- 所有文本文件统一使用 UTF-8 编码
- 文件命名：
  - Python: `NN_description.py`
  - Stata: `NN_description.do`
  - 输出: `NN_description.{ext}`
  - `NN` 为两位数字序号，保证执行顺序
- 关联文件使用相同基名，如 `02_regression.do` → `02_regression.log`

### 写作纪律 (Writing Discipline)

- 每句话只表达一个具体信息点。
- 写之前先问自己：我具体想说什么？这是最清楚的说法吗？能不能说得更具体？
- 删除不能提供有用信息的句子。
- 优先使用直接表达，不使用抽象包装。
- 不要使用模糊说法（如"优化流程""增强鲁棒性"），除非同时说明具体动作。

### 澄清规则 (Clarification Rule)

- 如果用户请求有歧义，先问一个简短的澄清问题。
- 当存在多个合理解释时，不要默默选择其中一个。
- 如果可以基于低风险假设继续执行，应简短说明该假设。

## MCP 服务器配置

项目使用以下 MCP 服务器，均在 `.mcp.json` 中配置：

| 服务器 | 用途 | 启动方式 |
|--------|------|---------|
| **stata-mcp** | StataMP 18 回归分析 | `uvx stata-mcp` |
| **paper-search-mcp** | 学术文献搜索（arXiv/PubMed/Google Scholar） | `uv run --with paper-search-mcp python -m paper_search_mcp.server` |

### stata-mcp

使用 [SepineTam/stata-mcp](https://github.com/SepineTam/stata-mcp) 通过 MCP 协议操作本地 StataMP 18。

> 依赖：需要 `uv`（已安装），首次运行会自动从 PyPI 下载。

**Stata 可执行文件路径**：`D:\Program Files\Stata\StataMP-64.exe`

**工作流**：
1. 在 `analysis/do-files/` 中生成 .do 文件（UTF-8 编码）
2. 通过 `stata_do` 工具执行 .do 文件
3. 通过 `read_log` 工具读取日志获取结果
4. 将关键输出（系数表、检验统计量）提取到 `analysis/output/`

**可用工具**：`stata_do`、`write_dofile`、`get_data_info`、`read_log`、`ado_package_install`、`help`

### paper-search-mcp

使用 [paper-search-mcp](https://github.com/openags/paper-search-mcp) 搜索学术文献。

**可用工具**（13 个）：`search_arxiv`、`search_pubmed`、`search_google_scholar` 等搜索功能，以及对应的下载和全文读取功能。

## LaTeX 编译

论文使用本地 TeX Live 发行版编译（因 Overleaf 免费版有编译时长限制）。

**编译命令**（项目根目录执行）：
```bash
cd paper
xelatex main.tex
biber main
xelatex main.tex
xelatex main.tex
```

**前置条件**：安装 [TeX Live](https://tug.org/texlive/)（Windows 用户建议用 TeX Live GUI 安装器，安装 `collection-langchinese` 和 `collection-bibtexextra` 以包含 `biblatex-gb7714-2015` 宏包）。

> 论文源码在 `paper/` 目录中本地维护，随项目版本管理。

## 人机协作协议

**必须与用户对话的场景**：
1. 选题阶段：研究方向、研究问题的确定
2. 实证阶段：核心模型设定、关键变量选择
3. 论文阶段：整体结构、论文章节的确认

**可以自动执行但需反馈用户确认的场景**：
1. 数据源获取方案
2. 稳健性检验策略
3. 最终结论的验证

**全自动执行无需确认**：
1. 数据清洗具体操作（按已确认方案执行）
2. Stata 代码生成与执行
3. 文献检索与初步摘要
4. LaTeX 代码生成

## pipeline.py

`pipeline.py` 是轻量级工作流状态管理工具：

```bash
python pipeline.py status      # 查看当前进度
python pipeline.py advance     # 推进到下一阶段（需确认已完成当前阶段）
python pipeline.py history     # 查看已完成阶段记录
python pipeline.py reset       # 重置工作流（新论文项目时使用）
```

状态存储在 `pipeline_state.json` 中，随项目版本管理。
