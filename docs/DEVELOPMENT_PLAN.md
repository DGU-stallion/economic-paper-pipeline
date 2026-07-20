# 论文助手 5.0 开发计划

## 目标

将现有经济学实证论文工作流升级为“论文助手”：一套运行于 Claude Code、Codex、Kiro、Cursor、OpenCode 等 Coding Agent 的主动式研究协作 Skill。

用户应能从 GitHub README 复制一段自然语言给自己的 Agent，由 Agent 完成安装、环境诊断、能力配置和 Demo 验证。安装后，论文助手能够读取现有项目证据，判断论文各维度的完成度、阻塞项和风险，并推荐或执行下一最佳行动。

## 开发纪律

1. 每个里程碑开始前明确范围、非目标和验收标准。
2. 先为缺陷或新行为建立失败测试，再做最小实现。
3. 只修改当前里程碑需要的文件，不顺带重构。
4. 不新增非必要依赖；新增依赖必须锁定版本并说明理由。
5. 每个里程碑完成后运行相关测试、检查 diff、独立提交并推送功能分支。
6. 不直接推送 `main`；当前开发分支为 `feat/paper-assistant-v5`。
7. 用户数据默认 local-first；联网、安装系统软件和数据外发必须有明确边界。
8. LLM 草稿、用户提供结果和真实执行结果必须具有不同的证据状态。

## 里程碑 1：Agent 一句话安装与环境诊断

### 范围

- 重写 README 首屏产品定位和可复制安装 Prompt。
- 增加 `AGENT_INSTALL.md`，作为 Agent 安装契约。
- 增加仅依赖 Python 标准库的 bootstrap/doctor。
- 检测 Python、分析依赖、搜索能力、TeX Live 和 Agent 类型。
- 输出稳定的 JSON 安装/诊断报告，不静默安装大型系统软件。

### 非目标

- 本阶段不重构分析后端。
- 不自动安装 TeX Live、Stata、R 等大型系统软件。
- 不承诺所有 Agent 的专属安装适配。

### 验收

- README 中的 Prompt 可独立指导 Agent 找到安装契约。
- `python3 install/bootstrap.py --check --json` 在无第三方依赖时可运行。
- Doctor 清晰区分必需、推荐、可选和不可用能力。
- 缺少可选能力时退出正常并提供修复建议。
- 安装相关测试通过。

## 里程碑 2：可安装核心与真实测试

### 范围

- 增加标准 Python 包元数据、统一版本源和 `epp` CLI。
- 修复 Data、Analyze、Verify、Write 模块损坏的 CLI 入口。
- 用隔离临时目录重写测试。
- FE、DID 和 LaTeX 测试必须执行真实行为。
- 统一错误退出码和基础 JSON envelope。

### 非目标

- 不增加新的计量模型。
- 不在本阶段完成完整工作流引擎。

### 验收

- 干净虚拟环境可以安装并运行 `epp doctor`。
- 八个模块的 `--help` 均返回 0。
- FE/DID 测试读取 fixture 并断言结果与产物。
- 测试不修改仓库中的当前项目或用户数据。

## 里程碑 3：论文状态智能

### 范围

- 引入版本化论文状态 schema。
- 扫描研究问题、文献、数据、识别、实证、写作和复现证据。
- 生成 readiness、blockers、unknowns 和 next actions。
- 支持导入已有论文项目并重建状态。
- 增加保守、协作、自动推进三种主动等级。

### 非目标

- readiness 不使用未经验证的复杂模型。
- 不根据文件名直接宣称研究任务已经完成。

### 验收

- 状态判断基于实际文件或结构化 context 证据。
- 缺失、空值和 placeholder 不计为完成。
- 同一项目重复扫描得到确定性结果。
- 输出 2—3 个带理由和前置条件的下一行动。

## 里程碑 4：工作流执行闭环

### 范围

- 实现统一 `plan → run → commit` 生命周期。
- 接通模块输入验证、context patch、artifact 登记和合法状态转换。
- 增加中断恢复、原子状态保存和完整 revision undo。
- 明确 `planned`、`user_supplied`、`executed`、`verified` 证据状态。

### 非目标

- 不一次性自动化所有 LLM 驱动内容。
- 不让 LLM 模板冒充真实实证结果。

### 验收

- 缺失输入时不能推进，错误包含可执行修复建议。
- 模块成功且产物验证后才更新状态。
- 非法状态和工作区外路径被拒绝。
- 中断后能够从上一稳定 revision 恢复。

## 里程碑 5：跨 Agent 适配与黄金路径

### 范围

- 增加 Agent-neutral Skill manifest 和 `SKILL.md`。
- 提供 Claude Code、Codex、Kiro 的首批薄适配器。
- 宿主 Agent 显式声明 WebSearch、MCP 等能力。
- 打通“选题验证 → 文献 → 数据 → FE → 稳健性 → 写作 → PDF”黄金路径。

### 非目标

- Agent 适配器不得复制核心研究逻辑。
- 未实现的 IV、RDD 等模型不得标记为可用。

### 验收

- 三类 Agent 使用同一核心状态和 artifact schema。
- 不具备专有 Skill 机制的 Agent 可通过 CLI 协议使用。
- Agent 切换后无需原始聊天记录即可继续。
- 黄金路径在 CI 或可重复本地环境中通过。

## 最终发布门禁

- README 示例均经过自动验证。
- 版本、Python 要求、依赖和能力矩阵只有一个事实源。
- 所有随机过程记录 seed。
- 正式论文不得包含未标记 placeholder。
- 每条引用和实证数字均有验证状态与 provenance。
- macOS、Linux、Windows 至少完成安装和核心 Smoke Test。
- 功能分支通过完整测试后再创建 PR，不直接推送 `main`。
