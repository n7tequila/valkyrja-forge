---
name: valkyrja-spec
description: OpenSpec 开发治理层——把已发布 PRD 转为 requirement baseline，裁决 change 划分，校验 PRD↔spec 双向追溯，并为归档把关。当用户要基于已发布 PRD 开始开发、建立需求基线、拆分 OpenSpec change、检查需求覆盖与追溯、开始实现某个 change、或准备归档某个 change 时，必须使用本技能。即使用户只是随口说"PRD 定稿了可以开工了"、"这版需求拆成几个 change"、"看看哪些需求还没做"、"开始开发这个 change"、"这个 change 能归档吗"、"实现有没有跑偏需求"，只要上下文涉及 openspec/ 工作区或 Released PRD 的下游消费，都应触发本技能。
---

# Valkyrja Spec（OpenSpec 开发治理层）

本技能把**已发布 PRD** 转为可追溯的 OpenSpec 开发流。
它是一个**治理编排层**：标准的 propose / apply / archive 由官方 OpenSpec skill 与 CLI 承担，
本技能只负责它们不做、也不该做的事——需求基线、change 划分裁决、追溯闭环、归档门禁。

## 第一原则（宪法，8 条，优先于本文件其他一切内容）

1. **唯一输入是 `prd/releases/vX.Y.md`。** `prd/current.md` 与五类源目录是上游内部实现，
   一律不读；只可沿 PRD 中需求块的 `Sources:` 显式回溯被列出的那些文件。
2. **本技能不铸造任何 ID，包括 Q。** FRID（见下）与 Q 的编号空间均属上游。
   缺口记为**无编号的「待上游澄清项」**，回流上游由 valkyrja-prd 铸 Q。
   （上游 Q 编号靠扫描 initiative 内 DISC/PRD/STATUS.md 取最大号 +1，
   基线文件不在其扫描范围内——下游铸 Q 会导致上游**静默撞号**。）
3. **只提取、解释、标记冲突，不新增需求。** 发现缺失或矛盾时提问，不静默补充。
   新增需求的唯一出口是回上游 discuss → decide → synthesize → release，再 rebaseline。
4. **WHAT 与 HOW 分离。** spec 只写可观察行为；技术选型进 design.md。
5. **基线只记「裁决」与「计划」，绝不记「现状」。** 现状一律现算并与计划对账。
   **派生值（digest、覆盖率、计数、状态）一律不落盘**——冻结的 release 文件永远在盘上，
   任何比对都能现算。
6. **特权动作只能由人类显式确认后执行。** AI 可以给出判断与建议，但无裁决权。
7. **历史不删除。** 基线可 supersede，不覆盖；已发布需求不得被下游单方面丢弃。
8. **委托优先于重造。** 官方 skill 与 CLI 已实现的机制一律委托，不自行实现。

## 术语：FRID（Formal Requirement ID）

```
FRID = REQ | BR | SEC | NFR
```

**本文件中所有覆盖检查、集合运算、追溯判定一律针对 FRID 全集，不得只针对 `REQ-*`。**
BR（业务规则）、SEC（安全）、NFR（非功能）与 REQ 同为正式产品需求，
漏掉任何一类都会造成「功能做完了、安全或性能漏了、trace 依然 PASS」的假安全。
写 parser 时 active_ids = REQ ∪ BR ∪ SEC ∪ NFR。

常用集合（全部现算，均不落盘）：

| 集合 | 定义 |
|---|---|
| `active(vX.Y)` | 该 release 中**未**标 DEPRECATED 的 FRID 全集 |
| `deprecated(vX.Y)` | 该 release 中**明确标记 DEPRECATED** 的 FRID 全集 |
| `historical` | `prd/releases/` **全部**版本中出现过的 FRID 并集 |
| `included` | 基线中裁决为纳入（直通/拆分）的 FRID |
| `deferred` | 基线中裁决为延期的 FRID（仍需实现） |
| `non-software` | 基线中裁决为非软件交付的 FRID（不需 spec 覆盖） |
| `external` | 基线中裁决为**由本仓之外的系统交付**的 FRID（本仓不 spec，但欠账仍在） |
| `conflicted` | 基线中裁决为冲突、待上游收敛的 FRID（不得被任何 change 覆盖） |

六种处置与五个裁决集合的对应：直通与拆分 → `included`；延期 → `deferred`；
非软件 → `non-software`；外部 → `external`；冲突 → `conflicted`。
**每条 active FRID 恰好落入一个集合。**

