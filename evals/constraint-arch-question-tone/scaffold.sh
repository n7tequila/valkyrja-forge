#!/usr/bin/env bash
# 造一个已 bootstrap 过技术契约治理的仓库：docs/architecture/ 骨架齐全，
# 但 decisions/ 为空 —— 于是任何 ADEC-*.md 都必然是本次运行新建的。
set -euo pipefail

mkdir -p docs/architecture/discussions
mkdir -p docs/architecture/decisions
mkdir -p docs/architecture/conventions
mkdir -p docs/architecture/contracts
mkdir -p src

cat > docs/architecture/STATUS.md <<'EOF'
<!-- 本文件由 valkyrja-arch 自动重算刷新，人不手改。 -->

# Architecture STATUS — DEMO_APP

- **架构 DOMAIN**: DEMO_APP（永久冻结）
- **最近决策**: 无
- **契约**: 无
- **待决议题**: 无
- **backlog 触发待办**: 无
- **应回流上游**: 无
EOF

cat > docs/architecture/inventory.md <<'EOF'
# 公共对象清单

暂无。
EOF

cat > docs/architecture/backlog.md <<'EOF'
# 规则候选

暂无。
EOF

cat > src/server.py <<'EOF'
def handle(request):
    return {"ok": True}
EOF

cat > README.md <<'EOF'
# demo-app

一个已建立技术契约治理的后端服务。
EOF
