# 三级阶梯与 REWRITE

判断链是：坏味道，局部重构能不能解决；不能，结构抽象能不能；不能，才谈模式。
每一级有自己的手法词典、确认方式和风险先验。级别越高越贵，越要先出示落选方案。
手法名用 Fowler《重构》第二版的名字；Beck 的 tidyings 与 Kerievsky 的模式手法用各自原名。

## 四级一览

| 级 | 解决什么 | 依据 | 允许的手法 | 确认 | 风险先验 |
|---|---|---|---|---|---|
| Level 1 局部 | 可读性、单个函数内的结构 | Beck《Tidy First?》15 个 tidyings；Fowler「重新组织函数」 | Guard Clauses、Rename Variable / Change Function Declaration（改名）、Extract Function、Inline Function、Inline Variable、Extract Variable（解释变量）、Replace Magic Literal、Chunk Statements、Extract Helper、Remove Dead Code、Slide Statements、Split Loop、Replace Loop with Pipeline | 整批 | 低；Extract Function 为中 |
| Level 2 结构 | 职责归属、公开形状、层级 | Fowler「搬移特性」「处理继承关系」；Feathers seam；Ousterhout deep module；Sato Parallel Change | Move Function、Move Field、Extract Class、Inline Class、Hide Delegate、Remove Middle Man、Introduce Parameter Object、Replace Primitive with Object、Extract Interface（Feathers 解依赖手法，仅作 seam）、Collapse Hierarchy、Pull Up Method / Field、Push Down Method / Field、Replace Type Code with Subclasses、Replace Conditional with Polymorphism、Replace Subclass with Delegate、Replace Superclass with Delegate | 逐条，按依赖序 | 中；碰层级为高 |
| Level 3 模式 | 稳定的、已有多个实例的变化维度 | Kerievsky《重构与模式》27 个手法；GoF 只当词汇 | Replace Conditional Logic with Strategy、Replace State-Altering Conditionals with State、Move Creation Knowledge to Factory、Introduce Polymorphic Creation with Factory Method、Encapsulate Composite with Builder、Form Template Method、Move Embellishment to Decorator、Unify Interfaces with Adapter、Replace Hard-Coded Notifications with Observer、Replace Conditional Dispatcher with Command、Inline Singleton | 逐条，先讨论 | 高 |
| REWRITE | 行为必须变，或拆不出保行为的小步 | Feathers 五步法；Mikado；Branch by Abstraction；Strangler Fig | 不是重构；路径见 safe-change.md | 单独裁决 | 另计 |

## 级与级之间的门

- **1 到 2**：局部重构做完，问题还在吗？Extract Function 之后三处同步修改仍然存在，才升到 2。
- **2 到 3**：四个条件同时满足才升。同一条件逻辑在多处重复（Repeated Switches，不是单个 switch）；
  已经存在至少两个真实的变化实例（Rule of Three，Don Roberts）；Kerievsky 第 4 章的模式层信号
  之一在场：Conditional Complexity、Solution Sprawl、Combinatorial Explosion、Oddball Solution；
  反向检查通过：这不是 Sandi Metz 说的「错误抽象」候选。
- **到 REWRITE**：写不出「每步一个手法、步间全绿」的步骤，或者目标本身要改可观察行为。

## 确认与执行的顺序

**确认自上而下，执行自下而上。**

- 报告按热点分组；每个热点先出最高级的那条。裁了 Level 3 的形状之后，下面的 Level 1 条目
  有的成了它的实现步骤，有的失效，重新列出再批。
- 执行按 Fowler 的小步：先 Level 1 的机械手法（IDE 执行），再搬移，再层级，最后模式。
- 前置条件多于三个时用 Mikado：试一次，记下卡住的前置，回退，先做叶子。见 safe-change.md。

## 止损

- 一次审查里 Level 3 候选超过 5 条，报告「门禁在漏」，不逐条问。
- 单条步骤超过 8 步，拆成多条或改 REWRITE。
- 一步之后测试变红且五分钟内看不出原因：回退这一步，不带红前进。

## 风险先验（写风险行的起点）

两项实证研究给出按手法分层的数字。Bavota 等 2012 年在 3 个 Java 系统上统计被重构的类后续
需要修 bug 的比例；Di Penta 等 2020 年在 103 个系统上算行级优势比（OR，大于 1 表示更容易引入
后续修复）。手法名沿用研究所用的第一版命名。

| 先验 | 手法 | 数字 |
|---|---|---|
| 高 | Extract Subclass | 40%（4/10）；OR 2.07 |
| 高 | Extract Class | OR 1.65 |
| 高 | Push Down Method | OR 1.44（Bavota 0/45，样本小） |
| 高 | Extract Superclass | OR 1.27 |
| 高 | Move-and-Inline、Extract-and-Move 组合 | OR 1.65 / 1.52 |
| 高，两项研究矛盾 | Pull Up Method | 40%（6/15）；OR 1.03 不显著 |
| 中 | Inline Temp（二版名 Inline Variable） | 26% |
| 中 | Replace Method with Method Object（二版名 Replace Function with Command） | 25% |
| 中 | Extract Method（二版名 Extract Function） | 21%；OR 0.86 |
| 中 | Consolidate Conditional Expression | 18% |
| 中 | Move Method / Move Field | 13% / 12%；Move Field 的 bug 有 69% 落在目标类 |
| 低 | Rename | 15%；OR 0.46 到 0.66 |
| 低 | Extract Interface | 4% |

用法：先验只是起点，风险行必须接着写具体机制（Java / Spring 见 risk-java-spring.md）。
先验为高的手法，兜底至少第二档；Level 3 一律第三档（见 evidence.md）。

## Level 1 为什么可以整批

三个理由，缺一不成立：手法是机械的，由 IDE 引擎执行而非手写（Belshee 团队的 provable-refactorings
论证这类手法靠编译器与静态分析保证正确，不依赖测试）；不改公开签名；批量结束后跑一次全量测试。
任一条不满足的条目移出批量清单，按 Level 2 逐条确认。