**`external` 与 `non-software` 必须分开，理由与 deferred/non-software 同构**：
`non-software` 是「永久不需要任何 spec」，`external` 是「需要 spec，但那份 spec 属于
另一个 openspec 实例」。混为一谈会让跨系统欠账被永久免责——本仓看不见它，
别处也没人记得它欠着。`external` 项必须在 status 中持续单列，并记录**由哪个系统承担**。

`active` 与 `deprecated` 在同一 release 内互斥且共同构成该 release 的 FRID 全集。
**赋予「这条需求可以退出系统」权威的是 PRD 本身把它标为 DEPRECATED，而不是 rebaseline**——
rebaseline 只是消费这个事实并据此规划退休。因此 `deprecated` 取自 release 原文，
不取自基线裁决。

**退休型 change**：`deprecated` FRID 若需从系统中移除，由 rebaseline 规划一个退休
change，其 `Covered-FRIDs` 即这些 deprecated FRID。故一个 change 的 `Covered-FRIDs`
可以取自 `included`（实现）或 `deprecated`（退休），二者不得混在同一个 change 内——
混合会让 V4.3 的 ADDED 规则与 V4.4 的 REMOVED 规则在同一 change 内互相干扰。

## 前提检测（会话启动仪式的一部分，不是独立动作）

每次会话首次进入本技能时，按顺序检测并把结果并入状态复述：

1. **CLI 可用性**：`openspec --version` ≥ 1.9.0。缺失则给出
   `npm install -g @fission-ai/openspec` 并停止——本技能的全部动作都依赖它。
2. **`openspec/` 根**：`openspec context --json` 是否返回有效 root。
   缺失则**回显将执行的命令与将生成的文件清单，经人确认后**代跑
   `openspec init --tools claude`。须提前说明：该命令会按**当前 profile 与 delivery 设置**
   在 `.claude/` 下生成对应的 workflow skills 与 `/opsx:*` 命令
   （数量随 profile 而变，不要向用户断言固定数量）。
3. **官方 sync workflow**：`.claude/skills/openspec-sync-specs/` 是否存在。
   缺失**不阻塞**——归档走 CLI 有确定性替代（见「归档路径的选择」）。
4. **官方 verify workflow**：`.claude/skills/openspec-verify-change/` 是否存在。
   **verify 不在官方 `core` profile 内**，刚 init 的项目大概率没有。
   **缺失比 sync 严重**：本技能的 trace 只管 PRD ↔ spec，不做「代码 ↔ artifacts」，
   缺了它闭环少一段且**无任何替代**——必须显式告知后果，不可一句「可补装」带过。

   > 3、4 两项的补救**取决于 profile，必须先 `openspec config get workflows` 判断**
   > 是「产物过期」还是「profile 未启用」——手段完全不同，且后者要改全局配置
   > （特权动作）。完整条件分支见
   > [references/openspec-compatibility.md](references/openspec-compatibility.md)。

5. **基线**：`docs/product/baselines/` 下该 DOMAIN 的最新基线是否存在且 `status: active`。

然后读取基线、基线 `prd_release` 指向的 release（只读机读区与 Open Questions）、
`openspec list --changes --json` 并逐个 `openspec status --change <name> --json`（现算），
用 3–5 句复述：基线版本、纳入/延期/非软件/外部/冲突分布、planned change 进度、
计划外 change、阻塞项。

## 产物与目录

```
docs/product/baselines/<DOMAIN>-v<X.Y>.md     # 本技能唯一的持久化产物
openspec/                                      # CLI 拥有，本技能只读或经 CLI 写
├── config.yaml                                # 本技能经握手写入通用治理协议（不绑定具体 PRD）
├── specs/<capability-path>/spec.md            # 主 spec，真相源；只经 CLI 合并
└── changes/<change-name>/                     # 只经 `openspec new change` 创建
    └── proposal.md                            # 含 Requirement Authority 块（PRD 绑定在此）
```

基线落点的理由（**不要改回去**）：不放 `openspec/`——那是 CLI 拥有的 vendor 目录，
未来版本可能对未知子目录赋予含义或在 `doctor`/`validate` 中报警；
不放 `initiatives/<slug>/`——该树由 valkyrja-prd 拥有，其 check 会把外来文件判为不合契约，
且基线是**下游解释**，不属于上游需求工作区。

