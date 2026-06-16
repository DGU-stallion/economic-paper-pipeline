---
name: econ-reset
description: 重置当前项目到初始状态
---

用户说"从头开始"时：
1. 确认是否真的要重置（不可逆）
2. 确认后 → 清空 context_store + 状态回退到概念引导初始化
3. 有 Python 后端：更新 pipeline_state.json
4. 对话模式：清空对话记忆中的项目状态
