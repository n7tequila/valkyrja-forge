---
id: conv-db-relational-postgres
concern: 数据
stack: postgres
version: 2026-08-20
source: 自有（内部项目 db-standard 泛化，多条规则由真实生产/测试事故驱动）
license: 自有
modified: 提炼泛化
status: redistributable
---

# 关系型数据库约定（PostgreSQL）

## 命名

- 全部标识符 **snake_case**；完整单词，仅允许公认缩写（id/no/url/ip）。
- 表名**单数名词**；避开保留字（`case`/`user`/`order`），遇到则加业务前缀。
- **布尔字段禁 `is_` 前缀**（`active` 不是 `is_active`）：PG 系统目录从不用它；
  JPA/Hibernate 对 `is_` 字段生成 `isActive()` 与 JavaBean 规范歧义；
  `WHERE active = true` 更自然。
- 外键：有语义时用语义名（操作人 FK 用动词过去式 `created_by`/`confirmed_by`；
  区分"业务归属"与"操作人"）；无语义时 `{被引用表单数}_id`。必写 `REFERENCES` 约束。

## 类型铁律

- 主键 `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`；
  仅高频写入日志表可用 BIGSERIAL。
- 时间戳一律 **TIMESTAMPTZ**，**禁 `TIMESTAMP WITHOUT TIME ZONE`**（线上时区故障根源）；
  `created_at`/`updated_at NOT NULL DEFAULT now()`，永远放字段声明末尾。
- **枚举落 `VARCHAR` + 注释允许值，禁 PG `ENUM` 类型**——ENUM 增删值要 DDL 迁移，
  迁移工具不友好；VARCHAR + 应用层枚举校验更灵活。
- JSONB 只放非结构化 metadata / 快照 / 扩展参数；
  **禁止把核心查询条件放进 JSONB**（走不了索引）。

## ORM 绑定陷阱（事故驱动）

**PG 非 ANSI 类型必须显式参数绑定——`columnDefinition` 只管 DDL 生成，不管绑定。**
只写 columnDefinition 会在运行时抛 `column "x" is of type Y but expression is of
type character varying`；更危险的是配合吞错逻辑时**静默失效**
（真实事故：审计表 INET 列被当 VARCHAR 绑定，审计长期未真正落库，数轮 review 才暴露）。

| PG 类型 | JPA 映射 |
|---|---|
| JSONB | `@JdbcTypeCode(SqlTypes.JSON)` + columnDefinition |
| INET | `@ColumnTransformer(write = "?::inet")` + columnDefinition |
| UUID / TIMESTAMPTZ | Hibernate 6 原生支持，无需特殊绑定 |
| ARRAY | `@JdbcTypeCode(SqlTypes.ARRAY)` |

## 不可篡改表（审计/日志）

用触发器禁 `UPDATE`/`DELETE`（BEFORE 触发器 RAISE EXCEPTION）。
**测试连带约束**：断言用相对计数（before/after 差值），
禁止在 cleanup 中 `DELETE` 审计行——触发器会拒绝，反而弄挂后续测试。

## 测试种子数据隔离（事故驱动）

测试账号/demo 数据**禁止进主迁移路径**：

| 路径 | 加载条件 |
|---|---|
| `db/migration/` | 所有环境（仅生产 schema） |
| `db/testdata/` | 仅 dev profile 显式追加 |
| `src/test/resources/db/migration/` | 仅测试 classpath |

真实风险：种子账号混入主路径 → 生产库自动创建可预测凭据。
管理员初始化走启动时环境变量注入，不走迁移脚本。

## 采纳时须绑定的项目参数

- 保留字冲突表的前缀方案；日志表清单（允许 BIGSERIAL 的范围）
- 迁移工具与 profile 命名（上表按 Flyway 习惯书写，等价映射到项目工具）