**不得征用 `.openspec.yaml` 的 `initiative:` 字段**承载 initiative 关联——
该字段是 vendor 定义、schema 为 `.strict()`、值为 kebab-case，与 UPPER_SNAKE 的 DOMAIN
不兼容，且是版本升级期最易碎的地方。关联信息写进基线与 proposal.md。

## 契约一：Requirement Authority（proposal.md 内，机读）

**PRD 绑定属于 change，不属于项目。** `openspec/config.yaml` 是整个 OpenSpec root 的
项目级配置，一个仓库可能同时存在多个 DOMAIN 的 PRD（DEMO / DEMO_ADMIN / …）；
把具体 PRD 路径写进 config 会让后建的 change 覆盖先建的绑定，造成**串域**。
因此每个 change 在自己的 `proposal.md` 中声明权威来源：

```markdown
## Requirement Authority

PRD-Release: docs/product/initiatives/<slug>/prd/releases/v<X.Y>.md
Baseline: docs/product/baselines/<DOMAIN>-v<X.Y>.md
Covered-FRIDs: REQ-DEMO-006, SEC-DEMO-003, NFR-DEMO-001
```

- 三个键名固定、区分大小写、各占一行，值为仓库相对路径或逗号分隔的 FRID 列表。
- 该块以 `## Requirement Authority` 二级标题定界，至下一个二级标题结束。
- 已实测确认：proposal.md 增加本自定义节不影响 `openspec validate --strict`。

**三份清单的权威顺序**（避免各自漂移）：

```
基线的 Change 划分（计划）     ← 唯一权威，人裁决的产物
        │  必须相等（V4.0）
proposal 的 Covered-FRIDs（声明）
        │  必须相等（V4.5 / V4.6）
spec delta 的 Sources（实际）
```

## 契约二：Sources 行（spec delta 与主 spec 内，机读）

每个 `### Requirement:` 标题的**下一行**必须是 `Sources: <FRID>[, <FRID>...]`
（单行逗号分隔）。ID 类型只能是 FRID，**不得直接引 RN/DEC/TM**——那会绕过
`prd/releases/` 这一唯一 API。

三条关键判定，**任何一条简化都会让 trace 失效**：

- **历史 provenance ≠ 当前 authority**：ADDED 的 Sources 必须全部
  ∈ `active` ∩ `included`；MODIFIED **沿袭的旧 ID** 允许已 DEPRECATED
  （只需 ∈ `historical`）且不得删除；MODIFIED **本次新增的 ID** 才要求
  ∈ `active` ∩ `included`。不区分二者，需求退役后该 Requirement 怎么写都过不了 trace。
- **REMOVED** 触达的 FRID 必须 ⊆ `deprecated`（否则等于下游单方面丢弃 active 需求）。
- **RENAMED 与 REMOVED 语义相反**，判定不得共用——它只改标题不退役需求，
  沿用 deprecated 门槛会禁掉一切 active 需求的标题重构。

## 契约三：addressed(change)

**不得用「delta 的 Sources 并集」代表一个 change 处理了什么**——该并集会让
MODIFIED 的历史 ID 永久误报为范围蔓延，并让 REMOVED / RENAMED 型 change
（块内无 Sources 行，并集为 ∅）**永远无法放行**。

`addressed(change)` 按 delta 操作分别计算：ADDED 取 delta Sources；
MODIFIED 取 `delta_sources − (main_sources − Covered-FRIDs)`；
REMOVED / RENAMED 从主 spec 同名（或 FROM 所指）Requirement 的 Sources **反查**。
全部输入在盘上，现算不落盘。

> 契约二、契约三的完整规则、正则、算法验算与 V1–V6 检查清单见
> **[references/trace-contract.md](references/trace-contract.md)**——
> 执行 trace / check 或判定某条 delta 是否合规时读它。

## 意图路由

不要求用户输入动作名。根据用户话语自动路由：

| 用户话语特征 | 路由 |
|---|---|
| "PRD 定稿了"、"可以开工了"、"建立基线" | baseline（特权，需握手） |
| "拆成几个 change"、"怎么划分" | decompose（特权，需握手） |
| "开始开发这个 change"、"可以 apply 了"、"开始实现" | trace（pre-apply，V1–V5）→ 通过后委托官方 apply |
| "能归档吗"、"检查这个 change"、"追溯对不对" | trace（pre-archive，V1–V5） |
| "现在什么进度"、"哪些需求还没做" | status |
| "检查工作区"、"体检"、"skill 更新了" | check |
| "PRD 出新版了"、"v1.1 发布了" | rebaseline（特权，需握手） |

意图不明时按 status 处理（只读、无副作用）。

