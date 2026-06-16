---
name: econ-status
description: 查看当前项目进度和上下文
---

用户说"进展到哪了"时：
1. 加载当前项目的 pipeline_state.json（如存在）
2. 展示：当前阶段、已完成阶段列表、context_store 关键字段
3. 无文件 → 从对话记忆获取状态
4. 一句话总结当前能做什么、缺什么
