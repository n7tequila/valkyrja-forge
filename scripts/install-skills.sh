#!/usr/bin/env bash
#
# install-skills.sh — 将本仓库 skills/ 下的 Claude Code skill 批量安装到
# 系统级（~/.claude/skills/）或项目级（<project-root>/.claude/skills/）目录。
#
# 用法:
#   scripts/install-skills.sh [目标] [选项] [skill-name ...]
#
# 目标（二选一，默认 --project）:
#   --project [DIR]   安装到项目级 .claude/skills/（DIR 默认当前目录，即仓库根）
#   --system          安装到系统级 ~/.claude/skills/（对本机所有项目生效）
#
# 选项:
#   --all             安装 skills/ 下全部 skill（未指定 skill-name 时的默认行为）
#   --force           已存在同名 skill 时覆盖安装（不加此项遇到已安装则跳过并提示）
#   --no-backup       覆盖时不做备份（默认会备份，见下）
#   --dry-run         只打印将要执行的操作，不实际写入
#   --list            列出目标目录下已安装的 skill 及其 name/description，不安装
#   -h, --help        显示本帮助
#
# 参数:
#   skill-name ...    只安装指定的一个或多个 skill（对应 skills/<name>/ 目录名）
#                      不指定则等同 --all
#
# 覆盖安装行为:
#   --force 且目标已存在同名 skill 时，先将旧版本整体复制到
#   <目标skills目录>/.backup/<name>-<时间戳>/ 再覆盖，不静默丢失旧版本。
#   未加 --force 时，已存在的同名 skill 会被跳过并给出提示，不会报错中断。
#
# 校验:
#   安装前检查每个 skill 目录下必须存在 SKILL.md，且其 YAML frontmatter
#   含 name 与 description 字段，否则跳过该 skill 并报错（不中断其余 skill 的安装）。
#
# 示例:
#   scripts/install-skills.sh --project                # 装全部到当前项目
#   scripts/install-skills.sh --system --force           # 装全部到系统级，覆盖旧版本
#   scripts/install-skills.sh --project prd-workshop     # 只装指定 skill 到当前项目
#   scripts/install-skills.sh --system --list             # 查看系统级已装了哪些 skill
#   scripts/install-skills.sh --project --dry-run --force # 预览覆盖安装会做什么

set -euo pipefail

# ---------- 路径与默认值 ----------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_SRC_DIR="${REPO_ROOT}/skills"

TARGET_MODE=""            # project | system
PROJECT_ROOT="$(pwd)"
FORCE=0
NO_BACKUP=0
DRY_RUN=0
LIST_MODE=0
declare -a REQUESTED_SKILLS=()

# ---------- 输出辅助 ----------

c_info()  { printf '  %s\n' "$*"; }
c_ok()    { printf '  \033[32m✓\033[0m %s\n' "$*"; }
c_warn()  { printf '  \033[33m!\033[0m %s\n' "$*"; }
c_err()   { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; }
c_step()  { printf '\n\033[1m%s\033[0m\n' "$*"; }

die() { c_err "$*"; exit 1; }

# ---------- 参数解析 ----------

print_help() {
  # 打印 shebang 之后、直到第一处非注释行为止的头部注释块，
  # 避免脚本正文代码被当成帮助文本输出。用 awk 而非固定行号范围的
  # sed，兼容 macOS/BSD sed 且不受头部注释增删行数影响。
  awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      TARGET_MODE="project"
      shift
      # 可选的紧随目录参数（不是以 - 开头、且是已存在目录时才当作 DIR）
      if [[ $# -gt 0 && "$1" != --* && -d "$1" ]]; then
        PROJECT_ROOT="$(cd "$1" && pwd)"
        shift
      fi
      ;;
    --system)
      TARGET_MODE="system"
      shift
      ;;
    --all)
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --no-backup)
      NO_BACKUP=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --list)
      LIST_MODE=1
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    --*)
      die "未知选项：$1（--help 查看用法）"
      ;;
    *)
      REQUESTED_SKILLS+=("$1")
      shift
      ;;
  esac
done

[[ -z "$TARGET_MODE" ]] && TARGET_MODE="project"

if [[ "$TARGET_MODE" == "system" ]]; then
  SKILLS_DEST_DIR="${HOME}/.claude/skills"
else
  SKILLS_DEST_DIR="${PROJECT_ROOT}/.claude/skills"
fi

# ---------- --list 模式 ----------

