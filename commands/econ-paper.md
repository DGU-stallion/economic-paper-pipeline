---
name: econ-paper
description: 进入 LaTeX 论文撰写阶段
---

当用户输入 `/econ-paper` 时：
1. 调用 `python scripts/pipeline.py jump paper`
2. 确认论文偏好（模板、字数、参考文献格式、语言）
3. 自动生成章节内容并注入表格和图片
4. 告知用户编译方式（本地 xelatex 或 Overleaf 上传）
