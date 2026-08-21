#!/usr/bin/env python3
"""valkyrja-spec trace 检查器 —— V1..V5 + V4.8 的确定性实现。

用法: trace.py <产品仓库根> <change-name>
退出码: 0 = 放行 / 1 = 有 ERROR 不得放行（可直接用作 CI 门禁）。

定位：本脚本实现 SKILL.md 中 trace 动作的**确定性部分**。
语义判断（拆分完整性、DEC 范围覆盖）不在此，仍由人核对——
假阳性的"通过"比不检更危险。

来源：由首次真实运行倒逼产生，非预先设计（项目原则「格式契约先于工具」）。
两个已修 bug 值得记住，因为它们都是检查器自身的假结果：
  1. openspec list --json 返回 {"changes":[...],"root":{...}}，
     直接迭代顶层会把 "changes"/"root" 当成 change 名 → 假 ERROR
  2. superseded 检测用反斜杠-s 通配跨了行，把空的 superseded-by: 误判为已填 → 假 WARNING
维护提醒：SKILL.md 的检查条目变更时必须同步本文件——
设计文档/工具/skill 三载体漂移在本项目已发生过（V4.8 首次遗漏 skill 本体）。
"""
import json, os, re, subprocess, sys, glob

FRID = r'(?:REQ|BR|SEC|NFR)-[A-Z][A-Z0-9]*(?:_[A-Z][A-Z0-9]*)*-\d{3}'
SRC_RE = re.compile(rf'^Sources:\s*({FRID})(\s*,\s*{FRID})*\s*$')

E, W, OK = [], [], []
def err(c, m): E.append(f"{c}  {m}")
def warn(c, m): W.append(f"{c}  {m}")
def ok(c, m): OK.append(f"{c}  {m}")

