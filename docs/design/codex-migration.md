# Codex 迁移评估与验证

日期：2026-10-06。来源：源码审查、独立评审、本机 CLI 实测与模型行为冒烟。

## 结论与边界

保留原治理协议，迁移宿主接口，不另建一棵 Codex 技能源码。
产品发布权、技术裁决权、不可变 release、双向追溯门禁是工作流核心，不因换模型而放宽。
Claude 安装保持可用；模型路由、个人 MCP、OpenSpec 全局 profile 不属于迁移目标。

实施次序：先锁定安装回归，再适配技能路径/护栏/委托，再打包和验证，最后安装 Codex plugin。
安装器新增能力有先失败后通过的测试证据；原 trace 判定实现未修改。

## 改动理由

- 一个共享 `skills/`：避免双宿主协议与门禁版本分叉；portable 清单与 Claude 兼容清单通过版本一致性测试。
- 宿主取自当前会话，不以目录存在性推断。护栏块一份正文两宿主共用，写到当前宿主实际会读的指令文件，
  不自动各写一份（细则见下方「复审修订」）。
- `trace.py` 优先从已加载技能目录定位，避免误用另一份旧门禁。
- OpenSpec 使用官方 Codex skills-only 入口。缺 verify 不再建议切回不含 verify 的 core profile。
- 私有 catalog 保留原位置 `~/.claude/valkyrja/catalog/`，可用 `VALKYRJA_CATALOG_ROOT` 覆盖；Codex 同样读这里。
- 交互工具缺失时用文字问句等待确认；没有交互工具不等于已获确认。

首次模型冒烟发现两个负向路由提前读取 SKILL，再决定不接管。虽然无越权写盘，
仍违反原严格准入断言。因此前置 description 准入判断，保持 grader 不变，重新执行。
独立评审另发现读取判据假阳性；现在仅接受成功完成且输出含技能 frontmatter 的读取命令，
并用拒绝 echo、失败与未完成事件的测试锁定。行为轨迹保留在私有临时目录，不入库。

## 复审修订（2026-10-06，外部评审 + 真实运行）

Claude 侧复审了本次迁移是否守住原设计。核心——三层流水线、人拍板、特权确认、trace 终审、
opt-in 边界、trace 判定——没有变；偏差集中在适配层自身，经用户逐条裁决后修订：

- **护栏块合为一份**：原为 CLAUDE/AGENTS 两份正文且无跨份测试；Codex 版写的 `$valkyrja-*`
  只对复制安装成立（plugin 安装的注册名带 `valk:` 前缀，`codex debug prompt-input` 离线实测）。
  现三技能共用一份 `templates/guard-block.md`，入口写稳定技能名，精确调用名只写在 README。
- **写到宿主实际会读的文件**：实测 Claude Code 2.1.289 没有 CLAUDE.md 时读 AGENTS.md，
  有 CLAUDE.md 就不读 AGENTS.md（`@AGENTS.md` 导入可读）；Codex 只读 AGENTS.md。旧规则会在
  只有 AGENTS.md 的仓里新建 CLAUDE.md，悄悄挡掉原有规则。现规则：Codex 写 AGENTS.md；
  Claude 有 CLAUDE.md 写它，没有就写 AGENTS.md、不新建 CLAUDE.md；块在不在按宿主实际读到的内容判断。
- **写入安全**：回显解析软链后的真实路径；越出消费仓或写权限不明即停；旧版块只报告，修复单独确认、
  只换标记之间；重复块、缺结束标记、标记嵌套只报告。低频且需确认，不为此另写脚本。
- **context-handoff 恢复原默认**：交接前全量验证并提交本任务改动；保留「只提交本任务改动、归属不清先问」。
- **claude-to-codex 改名 host-handoff**：两个方向通用；不提交，靠旁置 JSON 的指纹核对兜底。
- **私有 catalog 回到原位置**：撤回 `~/.local/share` 与逐源回退（两个根各放同名源时会静默择一）。
- **spec SKILL.md 收回宿主细节**：少见分支与 trace 备用查找挪进 compatibility 第一节（667→655 行）。
- **evals/ 随 tests/ 同批提交**：`claude plugin eval` 已开放，Claude 侧按原计划补跑。

## 已验证

环境：Codex CLI 0.160.0（模型 `gpt-6.1-sol`）、Claude Code 2.1.289（行为检查用 Sonnet）、
OpenSpec 1.10.0、macOS。以下是复审修订后的结果，首轮迁移时的数字已替换。

确定性检查（每次结果相同）：

| 检查 | 结果 |
|---|---|
| `python3 tests/run_tests.py` | 22 场景，失败 0 |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | 49 测试通过，含护栏模板、技能引用、三段共享文字、文档调用名，以及 Codex 注册名离线测试 |
| `claude plugin validate .`、`bash -n`、`git diff --check` | 通过 |
| D6 脱敏 | 已跟踪文件 0 命中；新增未跟踪的 27 个文件另扫 0 命中 |
| Codex 注册名（隔离 `CODEX_HOME` + `codex debug prompt-input`，不调模型） | plugin 安装为 `valk:valkyrja-*`、`valk-tools:*`；复制安装不带前缀 |

模型行为（是证据，不是保证；次数如实列出）：

