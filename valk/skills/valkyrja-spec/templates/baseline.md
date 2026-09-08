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

<!-- 一条 FRID 一个三级标题。处置六选一：
     直通 | 拆分 | 延期 | 非软件 | 外部 | 冲突
     登记位置（机读口径，勿混）：本节只写 直通/拆分/冲突 三种；
     延期/外部/非软件 各自登记在下方对应专节（trace 以专节标题取集合，
     在本节写「处置：延期」不会被机器识别，该 FRID 会被判为漏裁决）。

     混合体 FRID（行为点分属不同交付归属）：
     - 行为点层级标注「交付：本仓软件 / 非软件 / 外部系统」，与 capability 并列；
     - FRID 层级仍只取一个处置：只要有至少一个本仓软件行为点即判「拆分」；
     - 判为拆分的混合体，其非软件/外部行为点必须逐点记明交付方式，
       否则那部分会随 FRID 一起被算作「已覆盖」而静默消失。 -->

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

## 外部系统项（external）

<!-- 是软件，但由本仓之外的系统交付（如后台 CMS、CRM/工单系统、埋点服务端）。
     与「非软件」必须分开：non-software 是永久不需要任何 spec，
     external 是需要 spec、但那份 spec 属于另一个 openspec 实例。
     混为一谈会让跨系统欠账在两边同时消失。
     status 与 V6.2 须持续单列，并显示承担系统。 -->

### <BR-DOMAIN-NNN>

承担系统：<后台 CMS | CRM/工单系统 | 埋点服务端 | …>
理由：<为什么不由本仓交付>
裁决日：<YYYY-MM-DD>

## 非软件项（non-software）

<!-- 不由代码交付的正式需求（如「指定工单跟进责任人并写入运营文档」）。
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

<!-- 格式见 SKILL.md 的 decompose 节。只存裁决字段——名称、capabilities、
     覆盖 FRID、顺序与依赖、说明；**粘贴段与 Requirement Authority 块不预存**，
     由 propose 壳现算生成（宪法 5：预存路径会在 rebaseline 后过期，
     真实事故：承袭基线的预存段仍指旧版路径）。
     「已建/未建」由 status 现算，不写入本文件。 -->

## 待上游澄清项

<!-- 本技能不铸造任何 ID（含 Q）。回流上游后由 valkyrja-prd 铸 Q-* 并纳入下一版 PRD。 -->

- 缺口：<描述：哪条需求的什么信息缺失，导致无法写出可验收 Scenario>
  影响：<阻塞哪个 change 的哪个环节>
  已回流上游：否

## 例外记录

<!-- skip_specs 例外、欠账放行、范围蔓延放行、计划外探索备案等，
     逐条记理由与裁决日。**机读判据**：trace 按「同一行含 change 名 + 类型关键词」
     查验裁决（change 名边界匹配，前缀名不互蹭），四个类型关键词固定为：
     欠账 / 蔓延 / skip_specs / 计划外——事项行必须同时含 change 名与对应关键词。
     注意「计划外」是**探索备案**：只消 trace 对该 change 的重复提醒，
     不放行它本身（计划外 change 一律不得通过门禁，唯一出口是 decompose 纳入计划）。 -->

- 事项：<change-name> 设 skip_specs: true
  理由：<为什么该 change 确实不携带任何 spec 级行为变更>
  裁决日：<YYYY-MM-DD>
- 事项：<change-name> 范围蔓延（<FRID>）裁决放行
  理由：<为什么超出 Covered-FRIDs 的触达是合理的>
  裁决日：<YYYY-MM-DD>