## 特权动作握手

沿用与 valkyrja-prd 一致的结构：识别意图后**不直接落盘** → 完整回显将要发生的事 →
等用户明确回复"确认"（或同义表达）后才写。
语气含疑问或犹豫（"感觉可以归档了？"）→ 视为倾向，回复"可记录为倾向，尚未执行"。

| 特权动作 | 回显必须包含 |
|---|---|
| baseline 定稿 | PRD 版本与路径；逐条处置分布；**拆分项带 PRD 原文要点逐条对照**（保底，不可降级为提取物清单）；**延期/非软件/外部/冲突项逐条列全**（外部项须含承担系统）；混合体 FRID 的非软件与外部行为点；新增待澄清项；将写入的文件路径 |
| decompose 裁决 | planned change 列表（名称/capability/覆盖 FRID/顺序依赖）；未被任何 change 覆盖的 `included` FRID（**必须为空**）；与磁盘既有 change 的冲突 |
| rebaseline 采纳 | 五态分类结果（NEW/UNCHANGED/CHANGED/DEPRECATED/DISAPPEARED）；**每条 CHANGED 的逐行 diff**；受影响的既有 change 清单；旧基线将被标 superseded |
| **归档放行** | trace V1–V5 **逐条**结果；将合并进主 spec 的 delta 摘要；**是否触发 capability 退休删除**；change 将被移动到的归档路径 |
| 代跑 `openspec init` | 完整命令行；将创建的文件清单；是否覆盖已有 `.claude/` 文件 |
| 写 `openspec/config.yaml` | 将写入的 context/rules 全文；对官方 propose 行为的影响说明 |
| 改 profile 补装 workflow | **这修改全局 `~/.config/openspec/config.json`，影响本机所有项目** |

**归档放行是本技能最重的特权动作**——它触发主 spec 改写与 change 目录移动，
且在 `.openspec.yaml` 含 `retire_capabilities: true` 时会**删除整个 capability 的
spec.md（工作树不可恢复，只能靠 git）**。回显必须逐条出示 trace 结果并单独高亮删除项、
给出 `git checkout` 恢复命令，**不得以「检查通过」一句带过**。

## 各动作运行协议

### baseline（特权）

解析 release 的机读区，对每条 FRID 裁决处置之一：

```
直通 ——— 内容明确、单一行为点        → 一条 Requirement
拆分 ——— 含多个可独立验证的行为点    → 多条 Requirement，Sources 全写同一原 FRID
延期 ——— 本轮不做，以后仍要实现      → deferred，status 须持续显示为「未实现」
非软件 — 不由代码交付（如写入运营文档）→ non-software，不要求 spec 覆盖，但必须记理由
外部 ——— 由本仓之外的系统交付        → external，须记明承担系统，status 持续单列
冲突 ——— 与其他条目或主 spec 矛盾    → 记待澄清项，回流上游，不得自行择一
```

**混合体 FRID 的处置规则**（真实 PRD 中很常见，勿简化）：一条 FRID 的多个行为点
可能分属不同交付归属——部分本仓软件、部分非软件、部分外部系统。此时：

- **行为点层级**标注交付归属（本仓软件 / 非软件 / 外部系统），与 capability 并列；
- **FRID 层级**仍只取一个处置，判据是：**只要存在至少一个本仓软件行为点，
  即判为 `included`（拆分）**；一个都没有时，按其余行为点的主导归属判
  `non-software` 或 `external`。
- 判为 `included` 的混合体，其非软件/外部行为点**必须在基线中逐点记明交付方式**——
  否则那部分会随 FRID 一起被算作「已覆盖」而静默消失。

如此每条 FRID 仍恰好落入一个集合，集合代数不破，而混合交付的事实不丢。

**延期与非软件必须分开，不得合并为「排除」**：二者在覆盖对账中的语义相反——
`non-software` 是「已解释完毕、永久不需要 spec」，`deferred` 是「仍欠一份实现」。
合并会让延期项在 V6.2 中被当作已解释，长期静默遗忘。

**冲突项不阻塞基线定稿与其他 FRID 的开发**：裁决为冲突的 FRID 同时记入
「待上游澄清项」回流上游，在 status 与 V6.2 报告中持续显示为「待上游收敛」；
在上游给出决议并 rebaseline 之前，它不属于 `included`，因此天然不得被任何
change 覆盖（V4.3 拦截）。

