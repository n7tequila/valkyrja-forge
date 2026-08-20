---
id: conv-naming
concern: 横切
stack: common
version: 2026-08-20
source: 自撰（综合作者既有全局规则与内部项目各层命名约定）
license: 自有
modified: 否
status: redistributable
---

# 跨层命名基线

## 各层风格总表

| 层 | 风格 |
|---|---|
| 代码变量/函数 | camelCase，描述性完整单词 |
| 类型/类/组件 | PascalCase |
| 常量 | UPPER_SNAKE_CASE |
| 数据库标识符 | snake_case（详见 conv-db-relational-postgres） |
| JSON 字段 | camelCase（详见 conv-api-envelope） |
| URL 路径段 | kebab-case，资源复数名词 |
| 错误码 | `<MODULE>_<REASON>` UPPER_SNAKE |
| 文件/目录 | 按栈惯例；同一仓库内一致，禁止混用 |

## 布尔命名的分层规则（易生矛盾，明确写死）

- **代码内**布尔变量/函数：`is/has/should/can` 前缀（`isVisible`、`hasPermission`）。
- **数据库列**：**禁 `is_` 前缀**（`active` 不是 `is_active`），理由见 DB 约定。
- **JSON 字段**：随项目 API 契约二选一并全局一致——跟代码（`isActive`）或
  跟 DB（`active`），**不允许两种并存**。采纳时必须绑定该选择。

三层规则并不矛盾：它们各自服从所在层的生态惯例；矛盾只在"未显式绑定 JSON 层"时产生。

## 语义规则

- 完整单词优先，仅允许公认缩写（id/no/url/ip）；**禁止自创缩写**。
- 时间戳一律 `At` 结尾（`createdAt`/`deletedAt`）；时长带单位（`timeoutMs`）。
- 操作人外键/字段用动词过去式（`createdBy`/`confirmedBy`），
  区分「业务归属」与「操作人」两种语义，不共用一个名字。
- 集合复数（`items`），映射写明键值（`userById`）。
- 同一概念全仓同一个名字——出现第二个名字时要么改名统一，要么说明这是不同概念。

## 反模式

| 反模式 | 后果 |
|---|---|
| `data`/`info`/`obj`/`temp` 类空心名 | 读者被迫追溯类型定义 |
| 同名不同义（一个 `status` 三种含义） | 检索污染、误改 |
| 否定式布尔（`isNotReady`） | 双重否定推理负担 |
| 类型后缀冗余（`userList: List<User>` 命名为 `userListArray`） | 噪音 |

## 采纳时须绑定的项目参数

- JSON 布尔风格二选一
- MODULE 前缀清单（与错误分类约定共用）
- 各栈文件命名细则的落点（指向对应 stack 约定）
