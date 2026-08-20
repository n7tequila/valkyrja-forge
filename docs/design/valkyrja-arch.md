# valkyrja-arch 技术契约层 · 设计定稿

> 状态：**已定稿**——D1–D11 全部经用户裁决（D1–D10：2026-08-20；
> D11 由首次 apply 暴露的缺口驱动，同日追加），见「已裁决」节。
> 起草依据来自 DEMO 首次端到端运行中 `add-lead-capture-flow` 的真实 design.md 产出。
> 实施顺序按 D9：skill 本体 + 最小 catalog → 试点项目 架构工作区 → 回填 design.md → 恢复测试主线。

## 已裁决（2026-08-20）

- **D1 契约落点 = 选项 A**：共享接口契约放 `docs/architecture/contracts/`，
  普通版本化文档，design.md 引用。不做成 OpenSpec capability——先简单，
  等真出现多消费方漂移再考虑升级（升级路径保留在 D1 备选记录中，不删）。
- **D2 技术基线不冻结发布**：不照搬产品侧「发布即冻结 + rebaseline」。
  采用 ADEC 累积（一决策一文件、不可变、可 supersede）+ 契约逐份版本化。
  design.md 消费「当前有效集」；staleness 风险由 `check` 动作的
  「契约消费方是否落后于版本」检查兜底。
- **D3 边界判据 = 验收可观察性**：技术结论若出现在产品验收口径（利益相关方可见、
  验收可测）→ 产品侧，走 TM → DEC → FRID；只约束工程内部怎么建 → 技术侧，
  走 ADISC → ADEC。配套三规则：
  (1) TM 保留原职不动，ADISC 是工程决策讨论场，同一调研两边按 ID 引用不复制；
  (2) 跨引用作为证据允许（ADEC↔TM、DEC↔ADEC），但权威不传递——产品承诺只出自
  DEC，工程约束只出自 ADEC；
  (3) ADEC 管辖事项日后变为产品可见时，上游正常铸 DEC/FRID，该 ADEC 标注让位；
  **冲突时产品侧永远优先**。
  实证检验：既有 DEC-015/016/017 均背书验收可观察的 FRID，位置正确**不迁移**；
  试点项目 基线待澄清项第 3 条（SEC-003 存储技术）按此判据**改判为降级 ADEC**，
  不回流上游——密文存储/明文不可见/密钥可轮换已是 spec 行为，存储选型验收不可测。
- **D4 架构 DOMAIN = 独立的系统级 DOMAIN（选项 B）**：ADEC/ADISC 的 DOMAIN
  命名**系统/代码库**而非产品，进入同一全局 DOMAIN 注册表、遵守全部既有规则
  （全局唯一、永久冻结、禁版本型命名）。**即使仓库与产品 1:1 也不复用产品 DOMAIN**——
  冻结规则让错误永久化；这是 config.yaml 串域教训（仓库级事物不得绑定单一产品）
  的同构应用。ID 形如 `ADEC-DEMO_KIOSK-001`，自证其系统级身份。
  试点仓库的架构 DOMAIN 定名 **`DEMO_KIOSK`**（用户裁决，2026-08-20 铸造即冻结；
  裁决过程中曾出现「不复用」与「定名 DEMO」的矛盾，经确认取 DEMO_KIOSK）。
- **D5 第一波 catalog 清单（已批准，约 20 条）**：经评审 内部项目规范体系
  （其 spec 仓与前后端代码仓的规范文档，全部用户自有、
  回归驱动、含 ArchUnit 固化先例）后大幅修订——自有/自撰约 17 条，ECC 摘编缩至 2 条。
  - 通用 10：api-envelope（api-design + 内部项目 API 规范合并）、幂等标识、
    错误分类（内部项目异常四层泛化）、共享契约格式、命名、测试分层、日志上下文（MDC）、
    鉴权（JWT/401-403/单飞刷新，内部项目前后端两侧）、审计写入（不可篡改表 +
    AFTER_COMMIT 三层防御）、注释（自撰）
  - 数据库：`conv-db-relational-postgres` 实体（db-standard.md 泛化）；
    NoSQL 文档/KV/时序仅 stub，待真实项目拉动
  - web-vanilla 3：离线优先、本地存储、埋点契约
  - java-spring 3：java-ddd（用户 skill + 内部项目十条规则合并）、spring-layering、
    spring-testing（新增）
  - typescript 3：ts-vue-element（内部项目自有，新增）、frontend-api-layer、
    ts-react-patterns（ECC 摘编）
  - **第四体裁「清单 inventory」**（内部项目 common-catalog 模式：防 AI 重复生成的
    公共对象目录）与 **standards-backlog 机制**（候选规则带触发条件，触发后 graduate）
    吸收进 valkyrja-arch skill 本体，不作为 catalog 条目。
  - 内部项目派生条目入公开仓前**必须去业务化**（剥离案件/公证/业务错误码等领域细节，
    只留模式），且发布前经用户检查（见 D6 的发布门禁）。
  - 执行顺序：自有 + 自撰先行，ECC 摘编两条后置。
