"""Verify Codex event grading without making model calls."""

import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('codex_eval', ROOT / 'evals/run_codex.py')
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def event(command, output='', exit_code=0, kind='item.completed'):
    return {'type': kind, 'item': {'type': 'command_execution', 'command': command,
                                  'aggregated_output': output, 'exit_code': exit_code}}


class EvalTests(unittest.TestCase):
    def grade_view(self, root, changed, base='prd/releases/v1.0.md', unreflected=()):
        return RUNNER.policy_failures('view-only', changed, root, view_expectation={
            'initiative': 'docs/product/initiatives/rec',
            'base': base,
            'unreflected': unreflected,
            'output': 'docs/product/views/rec.md',
        })

    def write_file(self, root, path, text):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return target

    def test_successful_skill_read_is_evidence(self):
        output = '---\nname: valkyrja-spec\ndescription: example\n---\n# Body\n'
        self.assertEqual(RUNNER.loaded_skills([event('cat .agents/skills/valkyrja-spec/SKILL.md', output)]),
                         ['valkyrja-spec'])

    def test_echo_path_and_started_or_failed_reads_are_not_evidence(self):
        output = '---\nname: valkyrja-spec\ndescription: example\n---\n'
        events = [event('echo .agents/skills/valkyrja-spec/SKILL.md', output),
                  event('cat .agents/skills/valkyrja-spec/SKILL.md', output, exit_code=1),
                  event('cat .agents/skills/valkyrja-spec/SKILL.md', output, kind='item.started'),
                  event('cat .agents/skills/valkyrja-spec/SKILL.md', 'No such file')]
        self.assertEqual(RUNNER.loaded_skills(events), [])

    def test_prompts_reuse_existing_cases(self):
        for case in RUNNER.CASES:
            self.assertTrue(RUNNER.read_prompt(case))

    def test_view_cases_have_explicit_fixture_expectations(self):
        cases = {case for case, (_, _, policy) in RUNNER.CASES.items() if policy == 'view-only'}
        self.assertEqual(cases, set(RUNNER.VIEW_EXPECTATIONS))

    def test_view_fixture_expectations_and_claude_regexes_match_sources(self):
        for case, expectation in RUNNER.VIEW_EXPECTATIONS.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                subprocess.run(['bash', str(ROOT / 'evals' / case / 'scaffold.sh')],
                               cwd=root, check=True, capture_output=True, text=True)
                initiative = root / expectation['initiative']
                base = (initiative / expectation['base']).read_text()
                cited = set(re.findall(r'(?m)^- (DEC-[A-Z0-9_]+-\d{3})\b', base))
                pending = set(expectation['unreflected'])
                body = '\n'.join(RUNNER.requirement_lines(base))
                decision_bodies = {}
                for dec in cited | pending:
                    source = (initiative / 'decisions' / (dec + '.md')).read_text()
                    section = re.search(r'(?ms)^## Decision\n(.*?)(?=^## |\Z)', source)
                    self.assertIsNotNone(section)
                    decision_bodies[dec] = section.group(1).strip()
                    body += '\n' + dec + '\n' + decision_bodies[dec]
                view = self.write_file(root, expectation['output'],
                                       '> 阅读稿，不作为需求依据。\n未发布草稿\n' + body)
                changed = [expectation['output']]
                self.assertEqual(RUNNER.policy_failures('view-only', changed, root, expectation), [])
                yaml = (ROOT / 'evals' / case / 'case.yaml').read_text()
                patterns = re.findall(r"(?m)^    pattern: '([^']+)'$", yaml)
                self.assertTrue(patterns)
                for pattern in patterns:
                    self.assertRegex(view.read_text(), pattern)
                # Both hosts must reject a pending DEC whose ID remains but body is absent.
                for dec in pending:
                    incomplete = view.read_text().replace(decision_bodies[dec], '')
                    view.write_text(incomplete)
                    self.assertTrue(RUNNER.policy_failures('view-only', changed, root, expectation))
                    self.assertTrue(any(not re.search(pattern, incomplete) for pattern in patterns))

    def test_write_policies_grade_only_observable_effects(self):
        for case, (_, _, policy) in RUNNER.CASES.items():
            with self.subTest(case=case):
                self.assertIn(policy, {'read-only', 'any', 'no-adec', 'no-governance', 'view-only',
                                       'arch-view-only'})
        self.assertEqual(RUNNER.policy_failures('read-only', []), [])
        self.assertTrue(RUNNER.policy_failures('read-only', ['README.md']))
        self.assertEqual(RUNNER.policy_failures('any', ['docs/product/initiatives/demo/STATUS.md']), [])
        self.assertTrue(RUNNER.policy_failures('no-adec', ['docs/architecture/decisions/ADEC-DEMO-001.md']))
        self.assertEqual(RUNNER.policy_failures('no-adec', ['docs/architecture/discussions/ADISC-DEMO-001.md']), [])
        self.assertEqual(RUNNER.policy_failures('no-governance', ['docs/login-requirements.md']), [])
        self.assertTrue(RUNNER.policy_failures('no-governance', ['docs/product/initiatives/login/STATUS.md']))

    def test_view_policy_requires_verbatim_requirements_and_header(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release = root / 'docs/product/initiatives/rec/prd/releases/v1.0.md'
            release.parent.mkdir(parents=True)
            release.write_text('# PRD\n\n## REQ-REC-001\n\n分段不超过 60 分钟。\n\nSources:\n- RN-REC-001\n'
                               '\n## Out of Scope\n\n- 转文字\n')
            view = root / 'docs/product/views/rec.md'
            view.parent.mkdir(parents=True)
            changed = ['docs/product/views/rec.md']
            view.write_text('> 阅读稿，不作为需求依据。\n\n> 分段不超过 60 分钟。\n')
            self.assertEqual(self.grade_view(root, changed), [])
            view.write_text('> 阅读稿，不作为需求依据。\n\n> 分段不超过一小时。\n')
            self.assertTrue(self.grade_view(root, changed))
            view.write_text('> 分段不超过 60 分钟。\n')
            self.assertTrue(self.grade_view(root, changed))
            self.assertTrue(self.grade_view(root, changed + ['docs/product/initiatives/rec/STATUS.md']))
            self.assertTrue(self.grade_view(root, []))

    def test_view_policy_checks_decisions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initiative = root / 'docs/product/initiatives/rec'
            (initiative / 'prd/releases').mkdir(parents=True)
            (initiative / 'decisions').mkdir()
            (initiative / 'prd/releases/v1.0.md').write_text(
                '---\nround: 1\n---\n\n## REQ-REC-001\n\n分段不超过 60 分钟。\n\nSources:\n- DEC-REC-001\n')

            def decision(name, round_, text, extra=''):
                (initiative / 'decisions' / (name + '.md')).write_text(
                    '---\nid: ' + name + '\nround: ' + round_ + '\nstatus: accepted\n' + extra +
                    '---\n\n# ' + name + '\n\n## Decision\n\n' + text + '\n\n## Context\n\n背景。\n')

            decision('DEC-REC-001', '1', '按 60 分钟切分，不做整段压缩。')
            decision('DEC-REC-002', '2', '下载须经主持人授权。')
            decision('DEC-REC-003', '2', '视觉基线为原型 v2。', 'frid-impact: none\n')
            view = root / 'docs/product/views/rec.md'
            view.parent.mkdir(parents=True)
            changed = ['docs/product/views/rec.md']
            base = '> 阅读稿，不作为需求依据。\n\n> 分段不超过 60 分钟。\n'
            pending = 'DEC-REC-002 下载须经主持人授权。\n'
            view.write_text(base + '按 60 分钟切分，不做整段压缩。\n' + pending)
            self.assertEqual(self.grade_view(root, changed, unreflected=('DEC-REC-002',)), [])
            view.write_text(base + '按一小时切分。\n' + pending)
            self.assertTrue(self.grade_view(root, changed, unreflected=('DEC-REC-002',)))
            view.write_text(base + '按 60 分钟切分，不做整段压缩。\nDEC-REC-002\n')
            self.assertTrue(self.grade_view(root, changed, unreflected=('DEC-REC-002',)))
            view.write_text(base + '按 60 分钟切分，不做整段压缩。\n')
            self.assertTrue(self.grade_view(root, changed, unreflected=('DEC-REC-002',)))

    def test_view_checks_only_the_fixture_selected_release_and_initiative(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prefix = 'docs/product/initiatives/'
            self.write_file(root, prefix + 'rec/prd/releases/v1.0.md',
                            '## REQ-REC-001\n\n分段不超过 60 分钟。\nSources:\n- RN-REC-001\n')
            self.write_file(root, prefix + 'rec/prd/releases/v1.1.md',
                            '## REQ-REC-001\n\n分段不超过 30 分钟。\nSources:\n- RN-REC-001\n')
            self.write_file(root, prefix + 'other/prd/releases/v1.0.md',
                            '---\nround: 10\n---\n## REQ-OTHER-001\n\n另一项目的需求。\nSources:\n- DEC-OTHER-001\n')
            self.write_file(root, prefix + 'other/decisions/DEC-OTHER-001.md',
                            '---\nstatus: accepted\nround: 11\n---\n## Decision\n\n另一项目的决定。\n')
            self.write_file(root, 'docs/product/views/rec.md',
                            '> 阅读稿，不作为需求依据。\n\n分段不超过 30 分钟。\n')
            self.assertEqual(self.grade_view(root, ['docs/product/views/rec.md'],
                                            base='prd/releases/v1.1.md'), [])

    def test_current_draft_body_is_checked_even_with_no_releases(self):
        for has_release in (False, True):
            with self.subTest(has_release=has_release), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.write_file(root, 'docs/product/initiatives/rec/prd/current.md',
                                '## REQ-REC-001\n\n分段不超过 30 分钟。\nSources:\n- RN-REC-001\n')
                if has_release:
                    self.write_file(root, 'docs/product/initiatives/rec/prd/releases/v1.0.md',
                                    '## REQ-REC-001\n\n分段不超过 60 分钟。\nSources:\n- RN-REC-001\n')
                view = self.write_file(root, 'docs/product/views/rec.md',
                                       '> 阅读稿，不作为需求依据。\n\n分段不超过 30 分钟。\n')
                changed = ['docs/product/views/rec.md']
                self.assertEqual(self.grade_view(root, changed, base='prd/current.md'), [])
                view.write_text('> 阅读稿，不作为需求依据。\n\n分段不超过 60 分钟。\n')
                self.assertTrue(self.grade_view(root, changed, base='prd/current.md'))

    def test_other_initiative_round_cannot_hide_a_pending_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_file(root, 'docs/product/initiatives/rec/prd/releases/v1.0.md',
                            '---\nround: 1\n---\n## REQ-REC-001\n\n分段不超过 60 分钟。\nSources:\n- RN-REC-001\n')
            self.write_file(root, 'docs/product/initiatives/other/prd/releases/v1.0.md',
                            '---\nround: 10\n---\n## REQ-OTHER-001\n\n另一项目的需求。\nSources:\n- RN-OTHER-001\n')
            self.write_file(root, 'docs/product/initiatives/rec/decisions/DEC-REC-002.md',
                            '---\nstatus: accepted\nround: 2\n---\n## Decision\n\n下载须经主持人授权。\n')
            view = self.write_file(root, 'docs/product/views/rec.md',
                                   '> 阅读稿，不作为需求依据。\n\n分段不超过 60 分钟。\n')
            changed = ['docs/product/views/rec.md']
            self.assertTrue(self.grade_view(root, changed, unreflected=('DEC-REC-002',)))
            view.write_text(view.read_text() + '\nDEC-REC-002 下载须经主持人授权。\n')
            self.assertEqual(self.grade_view(root, changed, unreflected=('DEC-REC-002',)), [])

    def test_no_prd_view_still_requires_the_expected_decision_body(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_file(root, 'docs/product/initiatives/rec/decisions/DEC-REC-002.md',
                            '---\nstatus: accepted\nround: 1\n---\n## Decision\n\n下载须经主持人授权。\n')
            view = self.write_file(root, 'docs/product/views/rec.md',
                                   '> 阅读稿，不作为需求依据。\n> 基于：尚无 PRD\n\nDEC-REC-002\n')
            changed = ['docs/product/views/rec.md']
            self.assertTrue(self.grade_view(root, changed, base=None, unreflected=('DEC-REC-002',)))
            view.write_text(view.read_text() + '\n下载须经主持人授权。\n')
            self.assertEqual(self.grade_view(root, changed, base=None, unreflected=('DEC-REC-002',)), [])

    def test_view_does_not_require_superseded_decisions_as_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_file(root, 'docs/product/initiatives/rec/prd/current.md',
                            '## REQ-REC-001\n\n分段不超过 30 分钟。\nSources:\n- DEC-REC-003\n')
            self.write_file(root, 'docs/product/initiatives/rec/decisions/DEC-REC-002.md',
                            '---\nstatus: superseded\nsuperseded-by: DEC-REC-003\nround: 2\n---\n'
                            '## Decision\n\n分段为 60 分钟。\n')
            self.write_file(root, 'docs/product/initiatives/rec/decisions/DEC-REC-003.md',
                            '---\nstatus: accepted\nround: 2\n---\n## Decision\n\n分段为 30 分钟。\n')
            self.write_file(root, 'docs/product/views/rec.md',
                            '> 阅读稿，不作为需求依据。\n\n分段不超过 30 分钟。\n分段为 30 分钟。\n')
            self.assertEqual(self.grade_view(root, ['docs/product/views/rec.md'], base='prd/current.md'), [])

    def test_released_prd_keeps_the_original_cited_decision_even_if_superseded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_file(root, 'docs/product/initiatives/rec/prd/releases/v1.0.md',
                            '## REQ-REC-001\n\n分段不超过 60 分钟。\nSources:\n- DEC-REC-001\n')
            self.write_file(root, 'docs/product/initiatives/rec/decisions/DEC-REC-001.md',
                            '---\nstatus: superseded\nsuperseded-by: DEC-REC-002\n---\n'
                            '## Decision\n\n分段为 60 分钟。\n')
            view = self.write_file(root, 'docs/product/views/rec.md',
                                   '> 阅读稿，不作为需求依据。\n\n分段不超过 60 分钟。\n'
                                   '替代历史：分段为 60 分钟。\n')
            changed = ['docs/product/views/rec.md']
            self.assertEqual(self.grade_view(root, changed), [])
            view.write_text('> 阅读稿，不作为需求依据。\n\n分段不超过 60 分钟。\n')
            self.assertTrue(self.grade_view(root, changed))

    def test_view_missing_fixture_base_or_expectations_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_file(root, 'docs/product/views/rec.md', '> 阅读稿，不作为需求依据。\n')
            changed = ['docs/product/views/rec.md']
            self.assertTrue(self.grade_view(root, changed))
            self.assertTrue(RUNNER.policy_failures('view-only', changed, root))

    def test_view_cannot_satisfy_the_expected_file_by_combining_other_views(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_file(root, 'docs/product/initiatives/rec/prd/releases/v1.0.md',
                            '## REQ-REC-001\n\n分段不超过 60 分钟。\nSources:\n- RN-REC-001\n')
            self.write_file(root, 'docs/product/views/rec.md', '> 阅读稿，不作为需求依据。\n')
            self.write_file(root, 'docs/product/views/other.md', '分段不超过 60 分钟。\n')
            self.assertTrue(self.grade_view(root, ['docs/product/views/rec.md', 'docs/product/views/other.md']))

    def arch_view_from_sources(self, root, expectation):
        """Complete verbatim fixture content, independent of the grader's selected snippets."""
        body = ['> **阅读稿，不作为技术依据。**']
        for number in (1, 2, 4, 5):
            source = root / f'docs/architecture/decisions/ADEC-DEMO_APP-{number:03}.md'
            body.extend(RUNNER.section_lines(source.read_text(), 'Decision'))
        contract = (root / 'docs/architecture/contracts/content-package.md').read_text()
        for heading in ('形状', '兼容规则', 'Changelog'):
            body.extend(RUNNER.section_lines(contract, heading))
        convention = (root / 'docs/architecture/conventions/conv-api-envelope.md').read_text()
        body.extend(['## 必须遵守的约定', 'API 响应信封与语义约定'])
        body.extend(re.findall(r'(?m)^## (.+)$', convention))
        body.append('## 已有的公共对象（先查这里，别重写）')
        inventory = (root / 'docs/architecture/inventory.md').read_text()
        body.extend(RUNNER.section_lines(inventory, '已有公共对象'))
        discussion = (root / 'docs/architecture/discussions/ADISC-DEMO_APP-003.md').read_text()
        body.extend(re.findall(r'(?m)^\*\*应回流上游\*\*：(.*)$', discussion))
        backlog = (root / 'docs/architecture/backlog.md').read_text()
        body.extend(re.findall(r'(?m)^### 1\. (.+)$', backlog))
        body.extend(re.findall(r'(?m)^\*\*触发条件\*\*：(.*)$', backlog))
        return self.write_file(root, expectation['output'], '\n'.join(body) + '\n')

    def test_arch_view_rejects_missing_or_changed_fixture_content(self):
        expectation = RUNNER.ARCH_VIEW_EXPECTATIONS['view-reading-arch']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['bash', str(ROOT / 'evals/view-reading-arch/scaffold.sh')],
                           cwd=root, check=True, capture_output=True, text=True)
            view = self.arch_view_from_sources(root, expectation)
            full = view.read_text()
            changes = (
                ('missing field', '| items | array | 是 | 内容条目列表，至少一条 |', ''),
                ('changed type', '| locale | string |', '| locale | integer |'),
                ('changed required flag', '| items | array | 是 |', '| items | array | 否 |'),
                ('missing version', '| 2 | 2026-09-25 | 新增可选字段 locale | 否 |', ''),
                ('missing object', '| dataclass | PageRequest | src/api/paging.py | 分页参数 |', ''),
                ('changed object path', 'src/api/paging.py', 'src/api/page.py'),
                ('appended object path suffix', 'src/api/paging.py', 'src/api/paging.py.bak'),
                ('appended object name suffix', 'PageRequest', 'PageRequestV2'),
                ('appended Chinese object suffix', 'PageRequest', 'PageRequest新版'),
                ('appended Chinese path suffix', 'src/api/paging.py', 'src/api/paging.py新版'),
                ('missing group', '### 共享内核', ''),
                ('missing convention heading', '统一信封', ''),
                ('renamed convention heading', '统一信封', '统一信封（废弃）'),
                ('prefixed Chinese convention heading', '统一信封', '旧统一信封'),
                ('missing last convention heading', '\n错误码\n', '\n'),
                ('reordered convention headings', '统一信封\n状态码与业务失败', '状态码与业务失败\n统一信封'),
                ('reordered fields',
                 '| items | array | 是 | 内容条目列表，至少一条 |\n| locale | string | 否 | 语言代码，缺省为 zh-CN |',
                 '| locale | string | 否 | 语言代码，缺省为 zh-CN |\n| items | array | 是 | 内容条目列表，至少一条 |'),
                ('missing backlog candidate', '所有对外接口统一限流', ''),
            )
            for label, original, replacement in changes:
                with self.subTest(change=label):
                    self.assertIn(original, full)
                    view.write_text(full.replace(original, replacement))
                    self.assertTrue(RUNNER.policy_failures(
                        'arch-view-only', [expectation['output']], root, expectation))
            for formatted in (
                '`统一信封`、`状态码与业务失败`、`错误码`',
                '「统一信封」「状态码与业务失败」「错误码」',
                '（统一信封）（状态码与业务失败）（错误码）',
                '|统一信封|状态码与业务失败|错误码|',
                '统一信封/状态码与业务失败/错误码',
                '[统一信封](../conventions/conv-api-envelope.md#统一信封)、'
                '[状态码与业务失败](../conventions/conv-api-envelope.md#状态码与业务失败)、'
                '[错误码](../conventions/conv-api-envelope.md#错误码)',
            ):
                with self.subTest(valid_format=formatted):
                    view.write_text(full.replace('统一信封\n状态码与业务失败\n错误码', formatted))
                    self.assertEqual(RUNNER.policy_failures(
                        'arch-view-only', [expectation['output']], root, expectation), [])
                    yaml = (ROOT / 'evals/view-reading-arch/case.yaml').read_text()
                    for pattern in re.findall(r"(?m)^    pattern: '([^']+)'$", yaml):
                        self.assertRegex(view.read_text(), pattern)

    def test_arch_view_edge_fixtures_and_write_policies(self):
        for case in ('view-reading-arch-symlink', 'view-reading-arch-resolved'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                subprocess.run(['bash', str(ROOT / 'evals' / case / 'scaffold.sh')],
                               cwd=root, check=True, capture_output=True, text=True)
                if case.endswith('symlink'):
                    output = root / 'docs/architecture/views/architecture.md'
                    self.assertTrue(output.parent.is_symlink())
                    self.assertEqual(output.resolve(), (root / 'docs/architecture/decisions/architecture.md').resolve())
                    self.assertEqual(RUNNER.CASES[case][2], 'read-only')
                    self.assertEqual(RUNNER.policy_failures('read-only', []), [])
                    self.assertTrue(RUNNER.policy_failures('read-only', ['docs/architecture/decisions/architecture.md']))
                else:
                    discussion = (root / 'docs/architecture/discussions/ADISC-DEMO_APP-003.md').read_text()
                    self.assertIn('**应回流上游**：', discussion)
                    self.assertIn('该回流事项已关闭', discussion)
                    self.assertIn('DEC-DEMO_PRODUCT-001', discussion)
                    self.assertIn('**应回流上游**: ADISC-DEMO_APP-003',
                                  (root / 'docs/architecture/STATUS.md').read_text())
                    self.assertTrue((root / 'docs/product/initiatives/demo-product/decisions/DEC-DEMO_PRODUCT-001.md').is_file())
                    expectation = RUNNER.ARCH_VIEW_EXPECTATIONS[case]
                    view = self.arch_view_from_sources(root, expectation)
                    # A closed historical quotation may be omitted without failing fidelity checks.
                    view.write_text(view.read_text().replace(
                        '上传文件的保留期限对用户可见，属于产品侧问题，需回流上游确定。', ''))
                    self.assertEqual(RUNNER.policy_failures(
                        'arch-view-only', [expectation['output']], root, expectation), [])

    def test_arch_view_cases_have_explicit_fixture_expectations(self):
        cases = {case for case, (_, _, policy) in RUNNER.CASES.items() if policy == 'arch-view-only'}
        self.assertEqual(cases, set(RUNNER.ARCH_VIEW_EXPECTATIONS))

    @unittest.skipUnless(shutil.which('node'), 'Node is needed to check Claude JavaScript regexes')
    def test_arch_view_regexes_work_in_claude_javascript_engine(self):
        script = (
            "const data = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
            "const regexes = data.patterns.map(pattern => new RegExp(pattern));"
            "for (const sample of data.samples) {"
            "if (regexes.every(regex => regex.test(sample.text)) !== sample.matches) "
            "throw new Error('Unexpected fixture match: ' + sample.name); }"
        )
        for case, expectation in RUNNER.ARCH_VIEW_EXPECTATIONS.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                subprocess.run(['bash', str(ROOT / 'evals' / case / 'scaffold.sh')],
                               cwd=root, check=True, capture_output=True, text=True)
                full = self.arch_view_from_sources(root, expectation).read_text()
                yaml = (ROOT / 'evals' / case / 'case.yaml').read_text()
                patterns = re.findall(r"(?m)^    pattern: '([^']+)'$", yaml)
                self.assertTrue(patterns)
                linked = full.replace('统一信封\n状态码与业务失败\n错误码',
                                      '[统一信封](#统一信封)、[状态码与业务失败](#状态码与业务失败)、[错误码](#错误码)')
                samples = [
                    {'name': 'verbatim', 'text': full, 'matches': True},
                    {'name': 'linked headings', 'text': linked, 'matches': True},
                    {'name': 'quoted headings', 'text': full.replace(
                        '统一信封\n状态码与业务失败\n错误码', '「统一信封」「状态码与业务失败」「错误码」'), 'matches': True},
                    {'name': 'changed punctuation', 'text': full.replace(
                        '新增可选字段不算破坏性变更；', '新增可选字段不算破坏性变更;'), 'matches': False},
                ]
                if case == 'view-reading-arch':
                    for original, changed in (('统一信封', '旧统一信封'),
                                              ('PageRequest', 'PageRequest新版'),
                                              ('src/api/paging.py', 'src/api/paging.py新版')):
                        samples.append({'name': changed, 'text': full.replace(original, changed),
                                        'matches': False})
                result = subprocess.run(['node', '-e', script],
                                        input=json.dumps({'patterns': patterns, 'samples': samples}),
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_arch_view_fixture_expectations_and_claude_regexes_match_sources(self):
        for case, expectation in RUNNER.ARCH_VIEW_EXPECTATIONS.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                subprocess.run(['bash', str(ROOT / 'evals' / case / 'scaffold.sh')],
                               cwd=root, check=True, capture_output=True, text=True)
                view = self.arch_view_from_sources(root, expectation)
                changed = [expectation['output']]
                self.assertEqual(RUNNER.policy_failures('arch-view-only', changed, root, expectation), [])
                yaml = (ROOT / 'evals' / case / 'case.yaml').read_text()
                patterns = re.findall(r"(?m)^    pattern: '([^']+)'$", yaml)
                self.assertTrue(patterns)
                for pattern in patterns:
                    self.assertRegex(view.read_text(), pattern)
                # Half-width punctuation in a full-width source line must fail on both hosts.
                quoted = view.read_text()
                halfwidth = quoted.replace('新增可选字段不算破坏性变更；', '新增可选字段不算破坏性变更;')
                view.write_text(halfwidth)
                self.assertTrue(RUNNER.policy_failures('arch-view-only', changed, root, expectation))
                self.assertTrue(any(not re.search(pattern, halfwidth) for pattern in patterns))

    def test_arch_view_policy_fails_closed(self):
        expectation = RUNNER.ARCH_VIEW_EXPECTATIONS['view-reading-arch']
        output = expectation['output']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['bash', str(ROOT / 'evals/view-reading-arch/scaffold.sh')],
                           cwd=root, check=True, capture_output=True, text=True)
            view = self.arch_view_from_sources(root, expectation)
            full = view.read_text()
            self.assertTrue(RUNNER.policy_failures('arch-view-only', [], root, expectation))
            self.assertTrue(RUNNER.policy_failures('arch-view-only', [output, 'docs/architecture/STATUS.md'],
                                                   root, expectation))
            self.assertTrue(RUNNER.policy_failures('arch-view-only', [output], root, None))
            view.write_text(full.replace('不作为技术依据', ''))
            self.assertTrue(RUNNER.policy_failures('arch-view-only', [output], root, expectation))
            view.write_text(full.replace('缓存层改用 Redis 7', '缓存层改用 Redis'))
            self.assertTrue(RUNNER.policy_failures('arch-view-only', [output], root, expectation))
            view.write_text(full)
            (root / 'docs/architecture/backlog.md').write_text('# 规则候选\n')
            self.assertTrue(RUNNER.policy_failures('arch-view-only', [output], root, expectation))

    def test_snapshot_includes_skill_tree_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / '.agents/skills/test/SKILL.md'
            skill.parent.mkdir(parents=True)
            skill.write_text('original')
            before = RUNNER.snapshot(root)
            skill.write_text('changed')
            self.assertNotEqual(before, RUNNER.snapshot(root))

    def test_snapshot_detects_retargeted_or_replaced_directory_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'decisions').mkdir()
            (root / 'contracts').mkdir()
            link = root / 'views'
            link.symlink_to('decisions', target_is_directory=True)
            before = RUNNER.snapshot(root)
            link.unlink()
            link.symlink_to('contracts', target_is_directory=True)
            self.assertNotEqual(before, RUNNER.snapshot(root))
            link.unlink()
            link.mkdir()
            self.assertNotEqual(before, RUNNER.snapshot(root))


if __name__ == '__main__':
    unittest.main()
