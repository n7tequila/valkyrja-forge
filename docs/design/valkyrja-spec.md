# valkyrja-spec 开发治理层 · 设计记录

> 状态：**已在真实项目验证至 apply 前全链**（baseline → decompose → propose →
> trace → rebaseline 联锁）。本文档记录设计决策及其依据；每条规则都注明来源——
> 是纸面推演、外部评审、还是真实运行踩出来的。

## 1. 定位：治理编排层，不是 OpenSpec 的替代品

设计前的关键调研结论（实测，非文档推断）：`openspec init --tools claude` 会按当前
profile 自动装官方 workflow skills（propose / apply / archive / explore 等）到项目
`.claude/`。**标准流程官方已经实现**。

因此本技能只做官方不做、也不该做的事：

| 官方负责 | 本技能负责 |
|---|---|
| change 目录创建、proposal/specs/design/tasks 生成 | Released PRD 消费与需求基线 |
| apply 实现、archive 合并 | change 划分裁决、追溯闭环、放行门禁 |
| validate 格式校验 | PRD ↔ spec 的语义追溯（validate 管不到的部分） |

宪法第 8 条「委托优先于重造」即源于此。**代价是必须接受官方 skill 的约束**
（planning boundary 强制回合边界、一次只建一个 change），不试图绕过——
它们与「人保留决策权」同向。

## 2. 三个机读契约

设计的核心是三个格式契约。**它们全部先手工实测再固化**（项目原则：格式契约先于工具）。

### 契约一：Requirement Authority（proposal.md 内）

```
## Requirement Authority
PRD-Release: <路径>
Baseline: <路径>
Covered-FRIDs: <逗号分隔>
```

**为什么放 proposal 而不是 config.yaml**（评审第二轮 P0）：`openspec/config.yaml`
是整个 OpenSpec root 的项目级配置，而一个仓库可能同时存在多个 DOMAIN 的 PRD。
把具体 PRD 路径写进 config，后建 change 的绑定会覆盖先建的——**串域**：
A 产品的 change 后续 apply 时读到 B 产品才是需求权威。PRD 绑定属于 change，不属于项目。

实测确认：proposal.md 增加此自定义节不影响 `openspec validate --strict`。

### 契约二：Sources 行（spec delta 与主 spec 内）

`### Requirement:` 标题的**下一行**必须是 `Sources: <FRID>[, <FRID>...]`。

**为什么是正文行而不是标题内嵌 ID**：MODIFIED delta 要求标题与主 spec 精确匹配，
把 ID 塞进标题会让「改需求标题文案」变成破坏性操作；放正文则标题可自由演进。
**为什么单行逗号分隔而非 PRD 那样的多行 bullet**：该行位于 Requirement 正文区内，
OpenSpec 会把它连同正文一并归属该 Requirement，多行 bullet 易与需求内容混淆。

四项实测（v1.9.0）：不触发 `validate --strict` 任何 issue；随 ADDED / MODIFIED
合并进主 spec；在 `show --json` 中为 `requirements[].text` 首行（CI 可首行正则提取）；
`openspec archive` CLI 自带合并实现，不依赖 sync skill 是否安装。

**历史 provenance 与当前 authority 的区分**（评审第三轮 P0）：需求 DEPRECATED 后，
「MODIFIED 必须保留既有 Sources」与「Sources 必须属于 active 集」两条规则直接对撞，
该 Requirement 无论怎么写都过不了 trace。分场景判定是唯一自洽解——
ADDED 全部必须 active∩included；MODIFIED 沿袭的旧 ID 只需 ∈ historical；
MODIFIED 本次新增的必须 active∩included。「本次新增」机器可判：
`delta Sources − 主 spec 同名 Requirement 的 Sources`。

### 契约三：addressed(change)（评审第三轮 P0，最隐蔽的一个）

**不得用「delta 的 Sources 并集」代表一个 change 处理了什么**——该并集在三种场景下
与事实不符：

| 场景 | 用并集的后果 |
|---|---|
| MODIFIED 保留历史 provenance ID | 历史 ID 被误判为范围蔓延，**永久假警报** |
| REMOVED（块内无 Sources 行） | 并集为 ∅，`Covered ⊆ ∅` 恒假，**正常删除型 change 永远无法放行** |
| RENAMED（同上） | 同上 |

因此按 delta 操作分别计算：ADDED 取 delta Sources；MODIFIED 取
`delta_sources − (main_sources − Covered)`；REMOVED / RENAMED 从主 spec 同名
（或 FROM 所指）Requirement 的 Sources **反查**。全部输入在盘上，现算不落盘。

## 3. FRID：一个术语挽救了三分之二的覆盖检查

