#!/usr/bin/env python3
"""Run the existing behavioral fixtures in writable, disposable Codex workspaces.

No YAML dependency: only the single-line execution.prompt field is read. Claude's
grader definitions are deliberately not interpreted as a Codex tool API.
Filesystem effects are graded here; final replies still require human review.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
# case -> (target skill, should load it, write policy). Policies only grade observable
# filesystem effects: read-only, any (routing-only cases), no-adec, no-governance, view-only.
CASES = {
    'routing-spec-fires': ('valkyrja-spec', True, 'read-only'),
    'routing-spec-declines-openspec-only': ('valkyrja-spec', False, 'read-only'),
    'routing-prd-declines-unopted': ('valkyrja-prd', False, 'read-only'),
    'routing-prd-fires': ('valkyrja-prd', True, 'any'),
    'routing-prd-fires-explicit-optin': ('valkyrja-prd', True, 'any'),
    'routing-prd-declines-doc-request': ('valkyrja-prd', False, 'no-governance'),
    'constraint-arch-question-tone': ('valkyrja-arch', True, 'no-adec'),
    'view-reading-verbatim': ('valkyrja-prd', True, 'view-only'),
    'view-reading-current': ('valkyrja-prd', True, 'view-only'),
}
GOVERNANCE_ROOTS = ('docs/product/', 'docs/architecture/', 'openspec/')
VIEW_ROOT = 'docs/product/views/'
REQUIREMENT = re.compile(r'^## (?:REQ|BR|SEC|NFR)-')
# Fixture-specific expected artifacts, not another implementation of view's selection rules.
# Keep these explicit: an output header must not get to choose what its own grader checks.
VIEW_EXPECTATIONS = {
    'view-reading-verbatim': {
        'initiative': 'docs/product/initiatives/rec',
        'base': 'prd/releases/v1.0.md',
        'unreflected': ('DEC-REC-002',),
        'output': 'docs/product/views/rec.md',
    },
    'view-reading-current': {
        'initiative': 'docs/product/initiatives/rec',
        'base': 'prd/current.md',
        'unreflected': ('DEC-REC-004',),
        'output': 'docs/product/views/rec.md',
    },
}


def read_prompt(case):
    source = (ROOT / 'evals' / case / 'case.yaml').read_text()
    match = re.search(r'(?m)^  prompt: (.+)$', source)
    if not match:
        raise ValueError('Expected a single-line execution.prompt in ' + case)
    return match.group(1)


def snapshot(workspace):
    return {str(path.relative_to(workspace)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in workspace.rglob('*') if path.is_file()}


def loaded_skills(events):
    loaded = set()
    for event in events:
        item = event.get('item', {})
        if (event.get('type') != 'item.completed' or item.get('type') != 'command_execution'
                or item.get('exit_code') != 0):
            continue
        command = item.get('command', '')
        output = item.get('aggregated_output', '')
        for skill, _, _ in CASES.values():
            # A mentioned path or a failed read is not evidence of loading.
            if (re.search(r'\b(cat|sed|head|more|less|bat)\b', command)
                    and re.search(r'(?m)^---\nname: ' + re.escape(skill) + r'\n', output)):
                loaded.add(skill)
    return sorted(loaded)


def requirement_lines(text):
    """Requirement statement lines from the fixture's selected PRD only."""
    lines = []
    inside = False
    for line in text.splitlines():
        if line.startswith('## '):
            inside = bool(REQUIREMENT.match(line))
        elif inside and line.startswith('Sources:'):
            inside = False
        elif inside and line.strip():
            lines.append(line.strip())
    return lines


def view_failures(workspace, changed, expectation):
    if expectation is None:
        return ['reading view evaluation lacks explicit fixture expectations']
    output = expectation['output']
    if output not in changed or not (workspace / output).is_file():
        return ['no reading view was written at ' + output]
    failures = []
    if any(path != output for path in changed):
        failures.append('reading view changed files outside its expected output')
    text = (workspace / output).read_text()
    if '不作为需求依据' not in text:
        failures.append('reading view lacks the non-authority header')
    initiative = workspace / expectation['initiative']
    base = expectation['base']
    base_text = ''
    if base is not None:
        source = initiative / base
        if not source.is_file():
            return failures + ['reading view fixture base is missing: ' + base]
        base_text = source.read_text()
        if any(line not in text for line in requirement_lines(base_text)):
            failures.append('reading view did not quote selected requirement text verbatim')
    cited = set(re.findall(r'(?m)^- (DEC-[A-Z0-9_]+-\d{3})\b', base_text))
    unreflected = set(expectation['unreflected'])
    for dec in sorted(cited | unreflected):
        source = initiative / 'decisions' / (dec + '.md')
        if not source.is_file():
            failures.append('reading view fixture decision is missing: ' + dec)
            continue
        section = re.search(r'(?ms)^## Decision\n(.*?)(?=^## |\Z)', source.read_text())
        lines = [line.strip() for line in section.group(1).splitlines() if line.strip()] if section else []
        if not lines or any(line not in text for line in lines):
            failures.append('reading view did not quote Decision paragraph verbatim: ' + dec)
        if dec in unreflected and dec not in text:
            failures.append('reading view omitted an expected unreflected decision: ' + dec)
    return failures


