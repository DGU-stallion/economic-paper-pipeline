# 论文助手安装与配置

论文助手的推荐入口是：从 README 复制安装 Prompt 给 Coding Agent，由 Agent 按 [`AGENT_INSTALL.md`](AGENT_INSTALL.md) 完成检测、安装和验证。

## 安装档位

| 档位 | 用途 | 环境 |
|------|------|------|
| Lite | 选题、研究设计、文献和写作协作 | Python 3.11+ |
| Standard | 默认；增加数据处理、FE、DID 和稳健性分析 | Lite + 锁定的 Python 分析依赖 |
| Full | 增加本地 LaTeX、可选 R/Stata/MCP | Standard + 经用户确认的系统软件 |

TeX Live、R、Stata、Node 和第三方 MCP 都不是 Standard 的静默安装项。

## Agent 安装

把 README 的“一句话安装”Prompt 发给 Claude Code、Codex、Kiro、Cursor 或 OpenCode。Agent 应：

1. 获取或更新仓库，但不覆盖未提交修改；
2. 读取 `AGENT_INSTALL.md`；
3. 先运行无修改 Doctor；
4. 在仓库 `.venv` 中安装 Standard 依赖；
5. 再次运行 Doctor 和安装测试；
6. 报告已启用能力、未启用能力和原因。

## 高级用户手动安装

要求：Git 和 Python 3.11+。

```bash
git clone https://github.com/DGU-stallion/economic-paper-pipeline.git
cd economic-paper-pipeline
python3 install/bootstrap.py --check --profile standard
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r install/requirements-standard.txt
.venv/bin/python install/bootstrap.py --check --profile standard
.venv/bin/python tests/run_tests.py
```

Windows 将 `.venv/bin/python` 替换为 `.venv\Scripts\python`。

也可以从源码安装统一命令：

```bash
.venv/bin/python -m pip install ".[standard]"
.venv/bin/epp doctor --json
```

## Doctor 能力矩阵

```bash
python3 install/bootstrap.py --check --profile lite --json
python3 install/bootstrap.py --check --profile standard --json
python3 install/bootstrap.py --check --profile full --json
```

Doctor 只检测，不隐式下载 MCP、不启动后台进程，也不安装系统软件。`status=degraded` 表示某个当前档位的必需能力缺失；命令本身仍正常退出，以便 Agent 读取完整报告并修复。

## 搜索与 API Key

论文助手优先使用宿主 Agent 已明确声明的搜索能力。Tavily、paper-search MCP 等属于增强能力：

- 启用前说明将发送的查询内容；
- API Key 只通过环境变量或系统密钥存储；
- 不把论文、原始数据、清洗数据或密钥上传到搜索服务；
- 未启用时必须明确降级原因，不能假定 WebSearch 始终存在。

## LaTeX

Standard 可以生成 `.tex`，但本地 PDF 编译属于 Full 能力。没有 `xelatex` 和 `biber` 时可使用 Overleaf。安装完整 TeX Live 前，Agent 必须先说明下载体积和替代方案并获得确认。

## 更新

更新前先检查工作区，避免覆盖本地修改：

```bash
git status
git pull --ff-only
.venv/bin/python -m pip install -r install/requirements-standard.txt
.venv/bin/epp doctor --json
```

用户论文建议保存在独立私有仓库或通过 `EPP_PAPERS_DIR` 指向仓库外目录。

## 卸载

删除论文助手代码目录和其 `.venv` 即可。删除前先确认论文项目不在该目录中，或已完成备份。
