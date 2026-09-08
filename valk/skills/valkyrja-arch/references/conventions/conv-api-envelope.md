---
id: conv-api-envelope
concern: 接口契约
stack: common
version: 2026-08-20
source: 自有（作者 api-design skill 与内部项目 API 规范合并提炼）
license: 自有
modified: 提炼泛化
status: redistributable
---

# API 响应信封与语义约定

## 统一信封

```json
{ "success": true, "requestId": "…", "timestamp": "…", "data": …, "error": null, "meta": null }
```

| 字段 | 约束 |
|---|---|
| `success` | **业务**成功/失败，不等于 HTTP 状态码 |
| `requestId` | 同时写入响应体与响应头（如 `X-Request-Id`）；未传入时服务端生成 |
| `timestamp` | ISO-8601 **含时区偏移**（如 `2026-08-20T10:30:00.000+08:00`） |
| `data` | 成功为业务数据；失败为 `null` |
| `error` | 成功为 `null`；失败为 `{ code, message }` |
| `meta` | 分页接口填 `{ page, size, total }`；非分页为 `null` |

- **分页信息放 `meta`，`data` 是纯数组**——不嵌套 `{ items, total }` 包装对象。
  （嵌套包装曾导致前端泛型误传、`meta` 静默丢失的运行时崩溃。）
- 信封由**统一包装层**（middleware / ResponseBodyAdvice 等）自动套；
  业务 handler 禁止手工构造信封、禁止返回领域对象。

## 状态码与业务失败

- **业务规则拒绝 = 422 + `success:false` + `error.code`，禁止 200+success:false**——
  后者让所有监控与重试策略失明。
- 语义映射固定：400 参数格式错 / 401 未认证 / 403 无权限 / 404 资源不存在
  / 409 冲突 / 422 业务校验失败 / 5xx 服务端。创建 201 + Location，删除 204。
- 登录场景的"用户不存在"回 401 不回 404（不泄露账号存在性）；管理场景照常 404。

## 错误码

- 结构 `<MODULE>_<REASON>`，UPPER_SNAKE_CASE；集中定义为常量/枚举，禁止字面量散落。
- `error.message` 面向调用方可读，不含堆栈与内部类路径。

## 命名与格式

| 位置 | 风格 |
|---|---|
| JSON 字段 | camelCase |
| URL 路径段 | kebab-case，资源用复数名词 |
| URL 查询参数 | camelCase |
| 时间戳字段名 | `At` 结尾（`createdAt` / `confirmedAt`） |

- 分页参数约定：`page` 从 1 起、`size` 有上限（如 100）且越界**拒绝**而非静默夹断。
- 响应中的用户引用**禁止裸 ID 字符串**——内联最小引用对象
  `{ userId, username, role }`，用户已删除时降级为仅含 ID。

## 采纳时须绑定的项目参数

- 信封扩展字段（如部署标识）与 `requestId` 头名
- MODULE 前缀清单（与错误分类约定共用）
- 分页 `size` 上限值
