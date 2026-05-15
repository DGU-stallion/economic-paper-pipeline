# 实证产出规范

## 必须产出的表格

| 编号 | 表格 | Stata 来源 | 保存位置 |
|------|------|-----------|---------|
| **T1** | 描述统计与组间平衡（处理 vs 控制，含 SMD/p 值） | `balancetable` + `asdoc sum` | `analysis/output/table1_balance.tex` |
| **T2** ★ | **基准回归——多列 M1→M6 渐进控制**（核心！） | `eststo` 6 个模型 → `esttab` | `analysis/output/table2_main.tex` |
| **T3** | 机制检验——同一处理变量，多个结果变量并列 | `eststo` 循环 → `esttab` | `analysis/output/table3_mechanism.tex` |
| **T4** | 异质性分析——子组 × 主系数 | 子组 `eststo` + `suest` Wald → `esttab` | `analysis/output/table4_heterogeneity.tex` |
| **T5** | 稳健性检验汇总——替代 SE/聚类/样本/安慰剂 | `eststo` × 变体 → `esttab` | `analysis/output/table5_robustness.tex` |

> **★ T2 是每篇经济学论文的核心。** 它是一张多列回归表，从原始相关（M1）逐步推进到完全设定的模型（M6）。不要把它缩减为单列。M1→M6 的稳定性本身就是识别有效性的论证。

## M1→M6 标准 6 列

```
M1: 原始双变量                     reg y treat
M2: +人口特征                      + age + edu
M3: +行业控制                      + tenure / firm_size
M4: +个体固定效应                   absorb(unit)
M5: +双向固定效应                   absorb(unit year)
M6: +交互固定效应 + 聚类标准误      absorb(unit year i.ind#i.year), vce(cluster unit)
```

## 必须产出的图形

| 编号 | 图形 | 说明 |
|------|------|------|
| **F1** | 趋势图——处理组 vs 控制组随时间变化 | `collapse (mean) y, by(year treat)` → `twoway line` |
| **F2** | 事件研究图——系数 + 95% CI | `eventstudyinteract` / `csdid` / `coefplot` |
| **F3** | 系数图——M1→M6 系数对比 | `coefplot m1-m6, keep(treat) vertical` |
| **F4** | 敏感性图——`bacondecomp` / `honestdid` / 聚类对比 | 按具体检验选择 |

## 文件命名

所有输出文件统一命名规则：

```
analysis/output/
  table1_balance.tex          # 描述统计
  table2_main.tex             # 基准回归
  table3_mechanism.tex        # 机制检验
  table4_heterogeneity.tex    # 异质性分析
  table5_robustness.tex       # 稳健性检验
  fig1_trend.pdf              # 趋势图
  fig2_event_study.pdf        # 事件研究图
  fig3_coefplot.pdf           # 系数图
  fig4_sensitivity.pdf        # 敏感性图
```

> 来源: [Awesome-Agent-Skills-for-Empirical-Research](https://github.com/brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research), skill 00.2
