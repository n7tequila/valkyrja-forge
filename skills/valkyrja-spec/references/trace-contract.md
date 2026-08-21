# trace 契约与检查清单（详版）

> **何时读本文件**：执行 `trace`、`check`，或需要判断某条 delta 的 Sources
> 是否合规时。SKILL.md 只保留契约摘要与 trace 流程；判定细节全在这里。
>
> **维护提醒**：本文件与 `tools/trace.py`、SKILL.md 的动作协议**三处同源**。
> 任何检查条目的增删改必须三处同步——V4.8 曾只进了设计文档与脚本、
> 漏了 SKILL.md 本体，由外部评估发现（三载体漂移，本项目已发生多次）。

## 契约二：Sources 行（完整规则）

每个 `### Requirement:` 标题的**下一行**必须是：

```
Sources: <FRID>[, <FRID>...]
```

- 正则：`^Sources:\s*((REQ|BR|SEC|NFR)-[A-Z][A-Z0-9]*(_[A-Z][A-Z0-9]*)*-\d{3})(\s*,\s*(REQ|BR|SEC|NFR)-[A-Z][A-Z0-9]*(_[A-Z][A-Z0-9]*)*-\d{3})*\s*$`
- 单行逗号分隔，与 PRD 的多行 `- ID` 列表**刻意不同**：该行位于 Requirement 正文区内，
  OpenSpec 会把它连同正文一并归属该 Requirement，多行 bullet 易与需求内容混淆。
- ID 类型只能是 FRID。**不得直接引 RN/DEC/TM**——那会绕过 `prd/releases/` 这一唯一 API。

### 历史 provenance 与当前 authority 的区分（关键，勿简化）

| 场景 | 规则 |
|---|---|
| ADDED Requirement | 全部 Sources 必须 ∈ `active(当前release)` ∩ `included` |
| MODIFIED Requirement — 沿袭的旧 ID | **允许**已 DEPRECATED 的 FRID 留存，只需 ∈ `historical`；不得删除 |
| MODIFIED Requirement — 本次新增的 ID | 必须 ∈ `active(当前release)` ∩ `included` |

「本次新增的 ID」机器可判：`新增集 = delta 的 Sources − 主 spec 中同名 Requirement 的 Sources`。
两侧都在盘上，现算即可，无需记录。

> 为什么必须区分：需求 DEPRECATED 后，若仍要求全部 Sources ∈ active，
> 则「保留历史 ID」与「Sources 必须活跃」两条规则直接对撞，该 Requirement
> 无论怎么写都过不了 trace。区分二者是唯一自洽解。

### REMOVED 的判定

被移除 Requirement 所引用的 FRID（从**主 spec 中同名 Requirement 的 Sources 行**反查，
REMOVED 块本身不带 Sources）必须 ⊆ `deprecated(当前release)`。
移除一个仍 `active` 的 FRID 的全部 spec 引用 → ERROR，正确出口是上游标 DEPRECATED
并发新 release，再 rebaseline。反之，已 DEPRECATED 的需求必须能被移除——
否则老需求永远删不掉。

### RENAMED 与 REMOVED 语义相反，判定不得共用

RENAMED 在 OpenSpec 中是 "Name changes only"——只改 Requirement 标题，
行为与身份都不变，因此**不要求其 FRID 已 DEPRECATED**（要求了就等于禁止一切
active 需求的标题重构）。它触达的 FRID 只需 ∈ `historical`；
覆盖关系照常由 `addressed()` 与 V4.5/V4.6 把关。

## 契约三：addressed(change)

**不得用「delta 的 Sources 并集」代表一个 change 处理了什么。** 该并集在三种场景下
与事实不符，会同时制造假警报与假放行：

| 场景 | 用 Sources 并集的后果 |
|---|---|
| MODIFIED 保留了历史 provenance ID | 历史 ID 被误判为范围蔓延，**永久假警报** |
| REMOVED（块内无 Sources 行） | 并集为 ∅，`Covered ⊆ ∅` 恒假，**正常删除型 change 永远无法放行** |
| RENAMED（块内无 Sources 行） | 同上 |

因此定义 **`addressed(change)`＝该 change 实际触达的正式需求集合**，按 delta 操作分别计算：

```
ADDED      addressed = delta 该 Requirement 的 Sources

MODIFIED   historical_exempt = main_sources − Covered-FRIDs
           addressed         = delta_sources − historical_exempt
           （main_sources = 主 spec 中同名 Requirement 的 Sources）

REMOVED    addressed = 主 spec 中被移除 Requirement 的 Sources

RENAMED    addressed = 主 spec 中 FROM 所指 Requirement 的 Sources
```

