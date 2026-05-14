# 会话交接文档

> 最后更新：2026-05-12

## 一、项目概览

- **论文题目**：数字经济发展对省际就业结构的影响——基于面板门槛模型的实证研究
- **工作流阶段**：全部 7 阶段完成
- **方法**：双向固定效应 + 面板门槛模型 (Hansen 1999)
- **数据量**：31 省份 × 2011-2023 年 = 403 观测值

## 二、各阶段状态

| 阶段 | 状态 | 产出 |
|------|------|------|
| 1. 选题研究 | ✅ | `topics/00_research_proposal.md` |
| 2. 文献综述 | ✅ | `literature/literature_review.md` |
| 3. 数据获取与清洗 | ✅ | `data/clean/china_provincial_panel.dta` (403×16) |
| 4. Stata实证 | ✅ | 5 个 .do 文件 + 5 表 4 图 |
| 5. 稳健性检验 | ✅ | 6 项检验 |
| 6. 结论验证 | ✅ | `analysis/05_conclusion_validation.md` |
| 7. LaTeX论文 | ✅ | 完整论文 `.tex` 文件 |

## 三、论文文件清单

```
paper/
  main.tex                          # 主文件（元信息、摘要、结构）
  chinese-erj.cls                   # 《经济研究》格式模板
  erjref.bib                        # 参考文献库（22条，中英双语，≥50%来自2021-2026）
  sections/
    01_introduction.tex             # 引言 (~950 中文字)
    02_literature.tex               # 文献综述与理论假说 (~1650)
    03_model.tex                    # 模型设定、变量与数据 (~1600)
    04_empirical_results.tex        # 实证结果分析 (~1600)
    05_robustness.tex               # 稳健性检验 (~760)
    06_conclusion.tex               # 结论与政策建议 (~1800)
```

**总字数**: ~9000 中文字（含摘要），在 8000-12000 约束内。

## 四、核心实证发现

1. **H1 支持**: 数字经济显著提升三产就业占比（M6 β=0.277, p=0.003）
2. **H2 部分支持**: 城镇化门槛方向正确，但 Bootstrap 未通过（高组仅 3 省）
3. **H3 部分支持**: 中部>东部，西部不显著
4. **关键稳健性**: 替换 D→数字金融指数后不显著（广义数字经济 > 狭义金融科技）

## 五、已知局限

1. 7 个变量缺失（就业规模、失业率维度无法检验）
2. 内生性仅靠 FE 控制，无工具变量
3. 门槛模型统计效力不足
4. 中部异质性系数过大（1.781），标准误也大（0.707）

## 六、编译说明

论文使用本地 TeX Live 编译。在 `paper/` 目录下执行：

```bash
xelatex main.tex
biber main
xelatex main.tex
xelatex main.tex
```

需安装 TeX Live 及 `collection-langchinese` 和 `collection-bibtexextra` 宏包组。

## 七、后续可改进方向

1. 获取缺失的 7 个变量（就业规模、失业率、FDI、R&D 等）
2. 使用 Bartik IV 或 shift-share 工具变量处理内生性
3. 用地级市数据（N>3000）重新估计门槛模型
4. 利用"宽带中国"试点政策做 DID 自然实验