- **D6 许可证纪律（四条 + 一边界）**：
  (1) 出处标注在**收集时**完成（frontmatter 四字段缺一不得入库），不做事后追溯；
  (2) 许可证未知 = 不进公开仓，无例外；`~/.claude/rules/` 来源不明文件第一波不采收、
  不做全量考古，某条目真需要时再**懒溯源**单个文件；
  (3) ECC 摘编双重署名：条目 frontmatter 记 source/license/modified + 仓库根
  `NOTICE.md` 集中保留第三方版权声明（已核实 ECC LICENSE 为 MIT，
  Copyright (c) 2026 Affaan Mustafa）；
  (4) 发布门禁：catalog 条目推公开仓前经人工检查（特权握手），检查单三项——
  业务细节已剥离（**含客户名与内部项目名**）/ 四字段齐全且 redistributable /
  摘编版权声明未丢。
  边界：内部项目泛化条目同受检查单第 1 项约束，**模式出仓、领域不出仓**；
  带强业务指纹的模式宁可降级 local-only 也不硬泛化。
  （修订 2026-08-20：第 1 项补「内部项目名」——某自有项目名曾散布于 13 条
  frontmatter 与本文档并已推送，因其不是「客户名」而未被字面检查触发。
  又一例检查单字面通过、意图落空；脱敏后公开仓统一以「内部项目」指代。）
- **D7 adopt 产物 = 自包含副本 + 指纹 + 本地优先**：
  副本落 `docs/architecture/conventions/`，frontmatter 记 `adopted-from`
  （catalog id + 日期版本）与 `adopted-by`（ADEC id）。四条规则：
  (1) 副本**就地改**成项目版，正文保持连贯；改动与理由记在 ADEC，不在正文打补丁标记；
  (2) 项目副本优先于 catalog（内部项目「以本文档为准」先例）；
  (3) **不自动同步**——catalog 更新不推送，`check` 发现版本落后只提示不报错，
  升级走新 ADEC 重新 adopt；
  (4) catalog 条目以日期为版本（无兼容性语义，不用 semver）。
  依据：执行模型要求规范随仓库分发（纯引用出局）；内部项目本地副本优先的实战先例。
- **D8 trace 新增 V4.8：design.md 依据标注的引用完整性**：
  扫描 `依据: DEC-*` / `依据: ADEC-*`，被引决策必须真实存在——幽灵引用 ERROR；
  被引决策已 superseded → WARNING。三个不做：不查「该标注而未标注」（机器判不出
  一句话是否约束，留给 config 注入）；不查 DEC 范围覆盖（语义判断，维持人工）；
  无架构工作区不特殊豁免（引了不存在的 ADEC 本来就是幽灵引用）。
  定性：这是**引用完整性**检查（与 Sources 同族，防 AI 编造权威），
  不是技术正确性检查，不违反「技术侧不造 checker」原则。
