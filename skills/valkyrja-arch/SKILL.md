---
name: valkyrja-arch
description: 技术契约治理层——讨论并裁决技术选型（ADEC）、采纳编码约定、定义跨 change 共享接口契约，为 OpenSpec 的 design.md 提供项目级技术地基。当用户要讨论技术方案、确定技术选型、采纳或制定编码/数据库/接口/日志/鉴权约定、定义或修订共享契约、盘点架构决策现状时，必须使用本技能。即使用户只是随口说"用什么存储"、"错误码怎么定"、"这个就定下来"、"把标准的 API 约定拿进来"、"内容包结构得定一下"，只要项目已有 docs/architecture/ 工作区，或用户明确要在本项目建立技术契约治理（bootstrap），都应触发本技能。未 opt-in 的项目（无该工作区且用户未要求建立）里的日常技术讨论不要接管，也不要主动提议 bootstrap。
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
4. **特权动作只能由人类显式确认后执行**：`bootstrap`（仅落盘步骤）、`decide`、
   `adopt`、`contract`、`publish`。
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

## 奠基性决策（必须在首个 change 进入 apply 之前完成）

一类特殊的 ADEC：**变更成本与其他决策根本不同**——契约变更破坏消费方（可控）、
存储选型变更换个实现（接口隔离即可），而奠基性决策一旦有代码就**要重写**，
成本随代码量指数上升。因此它们不能等到 apply 现场才定。

| 奠基项 | 内容 | 为什么必须提前 |
|---|---|---|
| **技术栈** | 语言/运行时、框架、UI 组件库、构建工具、测试框架、包管理 | 变更要重写；且**决定 catalog 的哪条 stack 轴可用** |
| **仓库代码布局** | surface→目录映射（前端/后端/小程序各落在哪）、是否 monorepo。**有哪些 surface 由产品侧范围决定，本层只裁决落位** | 多 surface 项目尤甚——第二个 surface 再补就要跨目录搬迁 |
| **编码约定采纳** | 按已定栈从 catalog adopt 对应条目 | 依赖上面两项 |

**技术栈是决策簇，不是单个决策**：选定语言与框架后才谈得上 UI 库、状态管理、
测试框架、编码规范——一串决策互为前提，须成组裁决。

**布局分两层**：**顶层 surface 划分必须显式裁决**（改起来最贵）；
**surface 内部结构随栈惯例走**（Vite 项目即 `src/`，Maven 项目即标准布局），
不必单独裁决，除非项目要偏离惯例。

奠基项齐备性由 `check` 核对；缺项时会话启动仪式**主动提议 `bootstrap`**。

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

工作区不存在时：确认系统名与**架构 DOMAIN**（见下），创建骨架与 STATUS.md，
并主动提议 `bootstrap`（骨架只是空目录，不构成任何决策）。

## ID 与格式契约

- ID 正则：`^(ADEC|ADISC)-[A-Z][A-Z0-9]*(_[A-Z][A-Z0-9]*)*-\d{3}$`，
  如 `ADEC-DEMO_KIOSK-003`。
- **架构 DOMAIN 命名系统/代码库，不是产品**。它进入与产品侧同一个全局 DOMAIN
  注册表，遵守全部既有规则：全局唯一、一经铸造永久冻结、禁版本型命名、
  禁连字符。**即使仓库与产品 1:1 也不得复用产品 DOMAIN**——冻结规则让错误永久化；
  这是「仓库级事物不得绑定单一产品」教训的同构应用（一仓多产品时，
  架构决策不属于任何单一产品）。新铸架构 DOMAIN 前须向用户说明以上各点，名字由用户定。
- 编号由本技能分配：**分配前全仓扫描该 DOMAIN 的全部 ID 引用**
  （decisions/ 目录之外还包括 `openspec/config.yaml` 投影、各 change 的
  design.md、源码注释），取「目录最大号」与「最大被引号」之大者 +1——
  目录部分丢失时，仍被外部引用的编号**不得复用**（bootstrap 的空目录
  前置扫描是本规则的特例）；发现重复即报错停止写入。
- ADEC frontmatter 至少含 `id / date / status / superseded-by`
  （status: accepted | superseded）。
