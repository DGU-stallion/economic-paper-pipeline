---
name: "Stata 实证 Skill"
version: "1.0.0"
skill_id: "skill-stata"
description: "数据清洗、Stata 回归分析、稳健性检验、异质性分析、结论验证"
stages_handled: [data, stata, robustness, conclusion]
required_mcp: [stata-mcp]
---

## Skill 定位

专门负责**数据获取清洗、Stata 实证回归、稳健性检验、异质性分析、结论验证**的全流程实证分析。

覆盖原工作流 Stage 3-6：数据 → 基准回归 → 稳健性 → 结论验证

**不负责**：选题、文献、LaTeX 写作

---

## 输入输出接口

### 输入 (来自协调器)

```json
{
  "project_name": "项目名称",
  "project_path": "papers/<project-name>/",
  "entry_point": "new|resume|jump",
  "topic_context": {
    "research_question": "研究问题",
    "y_var": {"name": "", "definition": ""},
    "d_var": {"name": "", "definition": ""},
    "control_vars": [],
    "identification_strategy": "DID|FE|IV|RDD|OLS"
  },
  "data_context": {
    "raw_data_paths": ["path1", "path2"],
    "cleaned_dta_path": null
  }
}
```

### 输出 (传递给下一个 Skill)

```json
{
  "status": "completed|partial|needs_data",
  "stage": "stata",
  "empirical_results": {
    "baseline": {
      "y_var": "",
      "d_var": "",
      "main_coef": 0.277,
      "p_value": 0.003,
      "significance": "1%",
      "n_obs": 3000,
      "r_squared": 0.35
    },
    "robustness": {
      "passed": 5,
      "total": 6,
      "failed_checks": []
    },
    "heterogeneity": {
      "dimensions": ["region", "size", "ownership"],
      "findings": []
    },
    "conclusion": "假设H1成立，H2部分成立"
  },
  "artifacts": {
    "tables": [
      "analysis/output/table1_descriptive.tex",
      "analysis/output/table2_main.tex",
      "analysis/output/table3_threshold.tex",
      "analysis/output/table4_robustness.tex",
      "analysis/output/table5_heterogeneity.tex"
    ],
    "figures": [
      "analysis/output/fig1_threshold.pdf",
      "analysis/output/fig2_coefplot.pdf",
      "analysis/output/fig3_trend.pdf"
    ],
    "logs": [
      "analysis/logs/01_describe.log",
      "analysis/logs/02_baseline.log"
    ]
  },
  "next_skill": "latex"
}
```

---

## 工作流程

### Step 0: 读取上下文（强制执行）

⚠️ **每次进入 Stata Skill 时必须先执行以下操作**，不可跳过：

1. **读取 project_config.json**（获取变量映射）
   ```bash
   python scripts/pipeline.py get-context
   ```
   或直接读取 `papers/<项目>/project_config.json`，获取：
   - `variables.Y.varname` — 被解释变量名
   - `variables.D.varname` — 核心解释变量名
   - `variables.X.varname` — 控制变量名列表
   - `variables.ID.varname` / `variables.YEAR.varname`
   - `model.cluster_level` — 标准误聚类层级

2. **读取 context_store.topic**（获取研究设计）
   从 `pipeline_state.json` 的 `context_store.topic` 获取：
   - 研究问题、假设、识别策略
   - 如果 context_store 为空，必须先向用户确认变量名

3. **读取 context_store.stata**（如有，恢复断点）
   如果存在，说明已完成部分实证工作，从断点恢复

**禁止**：在未读取 project_config.json 的情况下用硬编码变量名生成 do-file。

---

### Stage 3: 数据获取与清洗

#### Step 3.1 数据源确认
- 检查用户提供的原始数据文件
- 自动识别数据格式（CSV/Excel/DTA）
- 如缺失，生成数据需求清单供用户补充

#### Step 3.2 数据清洗脚本生成
自动生成 Python 清洗脚本 (`data/scripts/02_clean_and_export.py`)：
1. 缺失值处理（删除/插值/标记）
2. 异常值处理（Winsorize 1%/99%）
3. 变量生成（对数、交互项、虚拟变量）
4. 合并多个数据集
5. 导出为 Stata 格式 `.dta`

#### Step 3.3 数据质量检查
- 样本量报告
- 面板平衡性检查
- 描述性统计表（T1）
- 相关性分析表

