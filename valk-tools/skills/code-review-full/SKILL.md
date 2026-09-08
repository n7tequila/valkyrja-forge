---
name: code-review-full
description: 全面多智能体代码审查——把「后端 code-review、前端 code-review、Java DDD review、安全 review」四个维度并行分派给专业 agent（后端架构师 / 前端开发者 / 软件架构师 / 安全工程师），各自复用对应的现有审查 skill 与规则，最后按严重级别去重汇总并给出裁决。当用户要在提交或合并前对一处改动（工作区改动 / 分支 / PR）做彻底 review 时使用。触发词："全面 review"、"code-review-full"、"彻底审查这次改动"、"多维度代码审查"。
---

# code-review-full — 多智能体全面代码审查

把一次改动沿 **4 个维度并行**分派给专业 agent，每个 agent 复用对应的**现有审查 skill / 规则**，最后主循环汇总为一份按严重级别排序的报告 + 裁决。

- **只读**：所有 agent 只审查、不改代码；产出是报告。要修复，由用户另行发起。
- **并行**：4 个 agent 在**一条消息**里同时派发（彼此独立），汇总由主循环完成、不再派 agent。
- **报告面向用户**：只呈现结论，不堆砌各 agent 的原始输出。

## 维度 → agent → 复用的审查规则

| 维度 | agent（`subagent_type`） | 复用规则（现有 skill / rules） |
|------|--------------------------|--------------------------------|
| 后端 code review | `后端架构师` | `~/.claude/rules/common/code-review.md`（严重度模型 + 清单）+ `~/.claude/commands/code-review.md`（更细清单，可读）+ 项目 `backend/CLAUDE.md`、`backend/docs/*` + `~/.claude/rules/java/*` |
| 前端 code review | `前端开发者` | 同上 code-review 清单 + 项目 `frontend/CLAUDE.md`、`frontend/docs/*` + `~/.claude/rules/web/*`、`~/.claude/rules/typescript/*` |
| Java DDD review | `软件架构师` | **`java-domain-driven-design` skill 的 Code Review Mode**（`references/ddd-code-review.md`：code smell 目录 + 严重度模型 + 输出模板）+ 项目 `backend/docs/ddd-architecture-rules.md` |
| 安全 review | `安全工程师` | **`security-review` skill** + `~/.claude/rules/*/security.md`（OWASP Top 10、鉴权授权、注入、密钥、SSRF、路径穿越、XSS、输入校验）|

> 4 个 agent 均为「All tools」，可调用 Skill / Read / Grep / Bash。DDD 与安全维度**先用 Skill 工具调用对应 skill**再审查；若某 skill 不可用，退回 `~/.claude/rules/` 对应规则。

## 步骤

### 1. 确定审查范围 + 取 diff
按参数（可选）决定：
- **PR**（`#N` / URL / `--pr N`）：`gh pr diff <N> --name-only`；文件按 head revision 取全文。
- **base 分支**（如 `main`）：`git diff <base>...HEAD --name-only`。
- **无参数**：工作区改动 `git diff --name-only HEAD` + 未跟踪文件；若工作区干净，退化审查最近一次提交（`git show --stat HEAD` / `git diff HEAD~1...HEAD`）。
- 无可审内容 → 停止并告知「没有可审查的改动」。

公布审查范围 + 取 diff 的命令（后续原样传给各 agent）。

### 2. 归类改动文件
- **后端 Java**：`backend/**` 下 `*.java` / `pom.xml` / `*.sql` / `application*.yml`。
- **前端**：`frontend/**` 下 `*.vue` / `*.ts` / `*.tsx` / `*.css` / `package.json` / `vite.config.*`。
- **安全**维度覆盖**全部**改动文件；**DDD** 维度覆盖后端 Java。
- 某维度无相关改动 → 跳过该 agent，在报告里注明「本次无 X 改动」。

