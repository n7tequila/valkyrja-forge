# valk-tools

个人工作方式工具箱。两条**跟人走**的技能——换哪个项目都一样用，与项目领域无关。

本目录是 valkyrja-forge 仓里的**第二个 plugin**，与同仓的 `valkyrja` 协议
**没有任何依赖关系**，只共享 git 历史：

| | `valkyrja` | `valk-tools` |
|---|---|---|
| 治理什么 | 产品生命周期（需求 → 技术契约 → 开发） | 会话与个人工作回路 |
| 装到哪 | 消费产品仓，项目级 | 跟着人走，用户级 |
| 版本 | 独立 | 独立 |

## 两条技能

| 技能 | 做什么 | 斜杠入口 |
|---|---|---|
| `context-handoff` | 上下文将满时固化现场、清空、再无损接上；也用于新会话恢复现场 | `/valk-tools:context-handoff` |
| `merge-pr` | 开 PR/MR，GitHub 走 gh CLI，自建 forge 降级为标题正文 + compare URL | `/valk-tools:merge-pr` |

plugin 形态下技能名带前缀，如 `valk-tools:context-handoff`。

## 安装

```
/plugin marketplace add n7tequila/valkyrja-forge
/plugin install valk-tools
```

装完需重启。装 `valk-tools` 与装 `valkyrja` 互不影响，可以只装一个。

**不要再把 `skills/` 手动拷进 `~/.claude/skills/`**——两种形态同装会双注册
（同一技能出现两次），且手动那份不随 plugin 更新，模型可能读到旧版而无任何提示。
仓根的 `scripts/install-skills.sh` 按设计**不覆盖本目录**，只装 valkyrja 的技能。

## 编辑纪律

- `skills/*/SKILL.md` 是**唯一真相源**。每次调用全量进上下文——控制篇幅。
- `commands/*.md` 是**薄转接**：只转发意图，**不复述技能里的规则、清单或确认要求**。
  复述即产生第二个可独立演化的副本，必然漂移。要改规则，改 SKILL.md 那一处。
- 改了本目录内容，**只抬本 plugin 的版本**（`valk-tools/.claude-plugin/plugin.json`
  与仓根 `marketplace.json` 里 `valk-tools` 条目，两处必须一致），
  **不要动 valkyrja 的版本**——两个 plugin 的版本互不相干。

## 收录门槛

本 plugin 随公开仓分发，因此**只收不依赖本机私有配置、也不暴露仓库布局的技能**。
依赖 `~/.claude/rules/*` 或特定目录结构的技能留在 `~/.claude/skills/` 本地使用，
不进本目录——`code-review-full` 即因此未收录。
