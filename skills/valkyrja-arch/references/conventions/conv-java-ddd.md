---
id: conv-java-ddd
concern: 架构风格
stack: java-spring
version: 2026-08-20
source: 自有（作者 java-domain-driven-design skill 提供方法论；十条强规则提炼自 内部项目 评审回归）
license: 自有
modified: 提炼泛化
status: redistributable
---

# Java DDD 强制规则

> 完整方法论（战略边界、战术模式、发现流程）见作者的 java-domain-driven-design
> skill——本条目**只收 code review 必须阻止合并的强规则**，全部由真实评审回归驱动。

## 分层依赖

1. **domain 层 import 白名单**：只许 JDK 与共享内核（`common.domain.*`）。
   禁 `org.springframework.*`、`jakarta.persistence.*`、`org.hibernate.*`。
   框架适配（如 Security 的 GrantedAuthority 转换）放 infrastructure 静态工具。
2. **被 interfaces 与 infrastructure 同时依赖的载体类型放 application**，
   不放 infrastructure——否则 interfaces → infrastructure 层次倒置。
3. **应用层要用的注解（如 @Auditable）放 application 或共享基础设施模块**，
   禁放业务模块 infrastructure——注解定义在下层会迫使 application 反向 import。
4. 以上三条**用 ArchUnit 固化为测试**（package 依赖断言），违规即构建失败——
   分层规则不靠自觉。

## 权限与读模型

5. **行级权限判断归聚合根（读 + 写同权）**：可见性/可写性做成聚合根守卫方法
   （`isVisibleTo(userId, role)`），服务层只消费结果。
   **`@PreAuthorize` 只到角色级——同角色不同用户互访照样越权**（真实漏洞形态：
   B 用户可改 A 用户的数据）。所有写 Command 必须携带 `operatedBy + operatorRole`，
   加载聚合根后立即调守卫。
6. **应用服务的详情方法一次返回完整读模型**：同一上下文内的关联数据由
   ApplicationService 注入 Repository 内部组装；**Controller 不协调多次调用**。
7. **Controller 零业务逻辑**：只做参数解析 → Command 映射 → 委托 → 响应转换。
   禁止角色推导、状态条件、fallback 填充——逻辑下沉，Command 携带上下文。

## 跨模块

8. **跨上下文的 Identifier 与共享枚举放共享内核**；业务模块 domain 不得被其他
   模块直接 import——跨模块通信走 facade 的 published language DTO。
   （否则下游耦合到某一上下文的领域模型，且为未来反向依赖埋下循环。）
9. **同时依赖多个模块的边界 Filter/Converter 放装配层（starter）**，
   不放任何业务模块——各写一份会代码重复 + Spring 按 simple name 注册 Bean
   **装配时才炸**（`BeanDefinitionStoreException`，编译期无感）。
   配套：跨模块 `@Component` 起名前 grep 全仓；starter 必备 smoke test
   断言关键抽象实现唯一。

## 派生写入时序（本组最易错）

10. **业务事务后副作用（审计/消息/邮件）默认 AFTER_COMMIT 时序，三层防御缺一不可**：

| 层 | 工具 | 防什么 |
|---|---|---|
| 时序 | `@TransactionalEventListener(AFTER_COMMIT)` / registerSynchronization | 未 commit 不写副作用；回滚不留幽灵记录 |
| 隔离 | 副作用入口 `REQUIRES_NEW` | 副作用失败不污染业务事务 |
| 吞咽 | listener/aspect 内 try-catch | 副作用失败不打断业务 |

三个反模式各自的坑：同步 `@EventListener`（业务未 commit，FK 不可见静默丢）；
AOP 直接写库（业务回滚后副作用已 commit，幽灵记录）；
只加 REQUIRES_NEW（解决不了时序问题）。

**推论（静默丢数据级）**：AFTER_COMMIT 回调链上的 Service 入口**必须显式
`REQUIRES_NEW` 或 `NOT_SUPPORTED`**——afterCommit 运行在"事务已完成"上下文，
默认 `REQUIRED` **不会新建事务**，JPA save 表面成功、实际不提交、数据静默丢失。
同规则适用于调度任务与 `@Async`（均无外层事务）。

## Command 校验分层

- Command record 必填字段在**紧凑构造器**做存在性校验（requireNonNull/isBlank），
  作为编程契约兜底；主校验在 Controller DTO 的 Bean Validation 层。
- 兜底触发的归宿：NPE → 500（编程错误，说明 Controller 漏了校验）；
  IllegalArgument → 400。
