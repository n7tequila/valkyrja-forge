# 从信号到模式的路径

模式是最贵的一级。三条规矩：

1. **方向词是 Kerievsky 的：to、towards、away from。** 可以走向一个模式，走到问题消失就停，不必走完；
   也可以从一个模式往回走（Inline Singleton 就是）。他把一上来就套模式叫 Patterns Happy。
2. **每条模式候选必须先写落选的更简单方案**，并说清它解决什么、解决不了什么。写不出落选方案的，
   说明没试过更简单的路。
3. **稳定变化要有证据**：门禁第 3、4 问的答案加 git 数字。没有证据的模式候选结论是 KEEP 或 REJECT。

GoF 只提供词汇。下表每个模式一行，链接指向公开目录，不复述模式本身。

## 第一梯队：12 个

| 模式 | 信号 | 先试的更简单方案 | 何时才到模式 | Kerievsky 手法 | 往回走 | Spring 注记 |
|---|---|---|---|---|---|---|
| Strategy | 同一算法族按类型 switch，且多处重复 | Extract Function 每个分支；Replace Conditional with Polymorphism | 算法要运行时切换或独立测试；已有 3 个以上实现 | Replace Conditional Logic with Strategy | inline 回 switch | 实现类注入为 List，按 supports(type) 选 |
| State | 行为随状态变，状态迁移分散 | Decompose Conditional；枚举加集中的 switch | 状态数 3 个以上且迁移规则会变 | Replace State-Altering Conditionals with State | 回到枚举 | 状态机库是另一个选项，先评估 |
| Factory / Factory Method | 创建逻辑散落、new 依赖具体类型 | 把 new 收进一个静态工厂方法 | 创建知识在两处以上重复，或创建依赖运行时信息 | Move Creation Knowledge to Factory；Introduce Polymorphic Creation with Factory Method | inline 工厂 | 容器本身就是工厂；只在按运行时参数创建时才自己写 |
| Builder | 构造参数多、有顺序或可选组合 | Introduce Parameter Object；静态工厂方法 | 参数 6 个以上，或存在需要校验的非法组合 | Encapsulate Composite with Builder | 回到构造器 | Lombok @Builder 零成本但不解决校验；配置类用 @ConfigurationProperties |
| Adapter | 两套接口做同一件事，调用方在做转换 | 一个转换函数 | 第三方接口不可控且有两个以上调用方 | Unify Interfaces with Adapter；Extract Adapter | inline 转换 | 对外部 SDK 的 Adapter 同时是 Feathers 的 seam，两个理由叠加时价值最高 |
| Facade | 调用方要按顺序调子系统多个方法 | Extract Function 把顺序包起来 | 调用方两个以上且子系统会变 | Fowler 的 Hide Delegate 扩展 | inline | 应用服务层往往已经是 Facade，别叠 |
| Decorator | 在核心行为外叠加横切能力：重试、缓存、审计 | 直接加到方法里 | 能力要按组合开关，或核心类不可改 | Move Embellishment to Decorator | 合并回核心 | @Cacheable、@Retryable、AOP 先于手写 Decorator |
| Template Method | 多个类流程相同、步骤不同 | Extract Function 抽公共步骤 | 两个以上实现共享稳定流程 | Form Template Method | Collapse Hierarchy | 组合替代：可变步骤作为函数参数传入 |
| Observer | 一件事发生要通知多方，通知方硬编码 | 直接调用 | 通知方 3 个以上，或需要解耦发布节奏 | Replace Hard-Coded Notifications with Observer | 回到直接调用 | ApplicationEvent 就是 Observer，别手写 |
| Chain of Responsibility | 请求依次经过多个可选处理器 | 顺序 if | 处理器顺序会变、需要可插拔 | Kerievsky 无专门手法；按 Replace Conditional with Polymorphism 的变体走 | 回到顺序调用 | Filter / Interceptor 链已是现成实现 |
| Command | 请求要排队、撤销、记录 | 直接方法调用 | 需要延迟执行、撤销或审计 | Replace Conditional Dispatcher with Command | inline | 消息队列场景里 Command 就是消息体 |
| Composite | 树形结构里叶子与容器被分别处理 | 递归函数 | 叶子与容器操作一致且树会变深 | Replace One/Many Distinctions with Composite；Replace Implicit Tree with Composite | 回到显式遍历 | 无 |

## 第二梯队与谨慎名单

- **Singleton**：Spring 里 @Component 默认单例，手写 static instance 的先 Inline Singleton 交给容器。
- **Visitor**：只在类型集合稳定而操作频繁新增时（Move Accumulation to Visitor）；反之是 Combinatorial Explosion 的错误解法。
- **Interpreter**：只有 Combinatorial Explosion 且规则确实是一种小语言时（Replace Implicit Language with Interpreter）。
- **Bridge、Mediator、Prototype、Proxy**：先过七问，再翻词汇表。

## 词汇表链接

- 模式目录（只链接，不复述）：https://refactoring.guru/design-patterns/catalog
- Kerievsky 27 个手法的目录：https://www.industriallogic.com/xp/refactoring/catalog.html