`addressed(change)` 为各 delta 块结果的并集。全部输入都在盘上（主 spec + delta），
现算即可，不落盘。

验算 MODIFIED 那条公式：主 spec `Sources: OLD`，OLD 已 DEPRECATED，本次为 NEW 而改，
`Covered-FRIDs = {NEW}`，delta 按契约二必须写 `Sources: OLD, NEW`。
则 `historical_exempt = {OLD} − {NEW} = {OLD}`，`addressed = {OLD,NEW} − {OLD} = {NEW}`
——与 Covered 相等，不再误报。而若该 change 真的越权引入了计划外的 X，
`historical_exempt` 不含 X（X 不在 main_sources 中），X 会留在 addressed 里被 V4.5 抓到。

## 检查清单 V1–V6

**V1 前提**
- V1.1 CLI 可用且 ≥ 1.9.0
- V1.2 `openspec context --json` 返回有效 root
- V1.3 基线存在且 `status: active`
- V1.4 **技术地基已定**（仅当 `docs/architecture/` 存在时检查；无该目录则显式报
  「跳过」——不用 valkyrja-arch 的项目完全合法）：`decisions/` 下
  `foundational: stack` 与 `foundational: layout` 各须有一条
  `status: accepted` 的 ADEC → 缺项 **WARNING**：
  「技术地基未定：apply 将被迫在实现现场临时决定技术栈/布局且不留痕，
  建议先跑 valkyrja-arch 的 bootstrap」。
  WARNING 而非 ERROR 的理由：地基未定是**治理债**，不是追溯断裂，
  按放行规则可带裁决放行（裁决记入基线例外记录）。

**V2 PRD 侧**（防御 release 被手改）
- V2.1 `prd_release` 指向的文件存在
- V2.2 PRD 内 `[blocking]` 且 `Status: open` 的问题数 = 0 → 否则 ERROR
- V2.3 每个需求块含 `Sources:` 且至少一个 RN/DEC
- V2.4 无重复 FRID
- V2.5 **发版欠账门限**：欠账 :=（现算）initiative 内 `round` 大于当前 release
  `round` 的 DEC 集合（round 缺失时退化为 date 晚于 release date）。
  欠账非空 **且** 本 change **未开工**（tasks.md 无任何已勾选项，现算）→ **ERROR**，
  除非基线「例外记录」中有对本 change 的显式放行裁决（该行须同时含 change 名
  与「欠账」字样）。在途 change（已有勾选）不受此限——需求正式变更时由
  rebaseline 的 V4.0(a) 联锁逐个接手，两道闸接力。
  报告必须显示欠账条数与扫描的 DEC 总数（零对象与零发现须可区分）。
  理由：**决而未发的 DEC 对下游不可见**，新工作在已知过期的需求上启动是
  静默返工之源；讨论（DISC）不触发门限——决定尚不存在，谈不上跑偏；
  门限零语义判断（不依赖任何人工影响面标注，标注类方案的失效是静默的）。

**V3 基线对账**（计划 vs 现状）
- V3.1 `active(当前release)` ⊆
  （`included` ∪ `deferred` ∪ `non-software` ∪ `external` ∪ `conflicted`）
  → 差集＝漏裁决，ERROR
- V3.2 `included` / `deferred` / `non-software` / `external` / `conflicted` 五个集合
  两两互斥（每条 FRID 在基线中恰好一个处置）→ 否则 ERROR
- V3.3 基线引用的每个 FRID 在 PRD 中真实存在 → 幽灵 ID，ERROR
- V3.4 每个 `included` FRID 至少被一个 planned change 覆盖 → ERROR
- V3.5 磁盘 change 与计划对账，输出三态：已建 / 未建 / **计划外**

**V4 delta 侧**（逐 change）
- V4.0 proposal.md 含合法 `## Requirement Authority` 块，且**三重自洽**：
  (a) `Baseline:` 指向该 DOMAIN **当前 active** 的基线 → 指向 superseded 基线则 ERROR
  （**这是 rebaseline 与 trace 的联锁**：rebaseline 后所有既有 change 仍声明旧基线，
  会在此被逐个拦下，更新 Authority 块并重新对账后才能放行——需求变更不会静默穿过）；
  (b) `PRD-Release:` 等于该基线 frontmatter 的 `prd_release` → 否则 ERROR；
  (c) `Covered-FRIDs` **等于**该基线为本 change 计划的集合 → 不等则 ERROR（声明与计划漂移）
