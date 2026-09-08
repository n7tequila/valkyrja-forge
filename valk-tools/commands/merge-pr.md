---
description: 开 PR/MR —— 支持 GitHub（gh CLI）与自建 forge（Gitea/GitLab/Bitbucket）降级
argument-hint: [源分支 目标分支；如 "develop main"。留空则按当前分支推断]
---

# /valk-tools:merge-pr

`merge-pr` 技能的斜杠入口（plugin 安装形态下技能名为 `valk-tools:merge-pr`）。

## Arguments

`$ARGUMENTS`

## Delegation

用 Skill 工具调用 **`merge-pr`** 技能，把上述 Arguments 作为源分支与目标分支交给它处理。

- **不要在本文件里判断该用 gh 还是降级到 compare URL。** forge 探测与降级策略
  由 SKILL.md 决定，那里是唯一权威。
- Arguments 为空时：由技能按当前分支与上游推断源与目标，并在动作前回显确认。
- **创建 PR 是外向动作，确认规则以 SKILL.md 为准**，不因走斜杠入口而跳过。
