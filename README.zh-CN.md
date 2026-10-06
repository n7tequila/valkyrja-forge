# Valkyrja Forge

[English](README.md) | **简体中文**

把「松散的需求讨论」变成「可追溯的 AI 编码」的一套 Codex / Claude Code 共用技能：
产品契约（PRD）、技术契约（架构）、可验证交付（OpenSpec）三层治理。

核心主张：**AI 全程参与需求整理与代码实现，但每一步都可追溯、可审计，且不被 AI 悄悄篡改语义。**

---

## 为什么需要它

直接让 AI 读一份需求文档然后开始写代码，会遇到三个反复出现的问题：

1. **对话不是记忆。** 会话一断，上一轮讨论出的结论全部消失，下次从头再来。
2. **AI 会静默补全。** 需求里没写清楚的地方，AI 倾向于自行假设一个合理答案继续往下写，
   而不是停下来问——于是产品语义在无人察觉时被改写。
3. **做完了不知道做全没有。** 功能跑通了，但当初那条安全需求、那条性能指标有没有落地，
   没有任何机制能回答。

这套工作流用**文件系统**解决第一个问题，用**特权动作确认**解决第二个，
用**双向追溯链**解决第三个。

---

## 流水线

```
松散讨论（人 + AI 多轮对话）
      │
      │  valkyrja-prd
      ▼
Released PRD  ──────────────────── 产品 API：下游唯一可消费的契约
      │
      │                 技术讨论 ── valkyrja-arch ──→ docs/architecture/
      │                            （ADEC 决策 · 采纳约定 · 共享契约）
      │  valkyrja-spec                     │ design.md 消费（依据: ADEC-*）
      ▼                                    ▼
Requirement Baseline（需求基线：逐条裁决如何落地）
      │
      ▼
Change 划分 ──→ OpenSpec change（proposal / specs / design / tasks）
      │
      │  官方 OpenSpec：apply → verify
      ▼
trace（PRD ↔ spec 追溯校验）→ archive
      │
      ▼
openspec/specs/（系统当前行为的真相源）
```

追溯链是贯穿始终的那根线：

```
RN / DEC  →  PRD 的 REQ/BR/SEC/NFR  →  OpenSpec Requirement 的 Sources:  →  主 spec  →  代码
```

任何一条需求，都能反查「它为什么存在」；任何一条已发布需求，都能正查「它落地了没有」。

---

## 三个技能

| 技能 | 职责 | 状态 |
|---|---|---|
| **valkyrja-prd** | 讨论 / 决策 / 导入 / 合成 / 发布 PRD（WHAT） | 已在真实项目跑通完整流程 |
| **valkyrja-arch** | 技术选型决策（ADEC）/ 采纳约定 / 共享接口契约（HOW 的地基） | 已在真实项目完成首轮 adopt / decide / contract / publish |
| **valkyrja-spec** | 消费 Released PRD 与技术地基，驱动 OpenSpec 开发闭环 | 已在真实项目跑通首次完整闭环（含归档与 V6 首跑） |

### valkyrja-prd

把松散讨论治理为可追溯的产品状态。十个动作：`discuss`、`decide`、`import`、`prototype`、
`bootstrap`、`status`、`synthesize`、`release`、`check`、`view`。
不需要输入动作名，按话语自动路由；`decide` 与 `release` 是特权动作，必须人类显式确认。
`view` 按需生成一份给人看的阅读稿：把 PRD 和它的决策、讨论过程、未定事项合成一个文件，
默认写到 `docs/product/views/<slug>.md`；它只给人看，永远不作为需求依据。

工作区结构：

```
docs/product/initiatives/<slug>/
├── STATUS.md              # 唯一的派生缓存，其余状态一律现算
├── requirements/          # RN-*   规范化需求条目
├── discussions/           # DISC-* 讨论话题，按话题建档、追加式
├── decisions/             # DEC-*  决策，一决策一文件
├── tech-memos/            # TM-*   技术讨论（不产生需求，只被 DEC 引用）
├── prototype/             # 系统原型：original/vN 原件 + vN 背书基线包
├── others/originals/      # 外部原始文件，只读不改
└── prd/
    ├── current.md         # 可反复重新生成的草稿
    └── releases/vX.Y.md   # 发布即冻结，下游唯一可消费的产品 API
```

### valkyrja-arch

