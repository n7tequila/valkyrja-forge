# 规划判定细则：基线、拆分、交接段、规划自检、增量基线（详版）

> **何时读本文件**：执行 baseline、decompose、propose（交接段与规划自检）、rebaseline 时，**裁决或出示确认前必读**。
> SKILL.md 保留每条规则的触发点与结论；判定细则、理由、示例与真实运行中的事故在这里。
> 两处互相对应——改规则时两处一起对账，SKILL.md 的摘要不得与这里的细则矛盾。
> 本文件的规则不属于 trace 的 V 检查，不受三载体同步约束；V 检查的契约见 `trace-contract.md`。

## 一、FRID 集合：为什么这样分

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

## 二、baseline 判定细则

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
baseline 确认出示拆分项时，必须**逐条对照 PRD 原文要点**——每个行为点标注
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

## 三、decompose 与交接段

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

交接单**只存裁决字段**——名称、capabilities、覆盖 FRID、顺序与依赖、说明：

```
[1/14] add-recording-pause   capabilities: recording, privacy
       覆盖: REQ-DEMO-006, SEC-DEMO-003   顺序: 1（依赖：无）
       说明：录制与隐私地基，后续 change 依赖
```

**粘贴段不预存**——它的每个成分都是派生值（宪法 5）：预存路径会在
rebaseline 后过期（真实事故：承袭基线的预存段仍指旧版路径，propose 前才拦获），
预存提示永远缺 decompose 之后才出现的权威（如后铸的视觉基线 DEC）。

**交接段现算生成（decompose 的只读伴生，不落盘）**：用户说「下一个 propose」
或「propose <change>」时现场组装粘贴段——名称/capabilities/Covered-FRIDs
取自基线计划条目；PRD-Release 与 Baseline 取自**当前 active 基线**；
格式规则为常量（与 config 注入刻意双层冗余：注入是 prompt 级、官方 skill
可能忽略，粘贴段是第二道，trace 机检是终审）；实现约束提示按**当下**治理
状态现算（覆盖 FRID 相关的 DEC 背书/降级项、基线合并提示、涉 UI 时的
视觉基线与 token 权威、跨 change 边界注意）。生成后**默认走 propose 壳**：
经确认委托官方 propose，产后自动 trace（pre-apply）；此时交接段是本技能交给官方 propose 的
内部材料，回显时标明「供官方 propose 使用，无需复制」，不以可粘贴的代码块呈现——
它与跨宿主的交出提示词不是一回事（真实事故：用户把交接段贴进了另一宿主，险成双写者）。
用户说明只要交接段自行去贴时，才以可复制的块交付，交付后即停、不代跑。

## 四、规划自检细则

**规划自检（propose 产后、出示 apply 确认前；只读，单宿主与跨宿主都做）**——trace 只核编号，
看不出规划文件在语义上替产品拍板或与地基不一致，这三项由本技能逐条对照，结果并入 apply 确认回显：

1. **安全与非功能对照**：Authority 覆盖的每条 SEC / NFR（及带数值、时限的 FRID），在 design / tasks 的落点；
   design 对需求做了取舍、解释、降级或只部分满足的，列为待裁决问题（B）——design 里的说明不能代替裁决。
2. **验收行为的来源**：design / tasks 规定的验收可观察行为（输入几次、提示文字、退出码等）必须有 PRD / DEC 依据；
   标「无决策背书」的候选不得写成必做必测的验收行为，否则列为待裁决（B）。
3. **可执行性**：tasks 的验证与测试命令与布局 ADEC 规定的一致，且在当前仓库能跑（只读推演，不执行有副作用的命令）；
   不一致属「已有权威可答」，经确认用官方 update workflow 修正，不需裁决。**布局 ADEC 根本没写运行与测试命令时，
   这本身就是技术约定空缺（C），列为待裁决**——不因无可对照而跳过（真实运行：从旧地基起步，自检放过了跑不通的测试命令，
   最后靠复审接住）。

有待裁决项时不出示 apply 确认，按 cross-host.md 第三节「暂停交回」格式报告（附可整段粘给另一宿主处理的一段），
先按偏差归口回 valkyrja-prd / valkyrja-arch
（真实运行：两次 apply 暂停——安全需求被 design 悄悄打折、tasks 把无背书的候选写成必测行为——都本可在这里拦住）。

## 五、rebaseline：分类图示与理由

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
