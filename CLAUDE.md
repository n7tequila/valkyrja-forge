# valkyrja-forge

**这是协议 / 技能源码仓，不是应用仓。** 产出物是三个 Claude Code 技能
（`valkyrja-prd` / `valkyrja-arch` / `valkyrja-spec`）与一个确定性门禁脚本
`trace.py`，安装到**别的**产品仓库里使用。本仓没有应用代码，也不消费自己的协议。

## 第一纪律：三载体同源，任何规则只有一个权威副本

**检查条目（V1–V6 系列）的增删改必须同时改三处**，缺一即漂移：

- `skills/valkyrja-spec/tools/trace.py` —— 可执行判定（终审）
- `skills/valkyrja-spec/references/trace-contract.md` —— 详版契约
- `skills/valkyrja-spec/SKILL.md` —— 摘要表（只留组名与结论，不复述判定细节）

理由与事故史见 trace-contract.md 头部的同步提醒，**不要在本文件复述规则本身**。
推广到全仓：一条规则需要在第二处被提到时，写指针、不写副本。
本仓已发生过七次镜像面漂移，每次的根因都是「同一条规则有了第二个可独立演化的副本」。

## 提交前必跑（确定性检查，不许凭印象跳过）

```bash
python3 tests/run_tests.py            # trace.py 回归，期望末行「失败 0」
bash scripts/check-sanitization.sh    # D6 脱敏门禁，期望「0 命中」
```

动了 `.claude-plugin/` 或准备发版时另加 `claude plugin validate .`。

## 这是公开 MIT 仓：脱敏是硬门禁

客户名、客户缩写、内部项目名、试点的真实 change 名与业务词汇，一律不得出现在
任何入库文件中（**含 `docs/design/`**——历史上两次泄漏都发生在设计文档里）。
试点统一以「试点项目 / 试点仓」指代，示例用与真实项目无关的中性代号。
词表在 `~/.claude/valkyrja/d6-wordlist.txt`（私有，永不入库），由上面那条脚本扫描；
遇到新的敏感词先补词表、再清理正文。

## 目录职责

| 路径 | 是什么 | 编辑时注意 |
|---|---|---|
| `skills/**` | 唯一真相源，随安装分发 | `SKILL.md` 每次调用全量进上下文——控制篇幅，判定细则进 `references/` |
| `skills/*/templates/` | 落盘格式的权威 | 模板注释与 SKILL.md 曾经互相矛盾（交接单预存 Authority 块），改任一侧都要对账另一侧 |
| `commands/*.md` | 斜杠入口，薄转接 | 只转发意图，**不复述特权与确认规则**——那是 SKILL.md 的唯一权威 |
| `tests/` | trace.py 回归夹具 | **不随技能分发**（forge 开发资产）；新增检查分支就补场景 |
| `docs/design/` | 设计定稿与演进记录 | 每次协议修订追加一行演进记录，注明来源：纸面推演 / 外部评审 / 真实运行 |
| `.claude-plugin/` | plugin 与 marketplace 清单 | 两份 `version` 必须一致；内容变更后抬版本号，否则 `/plugin update` 认不出新版 |

## 本地验证

技能改完不会自动生效。用兜底安装脚本装到系统级，然后**开新会话**验证：

```bash
scripts/install-skills.sh --system --force
```

plugin 是分发主路径，但每次改动都要 `/plugin marketplace update` 且需重启，
调试期不适用。**两种形态不要同时装**——会双注册（同一技能出现两次）。

## 语言与机读常量

协议与文档以中文为主；README 双语等价，改一侧必须同步另一侧。
基线节标题、处置枚举、例外记录关键词、`依据:` 前缀等**中文字面量是机读协议的一部分**，
清单见 trace-contract.md 的「机读常量表」——改一个字就会让消费仓以误导性的形态报错。
