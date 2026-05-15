---
name: econ-stata
description: 进入 Stata 实证回归阶段
---

当用户输入 `/econ-stata` 时：
1. 调用 `python scripts/pipeline.py jump stata`
2. 确认清洗后 .dta 路径、模型设定、核心变量
3. 执行基准回归（M1→M6 渐进控制）
4. 自动提取关键系数，一句话总结结果
