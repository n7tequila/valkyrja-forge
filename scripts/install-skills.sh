#!/usr/bin/env bash
#
# install-skills.sh — 将本仓库 skills/ 下的 Claude Code skill 批量安装到
# 系统级（~/.claude/skills/）或项目级（<project-root>/.claude/skills/）目录。
#
# 定位：**离线/无 git 场景的兜底安装路径**。主路径是官方 plugin 体系——
#   /plugin marketplace add n7tequila/valkyrja-forge && /plugin install valkyrja
# （版本、升级、卸载由 plugin 机制原生提供，本脚本不再补造这些能力）。
#
# 用法:
#   scripts/install-skills.sh [目标] [选项] [skill-name ...]
#
# 目标（二选一，默认 --project）:
#   --project [DIR]   安装到项目级 .claude/skills/（DIR 默认当前目录——注意：
#                      在 forge 仓根照抄示例会装进 forge 仓自身；目标是产品仓，
#                      用 --project <目标仓路径> 或先 cd 到目标仓再调本脚本）
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
#   scripts/install-skills.sh --project valkyrja-prd     # 只装指定 skill 到当前项目
#   scripts/install-skills.sh --system --list             # 查看系统级已装了哪些 skill
#   scripts/install-skills.sh --project --dry-run --force # 预览覆盖安装会做什么

set -euo pipefail

# ---------- 路径与默认值 ----------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_SRC_DIR="${REPO_ROOT}/skills"

# 斜杠命令命名空间：仓内命令平铺于 commands/<名>.md（plugin 形态由 plugin 名
# 提供命名空间 /valkyrja:<名>）；本脚本安装到 <dest>/commands/<NS>/<名>.md，
# 由目录提供同名命名空间——两条安装路径产出同一命令名。
COMMAND_NS="valkyrja"
COMMANDS_SRC_DIR="${REPO_ROOT}/commands"

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

# 从工作树 cp -r 会带上 git 排除不了的垃圾（.DS_Store、__pycache__/*.pyc）——
# 项目级安装的 .claude/ 随消费仓提交，垃圾会进入其 git 历史，装后清一遍。
scrub_junk() {
  find "$1" -name '.DS_Store' -type f -delete 2>/dev/null || true
  find "$1" -name '*.pyc' -type f -delete 2>/dev/null || true
  find "$1" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
}

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
  CLAUDE_ROOT="${HOME}/.claude"
else
  CLAUDE_ROOT="${PROJECT_ROOT}/.claude"
fi

SKILLS_DEST_DIR="${CLAUDE_ROOT}/skills"
COMMANDS_DEST_DIR="${CLAUDE_ROOT}/commands/${COMMAND_NS}"

# 命令备份必须放在 commands/ 树之外。
# Claude Code 把 commands/ 下**每一层子目录都当命名空间递归扫描**，
# 所以 commands/<NS>/.backup/prd-<时间戳>.md 会被注册成一个幽灵命令
# /<NS>:.backup:prd-<时间戳>，且每次 --force 都新增两个、不断累积。
# （技能侧无此问题：技能加载器要求 <目录>/SKILL.md，.backup/ 本身没有，故不被识别。）
COMMANDS_BACKUP_DIR="${CLAUDE_ROOT}/.valkyrja-backup/commands"

# ---------- --list 模式 ----------

if [[ $LIST_MODE -eq 1 ]]; then
  c_step "已安装的 skill（${SKILLS_DEST_DIR}）"
  if [[ ! -d "$SKILLS_DEST_DIR" ]]; then
    c_info "目录不存在，尚未安装任何 skill。"
  else
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
  fi

  c_step "已安装的斜杠命令（${COMMANDS_DEST_DIR}）"
  if [[ ! -d "$COMMANDS_DEST_DIR" ]]; then
    c_info "目录不存在，尚未安装任何命令。"
  else
    found=0
    for f in "$COMMANDS_DEST_DIR"/*.md; do
      [[ -f "$f" ]] || continue
      name="$(basename "$f" .md)"
      desc="$(sed -n 's/^description:[[:space:]]*//p' "$f" | head -1)"
      c_ok "/${COMMAND_NS}:${name}  —  ${desc:0:60}$( [[ ${#desc} -gt 60 ]] && echo '…' )"
      found=1
    done
    [[ $found -eq 0 ]] && c_info "（空）"
  fi
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
      scrub_junk "$dest"
      c_ok "${name}：已覆盖安装（升级）"
    fi
    installed=$((installed + 1))
  else
    if [[ $DRY_RUN -eq 1 ]]; then
      c_info "[dry-run] 将新装 ${name} → ${dest}"
    else
      cp -r "$src" "$dest"
      scrub_junk "$dest"
      c_ok "${name}：已安装"
    fi
    installed=$((installed + 1))
  fi
