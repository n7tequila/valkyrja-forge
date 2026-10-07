#!/usr/bin/env bash
# 造一个有内容的技术契约工作区：奠基只定了技术栈（仓库布局缺）、一份采纳约定、一份契约、
# 一条被取代的选型、一个未收敛且带「应回流上游」的讨论、一条 backlog 候选。
set -euo pipefail
A=docs/architecture
mkdir -p "$A"/{discussions,decisions,conventions,contracts} src/api

cat > "$A/STATUS.md" <<'EOF'
<!-- 本文件由 valkyrja-arch 自动重算刷新，人不手改。 -->

# Architecture STATUS — DEMO_APP

- **架构 DOMAIN**: DEMO_APP（永久冻结）
- **最近决策**: ADEC-DEMO_APP-005（2026-09-20 定义 content-package 契约）
- **契约**: content-package@2
- **待决议题**: ADISC-DEMO_APP-003
- **backlog 触发待办**: 无
- **应回流上游**: ADISC-DEMO_APP-003
EOF

cat > "$A/decisions/ADEC-DEMO_APP-001.md" <<'EOF'
---
id: ADEC-DEMO_APP-001
date: 2026-09-01
status: accepted
superseded-by:
foundational: stack
---

# ADEC-DEMO_APP-001 技术栈

## Decision

后端使用 Python 3.12 与 FastAPI，前端使用 TypeScript 与 Vite，测试统一用 pytest 与 Vitest。

## 验收可观察性判定

技术栈不出现在验收口径中，属工程内部决策。

## Context

团队熟悉 Python，前端需要类型检查（ADISC-DEMO_APP-001）。

## Rejected Alternatives

- Node.js 全栈：后端已有 Python 代码，迁移成本高。

## 影响范围

全部 capability。
EOF

cat > "$A/decisions/ADEC-DEMO_APP-002.md" <<'EOF'
---
id: ADEC-DEMO_APP-002
date: 2026-09-05
status: accepted
superseded-by:
---

# ADEC-DEMO_APP-002 采纳接口信封约定

## Decision

采纳 catalog 的 conv-api-envelope 作为接口返回约定，错误码前缀改为 DEMO_，其余不改。

## 验收可观察性判定

返回结构只约束前后端之间，验收不可见。

## Context

前后端需要统一的成功与失败判断方式。

## Rejected Alternatives

无

## 影响范围

全部对外接口。
EOF

cat > "$A/decisions/ADEC-DEMO_APP-003.md" <<'EOF'
---
id: ADEC-DEMO_APP-003
date: 2026-09-08
status: superseded
superseded-by: ADEC-DEMO_APP-004
---

# ADEC-DEMO_APP-003 缓存用进程内 LRU

## Decision

缓存层使用进程内 LRU，上限 512 条。

## 验收可观察性判定

缓存实现验收不可见。

## Context

单实例部署，先用最简单的方案。

## Rejected Alternatives

无

## 影响范围

读多写少的查询接口。
EOF

cat > "$A/decisions/ADEC-DEMO_APP-004.md" <<'EOF'
---
id: ADEC-DEMO_APP-004
date: 2026-09-15
status: accepted
superseded-by:
---

# ADEC-DEMO_APP-004 缓存改用 Redis

## Decision

缓存层改用 Redis 7，键统一加 demo: 前缀，默认过期 30 分钟。

## 验收可观察性判定

缓存实现验收不可见。

## Context

改为多实例部署后，进程内缓存无法共享（ADISC-DEMO_APP-002）。

## Rejected Alternatives

- 继续用进程内 LRU：多实例下各自缓存，数据不一致。

## 影响范围

读多写少的查询接口。
EOF

cat > "$A/decisions/ADEC-DEMO_APP-005.md" <<'EOF'
---
id: ADEC-DEMO_APP-005
date: 2026-09-20
status: accepted
superseded-by:
---

# ADEC-DEMO_APP-005 定义 content-package 契约

## Decision

内容包导入接口按 content-package 契约传输，契约文件为 contracts/content-package.md。

## 验收可观察性判定