**复合需求拆分只发生在 OpenSpec 层，不发生在 ID 层**：原 FRID 保持不变、不细分，
拆出的每条 Requirement 的 `Sources:` 均写同一原 FRID。
**明确否决子 ID 语法**（如 `REQ-X-006#1`）——那会引入第二套 ID 语法、破坏单一正则，
且子编号自身会有重编号问题（违反宪法 2、7）。

**行为点的 capability 归属逐点标注，允许跨 capability**：一条 FRID 的多个行为点
很可能分属不同 capability（表单 UI / 隐私清理 / 离线队列），进而落入不同 change。
基线中 capability 标在**行为点层级**而非 FRID 层级；行为点编号只是基线内局部序号，
**不是 ID**，不得外流到 spec 或 proposal。

拆分完整性**不做数量自动判定**：行为点清单记入基线，trace 时**出示供人核对**。
语义完整性无法机检，一个假阳性的"通过"比不检更危险。

**拆分回显保底（不可降级，同族于 valkyrja-prd 的疑似 DEC 保底规则）**：
baseline 握手出示拆分项时，必须**逐条对照 PRD 原文要点**——每个行为点标注
对应的原文条目或引用原文短语，并显式列出「原文有而未映射」的余项（应为空）。
只出示提取物清单而不带原文对照，确认即退化为对提取者的信任；
已有真实案例：原文与提取物**数量相同但内容错位**（一条原文要点被静默丢弃、
另一条被拆成两条补位），数量核对无法发现，唯有逐条对照能接住。

**DEC 背书 vs TM 建议的分流**（决定实现细节能否进 spec）：

1. 扫描每个条目，标出含具体实现技术的措辞（具名技术、库、协议、存储引擎、部署形态）。
2. 读该条目的 `Sources:`：
   - **含 DEC** → 沿该 DEC 回溯（唯一允许的回溯路径），核对**该 DEC 是否在其自身
     声明的范围内覆盖了这条实现细节**（上游宪法 5：DEC 不自动覆盖未声明范围）。
     覆盖则判为**经决策的强制实现约束**；未覆盖（DEC 谈的是别的事）视同无背书。
   - **仅含 RN，或 DEC 未覆盖** → **不得进 spec**。技术措辞降级为 design.md 的候选，
     注明「来自 PRD 表述，无决策背书，不构成约束」，同时记一条待澄清项。
3. **即便有 DEC 背书，Requirement 与 Scenario 仍只写可观察行为**；技术选型写入
   design.md 并标注 `依据: DEC-X-NNN`。**技术名词不得出现在 Scenario 的 WHEN/THEN 中**——
   那会把实现锁进验收条件，使任何重构都必然破坏 spec。
   （官方 specs 指令本身已有同向要求："Avoid in specs: Library or framework choices"。）

**精度保真（与 WHAT/HOW 分离对称的反向规则，勿过度泛化前者）**：
上一条挡的是「实现细节混入 spec」，本条挡的是「产品精度被稀释」——二者同等重要：

- PRD 机读区**钉死的可观察数值与字面值**（阈值、枚举取值、字段名、物理尺寸、
  时限）必须**原样进入** spec 的 Requirement 或 Scenario，不得抽象为
  「达到上限」「不同的值」这类软化表述——软化后实现与测试失去判据，
  且该缺陷能穿过 validate 与集合类机检（格式全对、语义已丢）。
- 反向同样成立：PRD **只给描述未给具体名/值**的，spec 不得代为发明——
  命名与取值属于下游 design 或共享契约的职责，编名字即越权设计。
- 判据一句话：**「这个值换掉，验收会不会失败？」** 会 → 原样写入；
  PRD 没写 → 不发明。数字与字面值不是「技术名词」，禁技术名词的规则
  管的是库/框架/存储引擎/协议实现，不管产品承诺的精确值。

裁决按「多项确认交互协议」（节奏与粒度由用户选）出示，经确认后落盘。
首次建立基线时，若 `openspec/config.yaml` 尚无治理协议，一并提议写入（见下文注入）。

### decompose（特权）

基于基线提出 change 划分方案，产出**交接单**——**不自动批量建 change**。

**划分纪律：一条 FRID 的全部行为点应落在同一个 change 内。**
覆盖对账（V6.2）的粒度是 FRID，不是行为点——**一条 FRID 只要在主 spec 中出现过一次
就被计为 Implemented**。因此若把一条 FRID 的行为点拆到两个 change，先归档的那个
会让它立刻显示为「已覆盖」，而另一半其实还没做，形成静默的部分完成。
跨 capability 不是问题（一个 change 可含多个 capability 的 delta），
把同一条 FRID 拆到多个 change 才是。

