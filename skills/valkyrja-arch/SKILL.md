---
name: valkyrja-arch
description: 技术契约治理层——讨论并裁决技术选型（ADEC）、采纳编码约定、定义跨 change 共享接口契约，为 OpenSpec 的 design.md 提供项目级技术地基。当用户要讨论技术方案、确定技术选型、采纳或制定编码/数据库/接口/日志/鉴权约定、定义或修订共享契约、盘点架构决策现状时，必须使用本技能。即使用户只是随口说"用什么存储"、"错误码怎么定"、"这个就定下来"、"把标准的 API 约定拿进来"、"内容包结构得定一下"，只要上下文涉及 docs/architecture/ 工作区或工程技术约定的建立与演进，都应触发本技能。
---

# Valkyrja Arch（技术契约治理层）

本技能治理「**怎么建**」：技术选型、编码约定、跨 change 共享的接口契约。
它与 valkyrja-prd 同构（discuss → decide 的治理形态），但决策对象从产品语义
换成工程技术；产出被 OpenSpec 的 design.md 消费（`依据: ADEC-*`）。

## 第一原则（宪法，8 条，优先于本文件其他一切内容）

1. **只治理「怎么建」，不治理「要不要」。** 判据是**验收可观察性**：结论若出现在
   产品验收口径（利益相关方可见、验收可测）→ 属产品侧，回上游走 TM → DEC → FRID；
   只约束工程内部 → 本技能裁决为 ADEC。**冲突时产品侧永远优先**——
   ADEC 管辖事项日后被 DEC/FRID 覆盖时，该 ADEC 标注让位，不得对抗。
2. **本技能只铸 ADEC / ADISC，不铸任何产品侧 ID。** FRID、Q、DEC、TM、RN、DISC
   的编号空间均属上游。需要产品决策时回流上游，不代铸。
3. **文件系统是记忆，对话不是。** 未落盘的技术结论下个会话视为不存在；
   有效状态变化尽快 checkpoint。
4. **特权动作只能由人类显式确认后执行**：`decide`、`adopt`、`contract`、`publish`。
   语气含疑问（"就用 IndexedDB 吧？"）视为倾向，只记入 ADISC，不铸决策。
5. **历史不删除。** ADEC 一经铸造不可变，推翻用 `superseded-by` 链；
   契约版本只增不改；catalog 采纳的偏离记录在 ADEC 中，永不静默。
6. **派生值不落盘。** 决策计数、契约消费方清单、采纳数量等一律现算；
   STATUS.md 是唯一豁免的派生缓存。
7. **执行靠既有工具链，本技能不造 checker。** 约定的强制力来自
   linter / 类型检查 / 架构测试（ArchUnit 等）/ CI；`publish` 至多生成起步配置，
   不接管执行。valkyrja-spec 的 trace 只做**引用完整性**检查（V4.8），不做技术正确性。
8. **catalog 是素材，不是契约。** 只有经 `adopt` 落入项目 `conventions/` 的
   自包含副本才是项目规范；**本地副本优先于 catalog**，catalog 更新不自动同步。

## 术语：技术内容的三类与工作区的四种体裁

**三类技术内容**（来源、变更节奏、治理方式都不同，不得混为一谈）：

| 类别 | 例子 | 来源 | 变更特性 |
|---|---|---|---|
| **约定** convention | 错误信封形状、DB 命名铁律 | catalog 挑选（adopt） | 极少变 |
| **选型** selection | 本项目存储用 A 不用 B | 讨论后裁决（decide） | 少变，变则 supersede |
| **契约** contract | 内容包 manifest 结构、事件载荷字段 | 必须自己设计（contract） | 会演进，**变更破坏消费方** |

**四种工作区体裁**：

| 体裁 | 落点 | 性质 |
|---|---|---|
| 决策 | `decisions/ADEC-*` | 不可变，可 supersede |
| 约定副本 | `conventions/` | 采纳自 catalog 的自包含项目版 |
| 契约 | `contracts/` | 逐份版本化，有消费方 |
| **清单** inventory | `inventory.md` | 公共对象目录，**防 AI 重复生成已有实现**——编码前先查 |

外加 **backlog 机制**（`backlog.md`）：已识别但未沉淀的规则候选，每条必含
触发场景 / 当前状态 / 未来动作 / 触发条件；被实际触发后 **graduate** 为正式
ADEC 或约定，从 backlog 移除并记入 graduate 清单。不做投机性规则。

## 工作区结构

```
docs/architecture/
├── STATUS.md            # 唯一派生缓存
├── discussions/         # ADISC-* 技术讨论，按话题建档、追加式
├── decisions/           # ADEC-*  技术决策，一决策一文件
├── conventions/         # 已采纳约定的自包含副本
├── contracts/           # 共享接口契约，逐份版本化
├── inventory.md         # 公共对象清单
└── backlog.md           # 规则候选（带触发条件）
```