- **D9 接回 试点项目 测试的顺序 = arch 先行、最小可用**：
  (1) 建 valkyrja-arch skill 本体 + 仅 试点项目 design.md 三空缺直接需要的 4 条 catalog
  （幂等标识、错误分类、共享契约格式、本地存储），其余 16 条不阻塞后补；
  (2) 初始化 试点项目 `docs/architecture/`（DOMAIN=DEMO_KIOSK），经握手铸首批 ADEC
  （存储技术定案＝SEC-003 降级悬案、幂等采纳、错误采纳）+ 首份共享契约（内容包结构）；
  (3) 回填 add-lead-capture-flow 的 design.md，三个空缺段改为真实 `依据: ADEC-*`
  引用——同时是 V4.8 首次实战；
  (4) 恢复主线：apply → trace(pre-archive, 含 V4.8) → archive → V6 →
  rebaseline v1.1 → V4.0(a) 联锁。
  依据：剩余测试环节无法绕过 apply（未实现即归档＝让主 spec 说谎）；
  现在 apply 则三空缺各自现编、arch 建成后必返工。
  此顺序让 试点项目 成为三层（prd/spec/arch）在同一真实项目上的依次首验。
- **D10 第三个 skill 正式确认 + 命名**：加 `valkyrja-arch`，命令 `/valkyrja:arch`。
  本项推翻了 valkyrja-spec RC 评审时「暂不加第三个 skill」的建议，理由是前提已变：
  当时反对的是纸面推演式的投机扩张；现在是证据驱动——真实端到端产出的 design.md
  钉着三个具体空缺，且内部项目已独立演化出其雏形（standards-backlog graduate 机制）。
  评审建议隐含的条件「等真实需要出现再扩」恰好被满足。
  命令沿用薄转接模式：纯委托、零路由逻辑，重申 decide / adopt / contract / publish
  四个特权动作的握手不因斜杠入口放宽。
- **D11 bootstrap 入口流程 + 奠基性决策（2026-08-20，首次 apply 暴露）**：
  首次真实 apply 中，技术栈（Vue/TS/Vite）与仓库布局在实现现场被临时决定且不留痕
  ——skill 只能回答「把这个记下来」，回答不了「我该定什么」，偏离了
  「帮助用户做技术讨论与决策」的初衷（用户裁决：应有与 prd 同构的询问过程）。
  产出四件套：
  (1) **bootstrap 动作**（探测既有事实 → 读产品约束 → 四节清点 → 逐节裁决落盘），
  与 prd bootstrap 同构但多出「建议与候选」节——给技术建议属本层职责，
  建议必须给推导（产品约束先收敛候选集，AI 在剩余偏好空间内不做选择）；
  多点裁决**默认逐点推进按依赖序**，整批须用户显式要求（真实运行反馈：
  平铺全部选项造成选择过载，且掩盖决策点之间的依赖关系）；
  重跑幂等且只增（保号、不重置既有文件——ID 是身份，重编号让仓内引用
  静默指向错误决策）。
  (2) **奠基性决策**概念：技术栈 / 仓库布局 / 按栈采纳约定，变更成本与普通 ADEC
  根本不同（有代码即重写），必须在首个 apply 前完成；技术栈是决策簇须成组裁决；
  布局分两层（surface→目录映射显式裁决，surface 内部随栈惯例）。
  (3) **`foundational: stack | layout` 机读标记**（frontmatter）：
  「奠基项齐备」的唯一机读判据，check 与 V1.4 共用，不做语义猜测；
  supersede 时新 ADEC 必须继承标记。格式契约先于工具——没有标记，
  齐备性检查只能靠猜。
  (4) **spec 侧 V1.4（WARNING 级）**：arch 工作区存在但缺奠基 ADEC 时告警。
  WARNING 而非 ERROR：不用 arch 的项目合法（无目录则显式报跳过），
  地基未定是治理债不是追溯断裂。实测：对首次 apply 后的试点项目跑 V1.4，
  一次命中真实缺口（缺 stack + layout）——这正是当初缺席的那道提醒。
