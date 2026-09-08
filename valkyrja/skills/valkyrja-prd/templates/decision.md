---
id: DEC-<DOMAIN>-NNN
round: <N>
date: <YYYY-MM-DD>
status: accepted          # accepted | superseded
superseded-by:            # 仅 status=superseded 时填写，如 DEC-MEETING-021
frid-impact:              # 可选。仅背书类/流程类决策填 none（不改任何 FRID 语义，
                          # 豁免下游 V2.5 发版欠账门限）。机读判据是 frontmatter
                          # 行首的「frid-impact: none」原样拼写——写成「无」、写进
                          # 正文段落、或缩进都会让豁免静默失效（欠账死锁复活）。
                          # 该标记必须在 decide 确认回显中显式出示并说明理由。
---

# DEC-<DOMAIN>-NNN <一句话标题>

## Decision

<结论，一到两句话。这是唯一权威表述，synthesize 时以此为准。>

## Context

<为什么需要这个决策，一两句即可。>

## Sources

- DISC-<DOMAIN>-NNN   # 形成本决策的讨论
- RN-<DOMAIN>-NNN     # 相关原始需求（如有）

## Rejected Alternatives

<!-- 可选节。仅当讨论中真实出现过备选方案时填写；
     无真实备选（用户直接拍板）时删除本节。禁止为填模板编造备选方案。 -->

- <被否掉的备选方案 A>：<一句话否决理由>

## Closes Questions

- Q-<DOMAIN>-NNN      # 本决策回答了哪些 open question（如有）
