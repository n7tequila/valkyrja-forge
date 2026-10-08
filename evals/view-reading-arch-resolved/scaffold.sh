#!/usr/bin/env bash
# 保留历史回流标注与陈旧 STATUS，补充后续已处理记录；文件存储选型仍在议。
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../view-reading-arch/scaffold.sh"
mkdir -p docs/product/initiatives/demo-product/decisions

cat >> docs/architecture/discussions/ADISC-DEMO_APP-003.md <<'EOF'

## 2026-09-30 保留期限回流已处理

**处理结果**：上传文件的保留期限已回流产品侧，由 DEC-DEMO_PRODUCT-001 决定保留 30 天；该回流事项已关闭，不再待裁决。

**依据**：docs/product/initiatives/demo-product/decisions/DEC-DEMO_PRODUCT-001.md。

**剩余议题**：上传文件放本地磁盘还是对象存储仍在议，倾向对象存储，未铸 ADEC。
EOF

cat > docs/product/initiatives/demo-product/decisions/DEC-DEMO_PRODUCT-001.md <<'EOF'
---
id: DEC-DEMO_PRODUCT-001
round: 1
date: 2026-09-30
status: accepted
superseded-by:
---

# DEC-DEMO_PRODUCT-001 上传文件保留期限

## Decision

上传文件保留 30 天，期限对用户可见。

## Context

承接 ADISC-DEMO_APP-003 的保留期限回流事项。

## Sources

- docs/architecture/discussions/ADISC-DEMO_APP-003.md
EOF