- **D12 多项目共享模型（2026-08-21，apply 前讨论裁决）**：
  多仓统一技术规范**不做迁移工具、不做跨仓活引用**——执行模型要求规范随仓库
  分发（D7「纯引用出局」的同一理由），活引用在 clone/CI/离线下全碎，
  且单仓机检无法跨仓解析。改为**推广既有采纳模型**，三类内容分道：
  (1) **约定** → catalog 多源化：组织 catalog（私有仓）叠在内置 catalog 之上，
  adopt 时选源，`adopted-from` 指纹携带源标识；统一性来自**同源采纳 + 漂移可见**
  （check 比对版本落后，仅提示），不来自共享可变状态。
  (2) **组织级选型** → 组织 arch 仓（就是又一个 valkyrja-arch 工作区，独立
  DOMAIN，无需新 skill）铸组织 ADEC；项目**本地重铸**采纳 ADEC，Context 引
  组织 id 作证据（权威不传递，同 ADEC 引 DEC 模式）；design.md 永远只引本地
  ADEC，V4.8 解析规则零改动；偏离走本地 ADEC 记理由，巡检可见。
  (3) **跨仓契约** → 权威在组织仓，项目 vendor **逐字钉版副本**
  （`契约名@版本` 现成支持钉版）——与约定采纳相反的不对称性：约定鼓励
  项目化删改，**契约副本改一字即 fork，禁止任何项目化修改**。
  双向通道均沿既有纪律：promote（项目→组织）= 去业务化 + 出处四字段 +
  发布门禁（D5/D6）；adopt（组织→项目）= D7 管线。
  **契约三分类**（本项当日生效，c 类为 OWSC 下一步铸契约的真实形态）：
  a. 单仓跨 change 契约——现行协议已覆盖；
  b. 多仓同治理域契约——权威在组织仓；
  c. **对外部系统的接口记录**——权威在对方，我方只能记录自己的理解，
  frontmatter 标 `authority: external`，版本号语义为「我方理解的第 N 版」，
  对方变更只能被动发现，不得被当作我方可裁决演进的契约。
  **留待组织仓真实出现再裁的问题清单**（不预铸规则）：
  ①消费方登记——全体系首个不可现算、须人工维护的状态（跨仓 grep 不可达），
  登记义务挂点未定，且登记表失效是静默的；
  ②退役窗口——破坏性升级后生产方停旧版的条件（候选规则：登记表上旧版
  消费方清零前不得停）；
  ③跨源比对降级——组织源不可达时 check 须显式报「跳过（源不可达）」，
  不得静默通过（零对象 ≠ 零发现）。
  机制实现（adopt 多源、check 跨源比对、vendor 管线）**延后至第二个真实
  项目出现**（YAGNI）；c 类标记与语义先行入 SKILL.md 契约条款（本次同步），
  其余机制条款随实现一并入。owsc-demo 的 apply 不被本项阻塞。
  **切片一已实现（2026-08-21，用户裁决提前）**：多源 catalog——真实需求来自
  D6 悬案「local-only 条目全文没有家」。约定位置 `~/.claude/valkyrja/catalog/<源名>/`
  （子目录即源、不受 skill 升级覆盖）、指纹带源
  `adopted-from: <id>@<版本> (source: <源名>)`（无 source 段=内置，既有指纹
  零迁移）、源不可达显式报跳过（问题③的降级语义随之生效）、local-only 精化为
  「不得公开分发；许可允许时可 adopt 入私有项目仓」。切片二（组织 ADEC
  本地重铸）、切片三（跨仓契约 vendor）仍延后。

## 1. 问题（有真实证据，不是推测）

首次端到端跑到 propose 阶段时，官方 propose 在 design.md 中**被迫自行发明约定**三处：

| 空缺 | design.md 中的表现 |
|---|---|
| 幂等标识约定 | 留资补传与埋点上报都要幂等，但标识如何生成、什么格式、两者是否共用一套规则，本 change 只能自己定 |
| 错误与提示约定 | 超限 / 格式不合法 / 网络失败三类情况，文案层级、可重试性、是否上报——无项目级规范可依 |
| **跨 change 共享接口契约** | 同意文案版本号随内容包下发，这是本 change 与 `add-content-sync` 的共享约定。它既不属于 spec（不是可观察的产品行为），又不该只写在某一份 design.md 里（另一个 change 看不到） |

第三项揭示了一个**结构性空洞**：现有流水线里没有任何位置能容纳「跨 change 共享的技术契约」。
spec 装产品行为，design 装单个 change 的实现思路，config.yaml 装 prompt 级建议。

若剩余 13 个 change 各自决定这三类事，必然发散——这正是 AI 写代码跨 change 不一致的根因。

## 2. 关键区分：技术内容有三类，不是一类

设计的第一个结论是：把「技术侧的东西」当成一类来治理是错的。它们的来源、变更节奏、
归属和执行方式都不同。

