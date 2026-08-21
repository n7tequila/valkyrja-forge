---
name: valkyrja-prd
description: 产品需求工作坊——支持跨会话的需求讨论、决策沉淀、外部文档导入与 PRD 合成发布。当用户想讨论产品需求、整理需求思路、记录或确认产品决策、导入需求文档/会议纪要/客户材料、把一批存量历史文档批量初始化进需求工作区、询问需求进展状态、生成或更新或发布 PRD 时，必须使用本技能。即使用户只是随口说"我们聊聊 XX 功能"、"这个就这么定了"、"看看还有什么没讨论的"、"整理一版需求文档"，只要上下文涉及 product/initiatives/ 工作区或产品需求演进，都应触发本技能。
---

# Valkyrja PRD（产品需求工作坊）

本技能把松散的需求讨论治理为可追溯的产品状态，并合成标准 PRD。
它是一个**状态机 + 八个动作**，操作对象是文件系统中的 initiative 工作区。

## 第一原则（宪法，8 条，优先于本文件其他一切内容）

1. **文件系统是长期记忆，对话不是事实来源。** 对话是草稿，文件才是记忆。任何未落盘的结论，下个会话视为不存在。
2. **有效状态变化应尽快 checkpoint**，而不是等会话结束。会话可能随时中断。
3. **Decision 只能由人类显式确认后铸造。** AI 可以指出倾向，但无决策权。
4. **PRD 发布（release）只能由人类显式触发。** AI 可以建议"信息已较完整"，但无发布权。
5. **Accepted Decision 在其声明的范围内优先于 Discussion 与 Requirement Note。** DEC 不自动覆盖其未声明的范围；范围外的矛盾是冲突，须显式处理（见 synthesize 路由）。只有讨论、没有决策的争议点不得进入 PRD 正文，只能进 Open Questions。
6. **Tech Memo 只提供技术事实与建议，不得创造产品需求。** 技术约束进入 PRD 时，只写可观察的行为后果，技术原因留在 memo 中被引用。
7. **AI 发现缺失或矛盾时，只能提出 Question 或 Discussion，不得静默补充需求。**
8. **历史不删除。** 变化用 supersede / deprecated / 新版本表达；ID 永不复用、永不重编号。

## 工作区结构

每个需求主题（initiative）一个目录，**规范根路径为仓库的 `docs/product/initiatives/`**
（`docs/` 统一收纳全部文档，未来还将容纳 business-rules、architecture 等兄弟目录）：

```
docs/product/initiatives/<slug>/
├── STATUS.md            # 唯一豁免缓存，见下文
├── requirements/        # RN-*  规范化需求条目，**只允许 RN 文件**
├── discussions/         # DISC-* 讨论话题文件，按话题建档、追加式
├── decisions/           # DEC-*  决策，一决策一文件，轻量结构化
├── tech-memos/          # TM-*  技术讨论，自由格式
├── prototype/           # 系统原型：original/v<N>/ 原件；v<N>/ 背书基线包（见 prototype 动作）
├── others/              # 其他材料；originals/ 子目录存放不可修改的外部原文
└── prd/
    ├── current.md       # 可无限次重新生成的草稿
    └── releases/        # v1.0.md, v1.1.md … 发布即冻结，只增不改
```

若用户提及的 initiative 目录不存在：先确认主题名与 DOMAIN 代号
（如 MEETING、DEMO、PROJECT_MODULE，规则见"ID 与格式契约"），
创建骨架目录与 STATUS.md，再进入正常流程。
若在非规范路径发现既有工作区（如根目录下的 `product/initiatives/`）：照常使用，
但提示用户可整体移动到规范路径——工作区内部引用均为 ID 或 initiative 相对路径，
整树移动不破坏任何内容；此项亦纳入 check 的目录契约报告。

## ID 与格式契约

- ID 正则：`^(RN|DISC|DEC|TM|Q|REQ|BR|SEC|NFR)-[A-Z][A-Z0-9]*(_[A-Z][A-Z0-9]*)*-\d{3}$`，
  如 `DEC-MEETING-008`、`RN-DEMO-001`、`REQ-PROJECT_MODULE-003`。