评审第二轮 P0。原设计文本混用「REQ 集」指代四类正式需求，按字面实现 parser 会
只匹配 `REQ-*`。真实 PRD 的构成证明了危害：44 条需求里 REQ 只有 15 条，
**BR/SEC/NFR 占 29 条**——安全与性能需求会整类跳过覆盖检查，
造成「功能做完了、安全漏了、trace 依然 PASS」的假安全。

```
FRID = REQ | BR | SEC | NFR
```

全文所有覆盖检查、集合运算、追溯判定一律针对 FRID 全集。

## 4. 裁决集合的演化：从四类到六类

| 处置 | 集合 | 来源 |
|---|---|---|
| 直通 / 拆分 | `included` | 初始设计 |
| 延期 | `deferred` | 评审第二轮（原与「排除」混为一谈） |
| 非软件 | `non-software` | 评审第二轮 |
| **外部系统** | `external` | **真实运行发现** |
| 冲突 | `conflicted` | 初始设计（但集合代数漏了它，见下） |

**deferred 与 non-software 必须分开**：`non-software` 是「永久不需要 spec」，
`deferred` 是「仍欠一份实现」。合并会让延期项在覆盖对账中被当作已解释，长期静默遗忘。

**external 是真实 PRD 逼出来的**：一条需求可能是软件、但属于本仓之外的系统
（后台 CMS、线索池）。原五类无一能表达——判 `non-software` 会让跨系统欠账被永久免责，
判 `deferred` 又无法区分「本仓欠」与「别处在做」。

**混合体 FRID**（同批发现）：一条需求的行为点可能分属不同交付归属。解法是
**行为点层级标注交付归属，FRID 层级仍取单一处置**（只要有至少一个本仓软件行为点
即判 included），集合代数不破而混合事实不丢。

**自查发现的集合代数漏洞**：加入 deferred/non-software 后，V3.1 的漏裁决检查写成
`active ⊆ (included ∪ deferred ∪ non-software)`——**每条合法的「冲突」裁决都会被
误报为漏裁决**。这是与假安全相反方向的必然误报，同样毁掉 trace 可信度。

## 5. trace：放行门禁，不是格式检查器

**命名刻意与官方区分**：官方 `verify` workflow 判定「**实现代码**是否匹配 change
artifacts」；本技能的 `trace` 判定「**PRD ↔ spec** 的追溯闭环」。两种不同的一致性，
互补不互替。

检查分六组：V1 前提 / V2 PRD 侧（防 release 被手改）/ V3 基线对账 /
V4 delta 侧 / V5 委托官方 validate / V6 归档后。两个强制触发时机：apply 前、归档前。

**V6.2 的减法写法**（评审第三轮）：不得写成「active ⊆ 若干项之并，差集即缺口」——
`deferred`/`external`/`conflicted` 都是 active 子集且都不在覆盖侧，那样算出的差集
必然混入它们，把「已裁决延期」误报成「漏做」。必须显式做减法并分列七块，
只有 `unaccounted` 是 ERROR。

**V4.8 依据引用完整性**（arch 层设计时确立）：检查 design.md 的 `依据: DEC-*` /
`依据: ADEC-*` 指向的决策真实存在。定性为**引用完整性**检查（与 Sources 同族，
防 AI 编造权威），不是技术正确性检查——后者属 linter / 架构测试 / CI。

**放行规则**：任一 ERROR 不得放行；WARNING 可带裁决放行，裁决记入例外记录。
因此 V4.5 + V4.6 只在**无批准例外时**才等价于 `addressed == Covered`。

## 6. 与官方 skill 的冲突缓释

调研列出 12 条潜在冲突，真正会咬人的四条及对策：

| 冲突 | 对策 |
|---|---|
| propose 会重新追问 PRD 已定事项 | config.yaml 注入 context/rules。**但必须说明效力边界**：prompt 级建议，官方明文规定与内置指令冲突时以内置为准；真正保证在 trace 机检 |
| explore 可绕过治理层直接建 change | 不禁止（合法探索出口），但 status/trace 列为**计划外 change**，一律不得通过归档门禁 |
| `skip_specs: true` 是验证逃生口 | 视为需人工裁决的例外：trace 一律 ERROR，除非基线例外记录中已有裁决 |
| 官方 archive「警告从不阻塞」 | **归档改走 CLI**（`openspec archive`）——自带 validate→合并→退休→移动→失败回滚，不依赖 sync skill，且绕开「不阻塞」哲学 |

**诚实写明的能力边界**：用户直接调 `/opsx:archive` 或 CLI 时本技能**无法拦截**；
也**无法事后证明**某次归档当初是否跑过 trace（trace 只读、不写 receipt）。
`check` 能做的是重新验证归档产物现在是否仍满足契约——这与「当时是否放行过」是两回事。

