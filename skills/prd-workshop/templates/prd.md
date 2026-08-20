---
initiative: <slug>
version: <X.Y>            # release 时定稿；current.md 阶段写 X.Y-draft
round: <N>
date: <YYYY-MM-DD>
domain: <DOMAIN>
---

# PRD: <产品/功能名称> v<X.Y>

<!-- 以下至 Requirements 区之前均为人类阅读区，机器不解析。
     各节可选：无实质内容的节直接删除，禁止为填节而编造内容。 -->

## Background

<业务背景与问题，自由书写。>

## Goals / Non-Goals

<本版本要达成什么、明确不追求什么。>

## Actors

<角色列表。>

## User Journey / Business Flow

<核心用户流程或业务流程，自由书写（可用步骤列表或图）。>

## Dependencies

<依赖的外部系统、团队、前置条件。>

## Data & Audit Requirements

<数据留存、审计、合规方面的总体要求；具体可验证条目仍以 BR/SEC/NFR 区块表达。>

<!-- ============================================================
     以下 Requirements 区为机读区，格式为下游语法契约，不得变体：
     - 每条需求以二级标题定界：## REQ-XXX-NNN（或 BR/SEC/NFR）
     - 区块范围：该标题起，至下一个同级标题
     - 每区块必须含 Sources: 节：每行一个 "- ID"，至少一个 RN 或 DEC
       （权威来源只允许 RN 与 DEC；TM 经 DEC 回溯）
     - 区块内可写一行"验收要点"；细化的 Given/When/Then 场景
       属于下游 OpenSpec specs，不在 PRD 层展开
     ============================================================ -->

## REQ-<DOMAIN>-001

<需求陈述：描述可观察的系统行为（WHAT），不写实现方式（HOW）。>

Sources:
- RN-<DOMAIN>-NNN                  # 明确无冲突的需求可直通自 RN

## REQ-<DOMAIN>-002

<...>

Sources:
- RN-<DOMAIN>-NNN                  # 多来源共同收敛时全部列出
- DEC-<DOMAIN>-NNN                 # 经决策收束的需求含该 DEC

## BR-<DOMAIN>-001

<长期业务规则（Policy 层面的要求）。>

Sources:
- DEC-<DOMAIN>-NNN

## SEC-<DOMAIN>-001

<安全要求。>

Sources:
- DEC-<DOMAIN>-NNN

## NFR-<DOMAIN>-001

<非功能要求（性能、可用性等），写可验证的目标值。>

Sources:
- DEC-<DOMAIN>-NNN

## Deprecated Requirements

<!-- ID 永不删除、永不复用。作废需求移入本节，保留原文。 -->

## REQ-<DOMAIN>-0XX [DEPRECATED]

<原文保留>

Deprecated-by: DEC-<DOMAIN>-NNN
Deprecated-in: v<X.Y>

## Out of Scope

- <明确不做的事项>

## Open Questions

<!-- 机读格式：### Q-XXX-NNN [blocking|non-blocking] @owner -->

### Q-<DOMAIN>-001 [blocking] @product

<问题陈述。>

Status: open

### Q-<DOMAIN>-002 [non-blocking] @architecture

<问题陈述。>

Status: open
<!-- 若由 blocking 改判而来，须留痕：
     Status: reclassified non-blocking on <date> — <改判理由> -->
