# PaperPilot 6.0 升级计划 — 任务清单

## 命名变更总览

| 项目 | 旧值 | 新值 |
|------|------|------|
| 项目名 | economic-paper-pipeline | paperpilot |
| 显示名 | 论文助手 | PaperPilot |
| Python 包名 | economic_paper_pipeline | paperpilot |
| CLI 命令 | epp | pp |
| 版本 | 5.0.0a1 | 6.0.0a1 |
| 分支 | feat/paper-assistant-v5 | feat/paperpilot-v6 |

## 任务清单

### 阶段 A：命名重构（先改名，保持功能不变）

- [ ] A1. 创建开发分支 `feat/paperpilot-v6`
- [ ] A2. `scripts/__init__.py` — 版本改为 `6.0.0a1`
- [ ] A3. `pyproject.toml` — 包名 `paperpilot`，CLI 入口 `pp`，描述更新
- [ ] A4. `.claude-plugin/plugin.json` — name/version/description 更新
- [ ] A5. `scripts/pipeline.py` — help 输出中 `epp` → `pp`
- [ ] A6. 测试文件中所有 `epp` 引用更新
- [ ] A7. `SKILL.md` — 标题、版本、CLI 示例全部改为 PaperPilot / pp
- [ ] A8. `AGENT_INSTALL.md` — 项目名和命令更新
- [ ] A9. `adapters/*.md` — 项目名更新
- [ ] A10. `.github/workflows/ci.yml` — 如有项目名引用则更新
- [ ] A11. 运行全量测试，确认 58 tests 全绿
- [ ] A12. 提交："chore: rename to PaperPilot, CLI epp → pp, version 6.0.0a1"

### 阶段 B：Skills 包架构 (M6)

- [ ] B1. 创建 `skills/` 目录结构：
  ```
  skills/
  ├── paper-agent/SKILL.md          ← meta-skill (编排)
  ├── topic-explorer/SKILL.md       ← 选题探索
  ├── literature-survey/SKILL.md    ← 文献调研
  ├── data-collector/SKILL.md       ← 数据搜集与清洗
  ├── empirical-analysis/SKILL.md   ← 实证分析 (可选)
  ├── paper-writer/SKILL.md         ← 论文写作
  └── integrity-auditor/SKILL.md    ← 审查
  ```
- [ ] B2. 编写 `paper-agent/SKILL.md` — meta-skill 编排协议
- [ ] B3. 编写每个子 skill 的 `SKILL.md`（从现有 CLAUDE.md 8 能力拆分）
- [ ] B4. 定义 skill 间路径约定：`output/<skill>/<project>/latest/`
- [ ] B5. 定义 `agent_guide` 输出 schema（M9 同步完成）
- [ ] B6. 重写 `CLAUDE.md` — 精简为加载入口 + paper-agent 引用
- [ ] B7. 重写 `README.md` — 反映新架构、新名称、新 CLI
- [ ] B8. 更新根目录 `SKILL.md` 为项目级 manifest（指向 skills/ 子目录）
- [ ] B9. 运行全量测试确认不破坏现有功能
- [ ] B10. 提交："feat(m6): skills package architecture with paper-agent meta-skill"

### 阶段 C：Agent Guide 接口 (M9)

- [ ] C1. 在 `scripts/skill_guide.py` 实现 `get_agent_guide()` 函数
- [ ] C2. 每个 skill SKILL.md 中定义 `## Agent Guide Output` 节
- [ ] C3. workflow.py 的 `commit_result` 和 `verify` 自动附带 guide 输出
- [ ] C4. 测试：skill 执行后返回 next_steps + warnings + install_hints
- [ ] C5. 提交："feat(m9): agent guide interface — structured next-step recommendations"

### 阶段 D：引用验证增强 (M8)

- [ ] D1. 实现 `scripts/citation_verify.py` — OpenAlex title 搜索 + DOI 验证
- [ ] D2. 实现 Semantic Scholar API 作为可选增强
- [ ] D3. 支持批量 .bib 验证 → JSON 报告
- [ ] D4. 集成到 `integrity-auditor` skill
- [ ] D5. 测试：mock API 验证逻辑 + 真实 API smoke test（可选跳过）
- [ ] D6. 提交："feat(m8): citation verification via OpenAlex and Semantic Scholar"

### 阶段 E：实证分析解耦 (M7)

- [ ] E1. `empirical-analysis/SKILL.md` 分为引导层 + 后端层
- [ ] E2. 编写 `empirical-analysis/INSTALL_GUIDE.md` — 按需安装指引
- [ ] E3. 安装档位拆分：core（无实证）/ builtin / diff-diff / statspai
- [ ] E4. `pyproject.toml` optional-dependencies 调整
- [ ] E5. bootstrap.py 更新档位检测逻辑
- [ ] E6. 测试：无实证依赖时 skill 加载不报错，纯引导模式可用
- [ ] E7. 提交："feat(m7): decouple empirical analysis as optional skill"

### 阶段 F：收尾

- [ ] F1. 全量测试 (所有 OS)
- [ ] F2. 更新 docs/UPGRADE_PLAN_V6.md 标记完成
- [ ] F3. 推送分支，创建 PR
