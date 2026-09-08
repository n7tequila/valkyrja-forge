---
id: ADEC-<DOMAIN>-<NNN>
date: <YYYY-MM-DD>
status: accepted          # accepted | superseded
superseded-by:            # 被推翻时填新 ADEC id，本文件不删除
foundational:             # 仅奠基性 ADEC 填：stack | layout；其余留空或删除本行。
                          # supersede 奠基 ADEC 时新 ADEC 必须继承此标记
---

# ADEC-<DOMAIN>-<NNN> <决策标题一句话>

## Decision

<结论。一段话说清定了什么，含关键参数（技术名、格式、边界值）。>

## 验收可观察性判定

<为什么这是工程内部决策而非产品承诺：验收口径中不可见/不可测的理由一两句。
若部分内容验收可见，说明该部分已回流上游（引用对应 DEC/待澄清项）。>

## Context

<背景与约束。可引用 ADISC-*（讨论过程）、TM-*（产品侧技术事实，只读）、
DEC-*（产品决策，作为边界条件）、实测结论。引用只作证据，权威不传递。>

## Rejected Alternatives

<被否备选与否决理由，禁止编造。没有备选写"无"。>

## 影响范围

<受本决策约束的 capability / change / 契约。供 status 现算消费方时对照。>
