# valk-tools

个人工作方式工具箱。四条**跟人走**的技能——换哪个项目都一样用，与项目领域无关。

本目录是 valkyrja-forge 仓里的**第二个 plugin**，与同仓承载 valkyrja 协议的
`valk` plugin **没有任何依赖关系**，只共享 git 历史：

| | `valk` | `valk-tools` |
|---|---|---|
| 治理什么 | 产品生命周期（需求 → 技术契约 → 开发） | 会话与个人工作回路 |
| 装到哪 | 消费产品仓，项目级 | 跟着人走，用户级 |
| 版本 | 独立 | 独立 |

## 四条技能

| 技能 | 做什么 |
|---|---|
| `context-handoff` | 上下文将满时固化现场、清空、再无损接上；也用于新会话恢复现场。同一宿主内换会话 |
| `host-handoff` | 在 Claude Code 与 Codex 之间换宿主：交接包、Git/文件核验与项目指令更新确认，保留半完成工作与待确认边界 |
| `merge-pr` | 开 PR/MR，GitHub 走 gh CLI，自建 forge 降级为标题正文 + compare URL |
| `refactor-review` | 重构审查，只审不改：按局部→结构→模式三级阶梯判断哪里值得重构、哪里不该动，结论含 KEEP / REJECT / TESTS_FIRST / REWRITE，按级别分层确认；审完留重构台账，下次先对账 |

技能自身就是入口，无命令层。调用名按宿主与安装形态而定，`<技能名>` 即上表四个名字：

- Claude Code：plugin 安装 `/valk-tools:<技能名>`，复制安装 `/<技能名>`
- Codex：plugin 安装 `$valk-tools:<技能名>`，复制安装 `$<技能名>`

Codex 两种形态的注册名已于 2026-10-06 用 `codex debug prompt-input` 实测。
两宿主共用源码；选择/确认工具不可用时以文字问答等待人类回复。

### 做到一半，换个宿主接着做

在仍保留任务上下文的交出方会话里，以 Claude 交给 Codex 为例：

```text
/valk-tools:host-handoff 把当前任务交接给 Codex，交接包放在 <已有交接目录>/<任务名>.md。
```

然后在同一产品工作区里，接手方的新会话：

```text
$valk-tools:host-handoff 接收 <交接包路径>，继续 <具体任务>。
```

反方向（Codex 交出、Claude 接手）用同一协议，调用名换成各自宿主与安装形态对应的那个。
交出方给出的启动提示词会写明接手方的精确调用名。

交出方会话里还没有这个技能时（本地新增尚未发布），可以让该会话完整读取 checkout 中
`valk-tools/skills/host-handoff/SKILL.md` 再按它导出，不必重开丢掉上下文；
Claude 也可通过 `claude --resume <原会话ID> --plugin-dir /absolute/path/to/valkyrja-forge/valk-tools`
会话级加载。不要为此重复复制一份用户级技能或覆盖整份配置。

技能自带只读状态 helper：核对 HEAD、index、dirty 文件与选定产物哈希。它**不提交**——
未提交状态原样交给接手方，靠指纹核对发现漂移；这点与 `context-handoff` 交接前先提交不同。
Markdown 保存任务语义与证据指针，旁置 JSON 保存机器状态，两者都不能代替正式产品/技术权威
或本次门禁确认。没有交接包时可先从磁盘只读重建；未落盘的对话取舍仍需交出方或用户补齐。
这不是让一个宿主读取另一个宿主的会话记录，也不搬运认证或整个私有历史。

实测状态（隔离夹具，各方向单次运行，是行为证据，不是保证）：
Claude → Codex 在旧名 `claude-to-codex` 下实测；Codex → Claude 于 2026-10-06 实测，
含状态一致时接续与导出后被改动时停在只读对账两种情形。
详见 [技能协议](skills/host-handoff/SKILL.md) 与 [设计/验证记录](../docs/design/host-handoff.md)。

## 安装

```
/plugin marketplace add n7tequila/valkyrja-forge
/plugin install valk-tools
```

装完需重启。装 `valk-tools` 与装 `valk` 互不影响，可以只装一个。

Codex CLI 注册本地 checkout 后安装：

```bash
codex plugin marketplace add /absolute/path/to/valkyrja-forge
codex plugin add valk-tools@valkyrja-forge
```

复制式离线安装：`scripts/install-skills.sh --harness codex --plugin valk-tools --system`
（在仓根运行），落 `~/.agents/skills/`。项目级可用 `--project <目标路径>`。

**不要再把 `skills/` 手动拷进 `~/.claude/skills/`**——两种形态同装会双注册
（同一技能出现两次），且手动那份不随 plugin 更新，模型可能读到旧版而无任何提示。
同样不要在 Codex 同时保留 plugin 与手动副本。复制安装器现在通过
`--plugin valk-tools` 选择本目录；默认仍只安装 `valk`。

## 编辑纪律

- `skills/*/SKILL.md` 是**唯一真相源**。每次调用全量进上下文——控制篇幅。
- **本 plugin 不设 `commands/` 层。** 技能名本身就短，`/valk-tools:merge-pr` 直接
  调起技能即可。曾经加过同名的薄转接命令，结果是斜杠面板里同一个名字出现两次——
  命令与技能同名就会双列。valk 那边不撞是因为命令叫 `arch`、技能叫 `valkyrja-arch`，
  短命令是给长技能名当入口的；这里技能名已经短，命令纯属重复。
  **今后若要加命令，命令名必须与技能名不同**，否则不要加。
- 改了本目录内容，**只抬本 plugin 的版本**（根 `plugin.json`、
  `.claude-plugin/plugin.json` 与仓根 marketplace 的 `valk-tools` 条目三处必须一致），
  **不要动 `valk` 的版本**——两个 plugin 的版本互不相干。

## 收录门槛

本 plugin 随公开仓分发，因此**只收不依赖本机私有配置、也不暴露仓库布局的技能**。
依赖 `~/.claude/rules/*` 或特定目录结构的技能留在 `~/.claude/skills/` 本地使用，
不进本目录——`code-review-full` 即因此未收录。
