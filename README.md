# PaperPilot

> Agent skills for academic research — from topic exploration to publication.

PaperPilot 是一套以 Skills 形式运行于 Claude Code、Codex、Kiro、Cursor 等通用 Coding Agent 的科研协作系统。它不是一个独立 Agent，而是赋能已有 Agent 的技能包。

[![Version](https://img.shields.io/badge/version-6.0.0a1-blue)](https://github.com/DGU-stallion/economic-paper-pipeline)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![CI](https://github.com/DGU-stallion/economic-paper-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/DGU-stallion/economic-paper-pipeline/actions)

---

## 一句话安装

将这段话复制给你的 Coding Agent：

```text
请为我安装 PaperPilot：https://github.com/DGU-stallion/economic-paper-pipeline
读取 AGENT_INSTALL.md 完成安装，然后检查我的论文状态，告诉我下一步该做什么。
```

## Skills 架构

```
[paper-agent]  ← 元技能：诊断 + 编排 + 推荐
   │
   ├── topic-explorer        选题探索 (5W1H → 研究问题)
   ├── literature-survey     文献调研 (搜索 → 综述 → .bib)
   ├── data-collector        数据搜集 (获取 → 清洗 → 验证)
   ├── empirical-analysis    实证分析 (FE/DID/IV/RDD, 可选)
   ├── paper-writer          论文写作 (LaTeX 全文生成)
   └── integrity-auditor     审查 (引用验证 + 数字一致性)
```

每个 skill 是一个自给自足的 `SKILL.md`，可独立使用，也可由 paper-agent 编排。

## 核心特点

- **Skills 而非 Agent** — 不需要定制化 Agent 开发，赋能任何通用 Coding Agent
- **按需安装** — 核心文本技能零依赖，实证分析按需追加
- **证据状态追踪** — planned / user_supplied / executed / verified 四态严格区分
- **跨 Agent 通用** — Claude Code、Codex、Kiro、Cursor 共享同一状态，无需聊天记录即可切换
- **中文第一** — 面向中文经济学与社会科学研究者

## 快速开始

### AI Skill 加载（推荐）

```bash
git clone https://github.com/DGU-stallion/economic-paper-pipeline.git
cd economic-paper-pipeline
# Agent 自动读取 CLAUDE.md
```

然后用自然语言：
```
"我想研究数字经济对就业的影响"
```

### 安装实证分析能力（可选）

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[standard]"    # FE + DID
.venv/bin/pip install diff-diff            # Staggered DID (可选)
```

### CLI 使用

```bash
pp doctor --json           # 环境诊断
pp inspect . --json        # 论文状态
pp workflow plan analyze   # 计划实证
pp help                    # 命令列表
```

## 项目结构

```
paperpilot/
├── CLAUDE.md                 # Agent 加载入口 (paper-agent 行为规范)
├── SKILL.md                  # 项目级 skill manifest
├── AGENT_INSTALL.md          # 安装契约
│
├── skills/                   # 技能包
│   ├── paper-agent/          #   元技能 (编排)
│   ├── topic-explorer/       #   选题探索
│   ├── literature-survey/    #   文献调研
│   ├── data-collector/       #   数据搜集
│   ├── empirical-analysis/   #   实证分析 (可选)
│   ├── paper-writer/         #   论文写作
│   └── integrity-auditor/    #   审查
│
├── scripts/                  # Python 后端
│   ├── pipeline.py           #   CLI: pp <command>
│   ├── workflow.py           #   plan → commit → verify
│   ├── paper_state.py        #   7 维度状态扫描
│   ├── agent_caps.py         #   能力声明
│   ├── backends/             #   分析引擎
│   └── modules/              #   模块实现
│
├── papers/                   # 论文项目
│   └── <project>/
│       ├── pipeline_state.json
│       ├── topics/  literature/  data/  analysis/  paper/  audit/
│       └── .revisions/
│
├── adapters/                 # Agent 薄适配器
├── tests/                    # pytest (58 tests, 3 OS × 3 Python)
└── .github/workflows/ci.yml  # CI
```

## 开发

```bash
python3 -m pytest tests/ -v       # 运行测试
pp doctor --json                   # 检查环境
```

详见 [docs/UPGRADE_PLAN_V6.md](docs/UPGRADE_PLAN_V6.md)。

## 许可证

MIT License. 详见 [LICENSE](LICENSE).
