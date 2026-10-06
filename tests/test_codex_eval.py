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
                self.assertIn(policy, {'read-only', 'any', 'no-adec', 'no-governance'})
        self.assertEqual(RUNNER.policy_failures('read-only', []), [])
        self.assertTrue(RUNNER.policy_failures('read-only', ['README.md']))
        self.assertEqual(RUNNER.policy_failures('any', ['docs/product/initiatives/demo/STATUS.md']), [])
        self.assertTrue(RUNNER.policy_failures('no-adec', ['docs/architecture/decisions/ADEC-DEMO-001.md']))
        self.assertEqual(RUNNER.policy_failures('no-adec', ['docs/architecture/discussions/ADISC-DEMO-001.md']), [])
        self.assertEqual(RUNNER.policy_failures('no-governance', ['docs/login-requirements.md']), [])
        self.assertTrue(RUNNER.policy_failures('no-governance', ['docs/product/initiatives/login/STATUS.md']))

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
