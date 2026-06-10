# 经济学实证论文工作流 — 重构方案

版本: v2（模块化架构）
日期: 2026-06-10
状态: ✅ 全部完成

---

## 目录

1. [现状诊断](#1-现状诊断)
2. [设计原则](#2-设计原则)
3. [模块总览](#3-模块总览)
4. [模块详解](#4-模块详解)
5. [工作流编排](#5-工作流编排)
6. [文件结构](#6-文件结构)
7. [与现有代码的关系](#7-与现有代码的关系)
8. [迁移路径](#8-迁移路径)
9. [风险和不确定性](#9-风险和不确定性)
10. [决定日志](#10-决定日志)

---

## 1. 现状诊断

### 1.1 一个文件装六个职责

`scripts/pipeline.py`（2350 行）身兼：

| 职责 | 说明 |
|------|------|
| 状态定义 | 28 个 MICRO_STATES + 7 个阶段组 | 数据层 |
| 状态机引擎 | advance/jump/undo + 门禁检查 | 基础设施 |
| 选题业务 | 5W1H 引导、Gap 分析、SMART | 领域逻辑 |
| 文献业务 | 检索策略、筛选、综述撰写 | 领域逻辑 |
| Stata 业务 | do-file 模板渲染、Stata 调用、结果解析 | 领域逻辑 |
| LaTeX 业务 | 编译管线、引文修复、humanizer | 领域逻辑 |
| 项目管理 | new/use/list/status | 应用层 |
| 命令路由 | main() + 20+ cmd_* 函数 | 入口 |

业务逻辑和状态机混在一起，导致：
- 改选题话术要读 2350 行文件
- 新增模块要改 next_states 硬编码列表
- 无法独立运行某个功能（比如只跑文献综述）

### 1.2 按阶段切 vs 用户实际使用时按入口进

当前 28 个微状态假设用户从 topic-init 走完整条链。但用户实际场景是：

- "我有数据了直接跑回归" → 跳过 topic/literature/data
- "帮我写论文" → 只进 paper 阶段
- "扫一下文献" → 只进 literature 阶段
- "查一下这个数据能不能拿到" → 现在没入口

### 1.3 两个脆弱点

- **next_states 硬编码**：新增/插入状态需要修改列表
- **context_store 松散 dict**：`ctx.get("y_var", "")` 不报错不校验

---

## 2. 设计原则

### 2.1 模块边界按用户入口切，不按论文阶段切

```
❌ 按阶段: topic → literature → data → stata → robustness → conclusion → paper
   ↑ 这是论文写作流程，不是用户的使用入口

✅ 按入口: Conceptualize / Research / Literature / Data / Analyze / Verify / Write / Format
   ↑ 每个模块对应"用户手里有什么 → 用户想要什么"
```

### 2.2 每个模块有明确的 I/O 契约

模块 A 不依赖模块 B 的内部实现。只依赖 context_store 中的字段。契约声明在 `MODULE_CONTRACT` 中。

### 2.3 模块可独立运行（通过 \_\_main\_\_.py）

每个模块可以用 `python -m scripts.modules.<name>` 独立启动，**不依赖项目状态**。支持三种运行模式：

| 模式 | 说明 | 场景 |
|------|------|------|
| 引导模式 (Guided) | 逐步对话，每步确认 | 概念助手、新手用户 |
| 批处理模式 (Batch) | 自动执行，返回结果 | 分析助手、验证助手 |
| 点用模式 (Spot) | 不绑定项目状态，临时调用 | "帮我查个数据能否拿到" |

### 2.4 编排器不做业务逻辑

编排器只做：生命周期管理、模块路由、上下文传递、门禁验证。不包含任何阶段业务逻辑。

---

## 3. 模块总览

```
                       用户想法 / 一句话
                            │
                            ▼
                   ┌────────────────────┐
                   │   概念助手          │
                   │  (Conceptualize)    │
                   │                    │
                   │ 5W1H → Gap → SMART │
                   │ → 假说推演 → 方案   │
                   │                    │
                   │ 产出: Y/D/假设/方案 │
                   └────────┬───────────┘
                            │ 拿到方案
                            ▼
          ┌─────────────────────────────────┐
          │     调研助手 (Research)           │  ← 重新定义
          │    "所有从网络上找的工作"          │
          │                                  │
          │  依赖 web-access 作为浏览引擎     │
          │  并行搜索论文 + 数据源             │
          │                                  │
          │  ├─ 产出: 候选论文列表（摘要）     │
          │  └─ 产出: 数据源报告（变量/获取）  │
          └────────┬───────────┬─────────────┘
                   │           │
     ┌─────────────┘           └─────────────┐
     ▼                                       ▼
┌──────────────────┐              ┌──────────────────────┐
│ 文献助手           │              │ 数据助手              │
│ (Literature)      │              │ (Data)               │
│                   │              │                      │
│ "处理搜回来的论文" │              │ "处理拿到的数据"       │
│                   │              │                      │
│ 筛选 → 脉络梳理    │              │ 清洗 → 验证            │
│ → 综述 → .bib     │              │ → 描述性统计           │
│                   │              │                      │
│ 产出: 综述 + .bib │              │ 产出: 清洗后 .dta     │
└────────┬──────────┘              └──────────┬───────────┘
         │                                     │
         ▼                                     ▼
   ┌──────────────────────┐        ┌──────────────────────┐
   │ 论文助手 (Write)      │        │ 分析助手 (Analyze)    │
   │ 引言/文献综述章节     │        │ 回归 + 异质性         │
   │ 引用 .bib            │        │                      │
   └────────┬─────────────┘        └──────────┬───────────┘
            │                                 │
            └──────────┬──────────────────────┘
                       ▼
              ┌──────────────────┐
              │ 验证助手 (Verify) │
              │ 稳健性检验        │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ 格式助手 (Format) │
              │ 编译 → .pdf      │
              └──────────────────┘
```

### 3.1 模块清单

| # | 模块 | 用户场景 | 输入 | 输出 | 交互模式 | 依赖 |
|---|------|---------|------|------|---------|------|
| 1 | **Conceptualize** | "我有个想法，帮我理清" | 用户想法/一句话 | Y/D/假设/方案 | 引导 | 无 |
| 2 | **Research** (调研) | "帮我搜一下文献和数据" | 研究方案 | 候选论文列表 + 数据源报告 | 批处理 | web-access |
| 3 | **Literature** | "写一下文献综述" | 候选论文列表 | 综述 + .bib | 混合 | 无 |
| 4 | **Data** | "洗一下数据" | 原始 .csv/.dta | 清洗后 .dta + 报告 | 引导+批处理 | 无 |
| 5 | **Analyze** | "跑个回归" | 清洗后 .dta + 模型设定 | 回归表格 .tex | 批处理 | 无 |
| 6 | **Verify** | "结果稳不稳" | 基准结果 | 稳健性检验套件 | 批处理 | 无 |
| 7 | **Write** | "帮我写论文" | 回归表格 + 大纲 + 综述 | 完整 .tex | 混合 | 无 |
| 8 | **Format** | "编译一下" | .tex 源文件 | .pdf | 批处理 | TeX Live |

### 3.2 不覆盖的场景

| 场景 | 原因 |
|------|------|
| 理论模型论文（纯数学推导） | 不涉及数据/回归/稳健性 |
| 纯质性研究（访谈/田野） | 不同方法论体系 |
| 元分析 | 不同输入输出格式 |
| 非学术报告/政策简报 | 不同写作模板和输出格式 |

如果未来需要覆盖这些，Write 和 Format 模块可以直接复用，其余模块新增即可。

---

## 4. 模块详解

### 4.1 共享契约层（shared/contract.py）

每个模块通过 `ModuleContract` 声明 I/O 边界：

```python
@dataclass
class ModuleContract:
    name: str
    description: str

    # 这个模块消费的 context 字段
    consumes: Dict[str, FieldSpec]

    # 这个模块产出的 context 字段
    provides: Dict[str, FieldSpec]

    # 涉及的状态（可选，编排器用）
    states: List[str]

    # 独立运行入口
    entry_points: Dict[str, str]

    def validate_inputs(self, context: dict) -> List[str]:
        """检查 context 是否满足 consumes 要求"""
        ...

    def extract_outputs(self, context: dict) -> dict:
        """从 context 中提取本模块产出的字段"""
        ...
```

### 4.2 概念助手（conceptualize）

```
功能:
  从一个模糊的研究想法出发，通过结构化引导产出完整研究方案。

流程:
  5W1H 逐维讨论 → Gap 分析 → SMART 精确化 → 假说推演 → 研究方案

  5W1H 的 6 个维度:
  1. What  - 核心经济现象? Y/D 初步想法?
  2. Why   - 为什么重要? 理论贡献?
  3. Who   - 结论对谁有价值?
  4. When  - 时间跨度? 自然实验窗口?
  5. Where - 地理范围? 制度背景?
  6. How   - 识别策略? (OLS/FE/DID/IV/RDD)

交互方式:
  五个维度逐个讨论，中间允许回退。用户说"我们换一个方向"可以回到上一步。

产出:
  topics/01_research_proposal.md
  → 写入 context_store: research_question, y_var, d_var, identification, hypotheses
```

### 4.3 调研助手（research）— 新增

```
功能:
  负责"从网络上找"的所有工作。不限于数据可行性，也包括文献检索。
  核心原则：调研助手只负责找，不负责处理。找回来的东西交给对应的专业模块。

流程:
  1. 解析概念助手产出 → 提取搜索需求（研究问题、Y/D变量、关键词、时间窗口、地理范围）
  2. 使用 web-access 并行执行两条搜索线:
     ├─ 文献搜索线:
     │  - WebSearch + Google Scholar → 候选论文列表
     │  - Jina → 提取摘要和关键词
     │  - 并行分治: 多组关键词同时检索
     │  - 产出: paper_list (论文标题/作者/摘要/链接)
     │
     └─ 数据源搜索线:
        - WebSearch: 搜索可用数据集 (CFPS/CHFS/CGSS/上市公司数据库等)
        - CDP 浏览器: 登录数据发布平台官网，导航到变量列表
        - Jina: 提取数据说明文档的关键信息
        - 产出: data_source_report (数据集/变量覆盖/获取途径)
  3. 如果数据不可行 → 标记并建议回退概念助手

产出:
  两个独立的产出:
  ├─ literature/00_candidate_papers.md
  │  候选论文列表（供文献助手筛选处理）
  └─ data/00_research_report.md
     数据源可行性报告（供数据助手参考）

和 web-access 的集成:
  - 调研助手不自己实现 web 浏览能力
  - 运行时调用 web-access 的 CDP Proxy / WebSearch / 并行分治
  - 用户需要安装 web-access: npx skills add eze-is/web-access
  - 检测 web-access 是否可用，不可用则降级为仅 WebSearch/WebFetch

和文献助手的区别:
  ┌─────────────────┬───────────────────┬──────────────────┐
  │                 │ 调研助手           │ 文献助手          │
  ├─────────────────┼───────────────────┼──────────────────┤
  │ 职责             │ 找                 │ 处理             │
  │ 动作             │ 搜索 / 收集        │ 筛选 / 综合 / 写  │
  │ 依赖             │ web-access        │ LLM 分析能力     │
  │ 产出             │ 候选论文列表       │ 综述 + .bib      │
  │ 处理深度          │ 摘要级            │ 全文级            │
  └─────────────────┴───────────────────┴──────────────────┘
```

### 4.4 文献助手（literature）

```
功能:
  处理调研助手搜回来的候选论文，产出完整的文献综述。

流程:
  候选论文筛选 → 脉络梳理 → 综述撰写 → .bib 生成

  文献助手不做网络搜索，它只处理调研助手交给它的论文列表。
  如果用户自己已经有论文列表（跳过调研助手），也可以直接输入。

产出:
  literature/04_review_final.md
  paper/erjref.bib

输入 context_store:
  candidate_papers (从 research 来)
  research_question (从 conceptualize 来)

输出 context_store:
  total_papers, research_gap, key_theories
```

### 4.5 其余模块（data / analyze / verify / write / format）

保持与当前 `pipeline.py` 中业务逻辑一致，只做文件结构上的提取。

---

## 5. 工作流编排

### 5.1 编排器（orchestrator.py）

轻量状态机，不做业务逻辑：

```
orchestrator.py
├── ProjectManager      ← 项目 CRUD (new/use/list/status)
├── StateEngine         ← advance/jump/undo
├── ModuleRouter        ← 用户意图 → 模块
├── ContextValidator    ← consume/provide 字段校验
└── TransitionLogger    ← 状态转移历史
```

### 5.2 状态转移由契约推导，不再硬编码

当前 `next_states` 是写死的列表。改为：

```python
# shared/registry.py

modules = {
    "conceptualize": conceptualize.CONTRACT,
    "research":      research.CONTRACT,
    "literature":    literature.CONTRACT,
    "data":          data.CONTRACT,
    "analyze":       analyze.CONTRACT,
    "verify":        verify.CONTRACT,
    "write":         write.CONTRACT,
    "format":        format.CONTRACT,
}

def get_downstream(module_name: str) -> List[str]:
    """返回消费此模块产出的所有下游模块"""
    ...

def get_upstream(module_name: str) -> List[str]:
    """返回此模块依赖的所有上游模块"""
    ...
```

新增模块只需声明 consume/provide，编排器自动推导上下游依赖。

### 5.3 三种运行模式

**引导模式**（默认）:
```
用户: "我想写一篇关于最低工资的论文"
编排器: 创建项目 → 路由到 conceptualize
conceptualize: 启动 5W1H 对话，每步确认
→ 产出写入 context_store
→ 编排器标记 conceptualize 完成
→ 提示用户进入调研助手
```

**批处理模式**:
```
用户: "跑回归，用 AER 模板"
编排器: 检测 analyze 阶段上下文已就绪
analyze: 检查 context_store → ✅
analyze: 生成 do-file → 运行 Stata → 解析输出
编排器: 进入 verify → 执行 → 进入 write
```

**点用模式**:
```
用户: "不管项目，帮我搜一下 CFPS 2020 的文献和就业变量"
编排器: 检测到"点用"意图
research: 以临时上下文运行
research: 调用 web-access → 并行搜索论文 + 数据源 → 返回结果
编排器: 结果返回用户，不修改项目状态
```

---

## 6. 文件结构

```
economic-paper-pipeline/
├── CLAUDE.md                    ← Plugin 入口 + 使用说明
├── .claude-plugin/
│   └── plugin.json
│
├── scripts/
│   ├── pipeline.py              ← 向后兼容入口（调用 orchestrator）
│   ├── orchestrator.py          ← 编排器（状态机 + 模块路由）
│   ├── announce-plugin-loaded.sh← SessionStart 钩子
│   │
│   ├── shared/                  ← 共享层
│   │   ├── __init__.py
│   │   ├── contract.py          ← ModuleContract + FieldSpec
│   │   ├── registry.py          ← 模块注册 + 依赖推导
│   │   ├── state.py             ← pipeline_state.json 读写
│   │   └── paths.py             ← 文件路径约定
│   │
│   └── modules/                 ← 模块化业务逻辑
│       ├── __init__.py
│       ├── conceptualize/
│       │   ├── __init__.py      ← MODULE_CONTRACT
│       │   ├── __main__.py      ← 独立运行入口
│       │   ├── core.py          ← 5W1H 引导逻辑
│       │   └── templates/       ← 输出模板
│       │
│       ├── research/              ← 新增：调研助手
│       │   ├── __init__.py      ← MODULE_CONTRACT
│       │   ├── __main__.py      ← 独立运行入口
│       │   ├── core.py          ← 搜索调度 + 结果整理
│       │   ├── web_access.py    ← web-access 集成层
│       │   └── templates/       ← 候选论文列表/数据源报告模板
│       │
│       ├── literature/
│       │   ├── __init__.py
│       │   ├── __main__.py
│       │   ├── core.py          ← 检索 + 筛选 + 脉络梳理
│       │   └── templates/
│       │
│       ├── data/
│       │   ├── __init__.py
│       │   ├── __main__.py
│       │   ├── core.py          ← 诊断 + 清洗 + 验证
│       │   └── templates/       ← Stata 清洗模板
│       │
│       ├── analyze/
│       │   ├── __init__.py
│       │   ├── __main__.py
│       │   ├── core.py          ← 模型设定 + 回归 + 结果解析
│       │   └── templates/       ← Stata 回归模板
│       │
│       ├── verify/
│       │   ├── __init__.py
│       │   ├── __main__.py
│       │   ├── core.py          ← 稳健性检验套件
│       │   └── templates/
│       │
│       ├── write/
│       │   ├── __init__.py
│       │   ├── __main__.py
│       │   ├── core.py          ← 大纲 + 章节生成
│       │   └── templates/       ← LaTeX 章节模板
│       │
│       └── format/
│           ├── __init__.py
│           ├── __main__.py
│           ├── core.py          ← 编译管线
│           └── humanizer.py     ← AI 痕迹检测
│
├── commands/                    ← /econ-* 命令（保持不变）
├── hooks/                       ← 保持不变
├── papers/                      ← 用户项目（保持不变）
├── templates/                   ← 论文模板（保持不变）
├── tests/                       ← 测试
│   ├── test_contract.py
│   ├── test_orchestrator.py
│   └── modules/
│       ├── test_research.py
│       ├── test_conceptualize.py
│       └── test_analyze.py
│
└── docs/
    ├── REFACTORING_PLAN.md      ← 本文档
    └── MODULE_SPECS/            ← 各模块详细设计文档
```

---

## 7. 与现有代码的关系

### 7.1 保留不变

- `papers/` 目录结构
- `templates/` 论文模板
- `commands/` 命令文件
- `hooks/` 钩子配置
- `pipeline_state.json` 格式（向后兼容）

### 7.2 逐步替换

| 当前文件 | 替换方向 |
|---------|---------|
| `scripts/pipeline.py` | → orchestrator.py + modules/ |
| `scripts/memory.py` | → shared/state.py（整合 state 读写） |
| `scripts/announce-plugin-loaded.sh` | 保留，更新阶段推导逻辑 |
| `skills/coordinator/SKILL.md` | CLAUDE.md 直接接管协调职责 |
| `skills/topic/SKILL.md` | → modules/conceptualize/ |
| `skills/literature/SKILL.md` | → modules/literature/ |
| `skills/stata/SKILL.md` | → modules/analyze/ + verify/ |
| `skills/latex/SKILL.md` | → modules/write/ + format/ |

### 7.3 迁移期间的双轨运行

```
Phase 0-2:
  老: pipeline.py（不删，保持可用）
  新: modules/* + orchestrator.py（并行开发）

Phase 3-4:
  老 pipeline.py 逐渐瘦身 → 最终变为 orchestrator.py 的薄包装
  新模块完全就绪后，删除老 skills/
```

---

## 8. 迁移路径

### Phase 0：新建文件结构（不动老代码）

```
操作:
  1. 建 scripts/shared/ (contract.py, registry.py)
  2. 建 scripts/modules/ 目录
  3. 写 scripts/modules/research/ 作为第一个新模块
```

这一步不改 pipeline.py，不破坏现有功能。

### Phase 1：调研助手（research）作为第一个新模块

```
操作:
  1. 写 MODULE_CONTRACT
  2. 写 core.py（数据源路由 + 可行性判断逻辑）
  3. 写 web_access.py（web-access 集成层）
  4. 写 __main__.py（独立运行入口）
  5. 写 tests

验证:
  python -m scripts.modules.research \
    --research-question "最低工资对就业的影响" \
    --y employment --d min_wage
  → 输出数据可行性报告（最多用 web-access 搜数据源）
```

选择 research 作为第一个模块，因为它是纯新增，不依赖现有代码，风险最低。

### Phase 2：概念助手（conceptualize）

```
操作:
  1. 从 pipeline.py 提取 5W1H 相关的代码
  2. 写 MODULE_CONTRACT
  3. 写 __main__.py
  4. 写 tests

验证:
  python -m scripts.modules.conceptualize new
  → 独立运行选题对话，不依赖 pipeline.py
```

### Phase 3：编排器 + 其余模块

```
操作:
  1. 实现 orchestrator.py
  2. ModuleRegistry 用契约推导替代硬编码
  3. pipeline.py 改为 orchestrator.py 的薄包装
  4. 逐模块提取 literature / data / analyze / verify / write / format
```

### Phase 4：收尾

```
操作:
  1. 点用模式
  2. CLAUDE.md 更新
  3. 删除老 skills/ 目录
  4. 老 projects 的 pipeline_state.json 迁移
```

---

## 9. 风险和不确定性

### 9.1 已知风险

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| web-access 的 CDP Proxy 依赖 Node.js 22+ 和浏览器配置 | 中 | 降级策略：CDP 不可用时自动回退到 WebSearch/WebFetch |
| 用户没有安装 web-access | 中 | 模块启动时检测，提示安装（npx skills add ...），不影响其他模块 |
| 存量项目 pipeline_state.json 中的 old state ID（如 "topic-5w1h-what"）与新架构不兼容 | 低 | 写迁移脚本，将 old ID 映射到 module + state |
| 点用模式运行时，用户同时也在跑正式项目 | 低 | 点用模式不修改 pipeline_state.json，两套 context 隔离 |

### 9.2 尚未决定的设计问题

| 问题 | 当前立场 | 待决定 |
|------|---------|--------|
| 调研助手的数据源知识是内置规则还是 LLM 动态判断？ | LLM 动态判断（通用性强） | 是否需要为常见数据源（CFPS/CHFS）写特定的检索策略模版？ |
| 模块间通信的 context 存在哪？ | 沿用 pipeline_state.json 的 context_store | 是否需要引入 schema 版本控制？ |
| 每个模块的 "深度选择"（轻量/标准/深度）是否保留？ | 保留在老 pipeline.py 中 | 模块化后，深度选择放在模块内部还是编排器层面？ |

---

## 10. 决定日志

| 日期 | 决定 | 理由 |
|------|------|------|
| 2026-06-10 | 模块边界按用户入口切，不按论文阶段切 | 灵活入口是刚需 |
| 2026-06-10 | 新增调研助手（Research） | 搜索文献 + 数据源，web-access 作为浏览引擎 |
| 2026-06-10 | 调研助手与文献助手不合并，按"找 vs 处理"切分 | 找（research）依赖 web-access；处理（literature）依赖 LLM 分析 |
| 2026-06-10 | 调研助手依赖 web-access 作为浏览引擎 | 社科数据平台需登录态 + 动态页面操作 |
| 2026-06-10 | 调研助手和文献助手不合并 | 不同用户时刻、不同产出、不同下游消费 |
| 2026-06-10 | 采用模块化单体，不做微服务 | 单人工具不需要分布式系统复杂度 |
| 2026-06-10 | 编排器不做业务逻辑 | 保持轻量，只做路由和验证 |
| 2026-06-10 | 状态转移由契约推导，不硬编码 next_states | 新增模块不需要改现有代码 |
| 2026-06-10 | 概念助手不照搬 brainstorming 的一次一问 | 5W1H 框架本身就是结构化引导，不需要额外节奏 |
| 2026-06-10 | pipeline.py 重写为 orchestrator 的薄包装 | 后向兼容，旧命令继续工作 |
| 2026-06-10 | 8 模块模块化架构落地 | 契约驱动依赖，零校验警告 |
| 2026-06-10 | 重构全部 4 个 Phase 完成 | 2350 行单体 → 8 模块 + orchestator |
