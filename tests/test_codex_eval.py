"""Verify Codex event grading without making model calls."""

import importlib.util
from pathlib import Path
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

    def test_write_policies_grade_only_observable_effects(self):
        for case, (_, _, policy) in RUNNER.CASES.items():
            with self.subTest(case=case):
                self.assertIn(policy, {'read-only', 'any', 'no-adec', 'no-governance', 'view-only'})
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
            self.assertEqual(RUNNER.policy_failures('view-only', changed, root), [])
            view.write_text('> 阅读稿，不作为需求依据。\n\n> 分段不超过一小时。\n')
            self.assertTrue(RUNNER.policy_failures('view-only', changed, root))
            view.write_text('> 分段不超过 60 分钟。\n')
            self.assertTrue(RUNNER.policy_failures('view-only', changed, root))
            self.assertTrue(RUNNER.policy_failures('view-only', changed + ['docs/product/initiatives/rec/STATUS.md'], root))
            self.assertTrue(RUNNER.policy_failures('view-only', [], root))

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
            view.write_text(base + '按 60 分钟切分，不做整段压缩。\nDEC-REC-002\n')
            self.assertEqual(RUNNER.policy_failures('view-only', changed, root), [])
            view.write_text(base + '按一小时切分。\nDEC-REC-002\n')
            self.assertTrue(RUNNER.policy_failures('view-only', changed, root))
            view.write_text(base + '按 60 分钟切分，不做整段压缩。\n')
            self.assertTrue(RUNNER.policy_failures('view-only', changed, root))

    def test_snapshot_includes_skill_tree_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / '.agents/skills/test/SKILL.md'
            skill.parent.mkdir(parents=True)
            skill.write_text('original')
            before = RUNNER.snapshot(root)
            skill.write_text('changed')
            self.assertNotEqual(before, RUNNER.snapshot(root))


if __name__ == '__main__':
    unittest.main()