工作区不存在时：确认系统名与**架构 DOMAIN**（见下），创建骨架与 STATUS.md。

## ID 与格式契约

- ID 正则：`^(ADEC|ADISC)-[A-Z][A-Z0-9]*(_[A-Z][A-Z0-9]*)*-\d{3}$`，
  如 `ADEC-OWSC_KIOSK-003`。
- **架构 DOMAIN 命名系统/代码库，不是产品**。它进入与产品侧同一个全局 DOMAIN
  注册表，遵守全部既有规则：全局唯一、一经铸造永久冻结、禁版本型命名、
  禁连字符。**即使仓库与产品 1:1 也不得复用产品 DOMAIN**——冻结规则让错误永久化；
  这是「仓库级事物不得绑定单一产品」教训的同构应用（一仓多产品时，
  架构决策不属于任何单一产品）。新铸架构 DOMAIN 前须向用户说明以上各点，名字由用户定。
- 编号由本技能分配：扫描对应目录取最大号 +1；重复即报错停止写入。
- ADEC frontmatter 至少含 `id / date / status / superseded-by`
  （status: accepted | superseded）。
- **契约版本**：每份契约 frontmatter 含 `contract / version / date`，version 为
  递增整数，变更追加 Changelog 节说明破坏性；消费方（design.md）引用格式为
  `契约名@版本`（如 `content-package@2`）。
- **采纳副本指纹**：`conventions/` 下每份文件 frontmatter 含
  `adopted-from`（catalog 条目 id + 日期版本）与 `adopted-by`（ADEC id）。
  正文是就地修改后的连贯项目版；**改了什么、为什么改，记在 ADEC 里**，
  正文不打补丁标记。

## 会话启动仪式（Session Resume）

首次进入本技能时按顺序读取（不全量扫描）：

1. `STATUS.md`
2. `decisions/` 全部文件（决策必须短，全读）
3. `contracts/` 各文件的 frontmatter（只读版本与日期，不读全文）
4. `backlog.md` 中触发条件疑似已成立的项
5. 相关的最近 ADISC（按需，不超过 3 个）

然后用 3–5 句复述：有效 ADEC 数与最近决策、契约清单与版本、已采纳约定、
待决议题，再开始工作。

## 意图路由

不要求用户输入动作名。按话语自动路由：

| 用户话语特征 | 路由 |
|---|---|
| 探讨方案、比较技术、"聊聊用什么 XX" | discuss |
| "就用 X"、"定了"、"确认这个方案" | decide（特权，需握手） |
| "把 catalog 的 XX 拿进来"、"按标准约定来" | adopt（特权，需握手） |
| "定义 XX 契约"、"内容包结构定一下"、"改契约" | contract（特权，需握手） |
| "架构现状"、"有哪些决策"、"约定都有什么" | status |
| "体检"、"检查架构工作区" | check |
| "生成 lint 配置"、"把约定投影到 CI" | publish（特权，需握手） |

意图不明按 discuss 处理。**特权动作永不允许仅凭推断执行。**

## 特权动作握手

沿用与 valkyrja-prd 一致的结构：识别意图 → **不落盘** → 完整回显 → 等明确
"确认"后才写。疑问语气视为倾向，仅记 ADISC。

| 特权动作 | 回显必须包含 |
|---|---|
| decide | ADEC 编号、结论一句话、被否备选（禁止编造）、验收可观察性判定结果（为何不属产品侧）、引用的证据（TM/ADISC/实测） |
| adopt | catalog 条目 id 与版本、许可证 status、将做的项目化修改逐条、将铸的 ADEC 编号、落盘路径 |
| contract | 契约名与新版本号、字段级变更、**已知消费方及破坏性影响**、配套 ADEC |
| publish | 将生成/修改的每个文件、对 openspec/config.yaml 的注入 diff、对 CI 的影响说明 |

**contract 是本技能最重的特权**——契约有消费方，变更即破坏。回显必须列出
已知消费方（现算：grep 各 change design.md 中的 `契约名@` 引用），
不得以「已更新」一句带过。

## 各动作运行协议

### discuss
自由技术讨论。职责：推进比较、指出与既有 ADEC/契约/已采纳约定的冲突、
识别值得记录的增量并 checkpoint 到 ADISC。**讨论中出现的产品侧问题**
（按验收可观察性判据）标注「应回流上游」，不在本层裁决。
一个话题一个 ADISC 文件，追加式；候选规则记入 `backlog.md`（含触发条件）。

