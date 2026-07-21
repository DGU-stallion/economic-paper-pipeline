# 实证分析技能 — 按需安装指引

## 何时需要安装

当你或 Agent 提到以下需求时，需要安装实证分析依赖：

- "跑回归" / "做实证" / "run regression"
- "DID" / "双重差分"
- "工具变量" / "IV"
- "断点回归" / "RDD"
- "面板固定效应" / "FE"
- "稳健性检验"

## 安装档位

### Tier 1: builtin（推荐起步）

内置面板固定效应 + DID + 门槛回归 + 稳健性检验。

```bash
pip install paperpilot[standard]
```

包含：numpy, pandas, statsmodels, linearmodels, openpyxl, pyarrow

### Tier 2: diff-diff（现代 DID）

Callaway-Sant'Anna, Staggered DID, Synthetic DID, Honest DID, Event Studies。

```bash
pip install diff-diff
```

适用场景：政策评估、渐进式处理效应、平行趋势检验。

### Tier 3: statspai（完整因果推断）

IV, RDD, Synthetic Control, Double ML, 以及 R/Stata 对照验证。

```bash
pip install statspai
```

适用场景：需要工具变量、断点回归或合成控制法的研究设计。

## Agent 检测逻辑

Agent 应按以下逻辑判断是否需要安装：

```python
from scripts.agent_caps import detect_local_capabilities

caps = detect_local_capabilities()
if not caps["python_analysis"]:
    # 引导安装 Tier 1
    print("实证分析需要安装依赖：pip install paperpilot[standard]")
```

如果用户的识别策略超出 builtin 范围：

| 识别策略 | 所需 Tier |
|----------|-----------|
| FE（固定效应） | builtin |
| DID（简单交互项） | builtin |
| Threshold（门槛回归） | builtin |
| Staggered DID | diff-diff |
| Synthetic DID | diff-diff |
| IV（工具变量） | statspai |
| RDD（断点回归） | statspai |
| Synthetic Control | statspai |
| Double ML | statspai |

## 不安装时的行为

- empirical-analysis skill 仍可加载
- 以纯引导模式工作：帮助用户设计模型规格、写 Stata/R do-file 模板
- 所有引导产出标记为 `planned`（非 `executed`）
- 用户如果在外部工具执行后可手动提供结果，标记为 `user_supplied`
