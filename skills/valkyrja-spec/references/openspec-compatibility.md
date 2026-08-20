# OpenSpec 兼容性与官方 skill 冲突缓释（详版）

> **何时读本文件**：会话启动的前提检测发现缺 workflow、准备归档、
> 写 `openspec/config.yaml` 注入、或遇到官方 skill 行为与本技能门禁冲突时。
> SKILL.md 只保留检测清单与结论；条件分支与理由在这里。
>
> 以下行为均为对 OpenSpec **v1.9.0 实测确认**，非文档推断。

## 一、环境前提的条件分支

### `openspec init` 的副作用

会按**当前 profile 与 delivery 设置**在 `.claude/` 下生成对应的 workflow skills
与 `/opsx:*` 命令——**数量随 profile 而变，不要向用户断言固定数量**。
本技能代跑前须回显完整命令行与将创建的文件清单，经人确认。

### 缺 workflow 时的补救：先判 profile，再决定手段

评审曾建议「缺什么就跑 `openspec update`」。**实测推翻**：
`update` 按当前 profile 重新生成，profile 若排除了该 workflow，跑了也是空操作。

```
openspec config get workflows
     │
     ├── 含目标 workflow，但 skill 文件缺失
     │      → 安装产物过期。项目内跑 `openspec update`（只动本项目，无需改全局）
     │
     └── 不含目标 workflow（如 profile=custom 且排除了它）
            → `openspec update` 是空操作，跑了也不会装上。
              唯一出口是改 profile：`openspec config profile core`
              **这修改全局 ~/.config/openspec/config.json，影响本机所有项目**，
              属特权动作，必须经人确认，不得代跑。
```

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

## 二、归档路径的选择

trace（pre-archive）放行后，**优先委托 CLI**：`openspec archive <change-name>`
（回显后经人确认执行），随后跑 V6。

理由：CLI 自带 validate → 合并 delta → 必要时 capability 退休 → 移动 change
→ 失败时回滚的完整实现，**不依赖 `openspec-sync-specs` skill 是否安装**；
且官方 archive *skill* 的设计原则是「警告不阻塞」，与本技能的门禁语义相悖。

若用户偏好走官方 skill 路径，须先确认 sync workflow 已安装，否则合并链断裂。

## 三、config.yaml 注入：抑制 propose 重新追问已决事项

baseline 首次定稿时（经握手）写入 `openspec/config.yaml` 的 `context` 与 `rules`
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
保持探索态（不得归档）/ 删除。**计划外 change 一律不得通过归档门禁。**

### `skip_specs` 逃生口

`.openspec.yaml` 的 `skip_specs: true` 会让 `openspec validate` 接受零 delta 的 change。
本技能视其为**需人工裁决的例外**：trace 一律 ERROR，除非基线「例外记录」中已有
对该 change 的显式裁决与理由。
理由：零 delta 意味着该 change 不携带任何可追溯需求，会在覆盖对账中制造静默缺口。

### 已知治理缺口（诚实写明）

若用户直接调用 `/opsx:apply`、`/opsx:archive` 或 `openspec archive`，
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
