# 换宿主工作交接（host-handoff）

日期：2026-10-06。来源：用户明确要求接续 Claude 已进行到一半的工作；
现有 context-handoff 与治理产物审查、临时仓回归及独立评审。
本技能初版名为 `claude-to-codex`（单向），同日改名并改为双向，见「改名与双向」。

## 设计裁决

新增 `valk-tools/skills/host-handoff/`（初版目录 `claude-to-codex/`），而不是把普通会话压缩
变成宿主迁移工具。`context-handoff` 仅作路由指针；交接协议以本 SKILL 为唯一权威，
模板只定义记录载体。不复制 valk 协议，不增加依赖，不修改 trace 判定或 `valk` 版本；
工具箱单独升为 0.5.0。

接续分三类：

| 可恢复的信息 | 接续方式 |
|---|---|
| 同一工作区的代码、Git 状态、正式治理产物 | 从磁盘读取并核对，不重造、不清理 |
| 交出方仍持有的任务上下文、取舍、未完成事项 | 导出 Markdown 交接包与旁置状态 JSON |
| 未落盘且源会话已不可访问的决定 | 标未知，由用户补充，不从任务勾选或目录存在性猜测 |

[官方会话说明](https://learn.chatgpt.com/docs/projects)把 `codex resume` 定义为恢复已保存的
Codex 对话；`claude --resume` 同理只恢复 Claude 自己的对话。本实现采用可移植文件接续，
不把一个宿主的会话 ID 冒充成另一个宿主的。本地未发布技能可让交出方会话直接完整读取
checkout 中的 SKILL；无需导出整个私有会话库。

本技能不提交：未提交状态原样交给接手方，安全网是旁置 JSON 的指纹核对。
`context-handoff` 交接前先提交本任务改动，是因为它没有这层核对——两者不矛盾。

## 改名与双向（2026-10-06）

来源：外部评审（Codex 适配审查）+ 用户裁决。初版只覆盖 Claude → Codex，名字也写死方向；
而本仓此后两个宿主都要用，反方向（Codex 做到一半交回 Claude）是现实需求——
这次 Codex 适配本身就是 Codex 做了一半、由 Claude 审查接续的。若以后另写
`codex-to-claude`，两个技能大部分内容相同，又是一对会各自漂移的副本；若发布后再改名，
习惯、README 与提示词都要跟着改。初版尚未提交，此时改名代价最小。

裁决：改名 `host-handoff`，与 `context-handoff` 成对（一个同宿主换会话，一个换宿主）；
协议改为方向中立的「交出方导出 / 接手方核验后接续」，安全语义逐条保留；
helper 不分宿主，原样沿用（只改路径）。启动提示词必须写接手方的**精确调用名**——
Claude Code plugin `/valk-tools:host-handoff`、复制安装 `/host-handoff`；
Codex plugin `$valk-tools:host-handoff`、复制安装 `$host-handoff`
（Codex 两种形态的注册名用 `codex debug prompt-input` 实测）。反方向实测前不宣称支持。

## 为什么有状态 helper

自然语言交接容易遗漏 staged 与 unstaged 的区别，也无法发现导出后代码又被修改。
helper 只读采集 Git HEAD、分支、index 元数据指纹、dirty 文件和显式选定路径状态；
接收时输出是否匹配和差异路径，不执行配置迁移或旧补丁重放。

交接包自身排除以避免自引用，但 stage/commit 它会改变 index/HEAD，核验仍应失配。
敏感文件不读正文且明确列 omitted；显式敏感路径、越界路径和 symlink 父目录被拒绝。
文件指纹不带 diff 正文、环境变量、remote URL 或认证信息。

权威与权限不是哈希能传递的：验证通过只证明采集范围当前一致。
正式发布/决策沿项目原产物核对；未确认事项保持 pending，历史门禁结果不当作本次放行。
旧会话停止写入是交接前提，不由一个成功的 verify 结果替代。

## 验证

### 初版（旧名 `claude-to-codex`，Claude → Codex）

- 安装回归先 RED：缺第四个技能与单独安装的 helper/template，16 测试中 4 个失败子场景；实现后通过。
- 状态 helper 先确认无实现的 RED，再完成 19 个隔离测试。
- 全量 `test_*.py`：44 测试通过；原 trace：22 场景失败 0。
- 新 SKILL quick_validate、shell 语法、diff 空白检查、Claude marketplace/plugin 校验通过。
- 独立只读评审：状态、安装和打包测试复跑通过，无阻断问题。
- Codex 实际安装 `valk-tools` 0.5.0，installed/enabled；缓存中的新技能/helper 与源码一致。
- 独立 forward-test：导出方在临时仓生成包并两次 verify 匹配，保留 MM 源码与用户 untracked 笔记；
  未知历史信息标未知，小数金额接口提议保持 pending。
- 不继承源对话的另一接收方：先匹配证据，复现 RED，补足原整数分任务的负数处理，
  两项原测试及额外边界检查通过；index、用户笔记、正式需求与交接包不变，没有提交。
- 独立漂移场景：已允许路径搬迁，但新增文件触发 verify 退出 1；接收方停在只读对账，
  没有改代码、重写旧包或提交来制造匹配。这些都是隔离夹具验证，不是真实 Claude 宿主实跑。

### 反方向（`host-handoff`，Codex → Claude，2026-10-06）

夹具：临时 git 仓，基线提交含正数格式化与测试；未提交的负数分支桩（`NotImplementedError`）；
未跟踪的用户笔记；两宿主的复制安装（经 `.git/info/exclude` 排除，不计入 dirty）。
各情形单次运行，是宿主行为证据，不是确定性保证。

- **导出（Codex CLI 0.160.0，默认模型）**：`codex exec --ephemeral --skip-git-repo-check
  --sandbox workspace-write --ignore-user-config --json`，stdin 关闭，提示词以 `$host-handoff`
  开头并给出包路径。退出 0；包与旁置 JSON 落在指定位置；提交数不变、无 stash、
  用户笔记不变；独立重跑 `verify` 退出 0（match）。包头写明目标宿主与安装形态，
  启动提示词用了接手方精确名 `/host-handoff`。导出过程生成的 `__pycache__` 已被快照收录。
- **接收、状态一致（Claude Code 2.1.289，claude-sonnet-5-5）**：`claude -p "/host-handoff 接收 …"
  --setting-sources project,local --permission-mode acceptEdits`，允许 git/python3 等 Bash；
  init 事件确认只加载内置 plugin，用户级已装的旧版 valk-tools 未混入。
  先读包与 JSON、`git status`/`diff`，再 `verify`（match），之后才首次编辑；
  只完成负数分支与负数测试（2 个测试通过），另把 TASKS.md 对应项打勾并在回复中声明；
  未提交/暂存/stash，用户笔记与交接包不变；`ps` 被权限拒绝，如实报告未能确认源会话写入情况。约 $0.15。
- **接收、导出后被改动（同路径，导出后给 money.py 追加一行）**：`verify` 退出 1；
  接收方未改任何文件，未 reset/checkout/重写快照，指出漂移路径与新增内容，请用户确认后再继续。约 $0.06。

## 剩余边界

快照不是原子的，必须避免并发写入；JSON 未签名，应按协议核对来源与覆盖范围。
未选中的 clean 文件、ignored 文件、敏感正文与 symlink 目标不在内容指纹覆盖内。
非 Git 项目明确标 limited。状态匹配不证明实现正确、测试仍绿或新的操作获得授权。
不能恢复源会话中未提供/已丢失的内容，不能自动把另一机器缺失的未提交代码变出来。
两个方向都只在隔离夹具上单次实测，尚未宣称真实产品仓的全生命周期验收；
plugin 安装形态下的端到端交接未实测（注册名已离线实测）。
