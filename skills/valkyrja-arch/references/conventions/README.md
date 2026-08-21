# 约定目录（catalog）

> 本目录是**素材库**，不是任何项目的规范（宪法 8）。条目经 `adopt` 落入项目
> `docs/architecture/conventions/` 的自包含副本才是项目规范，本地副本优先。
> 本文件是条目格式与收录纪律的权威定义。

## 两轴组织

- **concern**：架构风格 / 接口契约 / 数据 / 前端 / 横切
- **stack**：`common`（通用）/ `postgres` / `web-vanilla` / `java-spring` /
  `typescript-vue` / `typescript-react` / `typescript-node` / …（按需增）

文件命名：`conv-<主题>[-<stack>].md`，通用条目省略 stack 段
（如 `conv-idempotency.md`、`conv-db-relational-postgres.md`）。

**多源**：本目录是**内置源**。私有源放 `~/.claude/valkyrja/catalog/<源名>/`
（每个子目录一个源，条目格式同构；私有 catalog 仓 clone/软链到此，
不受 skill 升级覆盖）。私有源是 `local-only` 条目全文的家——公开仓只放 stub，
全文在私有源，许可允许时可 adopt 入私有项目仓（`license-unknown` 仍不得
adopt 入任何仓）。私有源副本的指纹带源标识：
`adopted-from: <条目id>@<版本> (source: <源名>)`；无 source 段即内置源。

**分层条目**：框架级通用条目与具体库的绑定增量分开成两条
（如 `conv-ts-vue` 通用层 + `conv-ts-vue-element` 的 Element Plus 增量）。
绑定条目 frontmatter 以 `requires: <基础条目 id>` 声明依赖，
**采纳绑定条目前须先采纳其基础层**；不用该库的项目只采通用层，
不必带着删改负担采一条混合条目。

## 条目 frontmatter（缺一不得入库）

```yaml
---
id: conv-<主题>[-<stack>]
concern: <五选一>
stack: <见上>
version: <YYYY-MM-DD>        # 日期即版本；每次实质修订更新
source: <URL / 项目名 / "自撰">
license: <MIT | Apache-2.0 | 自有 | 未知 | ...>
modified: <否 | 摘编 | 改写 | 提炼泛化>
status: <redistributable | local-only | license-unknown>
---
```

## 收录纪律（D6 四条）

1. **出处四字段在收集时标注**，不做事后追溯考古。
2. **`license: 未知` ⇒ `status: license-unknown`，公开仓只放 stub**
   （标题 + 出处链接 + 一句"许可证待确认"），且**不得被 adopt 入任何项目仓**。
3. 第三方摘编（如 MIT 来源）：frontmatter 记全出处 + 仓库根 `NOTICE.md`
   集中保留原始版权声明。
4. **发布门禁**：条目推公开仓前经人工检查（特权确认），检查单——
   ①业务细节已剥离（无客户名/**内部项目名**/领域错误码/内部路径；
   自有来源统一以「内部项目」指代，不因项目属自有而豁免）；②四字段齐全且
   `redistributable`；③摘编条目原始版权声明未丢。

## 待编条目（等真实缺口驱动，勿提前写）

- `conv-checker-self-verification` —— **机制自身的失效是静默的**。
  本项目已重复撞上五次：config.yaml 解析失败被静默忽略、shell 未分词导致检查空跑、
  JSON 结构误解析产生假 ERROR、正则跨行匹配产生假 WARNING、
  「零发现」与「零对象」输出不可区分。
  候选规则：检查器必须同时报告**扫描对象数**与发现数；空集合的通过要显式说明；
  配置注入后必须正向实跑验证；解析外部工具输出前先断言结构假设。
  **触发条件**：下一个真实项目再次撞上此类问题时 graduate。

## 内容风格

- 以**选择 + 绑定 + 增量**为主：「采纳 X，额外规定 Y，不采纳 Z 因为…」，
  不整段重抄公开资料——两份副本必然漂移。
- 源自真实项目的条目**去业务化**：模式出仓、领域不出仓；带强业务指纹的
  模式宁可降级 `local-only` 也不硬泛化。
- 每条硬规则尽量附**为什么**（最好是真实事故/回归），这是与教科书条款的
  根本区别，也是对 AI 最有效的护栏形态。
- stub 条目正文只有三行：这是什么 / 全文在哪 / 为何未收全文。
