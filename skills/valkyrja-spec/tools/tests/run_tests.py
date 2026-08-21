#!/usr/bin/env python3
"""trace.py 回归夹具跑测器。

七个合成场景覆盖契约二/三的全部分支（--skip-cli 模式：验 V2–V4 集合代数层，
CLI 依赖项 V1.1/V1.2/V5 显式跳过——真实使用仍走全量）：

  1 全 ADDED 通过            5 RENAMED active 需求放行（∈ historical 即可）
  2 MODIFIED 历史豁免不误报   6 范围蔓延 → WARNING 放行
  3 REMOVED 退役需求放行      7 漏做 → ERROR 拦截
  4 REMOVED 活需求 → ERROR

报数纪律：输出场景总数与失败数；任何失败打印完整 trace 输出。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRACE = os.path.join(HERE, '..', 'trace.py')
REPO = os.path.join(HERE, 'fixtures', 'repo')

# (case, 期望退出码, 必须出现的输出片段, 不得出现的输出片段)
CASES = [
    ('case-added',          0, ['错误 0', '分场景判定全部通过', '源码依据 1 条'], []),
    ('case-mod',            0, ['错误 0'], ['范围蔓延']),
    ('case-removed-dep',    0, ['错误 0', 'REMOVED 触达 FRID 全部 ⊆ deprecated'], []),
    ('case-removed-active', 1, ['移除仍 active'], []),
    ('case-renamed',        0, ['错误 0', 'RENAMED 触达 FRID 全部 ∈ historical'], []),
    ('case-creep',          0, ['范围蔓延', '警告 1'], []),
    ('case-missing',        1, ['漏做'], []),
]

fails = 0
for name, exp_exit, must, must_not in CASES:
    r = subprocess.run([sys.executable, TRACE, REPO, name, '--skip-cli'],
                       capture_output=True, text=True)
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
    print(('PASS  ' if not probs else 'FAIL  ') + name
          + ('' if not probs else '   ' + '; '.join(probs)))
    if probs:
        fails += 1
        print(out)

print(f'—— 场景 {len(CASES)}，失败 {fails} ——')
sys.exit(1 if fails else 0)
