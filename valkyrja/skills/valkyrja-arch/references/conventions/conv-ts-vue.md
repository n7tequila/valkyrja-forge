---
id: conv-ts-vue
concern: 前端
stack: typescript-vue
version: 2026-08-20
source: 自有（内部项目前端编码约定泛化；由 conv-ts-vue-element 拆出的通用层）
license: 自有
modified: 提炼泛化
status: redistributable
---

# Vue 3 + TypeScript 通用编码约定

> 本条目**不绑定任何组件库**。组件库绑定增量见分层条目
> （如 [conv-ts-vue-element](conv-ts-vue-element.md)），自研组件体系直接用本条目。

## 样式分工

- **颜色与语义样式走 CSS Token**（`var(--color-primary)`），
  **布局/间距/字号走 utility class**——禁止组件内硬编码色值。
- **全局 vs scoped 边界**：跨组件复用的状态样式进全局样式表；
  组件私有结构才用 `<style scoped>`。
  ⚠ **scoped 的 data-v 选择器优先级高于全局**——与全局规则重叠时**静默覆盖**，
  维护共享样式清单（哪些类名已全局定义），scoped 内禁止重复定义同名类。
- 主题变量（主题色、圆角等）集中在全局 `:root` 一处维护，不散落组件。

## 类型系统

- **前端类型唯一来源**：`src/types/`；禁止组件或 store 内重复定义枚举。
- **前后端枚举强对齐**：枚举值以后端实际返回为准，原型/设计稿的值仅供参考——
  真实漂移案例：前端沿用原型枚举（`CREATED/TRANSLATING…`），后端实际是
  另一套（`DRAFT/IN_PROGRESS…`），列表页状态全错。
  后端枚举调整必须同步前端类型 + PR checklist 显式勾选。
  终极解法是 openapi-typescript 自动生成（列入演进方向，未落地前靠纪律）。
- 禁 `any`；接口返回类型必须在 `src/types/` 有定义。

## 路由

- **每个路由独立 view 文件，未实现页用专用占位 view**（接收页面名 prop）；
  **禁止拿业务 view 充当占位**——导航看似正常、内容语义错位，
  且面包屑/埋点全部错挂。
- 侧边栏导航项与路由定义**必须同步维护**——缺失路由会被兜底重定向**静默失效**。
- 权限用路由 `meta` 声明，不在组件内做角色判断。

## 交互纪律

- 所有异步操作显示 loading；失败必有用户可见反馈（按错误分类约定呈现）。
- 表单提交先本地 `validate()`，不把后端错误当第一道校验。
- 组件 PascalCase、文件名与组件名一致；按功能模块分目录，不按类型平铺。

## 采纳时须绑定的项目参数

- Token 命名表与全局共享样式清单（scoped 禁复定义的类名列表）
- 占位 view 的路径与 prop 约定
- 枚举对齐的 PR checklist 条目文案
