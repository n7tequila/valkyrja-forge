---
id: conv-ts-vue-element
concern: 前端
stack: typescript-vue
version: 2026-08-20
source: 自有（内部项目前端编码约定泛化，Element Plus 绑定层）
license: 自有
modified: 提炼泛化
status: redistributable
requires: conv-ts-vue
---

# Element Plus 绑定增量

> 本条目在 [conv-ts-vue](conv-ts-vue.md) 通用层之上引入 **Element Plus** 增量。
> **采纳本条目前须先采纳通用层**；不用 Element Plus 的项目不采本条目。

## 主题接入

- Element Plus 主题覆盖（主题色、圆角）集中在全局 `:root` 用其 CSS 变量
  一处维护，不散落组件——与通用层「主题变量集中维护」同一原则的库侧落点。

## 服务型 API 的样式陷阱

- **服务型 API（ElMessage / ElLoading）要求其 CSS 已全量加载**——
  组件按需自动引入覆盖不到服务型 API 的样式，需在入口全量引入样式
  （或按官方方案单独引入服务型组件样式）。表现为"消息弹出但无样式"。

## 图标纪律

- **图标一律 `<el-icon>` 组件，禁 Unicode 字符（✓ ✗ →）与 emoji**——
  跨平台字体渲染不一致、无法统一控制尺寸颜色、读屏语义缺失；
  loading 用组件自带旋转 class，禁字符叠加动画。

## 采纳时须绑定的项目参数

- 样式引入策略的选择：全量引入 vs 按需引入 + 服务型组件样式单独引入
