---
name: econ-status
description: 查看当前激活项目的进度和所处阶段
---

当用户输入 `/econ-status` 时：
1. 调用 `python scripts/pipeline.py status`
2. 将输出转化为友好的自然语言
3. 展示当前阶段、完成进度、下一步操作建议
4. 如无激活项目，提示用 `/econ-new` 创建或 `/econ-list` 查看已有项目
