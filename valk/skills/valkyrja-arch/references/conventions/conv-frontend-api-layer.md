---
id: conv-frontend-api-layer
concern: 接口契约
stack: typescript
version: 2026-08-20
source: 自有（内部项目前端 API 层规范泛化；单飞刷新与分页泛型均为真实缺陷驱动）
license: 自有
modified: 提炼泛化
status: redistributable
---

# 前端 API 层约定（HTTP 客户端 · 认证 · 信封解包）

## 单一入口

- **所有请求走同一个 http 实例**（拦截器统一注入认证头、解包信封、归一错误）；
  **禁止裸 fetch 或自建第二实例**——绕过实例即绕过认证与错误处理。
- API 模块按业务域拆分（`api/modules/xxx.ts`），每个模块只管自己的接口。
- **信封解包在 API 模块层完成**，调用方拿到的直接是业务数据——
  `data.data` 这种解包代码不允许扩散到组件层。
- 开发态 `baseURL` 走代理相对路径，不写完整后端 URL（绕过代理即触发 CORS）。

## 认证完整生命周期（含两个真实缺陷模式）

双 token（access + refresh）持久化；401 拦截器实现**单飞刷新**：

| 场景 | 行为 |
|---|---|
| 首个 401 | 用 refresh token 调刷新接口；**并发 401 全部排队**等同一次结果 |
| 刷新成功 | resolve 整个队列，原请求重试并标记防循环 |
| 刷新失败 | **reject 整个队列 + 清空本地认证 + 跳登录** |
| logout | **先调服务端吊销 refresh token**，再清本地 |

两个真实缺陷模式（review 重点盯）：

1. **队列项没有 reject 通道** → 刷新失败时排队请求**永久 pending** 直到超时——
   队列项必须 `{ resolve, reject }` 双通道，失败路径必须 flush 队列。
2. **logout 只清本地不调服务端** → refresh token 仍然有效，安全缺陷。

## 分页信封的泛型陷阱（真实崩溃驱动）

服务端分页信封：`data` 是**纯数组**、分页元数据在**顶层 `meta`**
（与单对象接口不同构）。因此：

- 信封类型必须含顶层 `meta?` 字段；
- **分页接口的泛型传元素数组类型**（`Envelope<Item[]>`），
  **不要传服务端内部的包装类型**——泛型传错时 `meta` 在类型上"存在"
  实际为 undefined，`result.meta.total` 运行时崩溃；
- 解包层给 `items` 与 `meta` 都做兜底默认值。

## 错误归一

拦截器把非 401 错误统一格式化为 `{ code, message }` 抛出；
呈现按错误分类约定（conv-error-taxonomy）执行，组件层不解析原始响应。

## 采纳时须绑定的项目参数

- token 存储介质与安全取舍（内存 / storage / cookie 方案按项目威胁模型定）
- 刷新接口路径与防循环标记名
- 代理配置与环境变量约定
