---
id: conv-comments-java-spring
concern: 横切
stack: java-spring
version: 2026-09-07
source: 自撰（豁免清单与具名陷阱源自作者规则与内部项目 review/构建事故）；标签纪律对齐 Oracle 文档注释规范与 Google Java Style 的公开条款，非摘编
license: 自有
modified: 否
status: redistributable
requires: conv-comments
---

# Javadoc 绑定增量

> 本条目在 [conv-comments](conv-comments.md) 通用层之上引入 **Javadoc** 增量。
> **采纳本条目前须先采纳通用层**；非 Java 栈不采本条目。
> 通用层已定「文档注释写契约不写实现」「首句独立成摘要」——这里不重述那两条，
> 只装 Java 侧的必写/豁免边界与具名陷阱。

## 写不写：豁免清单先于覆盖率

Java 生态默认「每个 public 成员都该有 Javadoc」。照做的结果是满屏
`/** 获取名称。@return 名称 */`——那是通用层禁止的叙事注释换了个壳。判据：

- **必写**：跨模块或跨 change 被调用的 public 类型与方法、抛 unchecked 异常的
  方法、有非显然边界或特殊返回值的方法、`@Deprecated` 成员、`package-info.java`。
- **豁免**：getter/setter、`@Override`（见下）、签名已完整表达契约的方法、
  包私有与 private 成员（该写普通注释就写普通注释）。

**覆盖率不作为 review 项**，也不开 checkstyle 的 Javadoc 全量强制。
强制覆盖率必然产出同义反复文档，比没有更糟——它让读者误以为自己读过了。

## 首句摘要的截断陷阱

- 摘要 = **第一个「句点 + 空白」之前**的全部内容，工具按此截断。首句里出现
  `e.g.` / `i.e.` / 版本号 `1.0. ` 会让摘要在半句处断掉，索引页显示残句。
  要举例就放到后续段落。
- 中英混排同理：中文全角句号后通常不接空格因而不触发，但**句中混入英文缩写
  仍会断**。摘要句里不放缩写是唯一稳的做法。
- 首句写名词性摘要，不用「本方法用于……」开头——那几个字对每个方法都成立，零信息。

## `@Override` 默认不写 Javadoc

- 覆写方法**默认不写**，让文档从父类型继承。写了等于同一份契约有了第二个可独立
  演化的副本，父类改了它不会跟着改——与通用层「过期注释比没有注释更危险」同源。
- 确有子类特有增量（更强的前置条件、额外副作用）时，用 `{@inheritDoc}` 承接
  父文档再补增量，不整段重写。

## 标签纪律

- `@param` / `@return` **只在有信息时写**：语义、单位、边界、可否为 null、
  空集合与 null 的区别。`@param tenantId 租户标识` 这种复述参数名的是噪声，删。
- `@throws` **必须覆盖 unchecked 异常**及其触发条件。checked 异常编译器已强制
  在签名里声明、读者看得见；unchecked 的不写就没人知道它会炸。
- `@Deprecated` 注解与 `@deprecated` 标签是两个东西，**必须成对出现**：
  只加注解的话 IDE 只划一条横线，不告诉调用方替代品是什么、何时移除。
  标签里写「替代 API + 移除时机或触发条件」，与通用层 TODO 纪律同口径。

## 转义与格式

- 含 `<` 或 `@` 的内容一律用 `{@code ...}` 包裹：裸写 `List<String>` 会被当成
  HTML 标签，轻则渲染丢内容，重则 doclint 直接报错；行首裸写 `@Override`
  会被当成块标签解析。
- 段落用 `<p>`，不靠空行。**Javadoc 不吃 Markdown**——JDK 23+ 的 Markdown 文档
  注释是另一套语法，项目要用须在参数节显式声明起始版本，两种语法不可混写。
- 要引用就用 `{@link}`，别用 `{@code}` 手写类名：`{@link}` 在目标被改名或删除时
  会构建失败，`{@code}` 写错永远静默。这是「让工具替人盯漂移」的最小落点。

## 接到构建上（宪法 8：执行靠既有工具链，不另造 checker）

- doclint 默认开启且严格：缺 `@param`、非法 HTML、坏 `{@link}` 都会让文档构建
  失败。**CI 必须跑一次文档构建**，否则这些问题攒到发版打包那一刻才爆，
  而那通常是最不能停的时刻。
- 不要用全局 `-Xdoclint:none` 了事——那是把上面所有规则一次性作废。确有历史包袱
  时按模块收窄豁免，并在 backlog 记下解除豁免的触发条件。

## package-info.java

- 每个对外包写 `package-info.java`：包的职责边界与允许的依赖方向
  （分层规则本身在 conv-spring-layering / conv-java-ddd，此处只放指针不复述）。
- 包级 nullability 默认标注（如 `@NonNullApi`、`@ParametersAreNonnullByDefault`）
  放这里。这是通用层五问第 4 问「用更强的类型说清」在 Java 侧的标准出口——
  能用标注表达的可空性，就不要写成一句 `@param 可以为 null`。

## 采纳时须绑定的项目参数

- 必写清单与豁免清单的项目版（在上面基础上增删）
- 文档注释语言（中文 / 英文，全项目统一，不混写）
- 是否启用 JDK 23+ Markdown 文档注释；启用则声明起始版本与迁移边界
- doclint 级别、模块级豁免清单，以及文档构建挂在哪个 CI 阶段
- checkstyle / spotless 里与 Javadoc 相关的规则开关——**须与上面的豁免清单一致**，
  不一致时以本约定为准并改配置（两份规则各自演化就是漂移的开始）
