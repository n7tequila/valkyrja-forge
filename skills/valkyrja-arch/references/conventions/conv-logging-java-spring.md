---
id: conv-logging-java-spring
concern: 横切
stack: java-spring
version: 2026-09-07
source: 自撰（具名陷阱源自作者规则与内部项目线上/构建事故）；门面隔离条对齐阿里 Java 开发手册日志章的公开条款，非摘编
license: 自有
modified: 否
status: redistributable
requires: conv-logging-context
---

# 日志绑定增量（SLF4J · Logback · Spring）

> 本条目在 [conv-logging-context](conv-logging-context.md) 通用层之上引入
> **SLF4J / Logback / Spring** 增量。**采纳本条目前须先采纳通用层**；
> 非 Java 栈不采本条目。
> 通用层已定 canonical line、字段稳定性、事件白名单、开发期日志纪律、
> 占位符原则与禁入清单——这里不重述，只装 Java 侧的落点与具名陷阱。

## 门面隔离

- 业务代码**只 import `org.slf4j.*`**，不出现 Logback / Log4j2 的具体类型。
  绑定实现是构建期的事：换实现只该动一处依赖，不该改全仓 import。
- logger 声明全项目统一一种：`private static final Logger log =
  LoggerFactory.getLogger(Xxx.class)` 或 Lombok `@Slf4j`，**二选一写死**。
  两种混用时 grep 不到全部声明点，改造（如加统一前缀、换门面）必然漏。
- `static final`：非 static 的 logger 每个实例持有一份引用，热点对象上是白付的
  内存与初始化开销。

## 占位符的两个静默陷阱

通用层已定「用占位符不用拼接」。Java 侧两个坑**都不报错、只出错内容**：

- **参数个数与 `{}` 个数必须一致。** 多给的参数被丢弃，多写的 `{}` 原样打进
  输出。编译通过、运行不抛，只是日志从此说谎。
- **末位 Throwable 不要配 `{}`。** SLF4J 只在「最后一个参数是 Throwable 且
  没有对应占位符」时才把它当异常打堆栈；一旦写了占位符，它退化成普通参数被
  `toString()` 掉，**堆栈整个丢失**：

  ```java
  log.error("import failed, batchId={}", batchId, e);        // 正确，有堆栈
  log.error("import failed, batchId={}, err={}", batchId, e); // 堆栈没了
  ```

  这与通用层「禁止 catch 后只打一行 message（丢堆栈 = 丢现场）」是同一后果的
  另一条路径，且更隐蔽——它看起来完全像是在正确记录异常。

## MDC 在 Spring 的落点

通用层已定「入口写入、finally 清除、异步显式传播」。Java 侧的具体接法：

- 入口用 `OncePerRequestFilter`，且 order 排在鉴权之前——鉴权失败的日志同样
  需要 requestId，否则最该排查的那批请求恰好没有上下文。
- 清除用 `MDC.clear()`；需要嵌套恢复时先 `MDC.getCopyOfContextMap()`，
  finally 里 `setContextMap` 回填。
- 线程池传播：给 `ThreadPoolTaskExecutor` 装 `TaskDecorator`，在提交处捕获
  context map、在任务内回填并在 finally 清除。**`@Async` 默认不传播**——
  不装 decorator 的话异步段日志上下文全空。
- **WebFlux / Reactor 栈上 MDC 直接失效**：Reactor 的 Context 不是
  ThreadLocal，一次请求会跨多个线程。响应式模块必须走 Reactor Context +
  日志钩子，不能沿用本节的 Filter 方案。项目若混用两种栈，在参数节写明
  哪些模块用哪套。

## Logback 配置陷阱

- 配置文件名用 **`logback-spring.xml`**，不用 `logback.xml`。后者在 Spring
  初始化之前就被 Logback 自己加载，`<springProfile>` 与 `<springProperty>`
  **静默失效**——环境相关的 appender 与级别看起来配了，实际没生效。
- `AsyncAppender` 的 `discardingThreshold` 默认在队列剩余 20% 时**丢弃
  INFO 及以下**，且不留任何痕迹。要么显式设 `0`（配合 `neverBlock` 权衡吞吐），
  要么在参数节写明「接受高负载下丢 INFO」——不许留默认值当没这回事。
- pattern 必须含 `%X{requestId}`（通用层规则的 Logback 语法落点）。

## canonical line 的 Java 落点

- 结构化输出用 `logstash-logback-encoder` 一类 JSON encoder；字段用
  `StructuredArguments.kv("durationMs", ms)` 传，**不要拼进 message**——
  拼进去的字段进不了 JSON 顶层，日志系统索引不到，等于没做结构化。
- canonical line 在拦截器 / Filter 的 finally 段统一输出一条，
  不散落到各 Service。
- `if (log.isDebugEnabled())` 只在**参数构造本身昂贵**时才包（序列化、拼接大
  集合）。占位符已经免掉了 `toString` 开销，逐行包 isXxxEnabled 是噪声。

## 异常只记一次

- 同一异常**只在统一异常处理器（`@RestControllerAdvice`）记一次**。各层
  catch-log-rethrow 会让一次故障在日志里出现三四遍，排障时误判为多次失败。
- 需要在中间层补充上下文时，包成自家语义异常带上参数往上抛，由处理器记；
  中间层不自己打 ERROR。
- catch 的**范围**规则属 conv-spring-layering 的「异常捕获范围」，此处只定
  「在哪记」，不复述「catch 什么」。

## 运行时级别调整

- 生产 DEBUG 默认关闭（通用层规则）。需要临时开时走 Actuator 的
  `/actuator/loggers`，改完**必须改回**。
- 该端点**必须鉴权并限制暴露**：未保护的 loggers 端点等于把日志级别开关和包
  结构一起交出去，既是信息泄露也是打满磁盘的放大器。
- 不要用 `--debug` / `debug=true` 代替：那开的是 Spring 的自动配置报告，
  不是应用日志级别，两者常被混为一谈。

## 采纳时须绑定的项目参数

- logger 声明形式（显式 `LoggerFactory` 还是 `@Slf4j`），全项目一种
- 响应式与 Servlet 模块的划分，以及各自的上下文传播方案
- `AsyncAppender` 的 `discardingThreshold` / `queueSize` / `neverBlock` 取值
  与其吞吐-完整性权衡的结论
- JSON encoder 选型与 canonical line 的输出点（哪个拦截器）
- Actuator loggers 端点的暴露范围与鉴权方式
