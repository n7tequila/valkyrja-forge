#!/usr/bin/env bash
# 造一个已发布 v1.0、之后又定了一条新决策的 initiative：current 与 release 正文相同，
# 所以阅读稿应以 release 为底，并把 round 2 的 DEC-REC-002 列进「已定未体现」。
set -euo pipefail
I=docs/product/initiatives/rec
mkdir -p "$I"/{requirements,discussions,decisions,tech-memos,others,prd/releases} src

body() {
cat <<'PRD'
# PRD: 会议录音 v1.0

## Background

会议结束后，参会人需要回放录音核对结论。

## REQ-REC-001

参会人可以在会议结束后 24 小时内下载完整录音。

Sources:
- RN-REC-001

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
}

printf -- '---\ninitiative: rec\nversion: 1.0\nround: 1\ndate: 2026-09-01\ndomain: REC\n---\n\n' > "$I/prd/releases/v1.0.md"
body >> "$I/prd/releases/v1.0.md"
printf -- '---\ninitiative: rec\nversion: 1.0-draft\nround: 1\ndate: 2026-09-01\ndomain: REC\n---\n\n' > "$I/prd/current.md"
body >> "$I/prd/current.md"

cat > "$I/STATUS.md" <<'S'
<!-- 本文件由 valkyrja-prd 技能在 checkpoint / decide / release 时自动维护，请勿手改。 -->

# Initiative Status

Initiative: rec
Domain: REC
Current PRD: v1.0
Current Round: 2
State: discovery

## Blocking Questions

（无）
S

cat > "$I/requirements/RN-REC-001.md" <<'R'
---
id: RN-REC-001
round: 1
date: 2026-08-20
status: active
source: 8 月 20 日需求会纪要
---

会后要能把录音下载下来自己听。
R

cat > "$I/requirements/RN-REC-002.md" <<'R'
---
id: RN-REC-002
round: 1
date: 2026-08-20
status: active
source: 8 月 20 日需求会纪要
---

长会议的录音文件太大，播放器打不开。
R

cat > "$I/requirements/RN-REC-003.md" <<'R'
---
id: RN-REC-003
round: 2
date: 2026-09-08
status: active
source: 9 月 8 日评审会纪要
---

有外部嘉宾的会议，录音不能谁都能下载。
R

cat > "$I/decisions/DEC-REC-001.md" <<'D'
---
id: DEC-REC-001
round: 1
date: 2026-08-25
status: accepted
---

# DEC-REC-001 长录音按 60 分钟分段

## Decision

超过 120 分钟的录音按每段最多 60 分钟切分，不做整段压缩。

## Context

整段压缩后音质下降明显，参会人回放时听不清发言。

## Sources

- DISC-REC-001
- RN-REC-002
D

cat > "$I/decisions/DEC-REC-002.md" <<'D'
---
id: DEC-REC-002
round: 2
date: 2026-09-10
status: accepted
---

# DEC-REC-002 下载需要会议主持人授权

## Decision

参会人下载录音前须经会议主持人授权。

## Context

外部嘉宾参会时，录音不宜被随意下载。

## Sources

- RN-REC-003
D

cat > "$I/discussions/DISC-REC-001.md" <<'D'
---
id: DISC-REC-001
round: 1
date: 2026-08-21
topic: 长录音怎么处理
status: resolved
resolved-by: DEC-REC-001
---

# DISC-REC-001 长录音怎么处理

讨论过整段压缩与按时长分段两种做法；压缩方案因音质问题被否决。
D

cat > "$I/discussions/DISC-REC-002.md" <<'D'
---
id: DISC-REC-002
round: 2
date: 2026-09-05
topic: 录音保留期限
status: active
resolved-by:
---

# DISC-REC-002 录音保留期限

有人主张保留 30 天，有人主张保留 180 天，尚无结论。
D

cat > src/app.py <<'PY'
def health():
    return {"ok": True}
PY