- **奠基标记**：奠基性 ADEC 的 frontmatter 另含 `foundational: stack | layout`。
  这是「奠基项齐备」唯一的机读判据——本技能的 `check` 与 valkyrja-spec 的
  trace V1.4 都以「存在 `status: accepted` 且带对应 `foundational` 标记的 ADEC」
  为准，不做语义猜测。**supersede 奠基 ADEC 时新 ADEC 必须继承标记**，
  否则推翻旧决策会让齐备性静默退化为「未定」。
- **契约版本**：每份契约 frontmatter 含 `contract / version / date`，version 为
  递增整数，变更追加 Changelog 节说明破坏性；消费方（design.md）引用格式为
  `契约名@版本`（如 `content-package@2`）。
- **契约权威标记**：接口权威在外部系统（本仓只能记录自己的理解）时，
  frontmatter 另标 `authority: external`——版本号语义变为「我方理解的第 N 版」，
  对方变更只能被动发现。无此标记默认权威在本仓。
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

**主动提议 bootstrap（这是「帮助决策」与「决策仓库」的分界线）**：复述后，
若工作区不存在、或存在但**奠基性决策缺项**（技术栈 / 仓库布局 / 对应编码约定
未采纳），**主动说明缺什么、后果是什么、建议先跑 `bootstrap`**——
不要等用户来问。奠基项缺失的后果是具体的：第一个进入 apply 的 change
会被迫在实现现场临时决定技术栈，而那个决定既没有依据也不会留痕。

## 意图路由

不要求用户输入动作名。按话语自动路由：

| 用户话语特征 | 路由 |
|---|---|
| "从零开始"、"技术地基"、"有没有定好的框架"、"该定什么" | bootstrap（落盘步骤特权，需确认） |
| 探讨方案、比较技术、"聊聊用什么 XX" | discuss |
| "就用 X"、"定了"、"确认这个方案" | decide（特权，需确认） |
| "把 catalog 的 XX 拿进来"、"按标准约定来" | adopt（特权，需确认） |
| "定义 XX 契约"、"内容包结构定一下"、"改契约" | contract（特权，需确认） |
| "架构现状"、"有哪些决策"、"约定都有什么" | status |
| "体检"、"检查架构工作区" | check |
| "生成 lint 配置"、"把约定投影到 CI" | publish（特权，需确认） |

意图不明按 discuss 处理。**特权动作永不允许仅凭推断执行。**

## 特权动作确认

沿用与 valkyrja-prd 一致的结构：识别意图 → **不落盘** → 完整回显 → 等明确
"确认"后才写。疑问语气视为倾向，仅记 ADISC。

| 特权动作 | 回显必须包含 |
|---|---|
| bootstrap | 探测到的既有技术事实逐条（含来源文件）、每条的处理提议（补铸 ADEC / 仅记录）、待定奠基项及候选、**产品侧约束如何排除了哪些候选**、将铸的全部 ADEC 编号、将 adopt 的 catalog 条目 |
| decide | ADEC 编号、结论一句话、被否备选（禁止编造）、验收可观察性判定结果（为何不属产品侧）、引用的证据（TM/ADISC/实测） |
| adopt | catalog 条目 id 与版本、许可证 status、将做的项目化修改逐条、将铸的 ADEC 编号、落盘路径 |
| contract | 契约名与新版本号、字段级变更、**已知消费方及破坏性影响**、配套 ADEC；`authority: external` 类**改列本仓内消费方适配点**（我方无权裁决对方，见 contract 协议 external 条款） |
| publish | 将生成/修改的每个文件、对 openspec/config.yaml 的注入 diff、对 CI 的影响说明 |

**contract 是本技能最重的特权**——契约有消费方，变更即破坏。回显必须列出
已知消费方（现算：grep 各 change design.md 中的 `契约名@` 引用），
不得以「已更新」一句带过。

**多点裁决默认逐点推进（step-by-step），不整批平铺**：涉及多个决策点时
（bootstrap 的奠基簇、成批 adopt 等），按**依赖顺序**排开，一次只出示一个
决策点，讲清因果——上游约束如何收敛了候选、本选择又约束哪些下游决策点——
等裁决后再进下一点。一次平铺全部选项会造成选择过载，且掩盖点与点之间的
依赖关系（真实运行反馈）。用户可显式要求整批。

## 各动作运行协议

### bootstrap（特权）——建立技术地基

