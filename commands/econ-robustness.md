---
name: econ-robustness
description: 进入稳健性检验阶段
---

当用户输入 `/econ-robustness` 时：
1. 调用 `python scripts/pipeline.py jump robustness`
2. 自动生成 5 项稳健性检验策略
3. 执行检验并反馈异常结果
