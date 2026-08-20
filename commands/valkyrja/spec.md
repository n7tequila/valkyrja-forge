---
description: OpenSpec 开发治理层 —— 需求基线、change 划分、PRD↔spec 追溯校验与归档门禁
argument-hint: [想做什么，自然语言即可；留空则先复述基线与进度]
---

# /valkyrja:spec

`openspec-development` 技能的斜杠入口。

## Arguments

`$ARGUMENTS`

## Delegation

用 Skill 工具调用 **`openspec-development`** 技能，把上述 Arguments 作为用户意图交给它处理。

- **不要在本文件里判断该走哪个动作。** 动作路由由 SKILL.md 的意图路由表决定，
  那里是唯一的路由权威——本命令只负责把请求转进去。
- Arguments 为空时：执行技能的会话启动仪式
  （前提检测 → 基线 → release → 现算 change 进度），复述后再问用户想做什么。
- **前提检测不得跳过**：OpenSpec CLI ≥ 1.9.0、`openspec/` 根、官方 sync 与 verify workflow
  是否安装。缺 verify 必须显式告知后果——它承担「实现代码 ↔ change artifacts」这一环，
  本技能不做这件事，缺了没有替代方案。
- **特权动作护栏（不得因走斜杠入口而放宽）**：`baseline` 定稿、`decompose` 裁决、
  `rebaseline` 采纳、**归档放行**均需完整回显后经人确认；归档回显必须逐条出示 trace 结果，
  并单独高亮 capability 退休删除（工作树不可恢复），不得以「检查通过」一句带过。
