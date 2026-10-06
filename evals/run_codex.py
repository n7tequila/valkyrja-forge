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
}
GOVERNANCE_ROOTS = ('docs/product/', 'docs/architecture/', 'openspec/')
VIEW_ROOT = 'docs/product/views/'
REQUIREMENT = re.compile(r'^## (?:REQ|BR|SEC|NFR)-')


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


def release_requirement_lines(workspace):
    """Requirement statement lines of every released PRD, which a reading view must quote verbatim."""
    lines = []
    for release in sorted(workspace.glob('docs/product/initiatives/*/prd/releases/*.md')):
        inside = False
        for line in release.read_text().splitlines():
            if line.startswith('## '):
                inside = bool(REQUIREMENT.match(line))
            elif inside and line.startswith('Sources:'):
                inside = False
            elif inside and line.strip():
                lines.append(line.strip())
    return lines


def frontmatter(text):
    match = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
    return match.group(1) if match else ''


def field(block, name):
    match = re.search(r'(?m)^' + name + r':[ \t]*(\S+)', block)
    return match.group(1) if match else None


def decisions(workspace):
    """Accepted DECs: id -> (round, frid-impact none?, Decision paragraph lines)."""
    found = {}
    for path in workspace.glob('docs/product/initiatives/*/decisions/DEC-*.md'):
        text = path.read_text()
        block = frontmatter(text)
        if field(block, 'status') != 'accepted':
            continue
        section = re.search(r'(?ms)^## Decision\n(.*?)(?=^## |\Z)', text)
        lines = [line.strip() for line in section.group(1).splitlines() if line.strip()] if section else []
        found[field(block, 'id') or path.stem] = (int(field(block, 'round') or 0),
                                                 bool(re.search(r'(?m)^frid-impact: none\s*$', block)), lines)
    return found


def released_context(workspace):
    """Highest released round and every DEC cited by a released PRD."""
    top, cited = 0, set()
    for release in workspace.glob('docs/product/initiatives/*/prd/releases/*.md'):
        text = release.read_text()
        top = max(top, int(field(frontmatter(text), 'round') or 0))
        cited.update(re.findall(r'(?m)^- (DEC-[A-Z0-9_]+-\d{3})\b', text))
    return top, cited


def view_failures(workspace, changed):
    views = [path for path in changed if path.startswith(VIEW_ROOT) and path.endswith('.md')]
    if not views:
        return ['no reading view was written under ' + VIEW_ROOT]
    failures = []
    if any(not path.startswith(VIEW_ROOT) for path in changed):
        failures.append('reading view changed files outside ' + VIEW_ROOT)
    text = '\n'.join((workspace / path).read_text() for path in views if (workspace / path).is_file())
    if '不作为需求依据' not in text:
        failures.append('reading view lacks the non-authority header')
    if any(line not in text for line in release_requirement_lines(workspace)):
        failures.append('reading view did not quote released requirement text verbatim')
    top, cited = released_context(workspace)
    accepted = decisions(workspace)
    if any(line not in text for dec in cited if dec in accepted for line in accepted[dec][2]):
        failures.append('reading view did not quote a cited Decision paragraph verbatim')
    unreflected = [dec for dec, (round_, exempt, _) in accepted.items() if round_ > top and not exempt]
    if any(dec not in text for dec in unreflected):
        failures.append('reading view omitted a decision made after the latest release')
    return failures


def policy_failures(policy, changed, workspace=None):
    if policy == 'read-only' and changed:
        return ['read-only routing question changed workspace files']
    if policy == 'no-adec' and any('ADEC-' in Path(path).name for path in changed):
        return ['question-tone prompt minted/changed a decision']
    if policy == 'no-governance' and any(path.startswith(GOVERNANCE_ROOTS) for path in changed):
        return ['ordinary request wrote into a governance workspace']
    if policy == 'view-only':
        return view_failures(workspace, changed)
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
        failures.extend(policy_failures(policy, changed, workspace))
        for path in changed:
            # Keep generated reading views for the human review the runner cannot automate.
            if path.startswith(VIEW_ROOT) and (workspace / path).is_file():
                shutil.copy2(workspace / path, output / (case + '--' + Path(path).name))
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