本技能的**入口流程**，与 valkyrja-prd 的 bootstrap 同构：
**探测 → 清点报告 → 逐节裁决 → 落盘**。它的存在理由是——本技能必须能回答
「**我该定什么**」，而不只是「把这个记下来」。
前三步**只读**，可直接执行；特权与确认只针对第四步落盘。

**重跑语义（幂等且只增）**：工作区已存在时，既有 ADEC / 契约 / 约定副本一律
作为「已有技术事实」进入清点，**保留原编号**，新决策取后续号——
ID 是身份，仓内 design.md 与源码注释都在引用它们，重编号会让这些引用
静默指向错误的决策（引用有效但语义漂移，比幽灵引用更难发现）。
落盘只**补缺失的文件**；已存在的 inventory.md / backlog.md 不重置，
STATUS.md 作为派生缓存按现状重算。

**空工作区的编号前置扫描**：`decisions/` 为空（或不存在）而要从 001 起编时，
必须先**全仓扫描** `ADEC-<DOMAIN>-` 引用（含 `openspec/config.yaml` 投影、
各 change 的 design.md、源码注释）。凡有命中即停止并要求人工处理——
清除残留引用，或从最大被引号 +1 续编。**空号池不等于空引用池**：
投影与引用可能在工作区之外存活（真实事故：重置后 config.yaml 旧投影使
001/002/003 被复用为不同语义，仅查 ID 存在性的检查全数假绿）。

**第一步：探测既有技术事实（只报事实，绝不推断意图）**

| 探测面 | 看什么 |
|---|---|
| 构建与依赖 | `package.json` / `pom.xml` / `build.gradle` / `go.mod` / `pyproject.toml` / `Cargo.toml` … |
| 目录布局 | 顶层 surface 划分、各 surface 根目录、是否 monorepo |
| 既有规范 | linter / formatter / tsconfig / 编辑器配置、编码规范文档、`CLAUDE.md` / `AGENTS.md` |
| CI | workflow 配置中已固化的运行时版本与检查项 |

> **发现 `package.json` 里有 vue，不等于「决定用 Vue」。** 那是**既成事实**，
> 必须问用户是否追认为决策。把探测结果直接当决策，就是在用推断替代裁决
> （违反宪法 4）。用户另有已定但未落盘的规范时，请其指出位置后读取。

**第二步：从产品侧读出技术约束**

只读 `prd/releases/` 与基线，沿 `Sources:` 回溯被列出的文件（与 valkyrja-spec
同一回溯纪律）。目标是找出**哪些 FRID 对技术选型构成硬约束**。
没有这一步，建议就只是偏好。

无任何 release 时（绿地项目先做技术地基是合法的）：本步显式记
「**产品约束：无 release 可读**」——空约束必须与「读了但没有约束」可区分
（机制静默失效教训）；此时按用户目标与偏好推进，并在所铸 ADEC 中标注
这些选型日后可能被首个 release 的 NFR/SEC 挑战。

**第三步：清点报告（四节；与 valkyrja-prd bootstrap 同构但不同节——
本层多出「建议与候选」，因为给技术建议属本层职责，而 prd 层 AI 不得补需求）**

| 节 | 内容 |
|---|---|
| 已有技术事实 | 探测到什么、来源文件、标注「建议补铸为 ADEC」或「仅记录」 |
| 待定奠基项 | 技术栈 / 仓库代码布局 / 按栈应采纳哪些 catalog 条目 |
| 建议与候选 | 每项 2–3 个候选，**并写明产品侧约束排除了哪些候选、依据哪条 FRID** |
| 缺口与冲突 | 既有事实与产品约束矛盾（如既有代码依赖某能力而某 NFR 禁止它） |

**建议必须给推导，不得凭喜好。** 正确形态是「NFR-X-002 禁止硬依赖 Service Worker
→ 排除依赖 SW 的方案；DEC-X-015 要求从本地文件夹直接打开即可运行 → 倾向零运行时依赖」。
**产品约束先收敛候选集，剩下的才是用户的偏好空间**——AI 在偏好空间内不做选择。

**第四步：逐节裁决与落盘**

按「多点裁决默认逐点推进」规则（见特权动作确认节）出示：决策簇按依赖顺序
一次一个点，因果说清。**补铸与新决策同为 decide 级特权，逐条确认，
不得批量默认通过。** 经确认后：

