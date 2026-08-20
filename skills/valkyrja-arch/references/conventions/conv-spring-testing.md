---
id: conv-spring-testing
concern: 横切
stack: java-spring
version: 2026-08-20
source: 自有（内部项目 测试要求泛化，每条对应一类假阳性/假绿事故）
license: 自有
modified: 提炼泛化
status: redistributable
---

# Spring 集成测试反假绿约定

> 主题只有一个：**测试通过 ≠ 行为正确**。以下每条都对应一种
> "测试绿着、生产坏着"的具体机制。

## 1. 切面测试必须显式开代理

`@DataJpaTest` 等切片测试**默认不启用 AOP 自动代理**——被测切面
（`@Auditable`、`@Cacheable`…）静默不生效，断言的是"没有切面的世界"，全绿假阳性。

```java
@DataJpaTest
@EnableAspectJAutoProxy(proxyTargetClass = true)   // 不加这行，切面不存在
@Import({ TheAspect.class, ... })
```

## 2. AFTER_COMMIT 时序测试必须跳出测试事务

切片测试默认把测试方法包在**回滚事务**里——`AFTER_COMMIT` 监听器**永不触发**，
"副作用已写入"的断言在错误的宇宙里通过。

```java
@Test
@Transactional(propagation = Propagation.NOT_SUPPORTED)  // 跳出测试事务
void afterCommit_sideEffectPersisted() {
    service.doBusiness(...);   // 业务方法自带事务并真实 commit
    assertThat(sideEffectRepo.count()).isEqualTo(before + 1);
}
```

## 3. 派生写入必须有双断言时序 IT

凡 AFTER_COMMIT 模式的副作用（审计、外发消息），IT 必须同时覆盖：

1. **业务 commit 成功 → 副作用恰好发生 1 次**（查库计数 > 断言"无异常"——
   后者在静默丢数据场景照样绿）
2. **业务回滚 → 副作用计数不增长**（防幽灵记录）

缺此覆盖的派生写入 = 时序问题静默化，review 应阻止合并。

## 4. 异常断言先确认翻译路径

DB 约束违例的异常类型取决于访问路径——断言错类型的测试会"因为错误的原因失败"，
掩盖真实行为：

| 路径 | 抛出 |
|---|---|
| Spring Data Repository | `DataIntegrityViolationException`（Spring 已翻译） |
| 原生 EntityManager/native query | `org.hibernate...ConstraintViolationException`（未翻译） |

## 5. 不可篡改表用相对计数

审计表由触发器禁 UPDATE/DELETE。断言用 before/after 差值保证可重入；
**禁止 cleanup 里 DELETE 审计行**——触发器拒绝，cleanup 失败连坐后续所有测试。

## 6. IT 必须真的在 CI 跑

需要容器的 IT（Testcontainers）在无 Docker 环境会被**静默 skip**——
本地全跑、CI 实际没跑，兜底价值为零。CI 必须显式声明容器可用环境，
且把"IT 被 skip"当作失败处理。

## 采纳时须绑定的项目参数

- 切片测试注解族（@DataJpaTest / @WebMvcTest / 自定义切片）与各自代理开关
- CI 中容器环境的声明方式与 skip 检测手段
