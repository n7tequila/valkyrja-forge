<!-- change 的 specs/<capability-path>/spec.md 范例。
     本文件的 Sources: 行格式已在 openspec v1.9.0 实测验证：
     - 通过 `openspec validate --type change --strict`，零 issue
     - 经 `openspec archive` 合并后随 ADDED / MODIFIED 保留进主 spec
     - 在 `openspec show <spec> --type spec --json` 中为 requirements[].text 首行
     照抄本结构，不要变体。 -->

<!-- 仅当本 delta 引入全新 capability 时才写 Purpose；
     已存在的 capability 不要写（其 delta 的 Purpose 会被忽略）。
     需 50 字符以上，否则 --strict 报 too brief。 -->
## Purpose

<一到两句说明该 capability 是做什么的。>

## ADDED Requirements

### Requirement: <需求名称，自然语言，不含 ID>
Sources: <REQ-DOMAIN-NNN>

The system SHALL <可观察行为。只写 WHAT，不写实现技术>。

#### Scenario: <场景名称>
- **WHEN** <触发条件>
- **THEN** <预期结果>

<!-- 复合 REQ 拆分：拆出的每条 Requirement 的 Sources 都写同一个原 REQ ID。
     原 ID 保持不变、不细分，禁止子 ID 语法（如 REQ-X-006#1）。 -->

### Requirement: <同一原需求拆出的另一个行为点>
Sources: <与上面相同的 REQ-DOMAIN-NNN>

The system SHALL <另一个可独立验证的可观察行为>。

#### Scenario: <场景名称>
- **WHEN** <触发条件>
- **THEN** <预期结果>

## MODIFIED Requirements

<!-- 必须从主 spec 完整复制整个 Requirement 块（标题到全部 Scenario）后再编辑。
     标题须与主 spec 完全一致（whitespace-insensitive）。
     部分内容的 MODIFIED 会在合并时丢失细节。

     Sources 的两类 ID 判定标准不同（见 SKILL.md 契约二）：
     - 沿袭的旧 ID：必须保留、不得删除；**允许已 DEPRECATED**，
       只需在 PRD 历史中合法存在 —— 那是历史 provenance 凭证。
     - 本次新增的 ID：必须属于当前 release 的 active 集且已被基线裁决为纳入。
     机器判定：新增集 = 本 delta 的 Sources − 主 spec 同名 Requirement 的 Sources。 -->

### Requirement: <与主 spec 完全一致的标题>
Sources: <保留主 spec 原有 ID，可为 DEPRECATED>[, <本次新增的 active ID>]

The system SHALL <更新后的完整行为描述>。

#### Scenario: <主 spec 已有的场景，必须原样带上>
- **WHEN** <触发条件>
- **THEN** <预期结果>

#### Scenario: <本次新增的场景>
- **WHEN** <触发条件>
- **THEN** <预期结果>

## REMOVED Requirements

<!-- 注意：REMOVED 块本身**不写 Sources 行**（照 OpenSpec 原生格式，
     只有标题 + Reason + Migration）。
     它触达了哪些 FRID，由 trace 从**主 spec 中同名 Requirement 的 Sources**反查
     —— 这就是契约三 addressed() 存在的原因：直接取 delta 的 Sources 并集会得到 ∅，
     使正常的删除型 change 永远无法通过 V4.6。

     合法性条件（V4.4）：反查出的 FRID 必须全部 ∈ deprecated(当前 release)。
     移除一个仍 active 的需求的全部 spec 引用 → ERROR，
     正确出口是上游标 DEPRECATED 并发新 release，再 rebaseline 规划退休 change。 -->

### Requirement: <被移除的需求标题>
**Reason**: <为什么移除>
**Migration**: <使用方如何迁移>

## RENAMED Requirements

<!-- 同 REMOVED：本块不写 Sources 行。
     addressed() 从主 spec 中 FROM 所指 Requirement 的 Sources 反查。 -->

- FROM: `### Requirement: <旧名称>`
- TO: `### Requirement: <新名称>`

<!-- 格式硬约束（openspec 强制，违反会静默失效或校验失败）：
     - Scenario 必须正好 4 个 # —— 3 个或用 bullet 会静默失败
     - 每条 Requirement 至少一个 Scenario
     - 正文须含 SHALL / MUST，避免 should / may
     - 技术名词不得出现在 Scenario 的 WHEN/THEN 中
       （会把实现锁进验收条件，任何重构都必然破坏 spec）
     - delta 不得放在 specs/ 根，必须在 specs/<capability-path>/ 下 -->