```
铸奠基 ADEC（技术栈 / 仓库布局，一决策一文件，frontmatter 带 foundational 标记）
→ 按已定栈 adopt 对应 catalog 条目（走完整 adopt 管线，不跳步）
→ 补齐缺失的 inventory.md / backlog.md / STATUS.md（已存在的不重置）
```

补铸的 ADEC：`date` 用**裁决日**（与 prd 补铸 DEC 同规），正文注明其
**既成事实来源**（如「apply 现场决定，事后补铸」），不伪装成事前决策——
历史不美化是宪法 5 的应有之义。

### discuss
自由技术讨论。职责：推进比较、指出与既有 ADEC/契约/已采纳约定的冲突、
识别值得记录的增量并 checkpoint 到 ADISC。**讨论中出现的产品侧问题**
（按验收可观察性判据）标注「应回流上游」，不在本层裁决。
一个话题一个 ADISC 文件，追加式；候选规则记入 `backlog.md`（含触发条件）。

### decide（特权）
经确认后按 `templates/adec.md` 铸 ADEC。推翻旧决策时旧 ADEC 标
`superseded-by`，不删除。ADEC 可引用 TM / DEC 作证据（只读；沿产品侧
Sources 链规则），**但权威不传递**——引用 DEC 不等于本决策变成产品承诺。

### adopt（特权）

**前置：采纳 stack 类条目前，技术栈必须已有有效 ADEC。** catalog 按
`concern × stack` 两轴组织，栈未定就无从知道该取哪条轴上的条目——
此时不得凭代码里「看起来像什么」推断，正确出口是先走 `bootstrap` 或 `decide`
定下技术栈。通用条目（`stack: common`）不受此前置约束。

**前置二：requires 闭包。** 条目 frontmatter 声明 `requires: <基础条目>` 时，
基础条目必须已被本项目采纳（`conventions/` 有其副本）——未采纳则先走基础层
的 adopt，**不得孤立采纳绑定层**。

**第三方声明传播**：`modified: 摘编` 的第三方条目（如 MIT 来源）adopt 时，
其完整版权与许可声明必须随副本传播到**消费仓**（`docs/architecture/NOTICE.md`
或仓根 NOTICE），不能只在 catalog 侧留存——副本入了谁的仓，义务就跟到谁的仓。

从 catalog 选用约定的完整管线（不得跳步）：

```
读 catalog 条目（内置或私有源，多源规则见 catalog 节）
→ 核对许可证 status（license-unknown 不得采纳入仓；local-only 只可入私有项目仓）
→ 提议项目化修改（增/删/改，逐条）→ 确认 → 落盘 conventions/（自包含副本
+ 指纹 frontmatter，私有源带 source 标识）→ 铸 ADEC 记录采纳理由与全部偏离
```

catalog 更新**不自动同步**；`check` 发现 `adopted-from` 版本落后只提示。
升级 = 新一轮 adopt + 新 ADEC。

### contract（特权）
定义或修订共享接口契约。新契约按 `templates/contract.md`；修订时：
版本号 +1、Changelog 记破坏性、回显消费方影响。契约描述**接口形状与语义**
（字段、格式、版本兼容规则），不写实现——实现属各 change 的 design/代码。

**`authority: external` 类契约**（接口权威在外部系统，如对方的 CMS/收单后台）：
修订动因只能是「我方理解变化」或「对方实际行为变化」，不是我方裁决；
确认回显不列对对方的破坏性影响（我方无权裁决对方），改列**本仓内消费方**
需要跟进的适配点；不得对其做「我方可演进契约」式的版本规划。

### status（只读）
现场扫描计算：有效 ADEC / superseded 链、契约清单与各自版本、已采纳约定
及其 adopted-from 版本、backlog 中触发条件已成立的项、
**引用完整性摘要**（ADEC 互引、契约消费方引用的版本是否落后）。

