#!/usr/bin/env bash
# 造「独立使用 OpenSpec 官方流程」的仓库：只有 openspec/，没有 docs/product/ 的任何东西。
# 关键在于缺什么：无 baselines/、无 initiatives/、无 PRD。
set -euo pipefail

mkdir -p openspec/changes/bulk-import/specs/core
mkdir -p src

cat > openspec/project.md <<'EOF'
# Project

一个直接使用 OpenSpec 官方流程的项目，没有引入 valkyrja 需求治理。
EOF

cat > openspec/changes/bulk-import/proposal.md <<'EOF'
# Proposal

## Why

批量导入链路目前是一个大 change，覆盖解析、校验、落库三段职责。

## What Changes

- 新增批量导入入口
- 新增导入前校验
- 新增落库与回滚
EOF

cat > openspec/changes/bulk-import/specs/core/spec.md <<'EOF'
## ADDED Requirements

### Requirement: 批量导入

#### Scenario: 解析成功

- **WHEN** 上传合法文件
- **THEN** 解析出条目列表

#### Scenario: 校验失败

- **WHEN** 存在非法条目
- **THEN** 整批拒绝并报告首个错误
EOF

cat > src/importer.py <<'EOF'
def parse(path):
    raise NotImplementedError
EOF

cat > README.md <<'EOF'
# demo-service

批量导入服务。
EOF
