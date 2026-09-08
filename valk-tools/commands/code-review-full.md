---
description: 四维并行代码审查 —— 后端 / 前端 / Java DDD / 安全，按严重级别汇总裁决
argument-hint: [审查范围：留空=工作区改动；也可给分支名、提交区间或 PR 号]
---

# /valk-tools:code-review-full

`code-review-full` 技能的斜杠入口（plugin 安装形态下技能名为 `valk-tools:code-review-full`）。

## Arguments

`$ARGUMENTS`

## Delegation

用 Skill 工具调用 **`code-review-full`** 技能，把上述 Arguments 作为审查范围交给它处理。

- **不要在本文件里分派 agent，也不要复述四个维度各自的检查清单。**
  维度划分、agent 选型、复用哪些 skill 与 rules、严重度模型与去重规则
  一律以 SKILL.md 为唯一权威。
- Arguments 为空时：默认审查工作区未提交改动。
