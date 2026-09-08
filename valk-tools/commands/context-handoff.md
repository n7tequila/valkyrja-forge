---
description: 上下文交接与续接 —— 存（清空前固化现场）/ 取（新会话恢复现场）
argument-hint: [留空=按当前情形判断存还是取；也可直接说"准备清空"或"恢复现场"]
---

# /valk-tools:context-handoff

`context-handoff` 技能的斜杠入口（plugin 安装形态下技能名为 `valk-tools:context-handoff`）。

## Arguments

`$ARGUMENTS`

## Delegation

用 Skill 工具调用 **`context-handoff`** 技能，把上述 Arguments 作为用户意图交给它处理。

- **不要在本文件里判断走「存」还是「取」。** 方向判断与四步流程由 SKILL.md 决定，
  那里是唯一权威——本命令只负责把请求转进去。
- Arguments 为空时：由技能按当前会话状态自行判断方向（会话已有大量上下文 → 存；
  会话刚开始 → 取）。
- **交接前的验证要求与提交纪律以 SKILL.md 为唯一权威**，不因走斜杠入口而放宽。
