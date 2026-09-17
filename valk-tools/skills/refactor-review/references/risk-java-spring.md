# 风险：Java / Spring 里会静默坏掉的机制

风险行先写手法类型先验（ladder.md 的表），再对照这里逐条查。每条给出：什么手法会触发、
为什么测试可能抓不到、怎么查。IDE 的重构工具对下面这些**全部不会提醒**。

| 机制 | 触发手法 | 为什么静默 | 怎么查 |
|---|---|---|---|
| 同类内部调用绕过代理 | Extract Function 后在同类内调用带 @Transactional / @Async / @Cacheable / @Retryable 的方法；Move Function 把带注解方法挪走 | Spring 注解靠代理生效，this.method() 不经过代理，事务、异步、缓存全部失效，功能测试常常仍通过 | grep 带注解方法在同类内的调用点；集成测试里加回滚与并发用例 |
| JDK 代理与 CGLIB 切换 | Extract Interface 给一个原先无接口的 @Service | 有接口后容器可能改用 JDK 动态代理，向实现类强转的地方抛 ClassCastException | grep 对该类的强转与 getBean(Impl.class) |
| 字段名即契约 | Rename Field、Move Field、Extract Class 拆字段 | Jackson 以字段名出 JSON，JPA 以字段名映射列，MyBatis XML 以字符串引用属性；编译不报错 | grep 字段名出现在 .xml、.json、.sql、@JsonProperty、@Column、前端契约 |
| 字符串里的方法名与表达式 | Change Function Declaration 改名 | SpEL（@PreAuthorize、@Cacheable 的 key）、JPQL / @Query、反射、MyBatis、@Scheduled 的 bean 方法名都在字符串里 | grep 方法名的字符串形式；启动一次让容器解析表达式 |
| equals / hashCode / compareTo | Move Field、Extract Class、Replace Primitive with Object | 字段挪走后 equals 语义变，Set / Map 行为变，Lombok @Data 生成的实现随之变 | 检查被动字段是否参与 equals；集合去重用例 |
| Bean 名撞车 | 类改名 | @Service 默认 bean 名是类名首字母小写；改名后 @Qualifier 字符串、XML 配置、按名注入失效 | grep 旧类名的小写形式 |
| 异常类型与回滚规则 | 受检异常改非受检或反过来；Extract Function 时收窄或放宽 throws | @Transactional 默认只对 RuntimeException 回滚；类型一变回滚行为变 | 列出方法抛出的异常类型变化；回滚用例 |
| 事务边界随方法移动 | Move Function 把方法挪到另一个类；Extract Class | 事务从哪个代理开始随之变化；懒加载集合在事务外访问抛 LazyInitializationException | 标出每条步骤后事务开始与结束的位置 |
| 静态状态与 ThreadLocal | Extract Class 把持有静态字段的逻辑拆成多个实例 | 原本共享的状态被两个实例各持一份，或线程上下文丢失 | grep static 非 final 字段与 ThreadLocal |
| 序列化兼容 | 类改名、换包、改字段 | 实现 Serializable 的类，缓存或消息里的旧字节反序列化失败；serialVersionUID 变化 | 检查 Serializable 与缓存 / 队列里的存量数据 |
| Lombok 生成代码 | 涉及 @Data / @Builder / @Value 类的改名与抽取 | 生成的方法名、Builder 方法名随字段名变，调用方在别的模块 | 全仓 grep 生成方法的调用 |
| 反射与框架扫描 | 换包、改名 | @ComponentScan 范围、@EntityScan、MapStruct、序列化白名单按包名与类名字符串工作 | grep 包名字符串 |
| 初始化顺序 | Extract Class 拆出带 @PostConstruct 或依赖注入顺序的逻辑 | 新 bean 的初始化时机与旧的不同 | 启动一次，看日志顺序 |

## 类型先验回顾

层级手法（Extract Subclass、Extract Superclass、Push Down、Pull Up）与跨类搬移（Extract Class、Move-and-Inline）
在实证研究里最容易引入后续修复；Rename 与 Extract Interface 最安全。数字见 ladder.md。
先验为高的条目，风险行至少写出上表中两条相关机制的排查结果；写不出就说明还没查。

## 可观察行为清单

判断「这算不算改行为」时对照：返回值；异常类型与抛出时机；副作用及其顺序；事务边界；并发语义；
序列化与 API 响应形状；数据库写入内容与顺序；对外调用的次数与顺序。日志默认不算，被告警或审计
依赖的算。性能特征（如 N+1）通常不算行为，但写进风险行。
