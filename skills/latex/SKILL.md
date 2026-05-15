---
name: "LaTeX 写作 Skill"
version: "1.0.0"
skill_id: "skill-latex"
description: "LaTeX 论文模板管理、分章节撰写、表格图片注入、编译输出"
stages_handled: [paper]
required_mcp: []
---

## Skill 定位

专门负责**学术论文的 LaTeX 模板管理、章节内容生成、表格图片注入、编译输出**。

**写作质量保证**：所有章节生成时调用 `agents/writer-agent.md` 控制文笔风格和论证逻辑，生成后通过 `references/writing-quality-standards.md` 执行质量检查。

**不负责**：选题、文献、实证分析（但使用其产出）

---

## 输入输出接口

### 输入 (来自协调器)

```json
{
  "project_name": "项目名称",
  "project_path": "papers/<project-name>/",
  "entry_point": "new|resume|jump",
  "template": "economic-research|qje|aer|<custom>",
  "topic_context": {
    "title": "",
    "abstract_chinese": "",
    "abstract_english": "",
    "keywords_chinese": []
  },
  "literature_context": {
    "review_content": "",
    "bib_path": "literature/references.bib"
  },
  "stata_context": {
    "tables_dir": "analysis/output/",
    "figures_dir": "analysis/output/",
    "empirical_summary": {}
  }
}
```

### 输出 (最终产物)

```json
{
  "status": "completed|needs_review",
  "stage": "paper",
  "paper_summary": {
    "word_count": 9800,
    "sections_completed": 6,
    "tables_injected": 5,
    "figures_injected": 4,
    "references_count": 45,
    "constraints_check": {
      "word_count_ok": true,
      "bilingual_refs_ok": true,
      "recency_ok": true
    }
  },
  "artifacts": {
    "source_files": [
      "paper/main.tex",
      "paper/sections/01_introduction.tex"
    ],
    "pdf_path": "paper/main.pdf"
  },
  "next_skill": null
}
```

---

## 工作流程

### Step 1: 模板选择与初始化

#### 模板库
```
templates/paper/
├── economic-research/        # 默认：《经济研究》
├── qje/                      # 《经济学季刊》
├── aer/                      # 美国经济评论
└── <user-custom>/            # 用户自定义
```

向用户确认模板选择后，将对应模板复制到 `papers/<project-name>/paper/`

---

### Step 2: 分章节自动撰写

按标准学术论文结构逐节生成：

#### 01_introduction.tex (引言)
- 研究背景与现实意义
- 研究问题提出
- 识别策略与数据说明
- 核心发现与贡献
- 论文结构安排

#### 02_literature.tex (文献综述)
- 基于 `literature` 产出自动转换为 LaTeX
- 三支文献脉络梳理
- 本文边际贡献定位

#### 03_institutional.tex (制度背景，如适用)
- 政策背景介绍
- 制度变迁说明

#### 04_data.tex (数据与变量)
- 数据来源说明
- 变量定义表格
- 描述性统计（注入 T1）

#### 05_empirical.tex (实证结果)
- 基准回归结果（注入 T2）
- 稳健性检验（注入 T4）
- 异质性分析（注入 T5）
- 机制/门槛分析（注入 T3/F1）

#### 06_conclusion.tex (结论与政策建议)
- 主要结论总结
- 政策含义
- 研究局限与展望

---

### Step 3: 表格与图片自动注入

#### 表格注入规则
1. 扫描 `analysis/output/*.tex` 找到所有生成的表格
2. 按 T1-T5 编号对应到论文章节
3. 自动生成 `\begin{table}` 环境
4. 添加正确的表注和标签

```latex
\begin{table}[htbp]
  \centering
  \caption{基准回归结果}
  \label{tab:baseline}
  \input{tables/table2_main.tex}
  \note{注：括号内为 t 值；* p<0.1, ** p<0.05, *** p<0.01}
\end{table}
```

#### 图片注入规则
1. 扫描 `analysis/output/*.pdf` 找到所有生成的图片
2. 按 F1-F4 编号对应到论文章节
3. 自动生成 `\begin{figure}` 环境

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.8\textwidth]{figures/fig1_threshold.pdf}
  \caption{门槛效应识别}
  \label{fig:threshold}
\end{figure}
```

---

### Step 4: 参考文献处理

- 将 `literature/references.bib` 复制到 `paper/erjref.bib`
- 按用户偏好检查（语言要求、参考文献格式等）

---

### Step 5: 用户偏好检查

检查 `papers/<项目名>/conversation.json` 中的用户偏好：

| 检查项 | 数据来源 | 不满足处理 |
|------|---------|----------|
| 字数 | `preferences.paper_word_count` | 提示扩写/精简 |
| 参考文献格式 | `preferences.paper_ref_style` | 按格式要求调整 |
| 语言要求 | `preferences.paper_lang_requirement` | 提示补充或调整 |
| 其他 | `preferences.paper_extra_requirements` | 按用户要求处理 |

---

### Step 6: LaTeX 编译

#### 编译流程（自动执行）：
```bash
xelatex main.tex    # 第 1 次
biber main           # 参考文献
xelatex main.tex    # 第 2 次
xelatex main.tex    # 第 3 次（交叉引用）
```

#### 编译选项：
- **本地编译**（推荐）：使用用户安装的 TeX Live
- **Overleaf**：生成打包文件，用户手动上传

---

## 人机协作点

✅ **需要用户审阅修改**：
1. 引言部分（研究动机和贡献）
2. 文献综述的学术表达
3. 实证结果的解释与讨论
4. 结论和政策建议

⚠️ **编译失败处理**：
- 显示具体错误信息
- 自动修复常见错误（缺少宏包、语法错误）
- 无法修复时提示用户手动修改

---

## 写作规范

### 中文经济学论文规范
- 使用 `chinese-erj.cls` 文档类
- 宋体正文，黑体标题
- 公式编号按章节：(1.1), (1.2)
- 表注在上，图注在下
- 参考文献按 GB/T 7714-2015 格式

### 写作纪律
- 每句话只表达一个信息点
- 避免空泛表述，多用具体数据
- 实证结果引用必须精确到系数和显著性
- 删除无信息量的套话

---

## 产出文件结构

```
papers/<project-name>/paper/
├── main.tex                    # 主文档
├── chinese-erj.cls             # 文档类
├── erjref.bib                  # 参考文献
├── sections/
│   ├── 01_introduction.tex
│   ├── 02_literature.tex
│   ├── 03_institutional.tex
│   ├── 04_data.tex
│   ├── 05_empirical.tex
│   └── 06_conclusion.tex
├── tables/
│   ├── table1_descriptive.tex
│   ├── table2_main.tex
│   ├── table3_threshold.tex
│   ├── table4_robustness.tex
│   └── table5_heterogeneity.tex
├── figures/
│   ├── fig1_threshold.pdf
│   ├── fig2_coefplot.pdf
│   ├── fig3_trend.pdf
│   └── fig4_heterogeneity.pdf
├── image/                      # 模板图片
└── main.pdf                    # 编译输出
```

---

## 快速入口（跳转）

如果用户直接从论文阶段开始，确认：
1. 所有表格 .tex 文件路径
2. 所有图片文件路径
3. 参考文献 .bib 路径
4. 模板选择