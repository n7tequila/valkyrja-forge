<!-- 阅读稿模板（view 动作按此生成）。格式以本模板为唯一权威，SKILL.md 只指向这里。
     阅读稿是给人看的派生导出物，不是需求依据：本技能任何动作都不读回它，下游不得消费。
     选底、决策状态与输出路径安全以 SKILL.md 的 view 动作为准。

     引用纪律：
     - 逐字照搬，一个字不改（含数字、阈值、单位、标点；全角标点保持全角，不写成半角）：需求条目正文（标题到 Sources: 之前）、
       DEC 的 Decision 段、Open Questions、Out of Scope、Deprecated、PRD 阅读区、RN 正文
     - 可以摘要，标「摘要」并附出处 ID：DISC 讨论过程、TM、版本间变化、一页概览、DEC 的 Context
     - 不收全文，只给相对路径：others/ 下的外部原件
     - 只有讨论、没有决策的事项只写成「在议」，不得写成结论；不补任何来源里没有的需求
     - 条数、待定数等数字现场数，不抄 STATUS.md
     - 无内容的节整节删掉，不为填节编造

     文件头三行必须保留：第一行原样照抄；第二行按实际底稿三选一。 -->

> **阅读稿，不作为需求依据。** 开发与验收一律以 `prd/releases/` 下的已发布版本为准。
> 基于：<prd/releases/vX.Y.md | prd/current.md（未发布草稿，内容可能还会改）| 尚无 PRD>
> initiative：<slug>　DOMAIN：<DOMAIN>　生成时间：<YYYY-MM-DD HH:MM>

# <产品/功能名称> · 阅读稿

## 一页概览（摘要）

<三到五句人话：这是什么、给谁用、这一版覆盖什么、还有几件事没定。>

- 需求：REQ <n> 条、BR <n> 条、SEC <n> 条、NFR <n> 条
- 待定问题 <n> 个（其中 blocking <n> 个）；在议话题 <n> 个

## 背景、目标与流程

<照搬 PRD 阅读区原文：Background / Goals / Actors / User Journey / Dependencies / Data & Audit。>

## 需求逐条

### REQ-<DOMAIN>-001

> <需求正文，逐字照搬>

- **为什么这样定**：DEC-<DOMAIN>-NNN（<日期>）——<Decision 段原文>
  - **替代历史**（摘要）：原定 <摘要>（DEC-<DOMAIN>-NNN），已被 DEC-<DOMAIN>-NNN 取代
- **来龙去脉**（摘要）：<讨论过哪些方案、否决了什么、为什么>（DISC-<DOMAIN>-NNN）
- **原始出处**：RN-<DOMAIN>-NNN（来源：<会议纪要 / 客户材料 / …>）——<RN 正文原文>
- **技术背景**（摘要）：<一句话>（TM-<DOMAIN>-NNN，经 DEC-<DOMAIN>-NNN 引用）

<!-- 每条需求一节，按 PRD 中的顺序；没有对应材料的行删掉。BR / SEC / NFR 同此格式。
     「为什么这样定」沿底稿的 Sources 引用 DEC；引用后来被取代时仍保留其 Decision 原文，
     标为底稿历史依据并补替代历史行，不用后继决策改写底稿需求。 -->

## 视觉基线

<当前背书的原型版本、背书它的 DEC 与入口路径。>

## 还没定的

### 待定问题

<Open Questions 原文。>

### 在议话题（只是过程，没有结论）

- DISC-<DOMAIN>-NNN <话题>（active | parked）——（摘要）<在争什么、摆出过哪些选项>

### 已经定了、但这版文档里还没体现的决策

- DEC-<DOMAIN>-NNN（<日期>）——<Decision 段原文>

<!-- 选取口径见 SKILL.md 的 view 动作。本节要如实写明：这些决策可能还没合成进文档，
     也可能只影响范围外的事。 -->

## 范围外与已废弃

<Out of Scope 原文；Deprecated Requirements 原文。>

## 版本变迁（摘要）

- v<X.Y>（<日期>）：<这一版的主要内容或相对上一版的变化>
- 未发布草稿：<相对最新 release 的变化>（仅以 current 为底时）

## 出处索引

| 编号 | 文件 |
|---|---|
| <ID> | <initiative 内相对路径> |
