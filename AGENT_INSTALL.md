# 论文助手 Agent 安装契约

本文档供 Claude Code、Codex、Kiro、Cursor、OpenCode 等 Coding Agent 执行。用户不应被要求手动完成 Agent 可以安全完成的命令。

## 安全边界

1. 默认只在当前项目目录内操作，并使用隔离虚拟环境 `.venv`。
2. 不要上传用户的论文、原始数据、清洗数据、密钥或本地路径。
3. 不要把 API Key 写入仓库、日志或示例文件。
4. 安装 TeX Live、R、Stata、Node 等大型或系统级软件前必须说明体积、用途和替代方案，并获得用户确认。
5. 不要静默修改 Agent 的全局配置；优先使用仓库级配置。
6. 检测行为不得隐式下载 MCP 或启动长期后台进程。

## 标准安装流程

### 1. 获取仓库

如果当前目录不是论文助手仓库，克隆：

```bash
git clone https://github.com/DGU-stallion/economic-paper-pipeline.git
cd economic-paper-pipeline
```

如果仓库已存在，先检查工作区；不要覆盖用户未提交的修改。

### 2. 运行无修改诊断

```bash
python3 install/bootstrap.py --check --profile standard --json
```

读取 JSON 中的 `status`、`capabilities` 和 `recommendations`。不要仅根据命令退出码宣称所有能力均已就绪。

### 3. 安装 Standard 环境

Standard 是默认档位，包含 pandas 数据处理、Excel/Parquet 和 PanelOLS/DID 分析能力。

macOS/Linux：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r install/requirements-standard.txt
```

Windows PowerShell：

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r install\requirements-standard.txt
```

Lite 档位可以跳过第三方分析依赖。Full 档位中的 TeX Live、R、Stata 和额外 MCP 必须单独征得用户同意。

### 4. 重新诊断

使用虚拟环境中的 Python 再次运行：

```bash
.venv/bin/python install/bootstrap.py --check --profile standard --json
```

Windows 使用 `.venv\Scripts\python`。

### 5. 加载 Skill

把仓库根目录作为论文助手工作目录，读取 `CLAUDE.md` 了解当前能力契约。不同 Agent 的专属薄适配器将在 `adapters/` 中提供；缺少专属适配器时，使用仓库文档和 Python CLI，不要猜测不存在的命令。

### 6. 验证和报告

至少运行：

```bash
.venv/bin/python -m unittest tests/test_bootstrap.py -v
```

向用户报告：

- 安装档位和仓库路径；
- 已启用能力；
- 未启用能力及影响；
- 是否使用宿主 Agent 搜索；
- 是否配置了外部 MCP/API；
- 测试结果；
- 推荐的第一步：运行 Demo、创建新论文或导入已有论文。

不要把“脚本运行成功”表述为“全部研究能力可用”；以 Doctor 的能力矩阵为准。