if [[ $LIST_MODE -eq 1 ]]; then
  c_step "已安装的 skill（${SKILLS_DEST_DIR}）"
  if [[ ! -d "$SKILLS_DEST_DIR" ]]; then
    c_info "目录不存在，尚未安装任何 skill。"
    exit 0
  fi
  found=0
  for d in "$SKILLS_DEST_DIR"/*/; do
    [[ -d "$d" ]] || continue
    name="$(basename "$d")"
    [[ "$name" == ".backup" ]] && continue
    md="${d}SKILL.md"
    if [[ -f "$md" ]]; then
      desc="$(sed -n 's/^description:[[:space:]]*//p' "$md" | head -1)"
      c_ok "${name}  —  ${desc:0:70}$( [[ ${#desc} -gt 70 ]] && echo '…' )"
    else
      c_warn "${name}（缺少 SKILL.md，非法安装）"
    fi
    found=1
  done
  [[ $found -eq 0 ]] && c_info "（空）"
  exit 0
fi

# ---------- 校验源目录 ----------

[[ -d "$SKILLS_SRC_DIR" ]] || die "找不到源目录：${SKILLS_SRC_DIR}"

declare -a ALL_AVAILABLE=()
for d in "$SKILLS_SRC_DIR"/*/; do
  [[ -d "$d" ]] || continue
  ALL_AVAILABLE+=("$(basename "$d")")
done
[[ ${#ALL_AVAILABLE[@]} -eq 0 ]] && die "源目录下没有任何 skill：${SKILLS_SRC_DIR}"

if [[ ${#REQUESTED_SKILLS[@]} -eq 0 ]]; then
  TO_INSTALL=("${ALL_AVAILABLE[@]}")
else
  TO_INSTALL=("${REQUESTED_SKILLS[@]}")
  for name in "${TO_INSTALL[@]}"; do
    [[ -d "${SKILLS_SRC_DIR}/${name}" ]] || die "未找到 skill「${name}」（源目录：${SKILLS_SRC_DIR}）"
  done
fi

# ---------- 单个 SKILL.md 的最小校验 ----------

validate_skill() {
  local skill_dir="$1" name="$2"
  local md="${skill_dir}/SKILL.md"
  if [[ ! -f "$md" ]]; then
    c_err "${name}：缺少 SKILL.md，跳过"
    return 1
  fi
  if ! grep -q '^name:' "$md"; then
    c_err "${name}：SKILL.md 缺少 frontmatter 字段 name，跳过"
    return 1
  fi
  if ! grep -q '^description:' "$md"; then
    c_err "${name}：SKILL.md 缺少 frontmatter 字段 description，跳过"
    return 1
  fi
  return 0
}

# ---------- 安装主流程 ----------

c_step "安装目标：${TARGET_MODE}（${SKILLS_DEST_DIR}）"
[[ $DRY_RUN -eq 1 ]] && c_warn "dry-run 模式：只打印操作，不实际写入"

if [[ $DRY_RUN -eq 0 ]]; then
  mkdir -p "$SKILLS_DEST_DIR"
fi

installed=0
skipped=0
failed=0

for name in "${TO_INSTALL[@]}"; do
  src="${SKILLS_SRC_DIR}/${name}"
  dest="${SKILLS_DEST_DIR}/${name}"

  if ! validate_skill "$src" "$name"; then
    failed=$((failed + 1))
    continue
  fi

  if [[ -d "$dest" ]]; then
    if [[ $FORCE -eq 0 ]]; then
      c_warn "${name}：已安装，跳过（加 --force 覆盖升级）"
      skipped=$((skipped + 1))
      continue
    fi

    if [[ $NO_BACKUP -eq 0 ]]; then
      backup_dir="${SKILLS_DEST_DIR}/.backup/${name}-$(date +%Y%m%d%H%M%S)"
      if [[ $DRY_RUN -eq 1 ]]; then
        c_info "[dry-run] 将备份旧版本 ${name} → ${backup_dir}"
      else
        mkdir -p "$(dirname "$backup_dir")"
        cp -r "$dest" "$backup_dir"
        c_info "${name}：旧版本已备份至 ${backup_dir}"
      fi
    fi

    if [[ $DRY_RUN -eq 1 ]]; then
      c_info "[dry-run] 将覆盖安装 ${name} → ${dest}"
    else
      rm -rf "$dest"
      cp -r "$src" "$dest"
      c_ok "${name}：已覆盖安装（升级）"
    fi
    installed=$((installed + 1))
  else
    if [[ $DRY_RUN -eq 1 ]]; then
      c_info "[dry-run] 将新装 ${name} → ${dest}"
    else
      cp -r "$src" "$dest"
      c_ok "${name}：已安装"
    fi
    installed=$((installed + 1))
  fi
done

c_step "完成：安装/升级 ${installed}，跳过 ${skipped}，失败 ${failed}"
[[ $failed -gt 0 ]] && exit 1
exit 0