- DOMAIN 规则：每段以大写字母开头、可含大写字母与数字，段间以下划线分隔
  （如机构_子系统）；下划线不得出现在开头、结尾或连续出现。
  **连字符是 ID 的结构保留符，DOMAIN 内禁止使用**。
  **禁止版本型 DOMAIN**（如 PROJECT_V2）——版本由 PRD version 表达，
  不进入稳定 ID namespace。DOMAIN 须**跨 initiative 全局唯一**——REQ ID 会流出
  initiative 进入下游 baseline/spec 引用，那里没有 initiative 上下文，
  重名即全局撞车。**DOMAIN 一旦用于铸造任意 ID 即永久冻结，不得重命名**——
  改名等于对该域下全部 ID 批量重编号，违反宪法 8；initiative 的显示名称
  与目录 slug 可以变化，DOMAIN 不随之变化。
  新建 initiative 确认 DOMAIN 时须主动向用户说明以上各点。
- 编号由本技能分配：扫描对应目录取最大号 +1；发现重复 ID 立即报错并停止写入。
  **例外：`Q-*` 没有独立目录**——下一个 Q 编号须扫描本 initiative 内所有 DISC、
  PRD（current 与 releases）及 STATUS.md 中已出现的 Q ID 后取最大号 +1。
- REQ/BR/SEC/NFR 只在 synthesize 时于 PRD 内铸造；RN/DISC/DEC/TM/Q 在日常动作中铸造。
- 每个源文档（RN/DISC/DEC/TM）头部带 YAML frontmatter，至少含 `id`、`round`、`date`。
- PRD 内每条需求以二级标题定界：`## REQ-XXX-NNN`，区块内含 `Sources:` 节
  （每行一个 `- ID`，至少一个 RN 或 DEC）；
  Open Questions 节内每个问题以 `### Q-XXX-NNN [blocking|non-blocking] @owner` 起始。
  该格式是下游机器解析的契约，不得变体。

## 会话启动仪式（Session Resume）

每次会话首次进入某个 initiative 时，按顺序读取（不要全量扫描）：

1. `STATUS.md`
2. `prd/current.md`（无则读最新 release，均无则跳过）
3. `decisions/` 全部文件（决策必须短，全读）
4. STATUS.md 中列出的 blocking questions
5. 与当前话题相关的最近 DISC 文件（按需，不超过 3 个）

然后用 3-5 句话向用户复述当前状态（版本、轮次、最近决策、悬而未决的问题），再开始工作。
其余目录按需检索，不预读。

## 意图路由

不要求用户输入 mode 名。根据用户话语自动路由：

| 用户话语特征 | 路由 |
|---|---|
| 探讨、比较方案、提出想法、"聊聊 XX" | discuss |
| "就按 X"、"定了"、"确认采用"、"记下来作为决策" | decide（特权，需确认） |
| 上传/粘贴外部文档、"看看这份材料" | import |
| 新建 initiative 且已有一批存量文档、"把这些历史材料导进来" | bootstrap |
| 拿到原型稿、"评审原型"、"背书为视觉基线"、原型大改 | prototype（背书步特权，需确认） |
| "现在什么状态"、"还有什么没定" | status |
| "检查工作区"、"格式体检"、"skill 更新了，看看有什么影响" | check |
| "整理一版 PRD"、"更新 PRD" | synthesize-draft |
| "发布"、"这版定稿为 vX.Y" | release（特权，需确认） |

意图不明时按 discuss 处理。**decide 与 release 永远不允许仅凭推断执行**——见特权确认。

## 特权动作确认（decide / release 共用）

1. 识别到决策/发布意图后，**不直接落盘**。
2. 完整回显将要发生的事：
   - decide：DEC 编号、结论一句话、来源讨论、被否备选（如有，禁止编造）、将关闭的 Q（如有）。
   - release：版本号、相对上一 release 的 delta 摘要、blocking questions 检查结果。
