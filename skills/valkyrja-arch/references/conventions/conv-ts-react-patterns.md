---
id: conv-ts-react-patterns
concern: 前端
stack: typescript-react
version: 2026-08-20
source: everything-claude-code (github.com/affaan-m/everything-claude-code) 之 web patterns
license: MIT
modified: 摘编
status: redistributable
---

# React 模式约定

> 摘编自 ECC（MIT，版权声明见仓库根 NOTICE.md），按本 catalog 风格改写。
> Vue 栈对应条目见 conv-ts-vue-element；API 层（单飞刷新等）见
> conv-frontend-api-layer，两栈通用。

## 状态四分法（核心）

| 状态类别 | 工具族 | 铁律 |
|---|---|---|
| 服务器状态 | TanStack Query / SWR 类 | **不得复制进客户端 store**——复制即两份真相 |
| 客户端状态 | Zustand / Jotai / context | 只放纯 UI 态（弹窗开关、选中项） |
| URL 状态 | search params / 路由段 | 可分享的都放这：筛选、排序、分页、活跃 tab |
| 表单状态 | React Hook Form 类 | 不散落 useState |

- **能推导的不存**：computed 值现场 derive，不落 store（与本体系宪法同源）。
- 服务器状态用 stale-while-revalidate：缓存立即返回 + 后台再验证，
  用现成库不手搓。

## 组件组织

- **容器/展示分离**：容器管数据与副作用；展示组件纯 props 渲染、保持 pure——
  展示层可独立测试与复用。
- **复合组件**承载共享状态的关联 UI（`Tabs` + `Tabs.Trigger` + `Tabs.Content`）：
  父持状态、子经 context 消费，替代深层 prop drilling。
- 行为共享而标记不同时用 render props / slot；键盘与 ARIA 逻辑留在 headless 层。

## 数据获取

- 独立数据**并行取**，杜绝父子瀑布；可预取的下一步路由/状态提前预取。
- 乐观更新三步走：快照 → 乐观应用 → 失败回滚 **+ 用户可见的错误反馈**
  （静默回滚 = 用户以为成功了）。

## 采纳时须绑定的项目参数

- 四类状态各自的选型（库名与版本策略）
- URL 状态的序列化约定（参数命名、默认值省略规则）
