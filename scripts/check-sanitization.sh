#!/usr/bin/env bash
#
# check-sanitization.sh — D6 发布门禁的机检部分：脱敏词表扫描。
#
# 背景：D6 检查单第 1 项（客户名与内部项目名已剥离）此前为纯人工检查，
# 已两次「字面通过、意图落空」（客户缩写三处漏网并推送公开仓）。
# 本脚本把它变成确定性 grep：对 git 跟踪的全部文件扫描私有词表，
# 命中即退出码 1（建议接 pre-push 或 CI）。
#
# 词表位置（私有，绝不入库——词表本身就是要脱敏的内容）：
#   ${VALKYRJA_D6_WORDLIST:-~/.claude/valkyrja/d6-wordlist.txt}
# 格式：一行一个词（固定字符串，大小写不敏感）；# 开头为注释行。
#
# 词表不存在时显式报「跳过」并退出 0（零对象 ≠ 零发现：换机器/协作者
# 没有词表属正常，不能因此拦提交；但报告里必须能看出没扫）。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORDLIST="${VALKYRJA_D6_WORDLIST:-${HOME}/.claude/valkyrja/d6-wordlist.txt}"

if [[ ! -f "$WORDLIST" ]]; then
  printf 'D6 脱敏扫描：跳过（词表不存在：%s）\n' "$WORDLIST"
  exit 0
fi

# 剔除注释与空行后的有效词数
terms="$(grep -cv -e '^\s*#' -e '^\s*$' "$WORDLIST" || true)"
if [[ "$terms" -eq 0 ]]; then
  printf 'D6 脱敏扫描：跳过（词表为空）\n'
  exit 0
fi

# 有效词提取到临时文件（循环外一次，免得每文件起一次子进程）
TERMS_FILE="$(mktemp)"
trap 'rm -f "$TERMS_FILE"' EXIT
grep -v -e '^\s*#' -e '^\s*$' "$WORDLIST" > "$TERMS_FILE"

hits=0
errors=0
# 只扫 git 跟踪的文件——工作树垃圾与未跟踪文件不会被发布，不在门禁范围。
# -z + read -d ''：非 ASCII 文件名会被 git 默认 C-quote 转义，普通逐行读会拼出
# 不存在的路径而被静默跳过（fail-open，正是本脚本要根治的「字面通过、意图落空」）。
while IFS= read -r -d '' f; do
  set +e
  out="$(grep -n -i -F -f "$TERMS_FILE" -- "$REPO_ROOT/$f")"
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    printf '✗ %s\n%s\n' "$f" "$out"
    hits=$((hits + 1))
  elif [[ $rc -ge 2 ]]; then
    # 文件读不了必须响（fail-closed）——静默跳过等于没扫
    printf '! 无法扫描：%s\n' "$f"
    errors=$((errors + 1))
  fi
done < <(git -C "$REPO_ROOT" ls-files -z)

if [[ "$hits" -gt 0 || "$errors" -gt 0 ]]; then
  printf '\nD6 脱敏扫描：%d 个文件命中词表，%d 个文件无法扫描——发布前必须清理/修复（词表 %s）\n' \
    "$hits" "$errors" "$WORDLIST"
  exit 1
fi
printf 'D6 脱敏扫描：通过（%s 个词，全仓 0 命中）\n' "$terms"