| 类别 | 例子 | 本质 | 来源 | 变更节奏 |
|---|---|---|---|---|
| **约定**（convention） | REST 错误信封形状、DDD 聚合边界规则、命名规范 | 可复用、有业界共识 | 目录中挑选 | 极少变 |
| **选型**（selection） | 本项目用 REST 不用 GraphQL；本地存储用 A 不用 B | 项目决策，从候选中择一 | 讨论后裁决 | 少变，变则 supersede |
| **契约**（contract） | 内容包 manifest 结构；埋点事件载荷字段；补传接口形状 | **项目特有，目录里不可能有** | 必须自己设计 | 会演进，**变更破坏消费方** |

原始设想（约定库 + 发布到项目层）只覆盖第一类。第二类需要决策留痕。
**第三类是唯一完全无家可归的，也是最需要版本化的**——因为它像 API 一样有消费方。

## 3. 整体架构

```
                    ┌─────────────────────────────────────┐
                    │  约定目录 catalog（可复用素材）        │
                    │  skills/valkyrja-arch/references/    │
                    │  concern × stack 两轴，带出处与许可证  │
                    └──────────────┬──────────────────────┘
                                   │ 选用（adopt）
                                   ▼
  技术讨论 ─→ valkyrja-arch ─→  docs/architecture/
  （人 + AI）                    ├── decisions/   ADEC-*  技术决策（不可变、可 supersede）
                                ├── contracts/   共享接口契约（版本化）
                                ├── conventions/ 已采纳的约定（自包含副本）
                                └── STATUS.md    派生索引
                                   │
                                   │ design.md 消费，标注 依据: ADEC-*
                                   ▼
                    valkyrja-spec → OpenSpec change
                                     ├── specs   ← 源自 PRD（产品行为）
                                     └── design  ← 源自 ARCH（技术地基）
```

与产品侧的对称关系：

```
产品侧                          技术侧
RN（规范化需求条目）      ←→    catalog 条目（可复用约定）
DISC（讨论）             ←→    ADISC（技术讨论）
DEC（产品决策）          ←→    ADEC（技术决策）
TM（技术备忘）           ←→    —— 见待讨论 D7（边界重叠）
PRD release（冻结）      ←→    contracts（逐份版本化）+ ADEC 累积
```

**一个关键的不对称**：产品需求靠决策变更，技术契约靠**决策 + 发现**变更
（例如实测发现目标设备不支持某存储方案）。因此技术侧不宜照搬「整体冻结发布」，
更适合 ADR 式累积 + 契约逐份版本化。详见待讨论 D3。

## 4. 约定目录（catalog）设计

### 位置与加载

`skills/valkyrja-arch/references/conventions/` —— 按需加载，不进 SKILL.md 正文，
避免重蹈 valkyrja-spec 主文件过长的覆辙。

### 两轴分类

**concern（关注点）**：架构风格 / 接口契约 / 数据 / 前端 / 横切
**stack（技术栈）**：通用 / java-spring / typescript-node / typescript-react / go / python / web-vanilla

同一 concern 在不同 stack 下往往需要独立条目——DDD 在 Java（Spring + JPA）
与在 TypeScript 下的落地方式差异极大，不能合并。

### 条目 frontmatter（出处与许可证是硬要求）

```yaml
---
id: conv-api-error-envelope
concern: 接口契约
stack: 通用
source: <URL 或 "自撰">
license: MIT | Apache-2.0 | CC-BY-SA | 自有 | 未知
modified: 否 | 摘编 | 改写
status: redistributable | local-only | license-unknown
---
```

### 双层分发（因为 valkyrja-forge 是公开 MIT 仓库）

| status | 处理 |
|---|---|
| `redistributable` | 全文进公开仓，保留原版权声明 |
| `local-only` / `license-unknown` | **公开仓只放 stub**（标题 + 出处链接 + 为何不收全文），全文仅存于本机 `~/.claude/` |

把来源不明或带传染性许可证的内容收进 MIT 公开仓再分发，是实际法律风险，不是洁癖。

### 不重写已有内容

ECC 已有 `api-design`、`java-domain-driven-design`、`springboot-patterns`、
`frontend-patterns` 等；`~/.claude/rules/` 下另有 common + 六种语言分层规则。
catalog 条目应以**选择 + 绑定 + 增量**为主（「本项目采纳 X，额外规定 Y，不采纳 Z 因为…」），
而非再抄一遍——两份副本必然漂移。