### 3. 并行分派 4 个维度审查（**一条消息里 4 个 Agent 调用**）
每个 agent 的 prompt 都包含：① 审查范围（该维度相关的改动文件清单 + 取 diff 的命令）；② 要求**逐个读改动文件全文**（不能只看 diff hunk）；③ 复用对应审查规则（见上表）；④ 把发现按结构化列表返回：**严重级别 / `file:line` / 问题一句话 / 具体触发场景（输入→错误结果）/ 修复建议**；⑤ **自我核验每条发现**（能给出具体失败场景才保留，剔除误报），按严重级别排序返回。

- **`后端架构师`** — 后端 code review（范围 = 后端文件）：正确性、并发与事务边界、JPA/查询、异常处理与错误传播、REST 契约、性能（N+1/无界查询）、测试覆盖；套用 `~/.claude/rules/common/code-review.md` 清单 + 项目后端规范（`backend/CLAUDE.md`、`backend/docs/api-code-standard.md`）。
- **`前端开发者`** — 前端 code review（范围 = 前端文件）：正确性、TypeScript 类型安全、Vue 3 / Element Plus 惯例、状态管理、可访问性（a11y）、性能、组件测试；套用同一 code-review 清单 + 项目前端规范（`frontend/CLAUDE.md`、`frontend/docs/coding-conventions.md`）。
- **`软件架构师`** — Java DDD review（范围 = 后端 Java）：**先用 Skill 工具调用 `java-domain-driven-design` 进入 Code Review Mode**，按 `references/ddd-code-review.md` 的分层依赖方向、聚合根不变式、限界上下文边界、端口/适配器、贫血模型等 code smell 目录 + 严重度模型审查；叠加项目 `backend/docs/ddd-architecture-rules.md` 的强制规则（如 domain 零框架依赖、application 禁 import infrastructure、跨模块仅经 facade）。
- **`安全工程师`** — 安全 review（范围 = 全部改动）：**先用 Skill 工具调用 `security-review`**，按其清单 + `~/.claude/rules/*/security.md` 审查 OWASP Top 10、鉴权/授权、注入、密钥泄露、SSRF、路径穿越、XSS、输入校验、错误信息泄露。

### 4. 汇总（主循环执行，不再派 agent）
- 合并 4 个 agent 的发现；按 `file:line` **去重**：多维度命中同一处 → 保留**最高**严重级别，注明命中的维度（如「[后端 + 安全]」）。
- 按严重级别分组：**CRITICAL / HIGH / MEDIUM / LOW**；组内按维度排列。

### 5. 裁决 + 输出
裁决规则：有 **CRITICAL → BLOCK**；有 **HIGH → REQUEST CHANGES**；仅 MEDIUM/LOW → **APPROVE（附意见）**；无发现 → **APPROVE**。

输出（**中文，技术术语保留 English**）：

```
# 全面代码审查 — <范围（PR#N / <base>...HEAD / 工作区改动）>

## 裁决：<BLOCK | REQUEST CHANGES | APPROVE（附意见）| APPROVE>

## 概览
| 维度 | agent | CRITICAL | HIGH | MEDIUM | LOW |
|------|-------|:--------:|:----:|:------:|:---:|
| 后端 code review | 后端架构师 | … | … | … | … |
| 前端 code review | 前端开发者 | … | … | … | … |
| Java DDD | 软件架构师 | … | … | … | … |
| 安全 | 安全工程师 | … | … | … | … |

## 发现（按严重级别）
### CRITICAL
- [维度] `file:line` — 问题 → 修复建议（触发场景：…）
### HIGH
…
### MEDIUM
…
### LOW
…

## 跳过 / 无改动的维度
- <如「本次无前端改动，跳过前端 code review」>
```

## 约束
- 审查**只读**，agent 不改代码。
- 4 个 agent **并行**（一条消息 4 个 Agent 调用），互不依赖；某维度无相关改动则不派该 agent。
- 若改动很大（如 >50 文件），提示范围较大，各 agent 优先审源码改动，再看测试 / 配置 / 文档。
- 无 `gh` CLI 时，PR 模式退回本地 diff 并告知用户。
