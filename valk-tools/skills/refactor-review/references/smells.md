# 坏味道清单与方向

Fowler《重构》第二版第 3 章的 24 个坏味道，加 Kerievsky《重构与模式》第 4 章里 Fowler 没有的 4 个。
名字用第二版原名，正文是自己的话。每个味标一个**方向**：

- **局**：Level 1 局部手法即可。
- **结**：Level 2 搬移或统一，不新增结构。
- **加**：需要新增结构（类、参数对象、多态），Level 2。
- **去**：应当删除结构。
- **模式信号**：可能走到 Level 3，但先过 pattern-directions.md 的「先试更简单方案」。

味只是现象，不是评价。报告的现象行写的是代码里看得见的事，味名放在括号里当索引。

## Fowler 24 味

| 味 | 一句人话 | 方向 | 先试的手法 | 取证要点 |
|---|---|---|---|---|
| Mysterious Name | 名字看不出用途，读者得读实现才知道 | 局 | Change Function Declaration、Rename Variable、Rename Field | 调用处有没有注释在替它解释 |
| Duplicated Code | 同一段逻辑出现在两处以上 | 局 / 加 | Extract Function；跨类则 Pull Up Method 或抽一个被两者持有的协作类 | 三处才动；分辨是巧合相似还是同一份知识 |
| Long Function | 函数长到要靠注释分段 | 局 | Extract Function，注释变函数名；Replace Temp with Query | 行数、嵌套深度、局部变量数 |
| Long Parameter List | 参数多到调用处要数位置 | 局 / 加 | Introduce Parameter Object、Preserve Whole Object、Replace Parameter with Query | 几个参数是否总一起出现 |
| Global Data | 到处都能改的全局可变状态 | 加 | Encapsulate Variable | 写入点有几处 |
| Mutable Data | 可变数据被多处修改，改一处别处坏 | 加 | Encapsulate Variable、Split Variable、Separate Query from Modifier、Change Reference to Value | 谁在写 |
| Divergent Change | 一个类因为多种不同原因被改 | 加 | Split Phase、Extract Class、Move Function | git：不同需求的提交都碰它 |
| Shotgun Surgery | 一个改动要碰很多类 | 加 | Move Function、Move Field 归拢；Inline Class | git：上次同类需求的提交波及文件数 |
| Feature Envy | 函数对别的类的数据比对自己的更感兴趣 | 结 | Move Function；先 Extract Function 再 Move | 数它访问的外部字段 |
| Data Clumps | 几个字段总是成群出现 | 加 | Extract Class、Introduce Parameter Object、Preserve Whole Object | 三个以上字段同现于两处以上 |
| Primitive Obsession | 用 String / int 表达有规则的概念：金额、电话、状态 | 加 | Replace Primitive with Object、Replace Type Code with Subclasses | 校验逻辑是否散落 |
| Repeated Switches | 同一套条件逻辑在多处重复 | 加 / 模式信号 | Replace Conditional with Polymorphism；再看 pattern-directions.md | 数出重复的 switch 处数；单个 switch 不算 |
| Loops | 循环体在做过滤、映射、聚合 | 局 | Replace Loop with Pipeline | 可读性判断 |
| Lazy Element | 结构小到不值一提 | 去 | Inline Function、Inline Class、Collapse Hierarchy | 成员数、引用数 |
| Speculative Generality | 为假想需求预留的抽象 | 去 | Collapse Hierarchy、Inline Class、Change Function Declaration 删参数、Remove Dead Code | 实现数、调用数为 1 或 0 |
| Temporary Field | 只在某些情况下才有值的字段 | 加 | Extract Class、Introduce Special Case | 哪些路径不赋值 |
| Message Chains | a.getB().getC().getD() | 结 | Hide Delegate；Extract Function 再 Move Function | 链长 |
| Middle Man | 类大半方法只是转发 | 去 | Remove Middle Man、Inline Function | 转发方法占比 |
| Insider Trading | 两个模块私下大量交换数据 | 结 | Move Function、Move Field、Hide Delegate；抽共同类 | 相互访问对方内部的次数 |
| Large Class | 字段方法太多、职责杂 | 加 | Extract Class、Extract Superclass、Replace Type Code with Subclasses | 对照 God Class 阈值，见 evidence.md |
| Alternative Classes with Different Interfaces | 做同样事的类接口不一致 | 结 | Change Function Declaration 统一签名、Move Function；再看 Adapter | 差异点列表 |
| Data Class | 只有字段和 getter / setter | 结 | Move Function 把行为搬进来、Encapsulate Record | 谁在外面操作它 |
| Refused Bequest | 子类用不上父类的大部分东西 | 结 / 去 | Push Down Method、Push Down Field、Replace Subclass with Delegate | 子类覆盖或忽略的成员数 |
| Comments | 注释在解释代码为什么难懂 | 局 | Extract Function、Change Function Declaration、Introduce Assertion | 注释与代码是否重复 |

## Kerievsky 补的 4 味

| 味 | 一句人话 | 方向 | 先试的手法 | 取证要点 |
|---|---|---|---|---|
| Conditional Complexity | 条件逻辑复杂到读不出规则 | 模式信号 | Decompose Conditional；再看 Strategy / State / Command | 分支数与嵌套 |
| Solution Sprawl | 一件事的实现散在多个类里 | 模式信号 | Move Function 归拢；再看 Move Creation Knowledge to Factory | 完成一件事要看几个类 |
| Combinatorial Explosion | 多个维度组合出成倍的方法或类 | 模式信号 | 先拆维度；再看 Replace Implicit Language with Interpreter | 维度数乘取值数 |
| Oddball Solution | 同一问题在项目里有两种解法 | 模式信号 | 统一到一种；再看 Unify Interfaces with Adapter | 两种解法各几处 |

## 目录指针

- Fowler 第二版手法目录（只读、只链接）：https://refactoring.com/catalog/
- Luzkan 的 Code Smells Catalog，56 个味各带修复手法，MIT，可带署名改写：https://luzkan.github.io/smells/
- Kerievsky《重构与模式》第 4 章；Industrial Logic 的 Smells to Refactorings 对照表（只链接）：
  https://www.industriallogic.com/blog/smells-to-refactorings-cheatsheet/