技术契约治理层，与 valkyrja-prd 同构（discuss → decide），决策对象是工程技术。
八个动作：`bootstrap`、`discuss`、`decide`、`adopt`、`contract`、`status`、`check`、`publish`——
`bootstrap` 是入口流程：探测既有技术事实、读产品侧约束、在**首次 apply 之前**
驱动奠基性决策（技术栈、仓库布局）。
边界判据是**验收可观察性**：验收可测的属产品侧走 PRD，只约束工程内部的在此裁决为
ADEC。产物落 `docs/architecture/`（决策 / 已采纳约定副本 / 版本化共享契约 /
公共对象清单 / 规则候选 backlog）。

自带**约定目录（catalog）**：`valk/skills/valkyrja-arch/references/conventions/`，
按 concern × stack 两轴组织，条目带出处与许可证四字段；`adopt` 时以自包含副本
落入项目并铸 ADEC 记录偏离。条目以真实项目撞上的缺口驱动，事故背书的规则优先。

### valkyrja-spec

治理编排层——标准的 propose / apply / archive 委托给官方 OpenSpec 技能与 CLI，
本技能只做它们不做也不该做的事。六个动作：

| 动作 | 职责 |
|---|---|
| `baseline` | 解析 release，逐条裁决处置（直通 / 拆分 / 延期 / 非软件 / 外部 / 冲突） |
| `decompose` | 裁决 change 划分，产出交接单 |
| `trace` | PRD ↔ spec 双向追溯校验，**有放行语义**（apply 前与归档前强制） |
| `status` | 现算覆盖分账 |
| `check` | 全工作区契约体检 |
| `rebaseline` | 新 release 的增量基线（digest 比对，五态分类） |

产物落在 `docs/product/baselines/<DOMAIN>-vX.Y.md`。

四个动词（propose / apply / verify / 归档）以**壳**形态编排：门禁在前、确认在中、委托官方 OpenSpec 在后、产后自动检查——说 `next` 即可沿流水线推进一步，
任何特权确认都不被跳过。

> `trace` 与官方 `verify` 是两种不同的一致性：
> `trace` 管「PRD ↔ spec」，官方 `verify` 管「实现代码 ↔ change artifacts」，互补不互替。

---

## 调起入口

Codex 没有命令层，按技能注册名调用（也可由遵守 opt-in 边界的 description 路由自然语言）。
用 plugin 安装时，注册名带 plugin 前缀：

```text
$valk:valkyrja-prd   我们聊聊录像暂停
$valk:valkyrja-arch  看看技术地基
$valk:valkyrja-spec  这个 change 能归档吗
```

用复制式安装脚本时是不带前缀的 `$valkyrja-prd`、`$valkyrja-arch`、`$valkyrja-spec`。
实际注册了什么以 `/skills` 列出的为准。协议与确认门禁和 Claude Code 完全相同。

三个入口，用命名空间做内聚：

```
/valk:prd    <想做什么，自然语言即可>
/valk:arch   <想做什么，自然语言即可>
/valk:spec   <想做什么，自然语言即可>
```

它们刻意保持很薄——纯委托、自身不含任何路由逻辑，
好让各 `SKILL.md` 里的意图路由表始终是唯一的路由权威。例如：

```
/valk:prd   我们聊聊录像暂停
   → 路由到 discuss

/valk:prd   这个就这么定了
   → 路由到 decide（特权，需确认）

/valk:spec  这个 change 能归档吗
   → 路由到 trace
```

> `/valk:*` 短入口仍是 Claude Code 专属。Codex 读取同一份 `SKILL.md`、引用、模板
> 与 trace 脚本，不复制第二棵技能源码。首次落盘治理文件后，技能会为当前宿主
> 实际会读的指令文件提议写入治理块：Codex 是 `AGENTS.md`；Claude Code 有 `CLAUDE.md`
> 就写它，没有但有 `AGENTS.md` 就写 `AGENTS.md`（这时 Claude Code 读的就是它，不新建
> `CLAUDE.md`），两个都没有才新建 `CLAUDE.md`。你确认后才写；块正文两个宿主相同，
> 块外的原有内容一字不动。权威规则在护栏模板里。

---

## 安装

### Codex

本地开发先显式注册 checkout，再安装所需 plugin：

```bash
codex plugin marketplace add /absolute/path/to/valkyrja-forge
codex plugin add valk@valkyrja-forge
codex plugin add valk-tools@valkyrja-forge  # 可选，独立工具箱
```