## 5. valkyrja-arch skill 设计

### 定位

技术侧的讨论与决策治理层，结构与 `valkyrja-prd` 同构（discuss → decide 的
治理形态），只是决策对象从产品语义换成技术选型与契约。
它**不写实现代码，不写 spec，不替 design.md 做设计**——只产出被 design.md 消费的地基。

### 工作区

```
docs/architecture/
├── STATUS.md              # 唯一派生缓存
├── discussions/           # ADISC-* 技术讨论，按话题建档、追加式
├── decisions/             # ADEC-*  技术决策，一决策一文件
├── conventions/           # 已采纳约定的自包含副本（含出处）
├── contracts/             # 共享接口契约，逐份版本化
├── inventory.md           # 公共对象清单（防 AI 重复生成，D5 第四体裁）
└── backlog.md             # 规则候选（带触发条件，触发后 graduate）
```

### 动作集（D11 后为八个）

| 动作 | 性质 | 职责 |
|---|---|---|
| `bootstrap` | **特权**（落盘步骤） | 入口流程：探测既有事实 → 读产品约束 → 四节清点 → 逐点裁决 → 铸奠基 ADEC + 首采约定（D11） |
| `discuss` | 普通 | 技术议题讨论，识别增量并 checkpoint |
| `decide` | **特权** | 铸造 ADEC。技术选型、约定采纳、契约变更均由此固化 |
| `adopt` | **特权** | 从 catalog 选用约定 → 写入 `conventions/` + 铸一条 ADEC 记录采纳理由与增量 |
| `contract` | **特权** | 定义或修订共享接口契约，版本化 |
| `status` | 只读 | 现算：已采纳约定、有效 ADEC、契约版本、待决议题 |
| `check` | 只读 | 契约体检：ADEC 引用完整性、契约消费方是否落后于版本、许可证 status 合规 |
| `publish` | **特权** | 把技术地基投影到执行层（见第 7 节） |

### ID 命名空间

`ADEC-<DOMAIN>-<NNN>`、`ADISC-<DOMAIN>-<NNN>`，沿用产品侧的 `TYPE-DOMAIN-NUMBER` 结构
与「永不重编号」规则。DOMAIN 是否与产品侧共用见待讨论 D4。

## 6. 与 valkyrja-spec 的接口

**新增消费约定**：design.md 除现有的 `依据: DEC-*`（产品决策背书）外，
新增 `依据: ADEC-*`（技术决策背书）。二者语义并列：

- `依据: DEC-*` —— 该实现约束由**产品决策**强制（如 DEC-015 平台中立）
- `依据: ADEC-*` —— 该实现约束由**技术决策**强制（如 ADEC-003 幂等标识格式）
- 无任何依据 —— 候选方案，须注明「无决策背书，不构成约束」

**config.yaml 注入扩展**：`rules.design` 目前只有 2 条且全是关于*来源合法性*的
（须标注依据 / 无背书须注明）。技术契约层落地后应补入*技术怎么做*的条目摘要，
使 propose 生成 design.md 时能直接遵循项目地基。

**可能的 trace 扩展**：design.md 中标注的 `依据: (A)DEC-*` ID 是否真实存在，
是可机检的追溯项，与 Sources 检查同族。见待讨论 D8。

## 7. 执行模型（与产品侧根本不同）

产品侧靠 `trace` 机检；**技术侧靠既有工具链**：

| 层 | 载体 | 谁执行 |
|---|---|---|
| 决策与理由 | `docs/architecture/decisions/` | 人（评审时查阅） |
| 人类可读规范 | `docs/architecture/conventions/` | 人 + 任意 agent（随仓库分发） |
| AI 行为约束 | `openspec/config.yaml` 的 `rules.design` | propose/design 阶段的模型 |
| **真正的强制** | linter / 类型检查 / 架构测试 / CI | 工具链 |

**不要为技术契约再造一套 checker**。能接到 eslint / checkstyle / ArchUnit / tsc 上的，
就交给它们；`valkyrja-arch` 的 `publish` 动作至多生成起步配置，不接管执行。

## 8. 讨论清单处置

D1–D10 已全部裁决，结论收录于文首「已裁决」节。原始讨论过程见会话记录，
本文档只保留结论与依据。
