---
domain: <DOMAIN>
prd_release: docs/product/initiatives/<slug>/prd/releases/v<X.Y>.md
status: active            # drafting | active | superseded
date: <YYYY-MM-DD>
---

# Requirement Baseline — <DOMAIN>（PRD v<X.Y>）

<!-- ============================================================
     本文件只记「裁决」与「计划」，绝不记「现状」或任何派生值（宪法 5）。
     禁止出现：覆盖率、各类计数、change 已建/未建、归档与否、
               FRID→change 的实际映射、需求块 digest。
     以上一律现算 —— releases/ 冻结只增，历史版本永远在盘上。

     FRID = REQ | BR | SEC | NFR，四类同等对待，不得只处理 REQ-*。
     ============================================================ -->

## 需求裁决

<!-- 一条 FRID 一个三级标题。处置五选一：
     直通 | 拆分 | 延期 | 非软件 | 冲突 -->

### <REQ-DOMAIN-NNN>

处置：直通
capability：<capability-path>
裁决日：<YYYY-MM-DD>

### <REQ-DOMAIN-NNN>

处置：拆分
行为点：
<!-- capability 标在行为点层级，允许跨 capability ——
     一条 FRID 的多个行为点常分属不同能力域，进而落入不同 change。
     编号 1/2/3 只是本文件内的局部序号，不是 ID，不得外流到 spec 或 proposal。 -->
1. <行为点描述>
   capability: <capability-path>
2. <行为点描述>
   capability: <另一个 capability-path>
3. <行为点描述>
   capability: <又一个 capability-path>
原 ID 处置：<原 FRID> 保持不变、不细分；拆出的各条 Requirement 的
           Sources 均写 <原 FRID>；PRD 侧不产生任何新 ID。
裁决日：<YYYY-MM-DD>

### <SEC-DOMAIN-NNN>

处置：直通
capability：<capability-path>
实现约束：<DEC-DOMAIN-NNN> 背书「<结论一句话>」→ 行为部分进 spec；
         技术选型（<具体技术>）进 design.md，标注 依据: <DEC-DOMAIN-NNN>
裁决日：<YYYY-MM-DD>

### <REQ-DOMAIN-NNN>

处置：冲突
冲突描述：<与哪条 FRID 或主 spec 的哪个 Requirement 矛盾，矛盾点一句话>
对应澄清项：见「待上游澄清项」第 <N> 条
裁决日：<YYYY-MM-DD>

<!-- 冲突项不阻塞基线定稿与其他 FRID 的开发，但：
     - 必须同时在「待上游澄清项」记一条并回流上游；
     - 在上游决议并 rebaseline 前不属于 included，不得被任何 change 覆盖；
     - status 与 V6.2 报告中持续显示为「待上游收敛」。 -->

## 延期项（deferred）

<!-- 本轮不做，但以后仍需实现。
     必须与「非软件」分开 —— status 要持续把这些显示为「未实现」，
     且 V6.2 的覆盖对账不把它们算作已解释，否则会长期静默遗忘。 -->

### <REQ-DOMAIN-NNN>

理由：<为什么本轮不做>
预期版本：<v1.1 | 待定>
裁决日：<YYYY-MM-DD>

## 非软件项（non-software）

<!-- 不由代码交付的正式需求（如「指定线索跟进责任人并写入运营文档」）。
     不要求 spec 覆盖，但必须记录交付方式与理由，否则无法回答
     「这条需求到底谁负责」。 -->

### <BR-DOMAIN-NNN>

理由：<为什么不由软件交付>
交付方式：<运营文档 / 线下流程 / 合同条款 …>
裁决日：<YYYY-MM-DD>

## Change 划分（计划，非现状）

### <change-name>

类型：实现            <!-- 实现 | 退休 -->
capabilities：<capability-path>[, <capability-path>...]
<!-- 允许多值 —— 行为点可跨 capability，一个 change 内每个 capability
     对应一个 specs/<capability-path>/spec.md delta 文件。 -->
覆盖：<REQ-DOMAIN-NNN>, <SEC-DOMAIN-NNN>
顺序：<N>（依赖：<change-name> | 无）

### <retire-change-name>

类型：退休
<!-- 退休型 change 覆盖的是 deprecated(当前 release) 中的 FRID，
     以 REMOVED delta 把它们移出主 spec。
     实现型与退休型**不得混在同一个 change 内** ——
     那会让 V4.3 的 ADDED 规则与 V4.4 的 REMOVED 规则互相干扰。 -->
capabilities：<capability-path>
覆盖：<已 DEPRECATED 的 FRID>
顺序：<N>（依赖：<change-name> | 无）

<!-- OpenSpec 没有跨 change 依赖的概念，顺序与依赖只能记在这里。
     本节是三份清单的权威源：
       基线计划 → proposal 的 Covered-FRIDs → spec delta 的 Sources
     后两者必须与本节相等，由 trace 的 V4.0 / V4.5 / V4.6 校验。 -->

## 交接单

<!-- 格式见 SKILL.md 的 decompose 节，须含可照抄的 Requirement Authority 块。
     「已建/未建」由 status 现算，不写入本文件。 -->

## 待上游澄清项

<!-- 本技能不铸造任何 ID（含 Q）。回流上游后由 valkyrja-prd 铸 Q-* 并纳入下一版 PRD。 -->

- 缺口：<描述：哪条需求的什么信息缺失，导致无法写出可验收 Scenario>
  影响：<阻塞哪个 change 的哪个环节>
  已回流上游：否

## 例外记录

<!-- skip_specs 例外、计划外 change 纳入裁决、带 WARNING 放行等，逐条记理由与裁决日。 -->

- 事项：<change-name> 设 skip_specs: true
  理由：<为什么该 change 确实不携带任何 spec 级行为变更>
  裁决日：<YYYY-MM-DD>