- V4.1 每个 `### Requirement:` 有且仅有一个 `Sources:` 行 → ERROR
- V4.2 Sources 中 ID 类型只能是 FRID → ERROR（防绕过 release）
- V4.3 **分场景判定**（见上「契约二」）：
  - ADDED 的全部 Sources ∈ `active` ∩ `included` → 否则 ERROR
  - MODIFIED 沿袭的旧 ID ∈ `historical` 即可（允许 DEPRECATED）→ 否则 ERROR
  - MODIFIED 本次新增的 ID ∈ `active` ∩ `included` → 否则 ERROR
- V4.4a **REMOVED**：被移除 Requirement 所触达的 FRID（从主 spec 同名 Requirement 的
  Sources 反查）⊆ `deprecated(当前release)` → 否则 ERROR（不得移除仍 active 的需求）
- V4.4b **RENAMED**：FROM 所指 Requirement 触达的 FRID ⊆ `historical` 即可，
  **不要求 ∈ `deprecated`**——改标题是保持身份的 spec 重构，不是需求退役。
  沿用 REMOVED 的门槛会让任何 active 需求的纯标题重命名被误判为 ERROR。
- V4.5 `addressed(change)` ⊆ `Covered-FRIDs` → 超出部分 WARNING（范围蔓延，需人裁决）
- V4.6 `Covered-FRIDs` ⊆ `addressed(change)` → 缺失部分 ERROR（漏做）
  （**在没有经批准的 V4.5 例外时**，V4.5 + V4.6 等价于
  `addressed(change) == Covered-FRIDs`；若某条 WARNING 经人裁决放行，
  则合法状态为 `addressed ⊇ Covered`，该放行须记入基线的例外记录。
  **必须用契约三的 `addressed()`，不得退化为 Sources 并集**。）
- V4.7 `.openspec.yaml` 含 `skip_specs: true` → ERROR，除非基线「例外记录」中已有裁决
- V4.8 **design.md 依据标注的引用完整性**：扫描 `依据: DEC-*` / `依据: ADEC-*`，
  被引决策必须真实存在（DEC → initiative 的 `decisions/`；ADEC →
  `docs/architecture/decisions/`）→ 幽灵引用 ERROR；被引决策已 superseded → WARNING。
  三个不做：不查「该标注而未标注」（机器判不出一句话是否约束，留给 config 注入）；
  不查 DEC 范围覆盖（语义判断，维持人工）；无架构工作区不特殊豁免。
  定性：**引用完整性**检查（与 Sources 同族，防 AI 编造权威），
  不是技术正确性检查——后者属 linter/架构测试/CI，本技能不越界。

**V5 委托原生**
- V5.1 `openspec validate <change> --type change --strict --json` 退出码 0
- V5.2 `openspec status --change <name> --json` 中 required artifacts 无缺失

**V6 post-archive verification**（**归档后**执行，不属于放行判定）
- V6.1 主 spec 每个 Requirement 保留 `Sources:` → 缺失 WARNING
- V6.2 计算 `unaccounted`，**仅它是 ERROR**：

  ```
  unaccounted = active
              − main_spec_coverage      （主 spec Sources 并集）
              − open_change_coverage    （未归档 change 的 addressed 并集）
              − non_software
              − external
              − deferred
              − conflicted
  ```

  **不得写成「active ⊆ 若干项之并，差集即缺口」**——`deferred`、`external`、
  `conflicted` 都是 `active` 的子集且都不在覆盖侧，那样算出的差集必然混入它们，
  把「已裁决延期」「由外部系统承担」「待上游收敛」误报成「漏做」。
  报告须分列七块，只有最后一块是 ERROR：

  ```
  Active FRIDs   44
  ├ Implemented  25   已归档进主 spec
  ├ Open changes  7   未归档 change 覆盖中
  ├ Non-software  6   非软件交付（永久无需 spec）
  ├ External      3   外部系统承担（本仓不 spec，欠账仍在）
  ├ Deferred      1   已裁决延期，仍欠实现
  ├ Conflicted    2   待上游收敛
  └ Unaccounted   0   ← 真实缺口，ERROR
  ```

## 双向可达与放行

**双向可达小结**：正向（PRD → spec，防漏做）＝ V3.4 + V4.6 + V6.2；
反向（spec → PRD，防越权造需求）＝ V4.0 + V4.2 + V4.3 + V4.5。

**放行规则**：任一 ERROR 未清除则不得放行（apply 与归档同此标准）。
WARNING 可带裁决放行，裁决记入回显与基线的例外记录。

## 确定性实现

V1–V5 与 V4.8 的确定性部分已实现为 `tools/trace.py`
（用法 `tools/trace.py <产品仓库根> <change-name>`，退出码 0/1 可作 CI 门禁）。
**语义判断不在脚本内**——拆分完整性、DEC 范围覆盖仍由人核对；
一个假阳性的「通过」比不检更危险。