确需跨 change 时（如两半工作量悬殊、或分属不同团队排期）：必须在基线的
Change 划分中**显式标注该 FRID 为跨 change**，并知悉 V6.2 会在部分完成时高估其覆盖；
此时应在 status 报告中人工补充说明，不得依赖机检发现。

官方 propose 每次只建一个 change，且产出 artifacts 后必须停下等待新的用户回合
（planning boundary）。本技能**不试图绕过**这一约束——它与「人保留决策权」同向。
因此 N 路拆分＝N 个回合，交接单落盘保证会话中断不丢失。

交接单每条包含可直接粘贴给 `/opsx:propose` 的引导段：

```
[1/4] add-recording-pause    capabilities: recording, privacy    顺序: 1，无依赖
      覆盖: REQ-DEMO-006, SEC-DEMO-003
      ---8<--- 触发 /opsx:propose 时粘贴以下内容 ---8<---
      change 名称：add-recording-pause
      capability 路径：recording, privacy（一个 capability 一个 delta 文件）
      请在 proposal.md 中写入以下 Requirement Authority 块（键名与格式照抄）：

      ## Requirement Authority

      PRD-Release: docs/product/initiatives/demo/prd/releases/v1.0.md
      Baseline: docs/product/baselines/DEMO-v1.0.md
      Covered-FRIDs: REQ-DEMO-006, SEC-DEMO-003

      每个 "### Requirement:" 的下一行必须写 Sources: <对应 FRID>
      范围以上述 FRID 为准，不得扩展；发现缺口请停下提问，不要自行补充需求。
      ---8<-------------------------------------------
```

「已建 / 未建」状态由 `status` 现算，**不写入基线**（宪法 5）。

### trace（只读，有放行语义）

针对**单个 change** 的追溯与一致性判定，输出逐条结果与总体放行结论。
两个强制触发时机：**apply 之前**（pre-apply）与**归档之前**（pre-archive），
两次都跑 V1–V5。归档门禁不是独立动作，它就是 trace 的强制触发时机之一。

> 注意与官方 `verify` workflow 区分：官方 verify 判定「**实现代码**是否匹配 change
> artifacts」；本动作判定「**PRD ↔ spec 的追溯闭环**」。二者互补，互不替代。

状态机：

```
propose 完成
   → trace (pre-apply, V1–V5) → 通过 → 委托官方 apply
   → 官方 verify（实现 ↔ artifacts）
   → trace (pre-archive, V1–V5) → 人工确认放行
   → openspec archive
   → post-archive verification (V6)
```

**六组检查**（完整清单见
[references/trace-contract.md](references/trace-contract.md)，执行时必读）：

| 组 | 管什么 | 关键项 |
|---|---|---|
| V1 | 前提 | CLI ≥1.9.0、有效 root、基线 active、**技术地基已定（V1.4，WARNING 级）** |
| V2 | PRD 侧 | 防 release 被手改：blocking Q=0、Sources 合法、无重复 FRID |
| V3 | 基线对账 | 五集合互斥且全覆盖、无幽灵 ID、included 全被 planned change 覆盖、计划外 change |
| V4 | delta 侧 | Authority 三重自洽（含 **rebaseline↔trace 联锁**）、Sources 分场景判定、`addressed == Covered`、skip_specs 例外、依据引用完整性 |
| V5 | 委托原生 | `openspec validate --strict` 退出 0、required artifacts 齐备 |
| V6 | 归档后 | 主 spec 保留 Sources、`unaccounted` 七块分账 |

**双向可达**：正向（防漏做）＝ V3.4 + V4.6 + V6.2；
反向（防越权造需求）＝ V4.0 + V4.2 + V4.3 + V4.5。

**放行规则**：任一 ERROR 未清除则不得放行（apply 与归档同此标准）。
WARNING 可带裁决放行，裁决记入回显与基线的例外记录。

**确定性实现**：V1–V5 与 V4.8 已实现为 `tools/trace.py`，退出码 0/1 可作 CI 门禁；
语义判断（拆分完整性、DEC 范围覆盖）不在脚本内，仍由人核对。

### 归档路径的选择

trace（pre-archive）放行后，**优先委托 CLI**：`openspec archive <change-name>`
（回显后经人确认执行），随后跑 V6。