3. 等待用户明确回复"确认"（或同义表达）后才写文件。
4. 语气含疑问或犹豫（"就按 B 吧？"、"感觉可以定了？"）→ 视为倾向，回复
   "可记录为倾向，尚未铸造为正式 Decision"，仅在 DISC 中记录立场。
5. release 时若存在 open 的 blocking question：**一律阻止发布**，列出清单。
   `prd/releases/` 中的版本必须是下游可无条件消费的——这是不变量，无例外。
   若用户认为某个 Q 实际不应阻塞：正确出口是将其**显式改判为 non-blocking**
   （在该 Q 的 Status 行记录改判理由与日期），或铸造一个回答它的 DEC——
   而不是带着 blocking 项发布。改判本身是特权动作，需回显确认。

## 多项确认交互协议

适用于任何一次出示多个待确认项的场景（bootstrap 清点报告、synthesize delta 提案、
import 提案、批量疑似 DEC 裁决等）：

1. 待确认项超过 5 条时，先询问用户偏好，两个维度各选其一：
   - **节奏**：逐条确认 / 分组分批 / 一次性批量；
   - **粒度**：简略（每条一行）/ 详细（含原文摘录与理由）。
   同一会话内记住偏好，不重复询问；用户可随时切换。
2. 简略模式下，任何一条都可应用户要求"展开"查看详情。
   **例外保底：疑似历史 DEC 无论何种粒度，每条至少显示结论一句话 + 来源文件**——
   决策确认是最重的授权动作，不允许退化为标题清单。
3. 无论节奏与粒度如何：**确认必须显式且可枚举**。用户须明确指出各项处置
   （"全部确认"、"1、3、5 确认，2 否决，其余转 DISC"均可）；
   沉默、跳过、"差不多就这样"不构成确认，未被点名的项默认悬置并再次询问。
4. 批量确认不降低权威等级：整批确认 DEC 等同于对每条完成一次 decide 确认，
   宪法 3 的约束原样适用。

## Checkpoint 机制（贯穿所有动作）

**触发时机**：讨论形成新结论、新问题、立场变化、导入新信息——即"有效状态变化"时立即执行，
不积攒到会话末尾。一次长讨论应有多次 checkpoint，如同数据库事务。

**执行方式**：
1. 向用户出示本次增量摘要（将写入/修改哪些文件、各自要点，控制在 10 行内）。
2. 用户确认或修正后落盘。涉及产品语义的内容（RN/DISC/DEC/Q）未经确认不得落成正式状态；
   仅 STATUS.md 这类派生缓存可随确认过的变更自动刷新。
3. 同步更新 STATUS.md。

**DISC 文件粒度规则**：讨论按**话题**建档，不按次数建档。
一个话题一个文件（如 `DISC-MEETING-018-录像暂停.md`），
后续 checkpoint 以带日期的条目**追加**进同一文件，形成话题内时间线。
新话题才开新文件。文件数量应与话题数同阶，而非与讨论次数同阶。

## 各动作运行协议

### discuss
自由讨论。职责：推进思考、指出与既有 DEC/PRD 的冲突（宪法 5）、识别值得记录的增量并触发 checkpoint。
讨论中出现的未决问题记为 Q（写入相关 DISC，并在成为阻塞项时列入 STATUS.md）。

### decide
经确认后：按 `templates/decision.md` 生成 DEC 文件；若该决策回答了某个 Q，将其标记
`answered by DEC-XXX-NNN`；若推翻旧决策，旧 DEC 标记 `superseded-by`，不删除（宪法 8）。

### import
外部文档处理管线（不得跳步）：
```
读取原文 → 提取要点 → 归类五类 → 与现有 DEC/PRD/RN 比对
→ 输出导入提案（归档路径 + 提取出的 RN 草稿 + 冲突清单）
→ 用户确认 → 落盘（原文一律存 others/originals/ 且不可修改，
  提取物生成 RN-* 进 requirements/，RN 的 source 指向原文路径）
```
发现与 Accepted Decision 冲突时：**不覆盖 DEC**，提示冲突并建议开一个新 DISC 话题重议。

