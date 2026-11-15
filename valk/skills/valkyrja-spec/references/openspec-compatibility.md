# OpenSpec 兼容性与官方 skill 冲突缓释（详版）

> **何时读本文件**：会话启动的前提检测发现缺 workflow 或宿主入口来源不明、准备归档、
> 写 `openspec/config.yaml` 注入、宿主没给出技能路径而要定位 trace.py、
> 或遇到官方 skill 行为与本技能门禁冲突时。
> SKILL.md 只保留检测清单与结论；条件分支与理由在这里。
>
> 以下行为均为对 OpenSpec **v1.9.0 实测确认**，非文档推断；
> 标注 (1.10.0) 的条目在 v1.10.0 上补测，标注 (2.0.0) 的在 v2.0.0 上实测（2026-11-13）。
> trace.py 的 V1.1 以 **[1.9, 2.0] 为已实测验证区间**：端点 1.10.0 与 2.0.0 实测，
> 1.11–1.17 未逐版安装，按官方发布说明逐条核对过与第六节相关的改动。
> 高于区间只 WARNING 不拦，但升级后应回到本文件逐条复验第六节的依赖行为再抬区间上界。
> npm 安装自 1.16 起要求 Node ≥ 22.12；不满足时用官方独立安装包。
>
> **Codex 适配依据（2026-10-06）**：宿主目录、skills-only 与调用名来自
> [OpenSpec 官方支持工具表](https://github.com/Fission-AI/OpenSpec/blob/main/docs/supported-tools.md)
> 与本机 v1.10.0 CLI/安装源码核对；workflow 名与 profile 来自
> [官方命令说明](https://github.com/Fission-AI/OpenSpec/blob/main/docs/commands.md)。
> 这些是安装契约依据，不等于 Codex 模型行为已完成真实项目端到端验证。

## 一、环境前提的条件分支

### `openspec init` 的副作用

宿主由当前会话或用户显式指定，不由仓库里的目录推断。

(2.0.0) **所有宿主共用 `.agents/skills/openspec-*/SKILL.md` 一份正文**，按当前 profile 生成；
Claude 用 `openspec init --tools claude`，在 `.claude/skills/openspec-*` 放**指向
`.agents/skills/` 的目录软链**（实测 Claude Code 经软链正常加载），调用为 `/openspec-*`；
Codex 用 `openspec init --tools codex`，直接读 `.agents/skills/`，调用为 `$openspec-*`。
`/opsx:*` 命令已删除，`delivery` 设置不再需要；`openspec update` 会清理旧版生成且未被
编辑的命令与重复技能（编辑过的保留并列出）。同仓两宿主可一次 `--tools claude,codex`，
`.agents/skills/.openspec-target` 逐行记宿主（Claude 一行为 `claude own-files`）。

1.x 旧项目：Claude 在 `.claude/` 下生成独立 skills 与 `/opsx:*` 命令（受 delivery 影响），
Codex 为 skills-only；遇到时建议升级 CLI 后在项目内跑 `openspec update`（经确认，会改项目文件）。
**数量随 profile 而变，不要向用户断言固定数量**。
本技能代跑前须回显完整命令行与将创建的文件清单，经人确认。

root 已存在而当前宿主未配置时，以对应 init 补配置；另一个宿主的产物不算本宿主可用。
旧 Codex `.codex/skills/` 交给官方 init/update 协调：官方只在替代品写入后清理可识别的
受管旧产物，保留自定义和已偏离内容；不手工扫掉整个目录。
`.agents/skills/` 可能由 `agents` 或其他宿主维护，仅有目录不代表已按 Codex 配置；
有 `.agents/skills/.openspec-target` 时读取宿主标识，旧无标识产物读生成的调用语法
（`$openspec-*` 为 Codex，只有 `/openspec-*` 则为通用宿主）。
需要转为 Codex 时先回显影响，再显式 `openspec init --tools codex`。

### 缺 workflow 时的补救：先判 profile，再决定手段

评审曾建议「缺什么就跑 `openspec update`」。**实测推翻**：
`update` 按当前 profile 重新生成，profile 若排除了该 workflow，跑了也是空操作。

```
openspec config get workflows
     │
     ├── 含目标 workflow，但当前宿主的 SKILL.md 缺失或不可读
     │      → 宿主未配置则经确认 init 对应宿主；否则是安装产物过期，
     │        经确认项目内跑 `openspec update`（不改全局，可能刷新已配置的多个宿主）
     │
     └── 不含目标 workflow（如 profile=custom 且排除了它）
            → `openspec update` 是空操作，跑了也不会装上。
              改 profile：sync 可用 `openspec config profile core`；
              verify 必须通过 `openspec config profile` 选择包含 verify 的 custom 集。
              **core 不含 verify，切回 core 不能补装 verify。**
              **这修改全局 ~/.config/openspec/config.json，影响本机所有项目**，
              属特权动作，必须经人确认后才执行；选择后在项目运行 update。
```

检测以当前宿主根下完整 `SKILL.md` 为准（软链按解析后的目标判定）：Claude `.claude/skills/`、
Codex `.agents/skills/`。仅 1.x 旧项目可能出现 Claude delivery=commands 而技能未生成：
此时可用已存在的 `/opsx:*` 命令委托，或建议升级 CLI 后 `openspec update`；2.0 起无此分支。propose/apply/verify 委托前分别检测实际入口，
其 Codex 名为 `$openspec-propose`、`$openspec-apply-change`、`$openspec-verify-change`，
sync 为 `$openspec-sync-specs`；不要把 Claude 的 `/openspec-apply-change`（1.x 为 `/opsx:apply`）写成不存在的 `$openspec-apply`。

若同时提示 CLI 有新版本，先建议升级 CLI 再 `openspec update`——新版本可能带来新 workflow。

### sync 与 verify 的严重性不同

| workflow | 缺失后果 | 是否有替代 |
|---|---|---|
| `openspec-sync-specs` | 官方 archive skill 的合并链断裂 | **有**——归档改走 CLI（见下） |
| `openspec-verify-change` | 状态机中「实现代码 ↔ change artifacts」一环缺失 | **无** |

**verify 不在官方 `core` profile 内**（core ＝ propose / explore / apply / update /
sync / archive），因此一个刚 `openspec init` 的标准项目**大概率没有它**。

> **verify 缺失比 sync 缺失严重**：本技能的 trace 只管 PRD ↔ spec，
> 不做「代码 ↔ artifacts」这件事，缺了它就没有任何替代方案，闭环会缺一段。
> 缺失时必须显式告知用户这一后果，而不是一句「可补装」带过。

### 宿主没给出技能路径时定位 trace.py

正常情况下两个宿主都会给出已加载技能的路径（Claude 给技能基目录，Codex 的技能清单带文件路径），
SKILL.md 直接按它定位 `tools/trace.py`。只有宿主没给出时，才按当前宿主查安装位置并核对版本：

- Codex：`.agents/skills/valkyrja-spec/`、`~/.agents/skills/valkyrja-spec/`，或已安装 plugin 的缓存目录
- Claude：`.claude/skills/valkyrja-spec/`、`~/.claude/skills/valkyrja-spec/`，或 plugin 目录；
  命令或 hook 上下文提供了 `${CLAUDE_PLUGIN_ROOT}` 时可据此定位（Codex 不依赖该变量）

找到多份且无法确认哪份与当前加载的技能同版时报告歧义，不挑一份用；一份都没有时报工具故障。
两种情况都不得冒称 trace 已通过。

## 二、归档路径的选择

trace（pre-archive）放行后，**优先委托 CLI**：`openspec archive <change-name>`
（回显后经人确认执行），随后跑 V6。

理由：CLI 自带 validate → 合并 delta → 必要时 capability 退休 → 移动 change
→ 失败时回滚的完整实现，**不依赖 `openspec-sync-specs` skill 是否安装**；
且官方 archive *skill* 的设计原则是「警告不阻塞」，与本技能的门禁语义相悖。

若用户偏好走官方 skill 路径，须先确认 sync workflow 已安装，否则合并链断裂。

## 三、config.yaml 注入：抑制 propose 重新追问已决事项

baseline 首次定稿时（经确认）写入 `openspec/config.yaml` 的 `context` 与 `rules`
（模板见 `../templates/config-injection.yaml`）。

**config 只写与具体 PRD 无关的通用治理协议**——绝不写死某个 PRD 或基线路径，
否则多 DOMAIN 仓库中后写的绑定会覆盖先写的，造成**串域**（具体绑定见契约一，
在 proposal.md 的 Requirement Authority 块）。因此该注入通常**只需写一次**，
后续 initiative 复用同一份协议。

### 写入后必须实跑验证（静默失效的坑）

```
openspec instructions specs --change <任一change> --json
```

确认 `context` 与 `rules` 确已出现在返回中。

**config.yaml 解析失败时 CLI 只打一行 warning 便静默忽略整个文件**——
注入全部失效而表面无异常。已踩过的具体坑：多行 rule 条目未用 `|-` 块标量书写时，
正文中的冒号会被 YAML 误判为隐式键，整份配置报废。

### 效力边界（必须向用户说明）

这是 **prompt 级建议，不是强制**——官方 skill 明确规定 `context`/`rules`
与内置指令冲突时以内置指令为准。注入只降低摩擦，**真正的保证来自 trace 的机检**。

## 四、官方 skill 的三个冲突面

### explore 侧门

官方 explore skill 可不经本技能直接 `openspec new change`。
这是合法的探索出口，本技能不禁止，但 `status` 与 `trace` 必须把磁盘上存在却不在
基线计划中的 change 列为**计划外 change**，要求人裁决：纳入基线（补记裁决）/
保持探索态（不得归档）/ 删除。**计划外 change 一律不得通过归档门禁**——
唯一出口是 decompose 纳入计划；「保持探索态」的裁决可在基线例外记录做**备案**
（行含 change 名与「计划外」），备案只消 trace 对它的重复提醒，不改变不得归档。

### `skip_specs` 逃生口

`.openspec.yaml` 的 `skip_specs: true` 会让 `openspec validate` 接受零 delta 的 change。
本技能视其为**需人工裁决的例外**：trace 一律 ERROR，除非基线「例外记录」中已有
对该 change 的显式裁决与理由。
理由：零 delta 意味着该 change 不携带任何可追溯需求，会在覆盖对账中制造静默缺口。

### 已知治理缺口（诚实写明）

若用户直接调用 Claude `/openspec-apply-change`、`/openspec-archive-change`（1.x 为 `/opsx:*`），Codex
`$openspec-apply-change`、`$openspec-archive-change` 或 `openspec archive`，
本技能**无法拦截**——官方 archive skill 的原则是「警告不阻塞」，
且它不会执行本技能的门禁。本技能只能保证：**经由本技能执行的 apply 与归档，
一定先跑过 trace**。绕过路径只能靠约定与未来的 CI 兜底。

**不得在任何场合承诺本技能能拦截绕过路径，也不得声称能事后证明某次归档曾放行过**
（trace 只读、不写 receipt，事后没有状态证据）。

## 五、validate 前移（纯增益、零冲突）

官方 skill 从不调用 `openspec validate`，delta 正确性直到归档阶段才由合并逻辑检查。
本技能在 trace 的 V5.1 中显式调用，把校验前移到 apply 之前。

## 六、已实测确认的其他行为

- `Sources:` 行不触发 `openspec validate --strict` 任何 issue
- `openspec archive` 合并时会随 ADDED / MODIFIED 把 `Sources:` 一并带进主 spec
- 在 `openspec show <spec> --type spec --json` 中 `Sources:` 呈现为
  `requirements[].text` 的首行，可直接机读提取
- proposal.md 增加自定义 `## Requirement Authority` 节不影响 `validate --strict`
- `openspec list --changes --json` 返回 `{"changes":[...], "root":{...}}`——
  解析时须取 `changes` 键，直接迭代顶层会把 `"changes"`/`"root"` 当成 change 名
- `rules` 注入**只出现在带 `--change` 的 instructions 输出**中；不带 `--change`
  时静默不含任何 rules——**无 change 的仓里验证注入必须先
  `openspec new change` 造一次性探针 change**，验证后删除其目录，
  否则「探针为空」与「注入失效」不可区分（零对象 ≠ 零发现）
- (2.0.0) 以上各条与下面的嵌套 capability 在 2.0.0 上复验通过；另实测：
  delta 中的 `## Purpose` 只在**新建** capability 时带进主 spec，未写则归档留下占位
  Purpose，主 spec 的 `validate --strict` 会因占位失败（所以模板要求新 capability 写 Purpose）；
  1.16 起 `config.yaml` 无法解析时 `validate` 退出 1（V5 因此能暴露），但 `instructions`
  仍只警告并忽略，注入后的实跑验证仍须保留
- (2.0.0) **tasks.md 末尾追加的任务组被识别**：`openspec instructions apply --json`
  列出追加组里的未勾选项（带行号），状态从 `all_done` 回到 `ready`；不带复选框的说明文字
  不计入进度，`validate --strict` 照常通过——cross-host.md 复审组格式依赖这一点
- (2.0.0) 官方 spec-driven schema 指引在 tasks.md 末尾可选 `## Workflow follow-up` 节，以普通列表
  记录归档等需在归档时/之后做的步骤，不计入任务进度；本技能追加的复审组排在其后，不与之冲突
- (1.10.0) **嵌套 capability 是一等语义**：delta 放
  `specs/payments/refunds/spec.md` 时 `validate --strict` 通过，`archive` 输出
  「Applying changes to openspec/specs/payments/refunds/spec.md」——
  capability 身份是 specs/ 下**完整相对路径**，归档合并保持嵌套、不压平。
  trace 的主 spec 反查必须同口径（trace-contract.md「capability 身份」节）