def policy_failures(policy, changed, workspace=None, view_expectation=None):
    if policy == 'read-only' and changed:
        return ['read-only routing question changed workspace files']
    if policy == 'no-adec' and any('ADEC-' in Path(path).name for path in changed):
        return ['question-tone prompt minted/changed a decision']
    if policy == 'no-governance' and any(path.startswith(GOVERNANCE_ROOTS) for path in changed):
        return ['ordinary request wrote into a governance workspace']
    if policy == 'view-only':
        return view_failures(workspace, changed, view_expectation)
    return []


def run_case(case, model, timeout, output):
    target, should_load, policy = CASES[case]
    with tempfile.TemporaryDirectory(prefix='valk-codex-eval-') as directory:
        workspace = Path(directory)
        subprocess.run(['bash', str(ROOT / 'evals' / case / 'scaffold.sh')],
                       cwd=workspace, check=True, capture_output=True, text=True)
        subprocess.run(['bash', str(ROOT / 'scripts/install-skills.sh'),
                        '--harness', 'codex', '--project', str(workspace)],
                       check=True, capture_output=True, text=True)
        before = snapshot(workspace)
        # Ignore user config/MCP/plugin overrides, but keep the normal CLI auth.
        # User-wide instructions/skills may still be inherited by Codex itself.
        command = ['codex', 'exec', '--ephemeral', '--json', '--ignore-user-config',
                   '--ignore-rules', '--skip-git-repo-check', '--sandbox', 'workspace-write',
                   '--cd', str(workspace), '--model', model, read_prompt(case)]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, input='')
        except subprocess.TimeoutExpired as error:
            for suffix, content in (('.jsonl', error.stdout), ('.stderr', error.stderr)):
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='replace')
                (output / (case + suffix)).write_text(content or '')
            report = {'case': case, 'model': model, 'passed': False, 'error': 'timeout'}
            (output / (case + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2))
            return report
        (output / (case + '.jsonl')).write_text(result.stdout)
        (output / (case + '.stderr')).write_text(result.stderr)
        events = []
        for line in result.stdout.splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        loaded = loaded_skills(events)
        after = snapshot(workspace)
        changed = sorted(path for path in set(before) | set(after)
                         if before.get(path) != after.get(path))
        failures = []
        if result.returncode != 0 or not any(e.get('type') == 'turn.completed' for e in events):
            failures.append('Codex did not complete successfully')
        if (target in loaded) != should_load:
            failures.append('skill loading did not match the opt-in boundary')
        failures.extend(policy_failures(policy, changed, workspace, VIEW_EXPECTATIONS.get(case)))
        for path in changed:
            # Keep generated reading views for the human review the runner cannot automate.
            if path.startswith(VIEW_ROOT) and (workspace / path).is_file():
                shutil.copy2(workspace / path, output / (case + '--' + Path(path).name))
        replies = [event.get('item', {}).get('text', '') for event in events
                   if event.get('item', {}).get('type') == 'agent_message']
        report = {'case': case, 'model': model, 'passed': not failures,
                  'failures': failures, 'loaded_skills': loaded, 'changed_files': changed,
                  'reply': replies[-1] if replies else '',
                  'review_required': ('Read the generated view for invented requirements and open items '
                                      'presented as conclusions; also review the final reply.' if policy == 'view-only'
                                      else 'Read final reply for unconfirmed decisions or unsolicited bootstrap.')}
        (output / (case + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2))
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', help='Use the same model as real sessions; no stale default')
    parser.add_argument('--case', choices=sorted(CASES), action='append')
    parser.add_argument('--timeout', type=int, default=900)
    parser.add_argument('--output', type=Path, help='New directory for private transcripts; default: a temp directory')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    if args.list:
        print('\n'.join(CASES))
        return 0
    if not args.model:
        parser.error('--model is required when running cases')
    if not shutil.which('codex'):
        parser.error('codex CLI must be installed and authenticated')
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    if args.output:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False, mode=0o700)
    else:
        output = Path(tempfile.mkdtemp(prefix='valk-codex-results-'))
    os.chmod(output, 0o700)
    print('Private evidence directory: ' + str(output), flush=True)
    reports = []
    for case in args.case or CASES:
        report = run_case(case, args.model, args.timeout, output)
        reports.append(report)
        print(('PASS ' if report['passed'] else 'FAIL ') + case, flush=True)
    print('Final replies need manual review; this is not full-lifecycle verification.', flush=True)
    return 0 if all(report['passed'] for report in reports) else 1


if __name__ == '__main__':
    raise SystemExit(main())
