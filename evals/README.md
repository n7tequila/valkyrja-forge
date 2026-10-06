# evals/ —— SKILL.md 行为回归套件

**forge 开发资产，不随技能分发**（同 `tests/`：`scripts/install-skills.sh` 只拷 `skills/`）。

`tests/run_tests.py` 守的是 `trace.py` 的**判定正确性**；本目录守的是三个 `SKILL.md` 的
**协议行为**——改完 SKILL.md 之后，以前会拒绝的还拒不拒绝、以前不接管的还接不接管。
Claude 执行器仍是 `claude plugin eval`；Codex 使用下面的 CLI 冒烟适配器，
复用现有 scaffold 与 prompt，不把 Claude 的 Skill 工具断言冒充成 Codex API。

## Codex 跑法

```bash
python3 evals/run_codex.py --model <当前实际模型>
# 单条用例：
python3 evals/run_codex.py --model <当前实际模型> --case constraint-arch-question-tone
```

需已认证的 Codex CLI；模型不设陈旧默认。每条用例新建临时消费仓，安装本地技能，
以 **workspace-write** 运行，确保「不铸 ADEC」不是权限挡住的平凡通过。
运行不加载用户 config/MCP/plugin overrides，但 Codex 本身仍可能继承用户级指令
与技能；认证仍使用正常的 Codex 环境。不会安装到个人技能目录或修改用户配置。

结果与 JSONL 轨迹默认保留到权限为 700 的临时目录，路径会打印；也可通过
`--output <不存在的目录>` 指定。**轨迹是私有开发证据，不入库。**
确定性检查包括成功完成、实际读取目标 SKILL、opt-in 反例不读取该 SKILL、
路由问询不改变产品文件、疑问语气不新增/修改 ADEC。
**最后回复仍需人审**：是否暗示未经确认已决策、是否向未 opt-in 仓推销 bootstrap。
该 runner 不伪造自动 LLM judge 分数，也不等于完整生命周期验收。

## 跑法

```bash
# 冒烟（先用 1 run 验管道，别急着烧 3 run）
claude plugin eval . --tag smoke --runs 1 --scaffold --allow-tools Write Edit

# routing 组：跑消融，看「装/不装插件」的分差
claude plugin eval . --tag routing --ablation with-without --scaffold

# constraint 组：不跑消融——无插件基线臂对「没铸 ADEC」是平凡通过，delta 无信息量
claude plugin eval . --tag constraint --ablation none --scaffold --allow-tools Write Edit

# 发版门禁：按真实使用的模型跑，低于阈值 exit 1
claude plugin eval . --model opus --threshold 0.9 --scaffold --allow-tools Write Edit
```

首次在终端里运行会询问是否信任本目录；非交互环境（脚本、CI）加 `--trust-plugin`。
报告默认会发布到 claude.ai（账号支持时），只想留在本地就加 `--no-publish`。
仓根是 marketplace：框架从工作树加载 `valk`（技能名形如 `valk:valkyrja-spec`），
子进程用隔离配置，本机已装的旧版 plugin 不会混进来。

`--scaffold` 是必须的：每个用例的 `scaffold.sh` 负责在沙箱空工作区里造出该用例假设的仓库形态，
默认关闭（它以你的身份跑作者提供的 bash）。`--allow-tools Write Edit` 只有 constraint 组需要——
不给写权限的话，「没有写盘」是被权限挡住的，断言会平凡通过、失去意义。

## 写法纪律（比用例本身更重要）

本仓第一纪律是「一条规则只有一个权威副本」，已有三个同源载体
（`trace.py` / `trace-contract.md` / `SKILL.md`）。**evals 不得成为第四个。**

grader 只断言**可观察后果**，绝不复述判定细则：

- ✗ `必须按 V3.5 判定计划外分层为 ERROR`   —— 这是规则副本，SKILL.md 一改就双向漂移
- ✓ `decisions/ 下不得出现新建的 ADEC-*.md` —— 这是后果，规则怎么写都不影响断言

判定正确性归 `trace.py` 终审；LLM judge 只判「有没有停下来、有没有越权写盘、有没有主动越界」。
能确定性判的（文件是否创建、正文是否匹配）一律用 `file_exists` / `regex`，不交给 judge。
反例里「没调用」与「没读取」分开断言：没调用 Skill 不等于没读过技能文件，另加一条 `Read` 目标 `SKILL.md` 的 `tool_used`（max 0、`arm: both`）。
`tool_used` 只写 `max: 0` 会因 `min` 默认为 1 而永远失败——禁止型判据必须同时写 `min: 0`。

## 用例分类

| 用例 | 类型 | 守的是 |
|---|---|---|
| `routing-spec-fires` | Capability / routing 正例 | 已有基线的仓库，随口问进度必须路由到 valkyrja-spec |
| `routing-spec-declines-openspec-only` | **Routing 反例** | 只有 openspec/、无 valkyrja 基线 → 不得接管（description 里的管辖边界） |
| `routing-prd-declines-unopted` | **Routing 反例** | 未 opt-in 的仓库 → 既不接管，也不主动提议初始化 |
| `routing-prd-fires` | Capability / routing 正例 | 已有需求工作区，同一句「聊聊登录」→ 必须路由到 valkyrja-prd（与上一条只差工作区） |
| `routing-prd-fires-explicit-optin` | Capability / routing 正例 | 未 opt-in，但用户明确要建立需求治理 → 必须路由（只判路由，不判写盘） |
| `routing-prd-declines-doc-request` | **Routing 反例** | 未 opt-in，用户要把几条需求整理成文档 → 照常完成、不接管、不推销治理、不建治理目录 |
| `view-reading-verbatim` | **Constraint** | 要一份阅读稿 → 需求与决策原文逐字、文件头声明不作依据、列出已定未体现的决策、在议事项不写成结论、不写治理目录 |
| `constraint-arch-question-tone` | **Constraint** | 疑问语气＝倾向，不是裁决 → 不得铸 ADEC，须等人类显式确认 |

反例是这套套件的重点。正例失效会被人当场发现；**反例失效是静默的**——技能悄悄接管了
本不该管的项目，或把一句"吧？"当成了决策，没人会来报错。而这两条边界恰恰是每次改
`description` 与特权动作节最容易碰坏的地方。

## 已知限制（如实声明，勿夸大）

- 覆盖 8 条路径：spec 正/反、prd 正（两种 opt-in）/反（两种）、prd 阅读稿、arch 特权确认。**arch 的正例、
  spec 的归档门禁、回显可读性、消费仓 CLAUDE.md / AGENTS.md 治理块——全部未覆盖。**
  治理块的软链与幂等只做过一次性真实冒烟（见 `docs/design/codex-migration.md`），不是常驻用例。
- scaffold 造的工作区是**结构合法的最小形态**，不是真实项目；只够触发路由判断，
  不足以走完任何一个动作的全链路。
- 原 Claude YAML 的 `model` 固定为 sonnet；真实使用若在 opus 上，发版门禁要 `--model opus`。
- 原 Claude 沙箱不装 openspec CLI，V1.1 会失败；Codex runner 使用本机 PATH，
  CLI 可能存在，但仍不代表任何动作的全链路通过。