| 检查 | 结果 |
|---|---|
| Claude `plugin eval` 冒烟（4 条各 1 次） | 4/4 |
| Claude routing 组（各 3 次，装/不装插件对照） | spec 正例 3/3（不装插件 0/3）；spec 反例 3/3；prd 反例修前 1/3，见下 |
| Claude prd 用例，两轮修复后的最终版本 | 有工作区的正例 6/6；明确要建治理的正例 3/3；未 opt-in 反例 3/3；文档整理反例 3/3（其中 1 次评审误判，见下） |
| Codex prd 用例，最终版本（各 1 次） | 4/4，最终回复人审无越界 |
| Claude constraint 组（3 次，给写权限） | 3/3，均未写 ADEC，评审均判「在等确认」 |
| Codex `run_codex.py`（4 条各 1 次，复制安装） | 4/4；最终回复人审：prd 反例未推销治理，arch 只记「候选」 |
| 护栏块真实冒烟（两宿主，各情形 1 次） | 全部符合预期，见下 |
| host-handoff 反方向（Codex 交出 → Claude 接手） | 状态一致时接续；导出后被改动时 verify=1、停在只读对账，各 1 次 |

**护栏块真实冒烟**（Claude 只加载工作树 `valk`；Codex 用刷新到工作树版本的真实 plugin 安装）：
- 软链 CLAUDE.md → AGENTS.md，两宿主：第一轮只提议，回显解析后的真实路径 AGENTS.md 与块全文，未写；
  确认后写入真实文件，块与模板逐字一致、块外不变、软链仍在、块只有一份、未提交；新会话再体检不写。
- 只有 AGENTS.md，Claude：判定 Claude 读的是 AGENTS.md，提议写入 AGENTS.md 并明确不新建 CLAUDE.md；
  用户的「确认」早于回显时，它先补回显再等确认（多一轮）；确认后写入，CLAUDE.md 仍不存在。
- 旧版块，两宿主：只报告「旧版护栏块」并指出差异，未改文件。
- Codex 运行时，用户自己的 OMX 钩子在临时仓写了 `.gitignore`（`.omx/`），与本技能无关。
- 常驻测试只保证模板与引用一致；真实冒烟只是宿主行为证据。「块已在就不写」是规则，不能证明模型必然遵守。

**prd 准入边界的两轮修复**（真实运行发现，用户逐轮裁决）：
- 第一轮：仓库未 opt-in 时，装了插件的 Claude 不调用技能，却在回复末尾提议「先把需求治理工作区建起来」
  或「把讨论沉淀成需求文档」，违反原设计的「不主动提议初始化」。改动前的旧版对照 3 次也失败 1 次，
  不装插件 3/3 通过——问题原设计就有，此前 Claude 侧从未跑过这条用例。description 改为「不适用时
  不读取、不调用、不接管，也不主动建议建立需求治理工作区或把讨论纳入这套治理流程；普通功能讨论和
  用户要求的文档整理照常处理」，并补两条 prd 正例与一条文档整理反例进 evals/。
- 第二轮：新正例暴露 Codex 迁移引入的退化——已有工作区时 Claude 只有约一半启用 prd（HEAD 旧版 3/3）。
  根因：description 让模型先做「目录存在性检查」，Claude 用只匹配文件的 Glob 查 `initiatives/*`，
  而该目录按协议只有子目录，必然查空，于是误判未 opt-in。改为检查目录下有没有文件
  （如 `docs/product/initiatives/**`），并注明只查目录名会漏判。spec、arch 的工作区根目录下本来就有文件，未改。
- 评审误判一次：文档整理反例有 1 次被 LLM 评审 2:1 判失败；人审该回复完整交付了文档、通篇未提治理，
  结尾只问是否存成文件或先定待确认项，属用例标准允许的情形。如实记录，不收紧技能；用户裁决后为这条
  当天新写的用例补明「提议存成普通文件不算失败」（不涉及原有判据），复跑 3/3。
- 以上是本轮回归通过的行为证据，不是稳定性保证。

真实 CLI 集成在临时含空格路径的消费仓执行 `openspec init --tools codex`，安装本仓技能，
然后运行安装副本中的 trace，未使用 `--skip-cli`；V5 validate/status 均通过。
OpenSpec 配置以临时 `XDG_CONFIG_HOME` 隔离，未修改用户全局 profile。

## 剩余风险

- 行为证据次数少（1～6 次），不是稳定性统计，也不是 Codex 真实产品全生命周期验收。
- prd 准入边界本轮回归通过（见上），但样本小；description 中的检查写法依赖宿主工具语义（Claude 的 Glob 只匹配文件），宿主工具行为变化后要复验。
- 护栏写入只有一次性真实冒烟，没有常驻回归；归档交互未覆盖。
- Claude Code 没有 CLAUDE.md 时读 AGENTS.md，是 2.1.289 上实测的行为；宿主行为变了，写入目标规则要复验。
- 根指令块是 prompt 级提示。直接调用官方技能或 CLI 可绕开壳，强制门禁仍依赖 trace/CI。
- SKILL.md 仍较长（spec 655 行），整体渐进披露改造另做。
- D6 门禁只扫已跟踪文件：提交前先暂存（含 3 个已删的旧模板），再跑门禁。
- CLI 集成需要本机 OpenSpec，未安装时显式跳过。Codex runner 不加载用户 config，
  但可能继承 Codex 自身的用户级技能/指令，不是完全隔离的实验环境。
- runner 的读取证据依赖当前 CLI 的 shell 事件；其他读取工具可能造成假阴性。
  超时保留部分轨迹并结束 CLI，但尚未显式清理子进程组。
