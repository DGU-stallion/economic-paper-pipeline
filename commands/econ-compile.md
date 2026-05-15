---
name: econ-compile
description: 本地编译 LaTeX 论文（xelatex × 3 + biber）
---

当用户输入 `/econ-compile` 时：
1. 确认当前在论文撰写阶段
2. 执行本地 LaTeX 编译：
   - xelatex main.tex（第 1 次）
   - biber main
   - xelatex main.tex（第 2 次）
   - xelatex main.tex（第 3 次）
3. 编译成功则告知 PDF 路径
4. 编译失败则显示具体错误并尝试修复
