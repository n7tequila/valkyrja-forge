#!/usr/bin/env bash
# views 实际指向治理决策目录；阅读稿写入必须在解析真实路径后停止。
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../view-reading-arch/scaffold.sh"
ln -s decisions docs/architecture/views
