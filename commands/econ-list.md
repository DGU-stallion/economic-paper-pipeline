---
name: econ-list
description: 列出所有论文项目及其进度
---

用户说"我有哪些项目"时：
1. 扫描 `papers/` 目录下的子目录
2. 读取每个项目的 `pipeline_state.json`（如存在）
3. 展示表格：项目名、当前阶段、完成阶段数

无 Python 后端：扫描目录结构（若可访问）或让用户手动告知。
