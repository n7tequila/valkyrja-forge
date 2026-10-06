#!/usr/bin/env bash
# 造一个完全没有 opt-in 任何 valkyrja 治理的普通仓库。
# 关键在于缺什么：无 docs/product/、无 docs/architecture/、无 openspec/。
set -euo pipefail

mkdir -p src/api src/web docs

cat > README.md <<'EOF'
# demo-service

一个普通的后端服务，尚未引入任何需求治理流程。
EOF

cat > src/api/routes.py <<'EOF'
def register(app):
    @app.get("/health")
    def health():
        return {"ok": True}
EOF

cat > src/web/app.js <<'EOF'
export function mount(el) {
  el.textContent = "demo";
}
EOF

cat > docs/setup.md <<'EOF'
# 本地启动

安装依赖后运行开发服务器。
EOF
