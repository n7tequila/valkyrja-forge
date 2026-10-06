#!/usr/bin/env bash
# 造「已 opt-in 需求治理」的最小仓库：有 docs/product/initiatives/<slug>/ 骨架与 STATUS.md。
# 其余与 routing-prd-declines-unopted 相同，便于两条用例互为对照。
set -euo pipefail

mkdir -p src/api src/web docs
mkdir -p docs/product/initiatives/demo/{requirements,discussions,decisions,tech-memos,others,prd/releases}

cat > docs/product/initiatives/demo/STATUS.md <<'STATUS'
<!-- 本文件由 valkyrja-prd 技能在 checkpoint / decide / release 时自动维护，请勿手改。 -->

# Initiative Status

Initiative: demo
Domain: DEMO
Current PRD: none
Current Round: 1
State: discovery

## Blocking Questions

（无）
STATUS

cat > README.md <<'README'
# demo-service

一个普通的后端服务，需求在 docs/product/initiatives/ 下治理。
README

cat > src/api/routes.py <<'PY'
def register(app):
    @app.get("/health")
    def health():
        return {"ok": True}
PY

cat > src/web/app.js <<'JS'
export function mount(el) {
  el.textContent = "demo";
}
JS