---

### Stage 4: 基准回归分析

#### Step 4.1 模型设定确认
向用户展示并确认：
- 基准模型形式（Y = α + βD + γControls + FE + ε）
- 固定效应层级（个体/时间/双向）
- 标准误聚类级别（个体/省份/行业）
- 核心变量预期符号

#### Step 4.2 渐进式回归（M1-M6）
自动生成 `02_baseline.do`：
- M1: Y ~ D（单变量）
- M2: + 个体 FE
- M3: + 时间 FE
- M4: + 核心控制变量
- M5: + 其他控制变量
- M6: 完全设定 + 聚类标准误

输出 `table2_main.tex`（必须是标准实证表格格式）

#### Step 4.3 结果总结
用一句话总结核心发现：
> "核心系数 β = 0.277，p = 0.003，在 1% 水平上显著 ✅，与预期一致"

---

### Stage 5: 稳健性检验

自动执行 6 类稳健性检验，输出 `table4_robustness.tex`：

| 检验类型 | 说明 |
|---------|------|
| 子样本回归 | 排除特殊样本/极端年份 |
| 替换被解释变量 | Y 的不同度量方式 |
| 替换核心解释变量 | D 的不同度量方式 |
| 加入更多控制变量 | 缓解遗漏变量问题 |
| 不同标准误设定 | Robust/Cluster/Bootstrap |
| 安慰剂检验 | 随机分配处理组 |

#### 门槛效应/机制分析（如适用）
- 门槛模型：寻找门槛值 + 画图
- 中介效应：三步法或 Bootstrap

---

### Stage 6: 异质性分析

按预设维度分组回归：
- 地区：东部/中部/西部
- 企业规模：大型/中小型
- 所有制：国企/民企/外资
- 行业：制造业/服务业

生成：
- `table5_heterogeneity.tex`（分组回归表）
- `fig2_coefplot.pdf`（系数对比图）

---

### Stage 7: 结论验证

对比研究假设与实证结果：
| 假设 | 预期符号 | 实证结果 | 是否成立 |
|------|---------|---------|---------|
| H1 | + | β=0.277*** | ✅ 成立 |
| H2 | - | β=-0.045 | ⚠️ 不显著 |

生成 `analysis/05_conclusion_validation.md`

---

## 人机协作点

✅ **必须用户确认**：
1. 数据清洗策略（缺失值/异常值处理方式）
2. 基准模型最终设定（FE/聚类/控制变量）
3. 稳健性检验项目选择
4. 最终结论验证（是否接受实证结果）

⚠️ **异常情况反馈**：
- 核心系数不显著 → 提示可能原因 + 建议排查
- 符号与预期相反 → 请用户确认理论逻辑
- 样本量过少 → 建议补充数据

---

## 表格输出规范（严格遵守）

### T1 描述性统计
| 变量 | 观测数 | 均值 | 标准差 | 最小值 | 最大值 |
|------|-------|------|--------|--------|--------|
| Y | N | μ | σ | min | max |
| D | N | μ | σ | min | max |

### T2 核心回归（M1-M6 渐进）
| 变量 | M1 | M2 | M3 | M4 | M5 | M6 |
|------|----|----|----|----|----|----|
| D | β* | β** | β*** | β*** | β*** | β*** |
| 控制变量 | 否 | 否 | 否 | 是 | 是 | 是 |
| 个体FE | 否 | 是 | 是 | 是 | 是 | 是 |
| 时间FE | 否 | 否 | 是 | 是 | 是 | 是 |
| N | | | | | | |
| R² | | | | | | |

---

## Stata 环境要求

- 使用 `stata-mcp` MCP 服务器执行 .do 文件
- **零外部依赖原则**：所有 do-file 仅使用 Stata 内置命令
  - ✅ 用 `xtreg ..., fe` 替代 `reghdfe`
  - ✅ 用 `_pctile` 手动缩尾替代 `winsor2`
  - ✅ 手动计算 Sobel Z 值替代 `sgmediation`
  - 仅 `estout` 为唯一推荐的 ssc 包（用于表格输出，非必需）
- 所有 .do 文件 UTF-8 编码

---

## 快速入口（跳转）

从数据清洗阶段开始：
- 确认数据文件路径
- 确认 Y/D 变量定义

从基准回归开始：
- 确认清洗后 .dta 路径
- 确认模型设定和核心变量