---
name: econ-list
description: 列出所有论文项目及其当前状态
---

当用户输入 `/econ-list` 时：
1. 调用 `python scripts/pipeline.py list`
2. 用表格展示所有项目：项目名、当前阶段、创建时间
3. 高亮当前激活的项目