marketplace 仍与 Claude Code 共用；两个 plugin 各有 portable 根 `plugin.json`。
本地 marketplace 安装是 CLI 路径，不等于发布到公共目录。安装或升级后开新会话。

离线或只想装到**消费产品仓**时：

```bash
scripts/install-skills.sh --harness codex --project /path/to/your-product-repo
scripts/install-skills.sh --harness codex --plugin valk-tools --system
```

Codex 复制式安装落 `<项目>/.agents/skills/` 或 `~/.agents/skills/`，不写命令文件。
同一宿主请选择 plugin 或复制式安装之一，避免双注册悄悄读到旧版。既有 Claude
安装保持原样；不搬迁私有 catalog 或项目文档。

### Claude Code plugin

本仓即 plugin marketplace（`.claude-plugin/`）。在 Claude Code 里：

```
/plugin marketplace add n7tequila/valkyrja-forge
/plugin install valk
```

版本、升级（`/plugin marketplace update`）、启停与卸载由官方 plugin 机制
原生提供。plugin 形态下技能名带命名空间（如 `valk:valkyrja-spec`），
斜杠命令为 `/valk:prd|arch|spec`。

#### 第二个 plugin：`valk-tools`

本 marketplace 托管**两个互相独立的 plugin**。`valk-tools` 是个人工作方式工具箱——
上下文交接、Claude ↔ Codex 工作交接、跨 forge 开 PR、只审不改的重构审查——跟人走，不跟项目走：

```
/plugin install valk-tools
```

它有自己的版本，独立安装、升级与卸载；与 `valk` 只共享本仓的 git 历史，
不共享发版节奏，两者互无依赖。它**只带技能、不设命令层**——直接以
`/valk-tools:context-handoff`、`/valk-tools:host-handoff`、`/valk-tools:merge-pr`、`/valk-tools:refactor-review` 调起。
详见 [valk-tools/README.md](valk-tools/README.md)。

兜底脚本可安装两个 plugin，用 `--plugin valk-tools` 选工具箱；默认仍是 Claude Code
的 `valk`，保持原有用法兼容。

### 兜底路径：复制式安装脚本（离线 / 无 git 场景）

技能安装到**目标产品仓库**，本仓库只是技能源码仓。下列示例默认
**cwd 在 forge 仓根**——省略 `--project` 的目录参数会装进 forge 仓自身，装目标仓请用
`--project <目标仓路径>`，或先 `cd` 到目标仓再以绝对路径调本脚本：

```bash
# 装到指定产品仓（推荐写法）
scripts/install-skills.sh --project /path/to/your-product-repo

# 或：先进目标仓，再调 forge 仓里的脚本
cd /path/to/your-product-repo && /path/to/valkyrja-forge/scripts/install-skills.sh --project

# 装到本机全局（~/.claude/，对所有项目生效）
scripts/install-skills.sh --system

# 覆盖升级（自动备份旧版本；--no-backup 跳过备份）
scripts/install-skills.sh --system --force

# 只装指定技能（此模式下不装斜杠命令，
# 避免命令指向一个并未安装的技能）
scripts/install-skills.sh --project /path/to/your-product-repo valkyrja-prd

# 预览与查看
scripts/install-skills.sh --system --dry-run
scripts/install-skills.sh --system --list
```

以上命令加 `--harness codex` 即切换宿主。Codex 技能备份在
`.agents/.valkyrja-backup/skills/`，不进入技能发现树。

安装前会校验每个技能：`SKILL.md` 必须存在，且 frontmatter 含 `name` 与 `description`。
不合格的跳过并报错，不影响其余技能。脚本不提供版本追踪与卸载——那些是
plugin 主路径的职责，兜底脚本不再补造。

### 前置条件

bash（安装脚本）、python3 ≥ 3.7（trace.py 门禁）、OpenSpec CLI（见下）。
安装脚本与工作流目前只在 macOS/Linux 上验证过；Windows 用户建议走 plugin 主路径。

### 依赖

`valkyrja-prd` 无外部依赖。