### check（体检；报告只读，自动修复项另经确认执行）
对照本 SKILL.md 契约体检：ID 正则与编号连续性；ADEC frontmatter 完备性与
superseded 链完整性（指向的 ID 真实存在）；契约版本与 Changelog 一致性；
采纳副本指纹完备性；`adopted-from` 版本落后（**仅提示**；带 `(source: …)`
指纹的按源名在 `~/.claude/valkyrja/catalog/` 解析，源不可达**显式报
「跳过（源不可达）」**，不得静默通过）；
契约消费方引用落后版本（**仅提示**，升级是消费方 change 的决定）；
inventory 条目所指实现的存在性（记录了路径的条目）；
**奠基性决策齐备性**——`foundational: stack` 与 `foundational: layout`
是否各有一条 accepted ADEC（机读判据，见「ID 与格式契约」），
缺项报 `[需人工处理]` 并建议跑 `bootstrap`；已定栈有对应 catalog 条目
而未采纳的**仅提示**（少量甚至零采纳可以是合理裁决，不是缺陷）；
**投影一致性**（publish 产物）——扫描 `openspec/config.yaml` 中的
`ADEC-*`、`契约名@版本` 与约定文件引用：被引 ADEC 必须存在**且《标题》指纹
与 decisions/ 现文一致**（仅查 ID 存在性对「编号复用为不同语义」全盲），
被引 conventions/contracts 文件必须存在；指纹不匹配或文件缺失报
`[需人工处理]`（重跑 publish 重投影）；
**requires 闭包**——绑定层约定副本存在时，其 `adopted-from` 所指 catalog
条目声明的 `requires:` 基础层副本必须也已采纳，缺失报 `[需人工处理]`。
产出三态报告（可自动修复 / 需人工处理 / 仅报告），自动修复只改形式不改语义。

### publish（特权）
把技术地基**投影**到执行层，包括且仅包括：
1. 提议 `openspec/config.yaml` 的 `rules.design` 增补（把已采纳约定与有效 ADEC
   的要点摘要注入，供官方 propose 生成 design.md 时遵循）——**投影条目必须带
   标题指纹**，格式 `依据: ADEC-<id>《标题》`，使 check 的投影一致性检查能
   机检语义错位（仅记 ID 时，编号被复用为不同语义的错位不可检）；
   注入是 prompt 级建议，真正的保证在工具链与 V4.8。
   **投影是本技能产物在外部文件中的分身**：重置/重跑本工作区时必须同步
   清除或重投影，否则旧投影会以合法 ID 引用错误语义存活；
2. 生成 lint / 格式化 / 架构测试的**起步配置**（如 ArchUnit 测试骨架），
   交由项目工具链接管，本技能此后不追踪其执行。

## catalog（约定目录）

位于本技能 `references/conventions/`，**按需加载，不随 SKILL.md 进入上下文**。
条目按 concern × stack 两轴组织，frontmatter 契约与许可证纪律见
[references/conventions/README.md](references/conventions/README.md)。

**多源（D12 切片一）**：除内置 catalog 外，`~/.claude/valkyrja/catalog/<源名>/`
的每个子目录是一个**私有源**——条目格式与内置完全同构，把私有 catalog 仓
clone 或软链到该处即可（该位置不受 skill 升级覆盖）。adopt 亦接受显式源路径。

- **指纹带源**：私有源副本写 `adopted-from: <条目id>@<版本> (source: <源名>)`；
  无 `(source: …)` 即内置 catalog——既有指纹向后兼容，不需迁移。
- check 按源名解析比对版本；**源不可达显式报「跳过（源不可达）」**，
  不得静默通过（D12 问题③的降级语义随本切片生效）。
- 许可证纪律在多源下的精化：`license-unknown` 仍**不得 adopt 入任何仓**；
  `local-only` 的准确含义是**不得公开分发**（公开仓只放 stub）——其全文
  住私有源，在许可允许下（如自有内容）**可 adopt 入私有项目仓**。
核心纪律（宪法 8 + D6）：
- 出处四字段（source / license / modified / status）**收集时**标注，缺一不入库；
- `license-unknown` 条目**不得被 adopt 入任何仓**；`local-only` 的含义是
  **不得公开分发**（公开仓只放 stub，全文住私有源），许可允许时
  **可 adopt 入私有项目仓**——见上方多源节，两条规则以此处为准；
- 条目内容以「选择 + 绑定 + 增量」为主，不整段重抄已有公开资料；
- 源自真实项目的条目入库前**去业务化**：模式出仓、领域不出仓；
  客户名与内部项目名一律脱敏（自有项目统一以「内部项目」指代）。

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