done

# ---------- 安装斜杠命令 ----------
#
# 命令是技能的入口转接，随技能一起安装：commands/<NS>/<名>.md → /<NS>:<名>。
# 只在「安装了全部 skill」时安装（指定单个 skill 时不装，避免命令指向未安装的技能）。

cmd_installed=0
cmd_skipped=0

if [[ ${#REQUESTED_SKILLS[@]} -eq 0 && -d "$COMMANDS_SRC_DIR" ]]; then
  c_step "斜杠命令：/${COMMAND_NS}:*（${COMMANDS_DEST_DIR}）"

  # 迁移：早期版本把命令备份错误地放在 commands/<NS>/.backup/ 下，
  # 被 Claude Code 当作嵌套命名空间注册成幽灵命令 /<NS>:.backup:<名>-<时间戳>。
  # 这里把它整体移出扫描树（移动而非删除，备份内容不丢失）。
  legacy_cmd_backup="${COMMANDS_DEST_DIR}/.backup"
  if [[ -d "$legacy_cmd_backup" ]]; then
    if [[ $DRY_RUN -eq 1 ]]; then
      c_warn "[dry-run] 将迁移旧命令备份 ${legacy_cmd_backup} → ${COMMANDS_BACKUP_DIR}（消除幽灵命令）"
    else
      mkdir -p "$COMMANDS_BACKUP_DIR"
      for old_bak in "$legacy_cmd_backup"/*; do
        [[ -e "$old_bak" ]] && mv "$old_bak" "${COMMANDS_BACKUP_DIR}/"
      done
      rmdir "$legacy_cmd_backup" 2>/dev/null || true
      c_warn "已迁移旧命令备份至 ${COMMANDS_BACKUP_DIR}，并消除其产生的幽灵命令"
    fi
  fi

  [[ $DRY_RUN -eq 0 ]] && mkdir -p "$COMMANDS_DEST_DIR"

  for src_cmd in "$COMMANDS_SRC_DIR"/*.md; do
    [[ -f "$src_cmd" ]] || continue
    cmd_name="$(basename "$src_cmd" .md)"
    dest_cmd="${COMMANDS_DEST_DIR}/${cmd_name}.md"

    if [[ -f "$dest_cmd" && $FORCE -eq 0 ]]; then
      c_warn "/${COMMAND_NS}:${cmd_name}：已存在，跳过（加 --force 覆盖）"
      cmd_skipped=$((cmd_skipped + 1))
      continue
    fi

    if [[ -f "$dest_cmd" && $NO_BACKUP -eq 0 && $DRY_RUN -eq 0 ]]; then
      mkdir -p "$COMMANDS_BACKUP_DIR"
      cp "$dest_cmd" "${COMMANDS_BACKUP_DIR}/${cmd_name}-$(date +%Y%m%d%H%M%S).md"
    fi

    if [[ $DRY_RUN -eq 1 ]]; then
      c_info "[dry-run] 将安装 /${COMMAND_NS}:${cmd_name} → ${dest_cmd}"
    else
      cp "$src_cmd" "$dest_cmd"
      c_ok "/${COMMAND_NS}:${cmd_name}：已安装"
    fi
    cmd_installed=$((cmd_installed + 1))
  done
fi

c_step "完成：skill 安装/升级 ${installed}，跳过 ${skipped}，失败 ${failed}；命令 ${cmd_installed}，跳过 ${cmd_skipped}"
[[ $failed -gt 0 ]] && exit 1
exit 0