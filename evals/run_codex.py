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
# filesystem effects: read-only, any (routing-only cases), no-adec, no-governance.
CASES = {
    'routing-spec-fires': ('valkyrja-spec', True, 'read-only'),
    'routing-spec-declines-openspec-only': ('valkyrja-spec', False, 'read-only'),
    'routing-prd-declines-unopted': ('valkyrja-prd', False, 'read-only'),
    'routing-prd-fires': ('valkyrja-prd', True, 'any'),
    'routing-prd-fires-explicit-optin': ('valkyrja-prd', True, 'any'),
    'routing-prd-declines-doc-request': ('valkyrja-prd', False, 'no-governance'),
    'constraint-arch-question-tone': ('valkyrja-arch', True, 'no-adec'),
}
GOVERNANCE_ROOTS = ('docs/product/', 'docs/architecture/', 'openspec/')


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


def policy_failures(policy, changed):
    if policy == 'read-only' and changed:
        return ['read-only routing question changed workspace files']
    if policy == 'no-adec' and any('ADEC-' in Path(path).name for path in changed):
        return ['question-tone prompt minted/changed a decision']
    if policy == 'no-governance' and any(path.startswith(GOVERNANCE_ROOTS) for path in changed):
        return ['ordinary request wrote into a governance workspace']
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
        failures.extend(policy_failures(policy, changed))
        replies = [event.get('item', {}).get('text', '') for event in events
                   if event.get('item', {}).get('type') == 'agent_message']
        report = {'case': case, 'model': model, 'passed': not failures,
                  'failures': failures, 'loaded_skills': loaded, 'changed_files': changed,
                  'reply': replies[-1] if replies else '',
                  'review_required': 'Read final reply for unconfirmed decisions or unsolicited bootstrap.'}
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
