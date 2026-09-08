---
id: conv-spring-layering
concern: 架构风格
stack: java-spring
version: 2026-08-20
source: 自有（内部项目后端编码规范泛化，多条为线上/评审事故驱动）
license: 自有
modified: 提炼泛化
status: redistributable
---

# Spring 落地约定（装配 · 绑定 · 校验）

> 与 conv-java-ddd 分工：那边管分层与领域规则，这边管 Spring 机制层的
> 具名陷阱——每条背后都有一个"编译全过、运行才炸（或静默失效）"的事故。

## 参数绑定

1. **`@RequestParam` 与 `@PathVariable` 必须显式写参数名**，且统一用 `name=`
   不用 `value=` 别名。根因：Spring 靠反射取参数名，构建工具配了 `-parameters`
   但 **IDE 直接启动时用自己的编译器、不读该配置**——只在 IDE 里炸，CI 全绿，
   显式命名是唯一可靠解。
2. **枚举/强类型 ID 查询参数声明强类型**，禁止方法体内手工 `valueOf` 解析；
   每个类型一个 `Converter<String,T>` `@Component` 注册。
   Converter 抛 IllegalArgument → 统一映射 400（含参数名，不暴露类路径）。
3. 分页参数用 `@Min/@Max` **明确拒绝**越界，不做静默夹断。

## Validation 三件套（缺一让 400 退化 500）

全局异常处理器必须同时覆盖：`MethodArgumentNotValidException`（body @Valid）、
`ConstraintViolationException`（param 上的 @Min/@Max，需类级 `@Validated`）、
`HandlerMethodValidationException`（Spring 6.1+ 方法级校验）。
真实回归：`@Min(1) int size` 越界返回 500 而非 400——第二类没接住，被兜底吃掉。

## 异常捕获范围

三方解析库（POI/PDFBox 等）抛的是 **RuntimeException 子类不是 IOException**——
只 catch IOException 会让损坏文件直接穿透成 500。模式：先重抛自家语义异常，
再 `catch (Exception)` 兜住转译。

## Bean 装配

- **跨模块 `@Component` 禁同 simple class name**——Spring 默认按 simple name
  注册，碰撞不编译报错、装配时才抛 `BeanDefinitionStoreException`。
  同质职责收敛到装配层；异质同名显式命名。
- starter/装配层必备 `@SpringBootTest` smoke test：
  ①context 启动 ②关键抽象实现唯一性 ③关键基础设施 Bean 在位。
  单元测试与单模块编译**都不暴露**跨模块装配问题，smoke 是唯一兜底
  （真实回归：两模块各自定义同名 Filter，启动直接挂）。

## 事务时序

见 conv-java-ddd 规则 10（AFTER_COMMIT 三层防御 + REQUIRES_NEW 推论）——
该条是两份约定的交界，权威落在那边，此处只留指针避免双份漂移。

## 时区

**禁 `ZoneOffset.systemDefault()` / `TimeZone.getDefault()`**——部署环境的 JVM
时区不可信。固定部署地的系统用显式常量偏移；多时区系统一律 UTC 存储 + 边界转换。

## 采纳时须绑定的项目参数

- 装配层模块名与 smoke test 归属
- 时区策略（固定偏移常量 vs UTC 全链）
- Converter 所在包约定