### bootstrap（存量文档批量初始化）
适用于 initiative 建立之初、用户手上已有一批历史积累（旧需求文档、会议纪要、
聊天记录、半成品 PRD、技术方案）的场景。它是 import 的批量形态，
用**一次完整清点报告**代替逐份确认：

1. 用户指定文件或目录，AI 批量读取全部材料（数量大时分批，逐批汇报进度）。
2. 输出**清点报告**，包含四部分：
   - **归档方案**：每份原文归入 `others/originals/`（一律保留原样，不改写）；
     规范化提取物以 RN-* 进入 requirements/。
   - **RN 草稿清单**：从材料中提取的需求要点，每条标注来源文件。
   - **疑似历史决策清单**：材料中"已经定了但没有决策形式"的事项
     （如"当时确定录像由主持人手动启动"），每条标注来源与原文摘录。
   - **冲突与矛盾清单**：不同材料之间互相矛盾的表述。
3. 用户对报告**逐节裁决**（节奏与粒度按"多项确认交互协议"由用户选择）：
   - 疑似历史决策：确认的**补铸 DEC**（Sources 指向来源文档，date 用裁决日）；
     不确认的转为 DISC 话题或 Q。这是 bootstrap 的核心价值——
     若历史决策不被收编，首次 synthesize 会依宪法 5 将已定事项
     错误降级进 Open Questions。
   - 冲突项：一律转为 DISC 话题，不得由 AI 择一。
4. 裁决完成后统一落盘，初始化 STATUS.md，round 记为 1。
5. bootstrap 仍受宪法约束：AI 只能提取与标记，不得补充材料中不存在的需求；
   疑似决策的"确认"是 decide 级特权，必须由人逐条表态（可整批说"1、3、5 确认，
   其余转讨论"，但不可默认全部确认）。

### prototype（背书步特权）

原型是**制品类**外部材料（Figma 导出、claude.ai 生成的 HTML、图稿），
与 import 的话语类材料（文本 → RN 提取）体裁不同，走本动作。四步：

1. **收编**：原件入 `prototype/original/v<N>/`（原样保存不改写）；可执行包
   先拆壳取真身再机检——**核对清单必须从当前 release 机读区逐项提取、
   带 FRID 锚点，不得凭记忆编写**（真实踩坑两次：凭记忆的清单让原型
   忠实继承了清单作者的记忆漏洞）。
2. **评审**：机检报告 + 人工项（视觉占比、隐私残留、整体气质等机器不可判项）。
   反馈按**三层拆解**分流：观感层 → 原型迭代；行为层 → DISC 回流
   （**原型不得成为第二需求源**，行为唯一权威是 release）；
   标定/数值层 → 需求链。原型自带的清单外行为标注「建议」，逐条裁决。
3. **背书（特权）**：委托 decide 铸背书 DEC（「视觉基线 = 原型 v<N>」）
   + 建基线包 `prototype/v<N>/`（manifest 按模板 + token 值表提取 + 关键截图）。
   **未背书 = 参考材料，不构成任何权威**；背书要求原型与当时 release 一致。
   **尺寸权威不转移**：图稿像素不构成尺寸依据，物理尺寸权威始终在
   标定链（相关 DEC/NFR）。
4. **演进**：新版本新目录，背书 DEC 走 supersede 链，旧版冻结不删；
   大改先过三层拆解再动手；实现侧的观感机检载体是**视觉回归测试**
   （截图基线钉在背书版本上），不由本层承担。

跨层边界：向 openspec 注入视觉权威属 valkyrja-spec 的 config 特权——
本动作只产出待注入内容与背书 DEC id，不越层代写。

### status
现场扫描目录计算（不信任任何缓存）：当前 round、PRD 版本、DEC 总数、
open questions（blocking/non-blocking 分列）、活跃 DISC 话题、
距离可 synthesize 的缺口（哪些争议无决策、哪些 blocking Q 无答案）、
**发版欠账**（现算：`round` 大于最近 release round 的 DEC——决而未发。
非空时下游 valkyrja-spec 的 V2.5 门限会阻止新 change 开工；出账靠发版。
铸 DEC 即开始欠账——拍板是有代价的承诺动作，防碎片化拍板）。
若发现 STATUS.md 与扫描结果不符，以扫描为准并更新 STATUS.md。

