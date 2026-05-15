---
name: econ-topic
description: 进入选题研究阶段（5W1H → Gap Analysis → SMART）
---

当用户输入 `/econ-topic` 时：
1. 调用 `python scripts/pipeline.py jump topic`
2. 开始 5W1H 逐维引导对话（What → Why → Who → When → Where → How）
3. 每次只问一个维度，用户回答后再问下一个