`valkyrja-spec` 需要 [OpenSpec](https://github.com/Fission-AI/OpenSpec) CLI ≥ 1.9.0：

```bash
npm install -g @fission-ai/openspec
openspec init --tools claude    # 在目标产品仓库内执行
# Codex 改用：
openspec init --tools codex
```

`openspec init` 按当前 profile 生成官方 workflow 技能。官方 `core` profile **不含
`verify`**；完整闭环请用 `openspec config profile` 选择包含 propose、apply、verify、
sync、archive 的自定义工作流集合，再在产品仓运行 `openspec update`。这是用户显式
配置选择，技能不静默修改全局 profile。宿主路径与调用映射见
[OpenSpec 兼容说明](valk/skills/valkyrja-spec/references/openspec-compatibility.md)。

---

## 设计原则

贯穿三个技能，也是理解全部设计取舍的钥匙：

1. **文件系统是记忆，对话不是。** 任何未落盘的结论，下个会话视为不存在。
2. **人保留决策权，AI 只做提取和建议。** 产品决策与发布是特权动作，必须显式确认；
   语气含疑问即视为倾向，不算决策。
3. **能推导的数据不存。** 哈希、统计、覆盖率、状态一律现算，避免记录漂移。
   唯一豁免是 `STATUS.md`，且它只存最小状态、不存任何统计字段。
4. **ID 一旦铸造永不重编号。** 结构为 `TYPE-DOMAIN-NUMBER`；DOMAIN 是永久命名空间，
   一经使用即冻结、跨项目全局唯一、禁止版本型命名。
5. **WHAT 和 HOW 分离。** 需求文档只描述可观察行为；实现方案属于下游 design 层。
   技术名词不得出现在验收场景里——否则任何重构都会破坏 spec。
6. **格式契约先于工具。** 机器要解析的格式先手工验证，再写工具去解析它，
   而不是反过来为不存在的文档设计 parser。

---

## 仓库结构

```
valkyrja-forge/
├── README.md / README.zh-CN.md / NOTICE.md（指针；权威声明随 catalog 分发）
├── AGENTS.md                      # Codex 入口，指向共用仓库编辑规则
├── CLAUDE.md                      # 编辑规则唯一权威（不是消费仓治理块）
├── .claude-plugin/marketplace.json # 共用 marketplace；Codex CLI 显式注册
├── docs/design/                   # 三技能设计定稿与演进记录（含 D 系列裁决台账）
├── scripts/install-skills.sh      # 兜底安装脚本（离线/无 git；主路径是 plugin）
├── scripts/check-sanitization.sh # D6 脱敏机检门禁（词表私有，建议接 pre-push/CI）
├── tests/                         # trace、安装与打包回归（不分发）
├── evals/                         # 模型行为检查（不分发）
├── valk/
│   ├── plugin.json / .claude-plugin/plugin.json # portable / Claude 清单
│   ├── commands/                 # Claude 专属短入口
│   └── skills/
│       ├── valkyrja-prd/          # SKILL.md + templates/
│       ├── valkyrja-arch/         # SKILL.md + templates/ + 约定目录
│       └── valkyrja-spec/         # SKILL.md + templates/ + references/ + tools/trace.py
└── valk-tools/                    # 独立清单 + 四个个人工作方式技能
```

---

## 现状与下一步

- `valkyrja-prd` 已用真实项目验证，产出的 PRD 质量可直接进入下游开发。
- `valkyrja-spec` 的协议已经过多轮评审与修订，格式契约均已对 OpenSpec 实测验证
  （验证区间 [1.9, 1.10]：`Sources:` 行不触发 validate、能随合并进入主 spec、
  可机读提取、嵌套 capability 归档保持完整路径）。
  **整条流水线已在真实项目完成首次端到端运行（含归档、V6 八块分账首跑与全量复审修复）。**

后续计划：

- [x] 用真实 PRD 跑通首次端到端：baseline → decompose → propose → trace → apply → verify → trace → archive（2026-08-21 归档收官）
- [ ] `SKILL.md` 拆分 reference 文件（progressive disclosure）
- [ ] 把纯确定性检查（追溯校验、集合对账）下沉为脚本与 CI
- [ ] CI 禁止修改已发布的 `prd/releases/**`
- [x] Plugin 化（`.claude-plugin/`，v0.9.0）：版本/升级/卸载走官方机制，install.sh 降为兜底
- [x] Codex 适配：共用技能、两宿主通用的一份治理块、按宿主区分的 OpenSpec 调用、portable 清单、已测复制安装器；行为检查用 `claude plugin eval` 与 `evals/run_codex.py`。行为运行只是证据，不等于 Codex 产品生命周期全链路验收。

本次证据与剩余缺口见 [Codex 迁移评估](docs/design/codex-migration.md)。

---

## 许可证

MIT