### check（工作区契约体检）
将工作区与**当前 SKILL.md 契约**逐项比对——不做新旧 skill 版本对比，
不需要任何历史信息；不符的原因（契约演进或当初写错）不影响修复。
全部现算，不信任缓存。检查项：

1. **ID 契约**：全工作区所有 ID 对照当前正则；重复 ID；Q 跨文件撞号；DOMAIN 一致性。
2. **目录契约**：工作区位于规范根路径 `docs/product/initiatives/` 下；
   requirements/ 只含 RN 文件；外部原文位于 others/originals/。
3. **Frontmatter 契约**：各类文件必备字段齐全（如 RN 的 status/source）。
4. **引用完整性**：所有 Sources / superseded-by / resolved-by / Closes Questions
   指向的 ID 在工作区内真实存在。
5. **PRD 机读区契约**：current.md 的区块定界、Sources 多行列表格式、Q 头格式
   （复用 Pre-Release Lint 的 1、2 号检查，扩展到全工作区语境）。
6. **STATUS 一致性**：等同 status 修复的检查项。
7. **冻结版本**：prd/releases/ 下文件**仅报告不合项，永不就地修改**。

产出**体检报告**，每项标注三种处置之一：
`[可自动修复]`（纯形式：ID 格式、frontmatter 补齐、文件移位、Source→Sources 改写）、
`[需人工处理]`（涉及语义或裁决：重复 ID 让位、语义性修改——后者转入
discuss/decide 正常流程，不属于 check）、
`[仅报告（冻结）]`（release 文件；若下游需要消费不合契约的旧 release，
唯一出口是发布**格式迁移版**——内容不变、仅格式对齐、
delta 注明 format migration only，走正常 release 流程）。

自动修复按"多项确认交互协议"出示、经用户确认后执行，逐文件说明变更。
**迁移只改形式、永不改语义。**

Session Resume 时若读盘发现明显不合当前契约的内容，应建议执行 check，不自动执行。
本节检查清单同时是未来治理脚本（CI 化）的行为规范草案。

### synthesize（draft）

**需求进入 PRD 的路由规则（核心）**：
```
RN（active）─┬─ 内容明确 且 与现有 DEC/REQ 无冲突 ──→ 直接生成 REQ（Sources 含该 RN）
             └─ 存在选择、歧义、或与任何 DEC/RN/REQ 冲突 ──→ 进 DISC，
                须由 DEC 收束后方可生成 REQ（Sources 含该 DEC）
```
一个 REQ 可有多个来源（多个 RN + DEC 共同收敛），Sources 全部列出，不丢链。
DEC 只覆盖其自身声明解决/supersede 的范围；范围外的 RN 与 DEC 矛盾
不得静默取舍，一律记为 blocking conflict（生成 Q），直到出现针对该冲突的 DEC。
TM 永远不直接产生 REQ（宪法 6）。

**REQ ID 稳定性规则**：REQ/BR/SEC/NFR 的 ID 一旦在 `prd/current.md` 中铸造，
后续所有 draft 必须沿用——修改内容 ID 不变，废弃标 deprecated，
**禁止重新组织后重新编号**。需求拆分或合并时，必须在 delta 提案中明确告知
原 ID 的处置（如"REQ-X-003 拆分为 003（收窄后）与 012（新增）"），由用户确认。

- **首轮（无任何 release）**：通读全部 DEC + RN + DISC，按上述路由生成完整
  v1.0-draft 写入 `prd/current.md`。争议点无决策的，降入 Open Questions（宪法 5、7）。
- **后续轮次**：以最新 release 为基线，仅消化本 round 新增材料，先输出 **delta 提案**：
  ```
  MODIFIED REQ-XXX-NNN   （before / after / sources）
  ADDED    REQ-XXX-NNN
  DEPRECATED REQ-XXX-NNN （原因 + 依据的 DEC）
  ```
  用户逐条审阅确认后，才写入 `prd/current.md`。不要每次输出全文让用户重读。
