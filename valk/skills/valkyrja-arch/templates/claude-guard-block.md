<!-- 写入产品仓库根 CLAUDE.md 的 valkyrja 治理块。
     本文件在 valkyrja-prd / valkyrja-arch / valkyrja-spec 三个技能的 templates/ 下
     各存一份、**逐字一致**（技能可独立安装，必须各自自带）；改动须三处同步，md5 可验。

     写入纪律（协议见各 SKILL.md 的「消费仓 CLAUDE.md 治理块」）：
     - 目标文件已存在 → 只插入下面的界定块，其他内容一个字不动
     - 目标文件不存在 → 只创建含本块的文件；**不要顺手写项目概述**
       （那是 /init 的职责，两边各写一份必然打架）
     - 块已存在 → 什么都不做（幂等）
     - 落盘前回显全文并经用户确认（特权动作）

     内容纪律：块内只写**归属与禁令**，不复述任何协议规则，
     不写任何派生值（当前基线版本、change 清单、覆盖数——写了必然过期）。
     下列路径是本协议固定的工作区约定，与具体项目无关，可原样写入；
     即使某棵树尚未建立也照写——它是归属声明，不是现状清单。 -->

<!-- valkyrja:begin —— 由 valkyrja 技能维护；勿手改本块 -->
本仓的需求与技术治理由 valkyrja 技能承担。以下路径的写入**一律经技能或 OpenSpec CLI**，
不要直接手改：

- `docs/product/initiatives/**` —— 需求讨论、决策与 PRD，入口 `/valk:prd`。
  其中 `prd/releases/**` 是**已发布 PRD，不可变**：要改一律发新版本，绝不编辑既有版本。
- `docs/architecture/**` —— 技术选型（ADEC）、编码约定副本、共享接口契约，入口 `/valk:arch`。
- `docs/product/baselines/**` 与 `openspec/**` —— 需求基线、change 与主 spec，
  入口 `/valk:spec`；主 spec 只经 `openspec archive` 合并。

需求以**已发布 PRD 为唯一权威**：不要凭记忆复述需求，也不要在下游就地改写或收窄它；
发现缺口或矛盾时停下来问人。

本块是 prompt 级提示、**不是强制**——真正的门禁是 valkyrja-spec 的 trace 机检
（退出码 0/1 可作 CI 门禁）。
<!-- valkyrja:end -->
