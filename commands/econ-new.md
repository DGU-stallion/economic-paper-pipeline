---
name: econ-new
description: 创建新的论文项目
---

当用户输入 `/econ-new <项目名>` 时：
1. 调用 `python scripts/pipeline.py new <项目名>`
2. 切换到新项目
3. 告知用户已进入选题研究阶段
4. 开始引导 5W1H 对话

如果未提供项目名，追问用户。