接口结构只约束导入方与本服务之间，验收不可见。

## Context

导入方与本服务需要稳定的包结构。

## Rejected Alternatives

无

## 影响范围

内容导入 capability。
EOF

cat > "$A/conventions/conv-api-envelope.md" <<'EOF'
---
adopted-from: conv-api-envelope@2026-08-20
adopted-by: ADEC-DEMO_APP-002
---

# API 响应信封与语义约定

## 统一信封

所有接口返回 success、requestId、timestamp、data、error、meta 六个字段。

## 状态码与业务失败

HTTP 状态码表达传输层结果，业务失败用 success: false 表达。

## 错误码

错误码统一以 DEMO_ 开头，全大写加下划线。
EOF

cat > "$A/contracts/content-package.md" <<'EOF'
---
contract: content-package
version: 2
date: 2026-09-25
adec: ADEC-DEMO_APP-005
---

# 契约：内容包

## 用途与消费方

约定内容包导入接口的包结构；消费方为内容导入 capability。

## 形状

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| packageId | string | 是 | 内容包唯一标识，导入后不可修改 |
| items | array | 是 | 内容条目列表，至少一条 |
| locale | string | 否 | 语言代码，缺省为 zh-CN |

## 兼容规则

新增可选字段不算破坏性变更；消费方必须忽略未知字段。

## Changelog

| 版本 | 日期 | 变更 | 破坏性 |
|---|---|---|---|
| 1 | 2026-09-20 | 初版 | — |
| 2 | 2026-09-25 | 新增可选字段 locale | 否 |
EOF

cat > "$A/inventory.md" <<'EOF'
# 公共对象清单（inventory）

## 已有公共对象

### 共享内核

| 类型 | 名称 | 路径 | 用途 |
|---|---|---|---|
| dataclass | PageRequest | src/api/paging.py | 分页参数 |
EOF

cat > "$A/backlog.md" <<'EOF'
# 规则候选 Backlog

## 候选项

### 1. 所有对外接口统一限流

**触发场景**：压测时单接口被打满。
**当前状态**：只在导入接口上加了临时限流。
**未来动作**：铸 ADEC 并采纳限流约定。
**触发条件**：第二个对外开放的接口上线时。
EOF

cat > "$A/discussions/ADISC-DEMO_APP-001.md" <<'EOF'
---
id: ADISC-DEMO_APP-001
date: 2026-08-28
topic: 技术栈选择
---

# ADISC-DEMO_APP-001 技术栈选择

## 2026-08-28 后端语言

**议题**：Python 还是 Node.js。

**倾向**：Python，已铸 ADEC-DEMO_APP-001。
EOF

cat > "$A/discussions/ADISC-DEMO_APP-002.md" <<'EOF'
---
id: ADISC-DEMO_APP-002
date: 2026-09-12
topic: 多实例下的缓存
---

# ADISC-DEMO_APP-002 多实例下的缓存

## 2026-09-12 进程内缓存的问题

**议题**：多实例部署后缓存不一致。

**倾向**：改用 Redis，已铸 ADEC-DEMO_APP-004。
EOF

cat > "$A/discussions/ADISC-DEMO_APP-003.md" <<'EOF'
---
id: ADISC-DEMO_APP-003
date: 2026-09-28
topic: 上传文件存哪里
---

# ADISC-DEMO_APP-003 上传文件存哪里

## 2026-09-28 本地磁盘还是对象存储

**议题**：上传文件放本地磁盘还是对象存储。

**立场与依据**：
- 本地磁盘：简单，但多实例无法共享。
- 对象存储：可共享，要多一个依赖。

**倾向**：倾向对象存储，未铸 ADEC。

**应回流上游**：上传文件的保留期限对用户可见，属于产品侧问题，需回流上游确定。
EOF

cat > src/api/paging.py <<'EOF'
from dataclasses import dataclass


@dataclass
class PageRequest:
    page: int = 1
    size: int = 20
EOF

cat > README.md <<'EOF'
# demo-app

一个已建立技术契约治理的后端服务。
EOF
