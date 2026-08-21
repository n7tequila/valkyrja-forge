---
description: OpenSpec 开发治理层 —— 需求基线、change 划分、PRD↔spec 追溯校验与归档门禁
argument-hint: [想做什么，自然语言即可；留空则先复述基线与进度]
---

# /valkyrja:spec

`valkyrja-spec` 技能的斜杠入口（plugin 安装形态下技能名为 `valkyrja:valkyrja-spec`）。

## Arguments

`$ARGUMENTS`

## Delegation

用 Skill 工具调用 **`valkyrja-spec`** 技能，把上述 Arguments 作为用户意图交给它处理。

- **不要在本文件里判断该走哪个动作。** 动作路由由 SKILL.md 的意图路由表决定，
  那里是唯一的路由权威——本命令只负责把请求转进去。
- Arguments 为空时：执行技能的会话启动仪式（含前提检测，不得跳过），
  复述基线与 change 进度后再问用户想做什么。
- **特权动作与确认规则以 SKILL.md 为唯一权威，不因走斜杠入口而放宽**——
  四动词壳的委托步何时停下问人、归档回显必含什么、`next` 到门即停，
  一律以技能本体的动作协议为准，本文件不复述（复述即第二载体，必然漂移）。