def sh(*a, cwd=None):
    r = subprocess.run(a, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout, r.stderr

SKIP_CLI = '--skip-cli' in sys.argv[1:]
ARGS = [a for a in sys.argv[1:] if a != '--skip-cli']
R, CH = ARGS[0], ARGS[1]
CHDIR = os.path.join(R, 'openspec/changes', CH)

# ---------- V1 前提 ----------
if SKIP_CLI:
    # 夹具/离线模式：显式跳过 CLI 依赖项（V1.1/V1.2/V5），只验集合代数层。
    # 跳过必须显式入报告——零对象 ≠ 零发现。
    ok('V1.1', '跳过（--skip-cli 夹具模式，未验 CLI）')
    ok('V1.2', '跳过（--skip-cli）')
else:
    rc, out, _ = sh('openspec', '--version')
    ver = out.strip()
    ok('V1.1', f'CLI {ver}') if rc == 0 and tuple(map(int, ver.split('.')[:2])) >= (1, 9) \
        else err('V1.1', f'CLI 不可用或版本过低: {ver}')

    rc, out, _ = sh('openspec', 'context', '--json', cwd=R)
    try:
        root = json.loads(out)['root']['path']; ok('V1.2', f'root={os.path.basename(root)}')
    except Exception:
        err('V1.2', 'openspec context 未返回有效 root'); root = None

bl_files = sorted(glob.glob(os.path.join(R, 'docs/product/baselines/*.md')))
bl = None
for f in bl_files:
    t = open(f, encoding='utf-8').read()
    m = re.search(r'^status:\s*(\S+)', t, re.M)
    if m and m.group(1) == 'active':
        bl, BT = f, t
if bl: ok('V1.3', f'active 基线 {os.path.basename(bl)}')
else: err('V1.3', '无 status: active 的基线'); sys.exit(1)

# V1.4 技术地基（奠基性 ADEC）——WARNING 级：治理债，不是追溯断裂。
# 仅当 arch 工作区存在时检查；无目录时显式报「跳过」而非沉默（零对象≠零发现）。
arch_dir = os.path.join(R, 'docs/architecture')
if os.path.isdir(arch_dir):
    foundational = {'stack': False, 'layout': False}
    for p in glob.glob(os.path.join(arch_dir, 'decisions', 'ADEC-*.md')):
        b = open(p, encoding='utf-8').read()
        st = re.search(r'^status:[ \t]*(\S+)', b, re.M)
        fo = re.search(r'^foundational:[ \t]*(stack|layout)\b', b, re.M)
        if st and st.group(1) == 'accepted' and fo:
            foundational[fo.group(1)] = True
    lacking = sorted(k for k, v in foundational.items() if not v)
    if lacking:
        warn('V1.4', f'技术地基未定（缺奠基 ADEC: {lacking}）——建议先跑 valkyrja-arch bootstrap')
    else:
        ok('V1.4', '奠基性 ADEC 齐备（stack + layout）')
else:
    ok('V1.4', '无 arch 工作区，跳过（不用 valkyrja-arch 的项目合法）')

# ---------- 解析基线 ----------
prd_rel = re.search(r'^prd_release:\s*(\S+)', BT, re.M).group(1)
PRD = os.path.join(R, prd_rel)

def sections(t):
    d, cur = {}, None
    for ln in t.split('\n'):
        m = re.match(r'^##\s+(.+?)\s*$', ln)
        if m and not re.match(rf'^##\s+{FRID}', ln): cur = m.group(1); d[cur] = []
        elif cur is not None: d[cur].append(ln)
    return {k: '\n'.join(v) for k, v in d.items()}
S = sections(BT)

def ids_of(sec):
    return set(re.findall(rf'^###\s+({FRID})', S.get(sec, ''), re.M))

ruling = S.get('需求裁决', '')
blocks = re.split(rf'^###\s+({FRID})\s*$', ruling, flags=re.M)
disp = {}
for i in range(1, len(blocks), 2):
    m = re.search(r'^处置：(\S+)', blocks[i+1], re.M)
    disp[blocks[i]] = m.group(1) if m else '?'
included = {k for k, v in disp.items() if v in ('直通', '拆分')}
conflicted = {k for k, v in disp.items() if v == '冲突'}
deferred = ids_of('延期项（deferred）')
external = ids_of('外部系统项（external）')
nonsw = ids_of('非软件项（non-software）')

# ---------- V2 PRD 侧 ----------
if os.path.isfile(PRD): ok('V2.1', f'release 存在 {os.path.basename(PRD)}')
else: err('V2.1', f'release 不存在: {prd_rel}'); sys.exit(1)
PT = open(PRD, encoding='utf-8').read()

blocking = re.findall(r'^###\s+Q-\S+\s+\[blocking\]', PT, re.M)
openq = 0
for m in re.finditer(r'^###\s+(Q-\S+)\s+\[blocking\]', PT, re.M):
    tail = PT[m.end(): m.end() + 400]
    if re.search(r'^Status:\s*open', tail, re.M): openq += 1
ok('V2.2', f'blocking 且 open 的问题 = {openq}') if openq == 0 else err('V2.2', f'{openq} 条 blocking 未清')

pblocks = re.split(rf'^##\s+({FRID})\s*$', PT, flags=re.M)
prd_ids, bad_src = [], []
for i in range(1, len(pblocks), 2):
    fid, body = pblocks[i], pblocks[i+1]
    prd_ids.append(fid)
    srcs = re.findall(r'^-\s*((?:RN|DEC|TM)-\S+)\s*$', body, re.M)
    if not re.search(r'^Sources:\s*$', body, re.M) or not any(s.startswith(('RN-', 'DEC-')) for s in srcs):
        bad_src.append(fid)
ok('V2.3', f'{len(prd_ids)} 条需求块 Sources 合法') if not bad_src else err('V2.3', f'Sources 不合法: {bad_src}')
dups = {x for x in prd_ids if prd_ids.count(x) > 1}
ok('V2.4', '无重复 FRID') if not dups else err('V2.4', f'重复 FRID: {sorted(dups)}')

active = set(prd_ids)  # 本 release 无 [DEPRECATED] 标记
deprecated = set(re.findall(rf'^##\s+({FRID})\s+\[DEPRECATED\]', PT, re.M))
active -= deprecated
historical = set()
for f in glob.glob(os.path.join(os.path.dirname(PRD), '*.md')):
    historical |= set(re.findall(rf'^##\s+({FRID})', open(f, encoding='utf-8').read(), re.M))

# V2.5 发版欠账门限：决而未发的 DEC 对下游不可见；未开工 change 不得在
# 已知过期的需求上启动。round 比较为主（无同日歧义），date 为退化路径。
rel_round = re.search(r'^round:\s*(\d+)', PT, re.M)
rel_date = re.search(r'^date:\s*(\S+)', PT, re.M)
init_dir = os.path.dirname(os.path.dirname(os.path.dirname(PRD)))
dec_files = sorted(glob.glob(os.path.join(init_dir, 'decisions', 'DEC-*.md')))
debt = []
for f in dec_files:
    b = open(f, encoding='utf-8').read()
    # frid-impact: none = 不改 FRID 语义的背书类决策，无可发内容，豁免欠账
    if re.search(r'^frid-impact:[ \t]*none', b, re.M):
        continue
    dr = re.search(r'^round:\s*(\d+)', b, re.M)
    dd = re.search(r'^date:\s*(\S+)', b, re.M)
    if rel_round and dr:
        if int(dr.group(1)) > int(rel_round.group(1)):
            debt.append(os.path.basename(f)[:-3])
    elif rel_date and dd and dd.group(1) > rel_date.group(1):
        debt.append(os.path.basename(f)[:-3])
tasks_p = os.path.join(CHDIR, 'tasks.md')
started = os.path.isfile(tasks_p) and bool(
    re.search(r'^\s*[-*]\s*\[[xX]\]', open(tasks_p, encoding='utf-8').read(), re.M))
if not debt:
    ok('V2.5', f'发版欠账 0 条（扫描 {len(dec_files)} 条 DEC）')
elif started:
    ok('V2.5', f'欠账 {len(debt)} 条，但本 change 已开工——由 rebaseline V4.0(a) 联锁接手: {debt}')
else:
    exc = any(('欠账' in ln and CH in ln) for ln in S.get('例外记录', '').split('\n'))
    if exc:
        ok('V2.5', f'欠账 {len(debt)} 条，基线例外记录已裁决放行本 change')
    else:
        err('V2.5', f'发版欠账 {len(debt)} 条且本 change 未开工: {debt} —— 先发版，或取得基线例外裁决')

# ---------- V3 基线对账 ----------
allsets = {'included': included, 'deferred': deferred, 'non-software': nonsw,
           'external': external, 'conflicted': conflicted}
union = set().union(*allsets.values())
miss = active - union
ok('V3.1', f'active({len(active)}) 全部已裁决') if not miss else err('V3.1', f'漏裁决: {sorted(miss)}')

ovl = []
ks = list(allsets)
for i in range(len(ks)):
    for j in range(i+1, len(ks)):
        o = allsets[ks[i]] & allsets[ks[j]]
        if o: ovl.append((ks[i], ks[j], sorted(o)))
ok('V3.2', '五集合两两互斥') if not ovl else err('V3.2', f'重叠: {ovl}')

ghost = union - active - deprecated
ok('V3.3', '基线无幽灵 ID') if not ghost else err('V3.3', f'幽灵 ID: {sorted(ghost)}')

plan_sec = S.get('Change 划分（计划，非现状）', '')
pb = re.split(r'^###\s+([a-z][a-z0-9-]*)\s*$', plan_sec, flags=re.M)
plan = {}
for i in range(1, len(pb), 2):
    m = re.search(r'^覆盖：(.+?)(?=^\S+：|\Z)', pb[i+1], re.M | re.S)
    plan[pb[i]] = set(re.findall(FRID, m.group(1))) if m else set()
covered = set().union(*plan.values()) if plan else set()
unc = included - covered
ok('V3.4', f'{len(included)} 条 included 全部被 planned change 覆盖') if not unc \
    else err('V3.4', f'未被覆盖: {sorted(unc)}')

if SKIP_CLI:
    disk = set(os.listdir(os.path.join(R, 'openspec/changes'))) - {'archive'}
else:
    rc, out, _ = sh('openspec', 'list', '--changes', '--json', cwd=R)
    try:
        # 返回体形如 {"changes":[{"name":...}], "root":{...}} —— 必须取 changes 键，
        # 直接迭代顶层会把 "changes"/"root" 当成 change 名。
        disk = {c['name'] for c in json.loads(out)['changes']}
    except Exception:
        disk = set(os.listdir(os.path.join(R, 'openspec/changes'))) - {'archive'}
built, unbuilt, unplanned = disk & set(plan), set(plan) - disk, disk - set(plan)
ok('V3.5', f'已建 {len(built)} / 未建 {len(unbuilt)} / 计划外 {len(unplanned)}')
if unplanned: err('V3.5', f'计划外 change（不得归档）: {sorted(unplanned)}')

# ---------- V4 delta 侧 ----------
prop = os.path.join(CHDIR, 'proposal.md')
PP = open(prop, encoding='utf-8').read() if os.path.isfile(prop) else ''
# (?=^## |\Z)：块可以是文件最后一节——只要求"至下一个二级标题或文件末尾"
ab = re.search(r'^## Requirement Authority\s*\n(.*?)(?=^## |\Z)', PP, re.M | re.S)
if not ab:
    err('V4.0', 'proposal.md 缺 ## Requirement Authority 块')
    cov_declared = set()
else:
    b = ab.group(1)
    pr = re.search(r'^PRD-Release:\s*(\S+)', b, re.M)
    bb = re.search(r'^Baseline:\s*(\S+)', b, re.M)
    cf = re.search(r'^Covered-FRIDs:\s*(.+)$', b, re.M)
    if not all([pr, bb, cf]):
        err('V4.0', 'Authority 块三个键名不全'); cov_declared = set()
    else:
        cov_declared = set(re.findall(FRID, cf.group(1)))
        okk = True
        if os.path.normpath(os.path.join(R, bb.group(1))) != os.path.normpath(bl):
            err('V4.0a', f'Baseline 未指向当前 active 基线: {bb.group(1)}'); okk = False
        if pr.group(1) != prd_rel:
            err('V4.0b', f'PRD-Release 与基线 prd_release 不一致'); okk = False
        if cov_declared != plan.get(CH, set()):
            err('V4.0c', f'Covered-FRIDs 与基线计划不等：计划 {sorted(plan.get(CH,set()))} 声明 {sorted(cov_declared)}'); okk = False
        if okk: ok('V4.0', 'Authority 块三重自洽')

specs = sorted(glob.glob(os.path.join(CHDIR, 'specs', '**', '*.md'), recursive=True))

def main_spec_sources(cap):
    """主 spec 同名 Requirement → Sources 集合。主 spec 不存在返回 {}（首批 change 前的常态）。"""
    p = os.path.join(R, 'openspec/specs', cap, 'spec.md')
    if not os.path.isfile(p):
        return {}
    Lm = open(p, encoding='utf-8').read().split('\n')
    d = {}
    for i, ln in enumerate(Lm):
        if ln.startswith('### Requirement:'):
            nm = ln[len('### Requirement:'):].strip()
            nx = Lm[i+1].strip() if i + 1 < len(Lm) else ''
            d[nm] = set(re.findall(FRID, nx)) if SRC_RE.match(nx) else set()
    return d

# 契约二/三的全分支实现。addressed 严禁退化为 Sources 并集——
# 那会让 MODIFIED 历史 ID 永久假警报、REMOVED/RENAMED 型 change 永远无法放行。
addressed = set()
n_req = 0            # ADDED/MODIFIED Requirement 计数（须带 Sources 行）
badsrc = []          # V4.1/V4.2：Sources 行缺失或非法（仅 ADDED/MODIFIED 需要）
v43 = []             # V4.3：ADDED 越界 / MODIFIED 删既有、沿袭出 historical、新增越界、无主 spec 对应
v44a, v44b = [], []  # V4.4a REMOVED / V4.4b RENAMED
noop_blocks = []     # 无操作小节头的散 Requirement（格式异常，按 ADDED 从严）
ops_seen = set()
for f in specs:
    L = open(f, encoding='utf-8').read().split('\n')
    cap = os.path.basename(os.path.dirname(f))
    mains = main_spec_sources(cap)
    op = None
    for i, ln in enumerate(L):
        mo = re.match(r'^##\s+(ADDED|MODIFIED|REMOVED|RENAMED)\s+Requirements', ln, re.I)
        if mo:
            op = mo.group(1).upper(); ops_seen.add(op); continue
        if op == 'RENAMED':
            # OpenSpec RENAMED 形态：- FROM: `### Requirement: Old` / - TO: ...
            fm = re.match(r'^-\s*FROM:\s*`?#*\s*Requirement:\s*(.+?)`?\s*$', ln)
            if fm:
                nm = fm.group(1).strip()
                src = mains.get(nm)
                if src is None:
                    v44b.append(f'{cap}: FROM「{nm[:32]}」在主 spec 中不存在')
                else:
                    outh = src - historical
                    if outh:
                        v44b.append(f'{cap}:「{nm[:32]}」FRID ∉ historical: {sorted(outh)}')
                    addressed |= src
            continue
        if ln.startswith('### Requirement:'):
            nm = ln[len('### Requirement:'):].strip()
            nx = L[i+1].strip() if i + 1 < len(L) else ''
            has = bool(SRC_RE.match(nx))
            ids = set(re.findall(FRID, nx)) if has else set()
            if op == 'REMOVED':
                # REMOVED 块不带 Sources，从主 spec 同名 Requirement 反查（契约二）
                src = mains.get(nm)
                if src is None:
                    v44a.append(f'{cap}:「{nm[:32]}」在主 spec 中不存在')
                else:
                    still = src - deprecated
                    if still:
                        v44a.append(f'{cap}:「{nm[:32]}」移除仍 active 的 FRID: {sorted(still)}')
                    addressed |= src
                continue
            if op is None:
                noop_blocks.append(f'{cap}: {nm[:32]}')
            n_req += 1
            if not has:
                badsrc.append(f'{cap}: {nm[:36]}'); continue
            if op == 'MODIFIED':
                msrc = mains.get(nm)
                if msrc is None:
                    v43.append(f'{cap} MODIFIED「{nm[:30]}」主 spec 无同名 Requirement')
                    addressed |= ids
                else:
                    dropped = msrc - ids
                    if dropped:
                        v43.append(f'{cap} MODIFIED「{nm[:30]}」删除了既有 Sources: {sorted(dropped)}')
                    outh = (ids & msrc) - historical
                    if outh:
                        v43.append(f'{cap} MODIFIED「{nm[:30]}」沿袭 ID ∉ historical: {sorted(outh)}')
                    badn = (ids - msrc) - (active & included)
                    if badn:
                        v43.append(f'{cap} MODIFIED「{nm[:30]}」新增 ID 越界: {sorted(badn)}')
                    # 契约三：historical_exempt = main_sources − Covered-FRIDs
                    addressed |= ids - (msrc - cov_declared)
            else:  # ADDED（含无小节头的散块，从严按 ADDED 判）
                bad = ids - (active & included)
                if bad:
                    v43.append(f'{cap} ADDED「{nm[:30]}」越界: {sorted(bad)}')
                addressed |= ids

if noop_blocks:
    warn('V4.1', f'散 Requirement 无操作小节头（已按 ADDED 从严判定）: {noop_blocks}')
ok('V4.1', f'{n_req} 条 ADDED/MODIFIED Requirement 均有合法 Sources 行') if not badsrc \
    else err('V4.1', f'缺失/非法: {badsrc}')
ok('V4.2', 'Sources ID 类型全部合法（FRID）') if not badsrc else err('V4.2', '见 V4.1')
ok('V4.3', 'ADDED/MODIFIED 分场景判定全部通过') if not v43 else err('V4.3', f'{v43}')
if not ({'REMOVED', 'RENAMED'} & ops_seen):
    ok('V4.4', '本 change 无 REMOVED/RENAMED，判定不适用')
else:
    if 'REMOVED' in ops_seen:
        ok('V4.4a', 'REMOVED 触达 FRID 全部 ⊆ deprecated') if not v44a else err('V4.4a', f'{v44a}')
    if 'RENAMED' in ops_seen:
        ok('V4.4b', 'RENAMED 触达 FRID 全部 ∈ historical') if not v44b else err('V4.4b', f'{v44b}')

extra, missing = addressed - cov_declared, cov_declared - addressed
ok('V4.5', 'addressed ⊆ Covered-FRIDs') if not extra else warn('V4.5', f'范围蔓延（需人裁决）: {sorted(extra)}')
ok('V4.6', 'Covered-FRIDs ⊆ addressed') if not missing else err('V4.6', f'漏做: {sorted(missing)}')

# V4.8 design.md 依据标注的引用完整性（幽灵 ERROR / superseded WARNING）
design_p = os.path.join(CHDIR, 'design.md')
if os.path.isfile(design_p):
    DT = open(design_p, encoding='utf-8').read()
    cites = set(re.findall(r'依据:\s*((?:A?DEC)-[A-Z][A-Z0-9_]*-\d{3})', DT))
    ghosts, superseded_cited = [], []
    initiative_dec = glob.glob(os.path.join(R, 'docs/product/initiatives/*/decisions'))
    arch_dec = os.path.join(R, 'docs/architecture/decisions')
    for cid in sorted(cites):
        dirs = [arch_dec] if cid.startswith('ADEC-') else initiative_dec
        hits = [p for d in dirs for p in glob.glob(os.path.join(d, cid + '*.md'))]
        if not hits:
            ghosts.append(cid)
        else:
            body = open(hits[0], encoding='utf-8').read()
            # [ \t]* 而非 \s*：\s 含换行，会把空的 superseded-by: 误判为已填
            m = re.search(r'^(?:status:[ \t]*superseded|superseded-by:[ \t]*\S)', body, re.M)
            if m: superseded_cited.append(cid)
    if ghosts: err('V4.8', f'幽灵依据（决策不存在）: {ghosts}')
    elif not cites: ok('V4.8', 'design.md 无依据标注（无可检项）')
    else: ok('V4.8', f'{len(cites)} 条依据标注全部真实存在')
    if superseded_cited: warn('V4.8', f'引用了已 superseded 的决策: {superseded_cited}')

# V4.9 源码依据引用完整性（V4.8 的 source 延伸）——只查引用完整性，
# 不查技术正确性；两时机都跑，pre-apply 常为 0，必须报数（零对象≠零发现）。
V49_SKIP = {'.git', 'docs', 'openspec', 'node_modules', 'dist', '.claude',
            '__pycache__', '.valkyrja-backup', 'coverage'}
code_cites, scanned49 = {}, 0
for base9, dirs9, files9 in os.walk(R):
    dirs9[:] = [d for d in dirs9 if d not in V49_SKIP]
    for fn9 in files9:
        p9 = os.path.join(base9, fn9)
        try:
            if os.path.getsize(p9) > 1_000_000:
                continue
            tx9 = open(p9, encoding='utf-8').read()
        except (UnicodeDecodeError, OSError):
            continue
        scanned49 += 1
        for cid9 in re.findall(r'依据[:：]?\s*((?:A?DEC)-[A-Z][A-Z0-9_]*-\d{3})', tx9):
            code_cites.setdefault(cid9, os.path.relpath(p9, R))
_init_dec9 = glob.glob(os.path.join(R, 'docs/product/initiatives/*/decisions'))
_arch_dec9 = os.path.join(R, 'docs/architecture/decisions')
ghosts9, sup9 = [], []
for cid9, where9 in sorted(code_cites.items()):
    dirs_ = [_arch_dec9] if cid9.startswith('ADEC-') else _init_dec9
    hits9 = [p for d in dirs_ for p in glob.glob(os.path.join(d, cid9 + '*.md'))]
    if not hits9:
        ghosts9.append(f'{cid9}（{where9}）')
    elif re.search(r'^(?:status:[ \t]*superseded|superseded-by:[ \t]*\S)',
                   open(hits9[0], encoding='utf-8').read(), re.M):
        sup9.append(f'{cid9}（{where9}）')
if ghosts9:
    err('V4.9', f'源码幽灵依据: {ghosts9}')
else:
    ok('V4.9', f'源码依据 {len(code_cites)} 条全部真实存在（扫描 {scanned49} 个文件）')
if sup9:
    warn('V4.9', f'源码引用已 superseded 的决策: {sup9}')

meta = os.path.join(CHDIR, '.openspec.yaml')
MT = open(meta, encoding='utf-8').read() if os.path.isfile(meta) else ''
if re.search(r'^skip_specs:\s*true', MT, re.M):
    if CH in S.get('例外记录', ''): ok('V4.7', 'skip_specs 已有基线例外裁决')
    else: err('V4.7', 'skip_specs: true 但基线例外记录中无裁决')
else: ok('V4.7', '未使用 skip_specs')

# ---------- V5 委托原生 ----------
if SKIP_CLI:
    ok('V5.1', '跳过（--skip-cli 夹具模式，未跑 validate）')
    ok('V5.2', '跳过（--skip-cli）')
else:
    rc, out, _ = sh('openspec', 'validate', CH, '--type', 'change', '--strict', '--json', cwd=R)
    try:
        it = json.loads(out)['items'][0]
        ok('V5.1', 'openspec validate --strict 通过') if it['valid'] else err('V5.1', f"validate 失败: {it['issues']}")
    except Exception:
        err('V5.1', 'validate 输出无法解析')

    rc, out, _ = sh('openspec', 'status', '--change', CH, '--json', cwd=R)
    try:
        d = json.loads(out)
        need = d.get('applyRequires') or []
        st = {a['id']: a['status'] for a in d.get('artifacts', [])}
        miss2 = [a for a in st if st[a] not in ('done', 'skipped')]
        ok('V5.2', f"required artifacts 齐备（applyRequires={need}）") if not miss2 \
            else err('V5.2', f'未完成 artifact: {miss2}')
    except Exception:
        err('V5.2', 'status 输出无法解析')

# ---------- 报告 ----------
print(f"\n{'='*62}\ntrace(pre-apply)  change = {CH}\n{'='*62}")
for l in OK: print(f"  ✓ {l}")
for l in W: print(f"  ! {l}")
for l in E: print(f"  ✗ {l}")
print(f"{'-'*62}")
print(f"  通过 {len(OK)} / 警告 {len(W)} / 错误 {len(E)}")
print(f"  放行结论：{'✗ 不得放行（存在 ERROR）' if E else '✓ 放行' + ('（含警告，须人裁决并记入例外记录）' if W else '')}")
sys.exit(1 if E else 0)
