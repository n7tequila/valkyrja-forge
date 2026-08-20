# Valkyrja Forge

[English](README.md) | **简体中文**

把「松散的需求讨论」变成「可追溯的 AI 编码」的一套 Claude Code 技能。

核心主张：**AI 全程参与需求整理与代码实现，但每一步都可追溯、可审计，且不被 AI 悄悄篡改语义。**

---

## 为什么需要它

直接让 AI 读一份需求文档然后开始写代码，会遇到三个反复出现的问题：

1. **对话不是记忆。** 会话一断，上一轮讨论出的结论全部消失，下次从头再来。
2. **AI 会静默补全。** 需求里没写清楚的地方，AI 倾向于自行假设一个合理答案继续往下写，
   而不是停下来问——于是产品语义在无人察觉时被改写。
3. **做完了不知道做全没有。** 功能跑通了，但当初那条安全需求、那条性能指标有没有落地，
   没有任何机制能回答。

这套工作流用**文件系统**解决第一个问题，用**特权动作握手**解决第二个，
用**双向追溯链**解决第三个。

---

## 流水线

```
松散讨论（人 + AI 多轮对话）
      │
      │  prd-workshop
      ▼
Released PRD  ──────────────────── 产品 API：下游唯一可消费的契约
      │
      │  openspec-development
      ▼
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

## 两个技能

| 技能 | 职责 | 状态 |
|---|---|---|
| **prd-workshop** | 讨论 / 决策 / 导入 / 合成 / 发布 PRD | 已在真实项目跑通完整流程 |
| **openspec-development** | 消费 Released PRD，驱动 OpenSpec 开发闭环 | Release Candidate，**尚未端到端验证** |

### prd-workshop

把松散讨论治理为可追溯的产品状态。八个动作：`discuss`、`decide`、`import`、
`bootstrap`、`status`、`synthesize`、`release`、`check`。
不需要输入动作名，按话语自动路由；`decide` 与 `release` 是特权动作，必须人类显式确认。

工作区结构：

```
docs/product/initiatives/<slug>/
├── STATUS.md              # 唯一的派生缓存，其余状态一律现算
├── requirements/          # RN-*   规范化需求条目
├── discussions/           # DISC-* 讨论话题，按话题建档、追加式
├── decisions/             # DEC-*  决策，一决策一文件
├── tech-memos/            # TM-*   技术讨论（不产生需求，只被 DEC 引用）
├── others/originals/      # 外部原始文件，只读不改
└── prd/
    ├── current.md         # 可反复重新生成的草稿
    └── releases/vX.Y.md   # 发布即冻结，下游唯一可消费的产品 API
```

### openspec-development

治理编排层——标准的 propose / apply / archive 委托给官方 OpenSpec 技能与 CLI，
本技能只做它们不做也不该做的事。六个动作：

| 动作 | 职责 |
|---|---|
| `baseline` | 解析 release，逐条裁决处置（直通 / 拆分 / 延期 / 非软件 / 冲突） |
| `decompose` | 裁决 change 划分，产出交接单 |
| `trace` | PRD ↔ spec 双向追溯校验，**有放行语义**（apply 前与归档前强制） |
| `status` | 现算覆盖分账 |
| `check` | 全工作区契约体检 |
| `rebaseline` | 新 release 的增量基线（digest 比对，五态分类） |

产物落在 `docs/product/baselines/<DOMAIN>-vX.Y.md`。

> `trace` 与官方 `verify` 是两种不同的一致性：
> `trace` 管「PRD ↔ spec」，官方 `verify` 管「实现代码 ↔ change artifacts」，互补不互替。

---

## 斜杠命令

两个入口，用命名空间做内聚：

```
/valkyrja:prd    <想做什么，自然语言即可>
/valkyrja:spec   <想做什么，自然语言即可>
```

它们刻意保持很薄——纯委托、自身不含任何路由逻辑，
好让各 `SKILL.md` 里的意图路由表始终是唯一的路由权威。例如：

```
/valkyrja:prd   我们聊聊录像暂停
   → 路由到 discuss

/valkyrja:prd   这个就这么定了
   → 路由到 decide（特权，需握手确认）

/valkyrja:spec  这个 change 能归档吗
   → 路由到 trace
```

> **斜杠命令是 Claude Code 专属的**，属于手感增强，不是运行机制。
> 两个技能本来就按自然语言自动路由，所以在其他 harness 上完全可以不要命令，
> 把 `skills/` 下的目录放到该工具约定的位置即可，功能不打折——
> 你只是从 `/valkyrja:spec 建立基线` 变成直接说「建立基线」。
> `SKILL.md` 本身是纯 Markdown + YAML frontmatter，已有多个 harness 在消费这个格式。

---

## 安装

技能安装到**目标产品仓库**，本仓库只是技能源码仓。

```bash
# 装到当前项目（.claude/，随仓库共享）
scripts/install-skills.sh --project

# 装到本机全局（~/.claude/，对所有项目生效）
scripts/install-skills.sh --system

# 覆盖升级（自动备份旧版本到 .backup/）
scripts/install-skills.sh --project --force

# 只装指定技能（此模式下不装斜杠命令，
# 避免命令指向一个并未安装的技能）
scripts/install-skills.sh --project prd-workshop

# 预览与查看
scripts/install-skills.sh --project --dry-run
scripts/install-skills.sh --project --list
```

安装前会校验每个技能：`SKILL.md` 必须存在，且 frontmatter 含 `name` 与 `description`。
不合格的跳过并报错，不影响其余技能。

### 依赖

`prd-workshop` 无外部依赖。

`openspec-development` 需要 [OpenSpec](https://github.com/Fission-AI/OpenSpec) CLI ≥ 1.9.0：

```bash
npm install -g @fission-ai/openspec
openspec init --tools claude    # 在目标产品仓库内执行
```

`openspec init` 会按当前 profile 生成官方 workflow 技能。注意官方 `core` profile
**不含 `verify`**，而完整闭环需要它——技能的前提检测会提示这一点。

---

## 设计原则

贯穿两个技能，也是理解全部设计取舍的钥匙：

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
├── README.md / README.zh-CN.md
├── commands/
│   └── valkyrja/                  # 斜杠命令命名空间 → /valkyrja:*
│       ├── prd.md
│       └── spec.md
├── scripts/
│   └── install-skills.sh          # 同时安装技能与命令
└── skills/
    ├── prd-workshop/
    │   ├── SKILL.md
    │   └── templates/             # decision / discussion / prd / status
    └── openspec-development/
        ├── SKILL.md
        └── templates/             # baseline / spec-delta / config-injection
```

---

## 现状与下一步

- `prd-workshop` 已用真实项目验证，产出的 PRD 质量可直接进入下游开发。
- `openspec-development` 的协议已经过多轮评审与修订，格式契约均已对 OpenSpec v1.9.0
  实测验证（`Sources:` 行不触发 validate、能随合并进入主 spec、可机读提取）。
  **但整条流水线尚未做过一次真实的端到端运行。**

后续计划：

- [ ] 用真实 PRD 跑通首次端到端：baseline → decompose → propose → trace → apply → verify → trace → archive
- [ ] `SKILL.md` 拆分 reference 文件（progressive disclosure）
- [ ] 把纯确定性检查（追溯校验、集合对账）下沉为脚本与 CI
- [ ] CI 禁止修改已发布的 `prd/releases/**`
- [ ] 以 `skills/` 为唯一真相源，生成多 harness 适配目录

---

## 许可证

MIT
