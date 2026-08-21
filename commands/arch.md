---
description: 技术契约治理层 —— 技术选型决策（ADEC）、约定采纳、共享接口契约与架构现状
argument-hint: [想做什么，自然语言即可；留空则先复述架构现状]
---

# /valkyrja:arch

`valkyrja-arch` 技能的斜杠入口（plugin 安装形态下技能名为 `valkyrja:valkyrja-arch`）。

## Arguments

`$ARGUMENTS`

## Delegation

用 Skill 工具调用 **`valkyrja-arch`** 技能，把上述 Arguments 作为用户意图交给它处理。

- **不要在本文件里判断该走哪个动作。** 动作路由由 SKILL.md 的意图路由表决定，
  那里是唯一的路由权威——本命令只负责把请求转进去。
- Arguments 为空时：执行技能的会话启动仪式，复述架构现状后再问用户想做什么。
- **特权动作与确认规则以 SKILL.md 为唯一权威，不因走斜杠入口而放宽**——
  哪些动作特权、回显什么、产品侧/技术侧边界如何划，一律以技能本体为准，
  本文件不复述（复述即第二载体，必然漂移）。
