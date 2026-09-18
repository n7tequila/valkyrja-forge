# 抽象门禁

任何一条想推荐接口、抽象类、工厂、策略、适配器之类的候选，先过七问。答不上的问，
结论不能是 REFACTOR。REJECT 一个抽象的能力和推荐一个抽象一样重要。

## 七问

| 问 | 什么才算答了 | 出处 |
|---|---|---|
| 1 当前具体存在什么问题？ | 一个代码里看得见的现象，带文件与行号。「不优雅」不算 | Fowler 坏味道章：味是现象，不是评价 |
| 2 不重构，下一次需求变化要改哪里？ | 点名文件与位置，并说哪一处编译器不会提醒 | Fowler 预备性重构：先让改动变容易 |
| 3 是否已存在至少两个真实的变化实例？ | 数出来。一个不算，两个勉强，三个才动 | Rule of Three，Don Roberts；Repeated Switches：坏味道是同一条件多处重复，不是一个 switch |
| 4 变化维度是否明确且单一？ | 说出那个维度的名字（渠道、地区、格式）。两个维度纠缠时先拆维度 | Kerievsky 的 Combinatorial Explosion 信号 |
| 5 更简单的手法能不能解决？ | 逐个否定 Extract Function、Extract Class、Move Function、组合注入。否定不了就用它 | Kerievsky：refactoring towards patterns，走到问题消失就停 |
| 6 引入后复杂度是否真的下降？ | 比较改前改后：需要理解的类数、调用链长度、新增需求要碰的文件数。只有最后一项下降才算 | Ousterhout：抽象只有在减少调用方复杂度时才有价值 |
| 7 解决的是现在的复杂度还是假想的未来？ | 指出那个「已知的下一个需求」。指不出，写「推测」，结论倾向 KEEP，触发写「那个需求出现时」 | Fowler 的 Yagni 条目（2015）：YAGNI 只针对能力，不针对让软件更易修改的工作；所以有已知需求的预备性重构不受 YAGNI 否决 |

## 接口、抽象类、组合、具体类怎么选

默认是**具体类**。往上走每一步都要有下面列出的条件之一。

**接口，只在这些情况下**

- 已经有两个以上实现。
- 需要一条 **seam**。Feathers 的定义：不在该处编辑就能改变行为的位置。四个前置条件至少一个成立：
  多个实现已存在；不切开就确实无法测试，不是不方便；某个外部依赖正在实际伤害代码；
  公开面在泄漏实现细节。
- 它是模块边界，两侧由不同人或不同发布节奏维护。
- **Spring 项目注意**：依赖注入本身不需要接口，Mockito 能 mock 具体类。「为了测试」在 Spring 里
  很少构成抽接口的理由。单实现接口多数是 Speculative Generality。
- 抽了接口再检查 Ousterhout 的深浅：接口小、背后功能多才是 deep module；接口和实现一样宽、
  方法一一转发，是 shallow module，删掉。

**抽象类，只在这些情况下**

- 多个实现共享同一段流程且流程有稳定的不变量（Template Method 的场景）。
- 有共用状态和共用的 protected 实现。
- 满足 is-a，子类能替换父类出现的每个地方。

**组合，优先于继承，当**

- 目的只是复用代码。
- 行为需要运行时切换。
- 不满足 is-a。
- 存在两个以上正交的变化维度。
- 对应手法：Replace Subclass with Delegate、Replace Superclass with Delegate。

**重复代码不是抽父类的理由。** 两个类各有一个相同方法，先考虑抽成一个被两者持有的协作类，
再考虑父类。

## 去抽象检查

技能对两个方向同样负责。看到下面这些，候选方向是删：

| 味 | 现象 | 手法 |
|---|---|---|
| Speculative Generality | 只有一个实现的接口、只实例化一个类的工厂、没人传的参数、「以后可能用」的钩子 | Collapse Hierarchy、Inline Class、Remove Dead Code、Change Function Declaration 删参数 |
| Lazy Element | 类或函数小到不值得单独存在 | Inline Class、Inline Function |
| Middle Man | 一个类大部分方法只是转发 | Remove Middle Man |
| Shallow module（Ousterhout） | 一层 service 逐个方法转发给 repository | 删层，或让它拥有真实逻辑 |
| 架构 cosplay | 小 CRUD 里的 ports / adapters / use-cases 全套目录 | 合并到实际复杂度需要的层数 |
| 错误抽象（Sandi Metz，2016） | 共享方法里越来越多的参数和 if 来兼容不同调用方 | 先 inline 回各调用方，删掉没用的部分，再从剩下的重复里重新提取 |
| 手写单例 | static instance 的单例；Spring 里 @Component 默认已是单例 | Inline Singleton（Kerievsky），交给容器 |

## 自检

- 七问每一问有答案或写了「推测」。
- 选型落在具体类以外时，能指出上面列表里的哪一条条件。
- 去抽象检查跑过：候选是不是在往已经过度的方向再加一层。
