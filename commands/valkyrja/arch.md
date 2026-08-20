---
description: 技术契约治理层 —— 技术选型决策（ADEC）、约定采纳、共享接口契约与架构现状
argument-hint: [想做什么，自然语言即可；留空则先复述架构现状]
---

# /valkyrja:arch

`valkyrja-arch` 技能的斜杠入口。

## Arguments

`$ARGUMENTS`

## Delegation

用 Skill 工具调用 **`valkyrja-arch`** 技能，把上述 Arguments 作为用户意图交给它处理。

- **不要在本文件里判断该走哪个动作。** 动作路由由 SKILL.md 的意图路由表决定，
  那里是唯一的路由权威——本命令只负责把请求转进去。
- Arguments 为空时：执行技能的会话启动仪式
  （STATUS.md → decisions/ → contracts/ frontmatter → backlog 触发项），
  用 3–5 句复述现状，再问用户想做什么。
- **特权动作护栏（不得因走斜杠入口而放宽）**：`bootstrap`（落盘步骤）、
  `decide`、`adopt`、`contract`、`publish` 均须完整回显后经人明确确认才落盘；语气含疑问（"就用 X 吧？"）
  视为倾向，只记入 ADISC，不铸决策。contract 的回显必须列出已知消费方与
  破坏性影响，不得以「已更新」一句带过。
- **边界提醒**：验收可观察的事项属产品侧，本技能不裁决——标注「应回流上游」
  并提请用户走 /valkyrja:prd。