理由：CLI 自带 validate → 合并 delta → 必要时 capability 退休 → 移动 change
→ 失败回滚的完整实现，**不依赖 sync skill 是否安装**；且官方 archive *skill*
的原则是「警告不阻塞」，与本技能的门禁语义相悖。
详见 [references/openspec-compatibility.md](references/openspec-compatibility.md)。

### status（只读）

现场扫描计算，不信任任何缓存。核心产出是 **V6.2 的七块分账**
（Implemented / Open changes / Non-software / External / Deferred / Conflicted / Unaccounted），
外加：基线版本与状态、每个 planned change 的已建/未建与 artifact 进度
（`openspec status --change`）、**计划外 change 清单**、待澄清项。

`Deferred`、`External`、`Conflicted` **必须始终单独显示，不得因已裁决而隐藏或并入已覆盖**——
它们都是「已解释但仍欠账」，与 `Non-software` 的「已解释且永久无需 spec」性质不同。
`External` 还须一并显示承担系统，否则跨系统欠账会在两边同时消失。
基线与扫描结果冲突时以扫描为准，并提示基线中的「计划」是否需要经 decompose 更新。

### check（只读，无放行语义）

将工作区与**当前 SKILL.md 契约**逐项比对，全部现算。检查项：
基线 frontmatter 与结构契约；基线是否混入了禁止存储的现状或派生字段（宪法 5）；
`Sources:` 行格式契约（全 change 与主 spec）；`Requirement Authority` 块格式；
FRID 类型合法性；计划外 change；基线引用完整性；
**对已归档 change 补跑 V4/V6 类追溯检查**。

> **能力边界（不得含糊）**：本技能**无法**判定一个已归档 change 当初是否跑过 trace——
> trace 只读、不写 receipt，事后没有任何状态证据。check 能做的是**重新验证归档产物
> 现在是否仍满足追溯契约**，这与「当时是否放行过」是两回事。
> 不得声称能发现「未经 trace 放行即归档」的行为。

产出体检报告，每项标注 `[可自动修复]`（纯形式）/ `[需人工处理]`（涉及语义或裁决）/
`[仅报告]`（已归档内容，不就地修改）。自动修复经确认后执行，**只改形式、永不改语义**。

### rebaseline（特权）

新 release 发布后建立增量基线。**逐条五态分类，全部机器可判，不做语义解读**：

```
                    FRID
                     │
        ┌────────────┴────────────┐
     新 ID                      同 ID
        │                         │
        ▼                    比较需求块 digest
      NEW                         │
                        ┌─────────┴─────────┐
                      相同                不同
                        │                   │
                        ▼                   ▼
                    UNCHANGED            CHANGED → 出示逐行 diff，人重新裁决

旧版存在、新版标 DEPRECATED  → DEPRECATED（可据此允许 REMOVED）
旧版存在、新版直接消失且未标 DEPRECATED → DISAPPEARED → ERROR（上游违反 ID 生命周期）
```

**为什么必须比 digest**：ID 是身份不是版本。`REQ-X-006` 的正文从「手机号必填」改成
「手机号 + 姓名必填」时 ID 完全不变，纯 ID 集合运算得出「无变化」——
这是最危险的 false negative，会静默漏掉一次真实的需求变更。

**digest 不落盘**（宪法 5）：`prd/releases/` 冻结且只增，新旧两个版本文件永远都在盘上，
两侧 digest 每次现算。**不得把 digest 写进基线**——那是可推导数据，且会随格式化漂移。
digest 取需求块正文（`## <FRID>` 起至下一个二级标题，含 Sources 节）
去除行尾空白与空行后的规范化哈希。

**AI 只报告「变了」，不判断「变得重不重要」**：对每条 CHANGED 出示逐行 diff，
由人重新裁决其处置与受影响的既有 change；AI 不得代为判定「这是小改，沿用原裁决」。

逐条裁决沿用 baseline 的五类处置。旧基线标 `status: superseded`，不删除（宪法 7）。

**与 trace 的联锁（rebaseline 的效力保证）**：rebaseline 采纳后，所有既有 change 的
`## Requirement Authority` 块仍指向旧基线，会在下一次 trace 的 V4.0(a) 被逐个拦下——
每个受影响 change 须更新 Authority 块指向新基线、按新计划重新对账后才能继续
apply 或归档。**不得批量代改 Authority 块**：逐个更新迫使人对每个 change
重新确认「这次需求变更影响到它没有」，这正是联锁存在的目的。

## 本技能不做什么

以下一律委托，不得代劳：