- tech-memos 内容不生成 REQ；技术约束只以行为后果形式进入（宪法 6）。

### release（特权）
确认回显前先执行 **Pre-Release Lint**，结果纳入回显：

- 硬门禁（任一不过则不得发布）：
  1. **ID 完整性**——无重复、无重编号（对照 current 历史与上一 release）；
  2. **Sources 完整性**——每个 REQ/BR/SEC/NFR 至少一个合法 RN/DEC 来源；
  3. **blocking questions = 0**（既有规则）。
- 警告项（列出供人裁决，可带警告发布，裁决记入回显）：
  4. **跨条目一致性**——扫描互相矛盾的条目对，特别注意含"任何/所有/唯一/不得"
     等全称量词的条目与其他条目的对撞，列为 potential semantic conflict；
  5. **实现泄漏**——识别规定具体实现技术的条目，核对其 Sources：
     含 DEC 背书视为经决策的强制实现约束、放行；仅溯至 TM 建议的标警。
     只提示、不自动删改。

Lint 通过或裁决后，经确认：将 `prd/current.md` 复制为 `prd/releases/vX.Y.md`（版本号由用户定，
不与 round 绑定）；release 文件头部写入版本、日期、round；round 计数 +1；
更新 STATUS.md；最后提醒用户：**下游 valkyrja-spec 现在可以基于
`prd/releases/vX.Y.md` 做 baseline / rebaseline**。

## STATUS.md 规则

STATUS.md 是全系统**唯一被豁免的派生缓存**，仅为加速 Resume 而存在：

- **任何已确认的持久化状态变化发生后**（checkpoint、decide、import、bootstrap、
  synthesize、Q 改判、release、status 修复等，含未来新增动作），由本技能重算刷新；人不手改。
- State 生命周期：`discovery →(synthesize)→ drafting →(release)→ released →(新材料/新讨论)→ discovery`。
  新建 initiative 初始为 discovery；release 后 Current PRD 更新为新版本、Round +1。
- 只含：当前 PRD 版本、当前 round、DOMAIN 代号、initiative 状态一词、blocking questions ID 列表。
- **不得**加入任何统计字段（决策数、讨论数等）——那些现算。
- 与目录扫描结果冲突时，扫描为准。
- 不得以本文件为先例增加第二个缓存文件。

模板见 `templates/status.md`。

## 下游接口（对 valkyrja-spec 的承诺）

- 本 initiative 对下游的**唯一 API 是 `prd/releases/vX.Y.md`**。
- `prd/current.md` 与五类源目录是内部实现，下游禁止直接消费；
  下游仅可沿 PRD 中 `Sources:` 链接显式回溯。**PRD Requirement 的权威来源
  只允许 RN 与 DEC；TM 是 supporting evidence，通过 DEC 的 Sources 链继续回溯**——
  技术建议永远不能绕过产品决策直接获得需求权威。
- 因此本技能必须保证：每个 release 自洽、符合 ID 与格式契约、Open Questions 状态如实。

## 模板

- [decision.md](templates/decision.md) — DEC 文件结构（铸造决策时使用）
- [discussion.md](templates/discussion.md) — DISC 话题文件结构（新话题建档时使用）
- [prd.md](templates/prd.md)
- [prototype-manifest.md](templates/prototype-manifest.md) — 原型基线包清单 — PRD 标准结构（synthesize 时使用，含下游语法契约）
- [status.md](templates/status.md) — STATUS.md 结构

requirements/、tech-memos/、others/ 刻意不设内容模板（自由格式），但 frontmatter 要求：

- **RN（requirements/）**：`id / round / date / status / source`。
  `status`: active | superseded | withdrawn（superseded 时另加 `superseded-by`）；
  `source`: 该 RN 提取自哪份原始材料（如 `others/originals/客户需求说明.docx`，或"口述"）。
  RN 被推翻/合并/废弃时只改 status，不删除（宪法 8）。
  导入的原始人工文件本身不可修改，AI 只生成提取物。
- **TM（tech-memos/）**：`id / round / date`。
- **others/**：连 frontmatter 也不强制。