### decide（特权）
经握手后按 `templates/adec.md` 铸 ADEC。推翻旧决策时旧 ADEC 标
`superseded-by`，不删除。ADEC 可引用 TM / DEC 作证据（只读；沿产品侧
Sources 链规则），**但权威不传递**——引用 DEC 不等于本决策变成产品承诺。

### adopt（特权）
从 catalog 选用约定的完整管线（不得跳步）：

```
读 catalog 条目 → 核对许可证 status（license-unknown 不得采纳入仓）
→ 提议项目化修改（增/删/改，逐条）→ 握手 → 落盘 conventions/（自包含副本
+ 指纹 frontmatter）→ 铸 ADEC 记录采纳理由与全部偏离
```

catalog 更新**不自动同步**；`check` 发现 `adopted-from` 版本落后只提示。
升级 = 新一轮 adopt + 新 ADEC。

### contract（特权）
定义或修订共享接口契约。新契约按 `templates/contract.md`；修订时：
版本号 +1、Changelog 记破坏性、回显消费方影响。契约描述**接口形状与语义**
（字段、格式、版本兼容规则），不写实现——实现属各 change 的 design/代码。

### status（只读）
现场扫描计算：有效 ADEC / superseded 链、契约清单与各自版本、已采纳约定
及其 adopted-from 版本、backlog 中触发条件已成立的项、
**引用完整性摘要**（ADEC 互引、契约消费方引用的版本是否落后）。

### check（只读）
对照本 SKILL.md 契约体检：ID 正则与编号连续性；ADEC frontmatter 完备性与
superseded 链完整性（指向的 ID 真实存在）；契约版本与 Changelog 一致性；
采纳副本指纹完备性；`adopted-from` 版本落后（**仅提示**）；
契约消费方引用落后版本（**仅提示**，升级是消费方 change 的决定）；
inventory 条目所指实现的存在性（记录了路径的条目）。
产出三态报告（可自动修复 / 需人工处理 / 仅报告），自动修复只改形式不改语义。

### publish（特权）
把技术地基**投影**到执行层，包括且仅包括：
1. 提议 `openspec/config.yaml` 的 `rules.design` 增补（把已采纳约定与有效 ADEC
   的要点摘要注入，供官方 propose 生成 design.md 时遵循）——注入是 prompt 级
   建议，真正的保证在工具链与 V4.8；
2. 生成 lint / 格式化 / 架构测试的**起步配置**（如 ArchUnit 测试骨架），
   交由项目工具链接管，本技能此后不追踪其执行。

## catalog（约定目录）

位于本技能 `references/conventions/`，**按需加载，不随 SKILL.md 进入上下文**。
条目按 concern × stack 两轴组织，frontmatter 契约与许可证纪律见
[references/conventions/README.md](references/conventions/README.md)。
核心纪律（宪法 8 + D6）：
- 出处四字段（source / license / modified / status）**收集时**标注，缺一不入库；
- `license-unknown` / `local-only` 条目公开仓只放 stub，且**不得被 adopt 入仓**；
- 条目内容以「选择 + 绑定 + 增量」为主，不整段重抄已有公开资料；
- 源自真实项目的条目入库前**去业务化**：模式出仓、领域不出仓。

## 与 valkyrja-prd 的边界

- 判据即宪法 1 的验收可观察性；本技能发现需要产品决策的事项时，
  在 ADISC 标注「应回流上游」并提请用户走 valkyrja-prd 的 discuss/decide。
- TM 保留原职（给产品决策供技术事实）；同一份调研两侧按 ID 互引，不复制。
- 上游 DEC 已覆盖的技术约束（如平台中立、CSS 单位禁令）**不迁移、不重铸**——
  design.md 直接 `依据: DEC-*`；本技能只补它们未覆盖的工程内部决策。

## 与 valkyrja-spec 的接口

- design.md 的依据标注三态：`依据: DEC-*`（产品决策强制）、
  `依据: ADEC-*`（技术决策强制）、无依据（候选方案，须注明不构成约束）。
- 契约引用格式 `契约名@版本`；valkyrja-spec 的 trace V4.8 校验依据标注的
  **引用完整性**（幽灵 ERROR / superseded WARNING），不校验技术正确性。
- 本技能的产物路径（`docs/architecture/`）与产品侧（`docs/product/`）平级，
  互不越界写入。

## 模板

- [adec.md](templates/adec.md) — ADEC 决策文件
- [adisc.md](templates/adisc.md) — ADISC 讨论文件
- [contract.md](templates/contract.md) — 共享接口契约
- [inventory.md](templates/inventory.md) — 公共对象清单
- [backlog.md](templates/backlog.md) — 规则候选 backlog
- [status.md](templates/status.md) — STATUS.md 结构
