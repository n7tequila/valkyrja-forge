#!/usr/bin/env python3
"""trace.py 回归夹具跑测器。

19 个场景（末位 1 个条件执行），覆盖范围（如实声明，勿夸大）：
  契约二/三主干全分支（ADDED/MODIFIED 历史豁免/REMOVED 两向/RENAMED/蔓延/漏做）、
  V1.3 DOMAIN 定位与同域双 active、V3.5 计划外分层（本 change ERROR/探索备案
  消提醒/前缀名不蹭裁决）与杂散文件过滤、V4.1 块内多 Sources、V4.5 例外裁决两分支、
  V4.8 全角冒号幽灵依据、嵌套 capability path、TOOL ERROR 退出码 2
  （缺参/损坏输入/未预期异常经 excepthook 且管道下消息不丢）、--stage 报告头、
  CLI 未安装（V1.1，条件执行）。
仍未覆盖：V4.0a/b/c 各失败分支、V2.2/V2.3/V2.4 失败分支、V2.5 三分支、
  V4.7 两分支、V4.9 幽灵/superseded、V5 真实 CLI 正向链路——补齐前不得声称全覆盖。

--skip-cli 模式验集合代数层，CLI 依赖项 V1.1/V1.2/V5 显式跳过；真实使用仍走全量。
报数纪律：输出场景总数与失败数；任何失败打印完整 trace 输出。
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRACE = os.path.join(HERE, '..', 'trace.py')
FIX = os.path.join(HERE, 'fixtures')

# (repo子目录, case, 附加参数, 期望退出码, 必须出现的输出片段, 不得出现的输出片段)
CASES = [
    ('repo', 'case-added', [], 0,
     ['错误 0', '分场景判定全部通过', '源码依据 1 条', '5 条需求块 Sources 合法', 'DOMAIN T'], []),
    ('repo', 'case-mod', [], 0, ['错误 0'], ['范围蔓延']),
    ('repo', 'case-removed-dep', [], 0, ['错误 0', 'REMOVED 触达 FRID 全部 ⊆ deprecated'], []),
    ('repo', 'case-removed-active', [], 1, ['移除仍 active'], []),
    ('repo', 'case-renamed', [], 0, ['错误 0', 'RENAMED 触达 FRID 全部 ∈ historical'], []),
    ('repo', 'case-creep', [], 0, ['范围蔓延', '已有裁决', '警告 1'], []),
    ('repo', 'case-creep-raw', [], 1, ['范围蔓延且未见例外记录裁决'], []),
    ('repo', 'case-missing', [], 1, ['漏做'], []),
    ('repo', 'case-nested', [], 0, ['错误 0', '分场景判定全部通过'], ['主 spec 无同名']),
    ('repo', 'case-colon-full', [], 1, ['幽灵依据', 'DEC-T-999'], []),
    ('repo', 'case-v41-dup', [], 1, ['多个 Sources 行'], []),
    ('repo', 'case-added', ['--stage', 'pre-archive'], 0, ['trace(pre-archive)'], ['trace(pre-apply)']),
    ('repo-dual', 'case-added', [], 1, ['多个 active 基线'], []),
    ('repo-broken', 'case-x', [], 2, ['TOOL ERROR', 'prd_release'], []),
    # 未预期异常（非 UTF-8 基线）：须走 excepthook 出 TOOL ERROR + exit 2，
    # 且消息在 stdout 管道（本跑测器正是管道捕获）下不得丢失
    ('repo-crash', 'case-c', [], 2, ['TOOL ERROR', '工具自身故障'], []),
    # case-stray 有探索备案但本 change 计划外仍须 ERROR（✗ 前缀钉住级别）；
    # case-str 是 case-stray 的前缀名——他 change 提醒必须列出它、
    # 不得蹭到 case-stray 的备案被误消（exc_ruled 边界匹配回归）
    ('repo-unplanned', 'case-ok', [], 0,
     ['计划外 change（探索态合法', '警告 1', '已建 1 / 未建 0 / 计划外 2', "'case-str'"],
     ['.stray-dotfile', 'stray-note', "'case-stray'"]),
    ('repo-unplanned', 'case-stray', [], 1, ['✗ V3.5', '本 change 计划外'], []),
]

fails = 0

def check(label, r, exp_exit, must, must_not):
    global fails
    out = r.stdout + r.stderr
    probs = []
    if r.returncode != exp_exit:
        probs.append(f'exit {r.returncode} ≠ 期望 {exp_exit}')
    for s in must:
        if s not in out:
            probs.append(f'缺输出「{s}」')
    for s in must_not:
        if s in out:
            probs.append(f'不应出现「{s}」')
    print(('PASS  ' if not probs else 'FAIL  ') + label
          + ('' if not probs else '   ' + '; '.join(probs)))
    if probs:
        fails += 1
        print(out)

for repo, name, extra, exp_exit, must, must_not in CASES:
    r = subprocess.run([sys.executable, TRACE, os.path.join(FIX, repo), name,
                        '--skip-cli'] + extra, capture_output=True, text=True)
    check(f'{repo}/{name}' + (' ' + ' '.join(extra) if extra else ''),
          r, exp_exit, must, must_not)

# 缺参：TOOL ERROR + 退出码 2（工具故障与门禁 ERROR 不得共用退出码）
r = subprocess.run([sys.executable, TRACE], capture_output=True, text=True)
check('(无参数)', r, 2, ['TOOL ERROR', '用法'], [])
n_total = len(CASES) + 1

# CLI 未安装（条件执行）：裸 PATH 下 openspec 不可见时，V1.1 须给出可读报错
# 而非 FileNotFoundError 裸 traceback。若裸 PATH 竟有 openspec 则跳过本场景。
if shutil.which('openspec', path='/usr/bin:/bin') is None:
    env = dict(os.environ, PATH='/usr/bin:/bin')
    r = subprocess.run([sys.executable, TRACE, os.path.join(FIX, 'repo'), 'case-added'],
                       capture_output=True, text=True, env=env)
    check('(CLI 未安装)', r, 1, ['未安装或不在 PATH'], ['Traceback'])
    n_total += 1
else:
    print('SKIP  (CLI 未安装)：/usr/bin:/bin 下存在 openspec，场景不可构造')

print(f'—— 场景 {n_total}，失败 {fails} ——')
sys.exit(1 if fails else 0)
