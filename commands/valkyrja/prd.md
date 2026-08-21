---
description: 产品需求工作坊 —— 讨论、决策、导入存量文档、原型收编与视觉基线背书、盘点状态、合成与发布 PRD
argument-hint: [想做什么，自然语言即可；留空则先复述当前状态]
---

# /valkyrja:prd

`valkyrja-prd` 技能的斜杠入口。

## Arguments

`$ARGUMENTS`

## Delegation

用 Skill 工具调用 **`valkyrja-prd`** 技能，把上述 Arguments 作为用户意图交给它处理。

- **不要在本文件里判断该走哪个动作。** 动作路由由 SKILL.md 的意图路由表决定，
  那里是唯一的路由权威——本命令只负责把请求转进去。
- Arguments 为空时：执行技能的会话启动仪式
  （STATUS.md → prd/current.md → decisions/ → blocking questions），
  用 3–5 句复述当前状态，再问用户想做什么。
- **特权动作护栏（不得因走斜杠入口而放宽）**：`decide` 与 `release` 必须先完整回显、
  等人明确确认后才落盘；用户语气含疑问（"就按 B 吧？"）视为倾向，只记入讨论，不铸造决策。