## 7. 环境依赖的条件分支（实测修正）

评审曾建议「缺 sync workflow 就先跑 `openspec update`」。**实测推翻**：
`update` 按当前 profile 重新生成，profile 若排除了 sync，跑了也是空操作。
正确逻辑必须先判 profile：

```
openspec config get workflows
  ├── 含 sync 但文件缺失 → 产物过期，项目内 openspec update（不动全局）
  └── 不含 sync         → update 无效，唯一出口是改 profile（全局配置，需人确认）
```

同理适用于 `verify`。**verify 缺失比 sync 严重**：sync 缺失已由 CLI 归档绕过，
verify 缺失没有任何替代——闭环会缺「代码 ↔ artifacts」一段，必须显式告知后果。

## 8. 演进记录：每条规则的来源

| 轮次 | 发现 | 产出规则 |
|---|---|---|
| 初始设计 | 四项裁决（定位/追溯载体/init 前提/sync 处理） | 骨架 |
| 评审 1 | 追溯载体、委托边界确认 | — |
| 评审 2 | FRID 歧义；Authority 串域；rebaseline 纯 ID 比对的 false negative；historical vs active 对撞 | FRID 术语、Authority 移入 proposal、digest 五态、Sources 分场景 |
| 自查 | 集合代数漏 conflicted；官方 verify 撞名 | 补 conflicted、改名 trace |
| 评审 3 | addressed 的三个反例；RENAMED 误用 deprecated 门槛 | 契约三、V4.4a/b 拆分 |
| **真实运行** | external 处置缺失；混合体 FRID；FRID 跨 change 的部分完成盲区 | 第六处置、行为点级交付归属、decompose 划分纪律 |
| **首个 change 评审** | 精度稀释（阈值/字面值被软化）；拆分确认退化为信任 | 精度保真规则、拆分回显保底 |
| **首次 apply** | 技术栈/仓库布局在实现现场被临时决定且不留痕——arch 缺入口流程，spec 缺执法点 | V1.4（WARNING 级）：arch 工作区存在但缺 `foundational: stack/layout` ADEC 时告警；配套 valkyrja-arch 的 bootstrap 动作与奠基标记 |

最后两行是这份记录里最值钱的部分：

**精度保真**——原设计只有单向的 WHAT/HOW 分离（挡实现细节混入），
执行者会把「禁技术名词」过度泛化到数字与字面值，把 PRD 钉死的阈值软化成
「达到上限」。**这类缺陷格式全对、能穿过 validate 与全部集合机检**。
补上对称的反向规则，判据是「这个值换掉，验收会不会失败」。

**拆分回显保底**——baseline 握手只出示提取物、不对照 PRD 原文，
真实案例中原文 7 条对提取 7 条、**数量相同但内容错位**（一条被静默丢弃、
另一条被拆二补位），穿过了 AI 提取、人工确认、trace 22 项检查三道关，
最终由独立外部评审接住。教训：**两层人工确认如果审的是同一份派生物，
就不构成冗余——审核者必须看到源头，不是摘要。**

## 9. 文件结构：progressive disclosure

SKILL.md 曾达 685 行（超出 Claude Code 对 SKILL.md 的 ~500 行建议值，
且全文每次调用都进上下文）。按**「何时需要」而非「内容归类」**切分：

| 文件 | 内容 | 何时加载 |
|---|---|---|
| `SKILL.md`（540 行） | 宪法、术语与集合、启动仪式、三契约摘要、意图路由、握手、各动作流程、对外接口 | 每次调用 |
| `references/trace-contract.md`（190 行） | 契约二/三完整规则与算法、V1–V6 检查清单 | 执行 trace / check 时 |
| `references/openspec-compatibility.md`（128 行） | 环境前提条件分支、归档路径、config 注入、官方 skill 冲突缓释、实测行为清单 | 前提检测异常 / 归档 / 写 config 时 |

切分原则：**摘要留在 SKILL.md，判定细节进 reference**——路由与握手阶段
需要知道「有这条规则」，只有真正执行判定时才需要「规则的完整形式」。
每个 reference 头部写明「何时读本文件」，并带**三载体同步提醒**
（SKILL.md / reference / `tools/trace.py` 同源，改一处必须改三处）。

## 10. 未验证区域（诚实清单）

真实运行覆盖了 baseline → decompose → propose → trace → rebaseline 联锁。
以下分支尚未在真实数据上跑过：

- `addressed()` 的 MODIFIED / REMOVED / RENAMED 分支（需主 spec 已有内容）
- 退休型 change 与 `deprecated` 集合（需某版 PRD 出现 DEPRECATED 标记）
- V6 七块分账（需先完成一次真实 apply 与 archive）
- capability 退休删除的放行回显（需 `retire_capabilities: true` 场景）
