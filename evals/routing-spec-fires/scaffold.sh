#!/usr/bin/env bash
# 造「已 opt-in valkyrja 治理」的最小仓库形态：active 基线 + 对应 PRD release + openspec 工作区。
# 结构合法即可，不求内容真实——本用例只判路由。
set -euo pipefail

mkdir -p docs/product/baselines
mkdir -p docs/product/initiatives/demo/prd/releases
mkdir -p openspec/changes/demo-intake/specs/core

cat > docs/product/initiatives/demo/prd/releases/v1.0.md <<'EOF'
---
initiative: demo
version: 1.0
round: 1
date: 2026-01-02
domain: DEMO
---

# PRD DEMO v1.0

## REQ-DEMO-001

第1号可观察行为。

Sources:
- RN-DEMO-001

## REQ-DEMO-002

第2号可观察行为。

Sources:
- RN-DEMO-002

## REQ-DEMO-003

第3号可观察行为。

Sources:
- RN-DEMO-003
EOF

cat > docs/product/baselines/DEMO-v1.0.md <<'EOF'
---
domain: DEMO
prd_release: docs/product/initiatives/demo/prd/releases/v1.0.md
status: active
date: 2026-01-02
---

# Requirement Baseline — DEMO（PRD v1.0）

## 需求裁决

### REQ-DEMO-001
处置：直通
### REQ-DEMO-002
处置：直通
### REQ-DEMO-003
处置：直通

## 延期项（deferred）

## 外部系统项（external）

## 非软件项（non-software）

## Change 划分（计划，非现状）

### demo-intake
覆盖：REQ-DEMO-001
EOF

cat > openspec/changes/demo-intake/proposal.md <<'EOF'
# Proposal

## Why

夹具。

## Requirement Authority

PRD-Release: docs/product/initiatives/demo/prd/releases/v1.0.md
Baseline: docs/product/baselines/DEMO-v1.0.md
Covered-FRIDs: REQ-DEMO-001
EOF

cat > openspec/changes/demo-intake/specs/core/spec.md <<'EOF'
## ADDED Requirements

### Requirement: 第1号可观察行为

依据: REQ-DEMO-001

#### Scenario: 基本路径

- **WHEN** 触发
- **THEN** 产生可观察结果
EOF
