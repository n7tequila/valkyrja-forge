#!/usr/bin/env bash
# 复用已发布底稿；本夹具另有草稿、替代决策与独立 initiative。
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../view-reading-verbatim/scaffold.sh"

cat > "$I/prd/current.md" <<'PRD'
---
initiative: rec
version: 1.1-draft
round: 3
date: 2026-09-12
domain: REC
---

# PRD: 会议录音 v1.1 草稿

## Background

会议结束后，参会人需要回放录音核对结论。

## REQ-REC-001

参会人可以在会议结束后 48 小时内下载完整录音，下载前须经会议主持人或共同主持人授权。

Sources:
- RN-REC-001
- RN-REC-003
- DEC-REC-003

## REQ-REC-002

单次录音超过 120 分钟时自动分段，每段不超过 60 分钟。

Sources:
- RN-REC-002
- DEC-REC-001

## Out of Scope

- 录音转文字

## Open Questions

### Q-REC-001 [non-blocking] @product

录音保留多久后自动删除？

Status: open
PRD

cat > "$I/decisions/DEC-REC-002.md" <<'D'
---
id: DEC-REC-002
round: 2
date: 2026-09-10
status: superseded
superseded-by: DEC-REC-003
---

# DEC-REC-002 下载需要会议主持人授权

## Decision

参会人下载录音前须经会议主持人授权。

## Sources

- RN-REC-003
D

cat > "$I/decisions/DEC-REC-003.md" <<'D'
---
id: DEC-REC-003
round: 3
date: 2026-09-12
status: accepted
---

# DEC-REC-003 延长下载窗口并允许共同主持人授权

## Decision

参会人可以在会议结束后 48 小时内下载完整录音，下载前须经会议主持人或共同主持人授权。

## Sources

- RN-REC-001
- RN-REC-003
D

cat > "$I/decisions/DEC-REC-004.md" <<'D'
---
id: DEC-REC-004
round: 3
date: 2026-09-12
status: accepted
---

# DEC-REC-004 下载链接过期

## Decision

录音下载链接在首次访问后 12 小时失效。

## Sources

- RN-REC-003
D

mkdir -p docs/product/initiatives/other/{prd/releases,requirements}
cat > docs/product/initiatives/other/prd/releases/v1.0.md <<'PRD'
---
initiative: other
version: 1.0
round: 10
domain: OTHER
---

# PRD: 通知

## REQ-OTHER-001

通知发送后 5 分钟内可撤回。

Sources:
- RN-OTHER-001
PRD
cat > docs/product/initiatives/other/requirements/RN-OTHER-001.md <<'R'
---
id: RN-OTHER-001
round: 1
status: active
---

通知误发时希望能撤回。
R
