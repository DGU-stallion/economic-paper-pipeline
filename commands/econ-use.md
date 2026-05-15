---
name: econ-use
description: 切换到指定项目
---

当用户输入 `/econ-use <项目名>` 时：
1. 调用 `python scripts/pipeline.py use <项目名>`
2. 确认切换成功
3. 展示目标项目的当前阶段和状态
