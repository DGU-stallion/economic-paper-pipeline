# 经济学实证论文工作流 - Skill 原子化架构

## 架构总览

原有的单体 `CLAUDE.md` 已拆分为 **1 个协调器 + 4 个原子化子 Skill**：

```
┌─────────────────────────────────────────────────────────┐
│           skills/coordinator (协调器, 主入口)              │
│  - 多项目生命周期管理                                      │
│  - 自然语言意图识别                                        │
│  - 子 Skill 路由切换                                      │
│  - 跨 Skill 上下文传递                                     │
│  - 工作流状态维护                                          │
└────────────┬───────────┬───────────┬───────────────────┘
             │           │           │
    ┌────────┘   ┌───────┘   ┌───────┘
    ▼              ▼            ▼
┌───────────┐ ┌──────────┐ ┌───────────┐
│skills/topic│ │skill-    │ │skills/stata│ ┌────────────┐
│  选题研究  │ │literature│ │  实证分析  │ │skills/latex │
│  (Stage1) │ │  文献综述 │ │ (Stage3-6)│ │  论文写作  │
└───────────┘ │ (Stage2) │ └───────────┘ │ (Stage7)   │
              └──────────┘               └────────────┘
```

## 目录结构

```
economic-paper-pipeline/
├── skills/coordinator/              # 协调器 Skill（主入口）
│   ├── CLAUDE.md                   # 协调器定义文档
│   ├── skill.json                  # 元数据
│   ├── prompts/                    # 通用提示词
│   └── tools/
│       ├── context_manager.py      # 上下文管理
│       └── skill_router.py         # Skill 路由
│
├── skills/topic/                    # 选题研究 Skill
│   ├── CLAUDE.md                   # Skill 业务逻辑定义
│   ├── skill.json                  # 元数据（输入输出 schema）
│   ├── prompts/                    # 5W1H/Gap/SMART 提示词
│   └── tools/                      # 专用工具
│
├── skills/literature/               # 文献综述 Skill
│   ├── CLAUDE.md
│   ├── skill.json
│   ├── prompts/
│   └── tools/
│
├── skills/stata/                    # Stata 实证 Skill
│   ├── CLAUDE.md                   # 含数据/回归/稳健性/结论
│   ├── skill.json
│   ├── prompts/
│   └── tools/
│
├── skills/latex/                    # LaTeX 写作 Skill
│   ├── CLAUDE.md
│   ├── skill.json
│   ├── prompts/
│   └── tools/
│
├── shared/
│   └── interfaces/                 # 跨 Skill 接口规范
│       ├── topic_output.schema.json
│       ├── literature_output.schema.json
│       └── stata_output.schema.json
│
├── papers/<project-name>/          # 项目数据目录
│   └── pipeline_state.json         # 含 context_store 扩展字段
│
└── scripts/pipeline.py                     # 原有命令行工具（向后兼容）
```

## 设计原则

### 1. 单一职责
每个 Skill 只负责一个明确的业务领域：
- skills/topic: 只做选题推演，不碰实证代码
- skills/literature: 只做文献，不碰论文写作
- skills/stata: 只做实证分析，不碰选题确认
- skills/latex: 只做论文生成，不碰数据

### 2. 松耦合，高内聚
- Skill 之间不直接调用，通过协调器调度
- 所有数据传递通过 `context_store` 标准接口
- 每个 Skill 内部逻辑高度聚合

### 3. 标准接口
- 所有 Skill 输入输出严格遵循 JSON Schema
- Skill 可以独立升级、替换，不影响其他 Skill
- 向后兼容已有 scripts/pipeline.py

### 4. 可独立发布
每个 Skill 可以：
- 独立开发测试
- 独立版本迭代
- 独立打包发布
- 被其他项目复用

## Skill 间数据流

```
用户意图
   ↓
skills/coordinator 解析
   ↓
 路由到 skills/topic
   ↓ 输出（符合 topic_output.schema.json）
context_store["skills/topic"] = research_proposal
   ↓
 路由到 skills/literature
   ↓ 输入 = context_store["skills/topic"]
   ↓ 输出（符合 literature_output.schema.json）
context_store["skills/literature"] = literature_summary
   ↓
 路由到 skills/stata
   ↓ 输入 = context_store["skills/topic"] + ["skills/literature"]
   ↓ 输出（符合 stata_output.schema.json）
context_store["skills/stata"] = empirical_results
   ↓
 路由到 skills/latex
   ↓ 输入 = 所有前序 Skill 输出合并
   ↓ 输出 PDF 论文
```

