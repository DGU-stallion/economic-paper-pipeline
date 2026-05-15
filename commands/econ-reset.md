---
name: econ-reset
description: 重置当前项目（需二次确认）
---

当用户输入 `/econ-reset` 时：
1. 首先确认用户是否真的要重置：**"确定要重置「项目名」吗？这将清除所有进度，不可恢复。"**
2. 用户确认后，调用 `python scripts/pipeline.py reset`
3. 项目回到选题研究阶段
