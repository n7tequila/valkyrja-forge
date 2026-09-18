# 取证：压力、规模、兜底、影响、时机

报告里每个数字都要能回答「你怎么知道的」。这个文件给出取数的命令与判断口径。示例路径与类名是虚构的。

## 压力行

目标是把「以后可能会改」变成数字，或者老实写「推测」。

```bash
# 近 12 个月这个文件被改了几次
git log --since='12 months ago' --oneline -- path/to/File.java | wc -l

# 某个代码区域（比如那个 switch）的改动历史
git log -L '/switch (type)/,+40:path/to/File.java' --oneline

# 上一次「新增一种类型」的提交是哪个、碰了几个文件
git log --format='%h %ad %s' --date=short -S'case OVERSEAS' -- .
git show --stat <commit>

# 这个文件的改动通常和哪些文件一起出现（同提交共现）
git log --format='%h' -- path/to/File.java | head -20 \
  | xargs -I{} git show --name-only --format= {} | sort | uniq -c | sort -rn | head
```

写法：「近 12 个月改 9 次；上次加 OVERSEAS 的提交碰了 4 个文件」。
一次都没改过、也没有已知的下一个需求：写「无历史证据，属推测」，结论倾向 KEEP。
只改过一次：写实数，不夸大。

## 现象行的规模数字

Lanza 与 Marinescu 2006 年的检测策略，阈值来自 45 个 Java 项目的统计：

| 味 | 判定 |
|---|---|
| God Class | 访问外部类数据 ATFD 大于 5，且加权方法数 WMC 不低于 47，且紧密类内聚 TCC 低于 0.33 |
| Brain Method | 行数 LOC 大于 65，且圈复杂度高，且最大嵌套 MAXNESTING 不低于 5，且访问变量数 NOAV 大于 8 |

v1 不接工具，手数也行：方法行数、类的方法数与字段数、嵌套深度、一个方法访问了几个别的类的字段。
写成「calc 方法 90 行、嵌套 5 层、访问 3 个类的 11 个字段」，不写「太大了」。
数字到了阈值八成但没到：不立条目，记观察哨，见 ledger.md。

## 兜底三档

先跑基线：全量测试必须绿，红的不开工。然后按风险先验定档。

| 档 | 适用 | 要求 |
|---|---|---|
| 一 | 先验低的手法：Rename、Extract Interface、IDE 执行的 Level 1 | 既有测试全绿即可；批量结束后跑一次全量 |
| 二 | 先验中的手法 | 必须有测试覆盖**将被移动的分支**，写出测试类与用例名；没有先补 |
| 三 | 先验高的手法、所有 Level 3 | 在热点类上跑突变测试；存活突变体集中在将被移动的逻辑上即 TESTS_FIRST |

为什么覆盖率不够：行覆盖率与测试有效性只有弱相关（Inozemtseva 与 Holmes，2014）；真实缺陷里 73%
与突变体耦合（Just 等，2014）；LLM 生成的重构里有 18% 到 35% 改变了语义，其中约 21% 能通过既有测试
（Dristi 与 Dwyer，2026）。「测试绿」在第三档不是证据，突变体活不活才是。

PIT 的用法（Maven，按项目配置调整）：

```bash
mvn -q org.pitest:pitest-maven:mutationCoverage \
  -DtargetClasses='com.example.shipping.ShippingFeeCalculator*' \
  -DtargetTests='com.example.shipping.*Test'
# 报告在 target/pit-reports/，看 SURVIVED 的突变体落在哪些行
```

没装 PIT 的项目，第三档的最低线是 safe-change.md 里的生成式特征测试：用当前代码冻结 10 到 20 组
输入输出，严格相等，先钉住再动。这不如突变测试，但比「测试绿」强得多。

## 影响行

```bash
# 公开签名的调用方
grep -rn 'calc(' --include='*.java' src | grep -v 'ShippingFeeCalculator.java'
# 字符串形式的引用：MyBatis、SpEL、JPQL、配置
grep -rn 'calcShippingFee\|shippingFeeCalculator' \
  --include='*.xml' --include='*.properties' --include='*.yml' --include='*.java' src
```

IDE 的 Find Usages 更准，但字符串引用它找不到，两者都要跑。影响行写名字：文件数、签名、调用方类名。

## 时机行

| 时机 | 什么情况 | 对应 Fowler 的说法 |
|---|---|---|
| First | 有已知的下一个需求会碰这段代码，先重构再做需求 | 预备性重构 |
| After | 手头需求做完，顺手把刚碰过的地方收拾干净 | 顺手清理（litter-pickup） |
| Later | 没有紧邻的需求，但压力数字说明值得，排期集中做 | 计划性重构 |
| Never | 结论是 KEEP；进台账为不动，或带触发的观察 | 当作 API 用、不改就不碰 |

几个模块做完之后集中审一轮，产出的多数条目是 Later；其中有下一个需求已经排上的，标 First。
四个词来自 Kent Beck《Tidy First?》第 21 章。