- 撰写 proposal.md / design.md / tasks.md 正文 → 官方 propose
  （本技能只提供 Requirement Authority 块的内容与格式要求）
- 实现任务、勾选 tasks 复选框 → 官方 apply
- 判定实现代码是否匹配 artifacts → 官方 verify
- delta 合并进 `openspec/specs/` → `openspec archive` CLI（或官方 sync）
- 创建 change 目录 → 一律 `openspec new change`，**永不手工 mkdir**
  （手工创建会缺 `.openspec.yaml`，后续所有 CLI 命令失效）
- 决定 Scenario 措辞 → propose 的职责；本技能只经 config 注入约束 + 事后机检

## 与官方 skill 的分工与冲突缓释

**config.yaml 注入**：baseline 首次定稿时（经握手）写入 `context` 与 `rules`，
抑制 propose 重新追问 PRD 已定事项。三条硬约束：
①**只写与具体 PRD 无关的通用协议**（写死具体 PRD 会在多 DOMAIN 仓库造成串域）；
②**写入后必须实跑 `openspec instructions specs --change <任一> --json` 验证注入生效**
——解析失败时 CLI 只打一行 warning 便静默忽略整个文件，表面看不出异常；
③必须向用户说明**这是 prompt 级建议不是强制**，真正的保证来自 trace 机检。

**三个冲突面**：explore 侧门可绕过本技能建 change（不禁止，但列为**计划外 change**，
一律不得通过归档门禁）；`skip_specs: true` 是验证逃生口（trace 一律 ERROR，
除非基线例外记录已有裁决）；官方 archive「警告不阻塞」。

**已知治理缺口（诚实写明）**：用户直接调 `/opsx:apply`、`/opsx:archive` 或 CLI 时
本技能**无法拦截**，也**无法事后证明**某次归档曾放行过（trace 只读、不写 receipt）。
只能保证「经由本技能执行的 apply 与归档一定先跑过 trace」。
**不得在任何场合作出超出此范围的承诺。**

> 完整理由、条件分支与实测确认的行为见
> [references/openspec-compatibility.md](references/openspec-compatibility.md)。

## 与 valkyrja-arch 的接口（技术地基的消费约定）

- design.md 的依据标注三态：`依据: DEC-*`（产品决策强制）、`依据: ADEC-*`
  （技术决策强制）、无依据（候选方案，须注明「无决策背书，不构成约束」）。
  V4.8 校验其引用完整性。
- 共享接口契约引用格式 `契约名@版本`（如 `content-package@1`），
  契约本体在 `docs/architecture/contracts/`。
- `docs/architecture/` 归 valkyrja-arch 治理，本技能**只读不写**；
  发现工程内部决策缺位（design.md 被迫现编约定）时，提示用户走
  valkyrja-arch 补地基，不代铸 ADEC。

## 上游接口（对 valkyrja-prd 的消费约定）

- 消费的唯一 API 是 `docs/product/initiatives/<slug>/prd/releases/vX.Y.md`。
- 回溯只允许沿需求块 `Sources:` 列出的 ID 读取**被列出的那些文件**；
  可沿 DEC 的 Sources 继续回溯到 TM（只读，仅作理解材料，**内容永不进入 spec**）。
- **禁止**浏览 `requirements/`、`discussions/`、`tech-memos/` 目录，
  **禁止**读 `prd/current.md`。
- 例外：rebaseline 与 `historical` 集合需要读取 `prd/releases/` 下的**历史版本文件**，
  这仍在「唯一 API」范围内（同为已发布 release），不违反上一条。
- 发现 release 本身不自洽（blocking Q 未清、Sources 断链、ID 重复、
  FRID 未标 DEPRECATED 即消失）时：**不修复、不绕过**，报告并请用户回上游处理。

## 参考文件与模板

**references/（按需加载，不随 SKILL.md 进入上下文）**

- [trace-contract.md](references/trace-contract.md) — 契约二/三完整规则 +
  V1–V6 检查清单。**执行 trace / check 时必读**
- [openspec-compatibility.md](references/openspec-compatibility.md) —
  环境前提条件分支、归档路径、config 注入、官方 skill 冲突缓释。
  **前提检测异常、准备归档、写 config 时读**

**templates/**

- [baseline.md](templates/baseline.md) — 基线文件结构
- [spec-delta.md](templates/spec-delta.md) — 带 `Sources:` 行的 delta 范例（可照抄）
- [config-injection.yaml](templates/config-injection.yaml) — 写入 `openspec/config.yaml` 的通用协议
