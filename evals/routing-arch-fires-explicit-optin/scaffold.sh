#!/usr/bin/env bash
# 复用 prd 明确 opt-in 用例的普通仓库：无 docs/product/、无 docs/architecture/、无 openspec/。
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../routing-prd-fires-explicit-optin/scaffold.sh"
