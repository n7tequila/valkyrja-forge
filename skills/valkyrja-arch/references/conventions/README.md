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
4. **发布门禁**：条目推公开仓前经人工检查（特权握手），检查单——
   ①业务细节已剥离（无客户名/领域错误码/内部路径）；②四字段齐全且
   `redistributable`；③摘编条目原始版权声明未丢。

## 内容风格

- 以**选择 + 绑定 + 增量**为主：「采纳 X，额外规定 Y，不采纳 Z 因为…」，
  不整段重抄公开资料——两份副本必然漂移。
- 源自真实项目的条目**去业务化**：模式出仓、领域不出仓；带强业务指纹的
  模式宁可降级 `local-only` 也不硬泛化。
- 每条硬规则尽量附**为什么**（最好是真实事故/回归），这是与教科书条款的
  根本区别，也是对 AI 最有效的护栏形态。
- stub 条目正文只有三行：这是什么 / 全文在哪 / 为何未收全文。