## 协调器核心能力

### 1. 意图识别
通过 `skill_router.py` 解析用户自然语言，支持：
- 创建/切换/列出项目
- 推进阶段 / 跳转阶段
- 状态查询 / 重置项目
- 未知意图时追问澄清

### 2. 上下文管理
通过 `context_manager.py` 实现：
- 读取 Skill 所需的前序上下文
- 保存 Skill 输出到状态文件
- 断点续传（resume_point）支持

### 3. Skill 路由
- 根据 `pipeline_state.json` 的 `current_stage` 决定激活哪个 Skill
- 根据 `resume_point` 从中断位置继续
- Skill 完成后自动推进到下一阶段并切换 Skill

## 向后兼容策略

### scripts/pipeline.py 扩展
不修改原有代码，只在 `pipeline_state.json` 中新增字段：

```json
{
  "current_stage": 0,
  "history": [],
  // 以下为新增字段
  "context_store": {
    "skills/topic": {...},
    "skills/literature": {...},
    ...
  },
  "resume_point": {
    "skill": "skills/stata",
    "step": "data_cleaning",
    "partial_data": {}
  }
}
```

### 迁移路径
1. 已有项目继续正常工作
2. 新功能通过协调器 Skill 启用
3. 旧的单体 CLAUDE.md 可以保留作为参考

## Skill 开发规范

### 1. 必须包含的文件
```
skill-xxx/
├── CLAUDE.md          # Skill 完整行为定义（给 LLM 看的）
├── skill.json         # 元数据（给系统看的）
├── prompts/           # 提示词模板
└── tools/             # 辅助脚本（可选）
```

### 2. CLAUDE.md 必须包含
- Skill 定位（做什么，不做什么）
- 输入输出接口定义
- 工作流程分步骤说明
- 人机协作点（何时需要用户确认）
- 产出文件规范
- 快速入口（跳转时的前置检查清单）

### 3. skill.json 必须包含
- skill_id: 全局唯一标识
- stages_handled: 处理哪些阶段
- input_schema: 输入数据 Schema 路径
- output_schema: 输出数据 Schema 路径
- required_mcp: 依赖的 MCP 服务

## 新增 Skill 流程

1. 创建 `skill-xxx/` 目录
2. 编写 `CLAUDE.md` 定义 Skill 行为
3. 编写 `skill.json` 声明元数据
4. 在 `shared/interfaces/` 添加输入输出 Schema
5. 在 `skills/coordinator/skill.json` 的 `sub_skills` 中注册
6. 在 `skill_router.py` 中添加 `STAGE_TO_SKILL` 映射
7. 在 `context_manager.py` 中添加上下文合并逻辑

## 优势对比

| 维度 | 单体 CLAUDE.md | 原子化 Skill 架构 |
|------|----------------|-------------------|
| 可维护性 | ❌ 单文件上千行，难以修改 | ✅ 职责分离，模块化 |
| 可测试性 | ❌ 难以单独测试某阶段 | ✅ 每个 Skill 可独立测试 |
| 可复用性 | ❌ 只能整体使用 | ✅ 单个 Skill 可被其他项目复用 |
| 并行开发 | ❌ 多人编辑同一文件冲突 | ✅ 多人并行开发不同 Skill |
| 版本管理 | ❌ 整体版本号 | ✅ 每个 Skill 独立版本 |
| 出错影响 | ❌ 一处修改影响全局 | ✅ 错误隔离 |
| 向后兼容 | - | ✅ 完全兼容原有 scripts/pipeline.py |

## 使用方式

### 新工作流（推荐）
用户打开项目，直接与 `skills/coordinator` 对话，协调器自动：
1. 识别意图（创建/切换/继续）
2. 路由到对应子 Skill
3. 传递上下文数据
4. Skill 完成后自动推进

### 兼容工作流
用户仍然可以直接调用 `scripts/scripts/pipeline.py` 命令行工具：
```bash
python scripts/scripts/pipeline.py list
python scripts/scripts/pipeline.py new my-project
python scripts/scripts/pipeline.py status
```

## 下一步优化

1. ✅ 协调器和 4 个原子 Skill 框架
2. ✅ 接口规范 Schema
3. ☐ 完善 prompts/ 目录下的具体提示词
4. ☐ 实现各 Skill 专用工具函数
5. ☐ Skill 独立测试用例
6. ☐ Skill 版本管理工具
7. ☐ Skill 打包发布流程
