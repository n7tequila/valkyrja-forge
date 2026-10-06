"""Optional real-CLI integration; never mutates the user's OpenSpec profile."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('openspec'), 'OpenSpec CLI not installed')
class OpenSpecCodexTests(unittest.TestCase):
    def test_codex_install_and_bundled_trace_use_real_cli(self):
        with tempfile.TemporaryDirectory(prefix='valk-openspec-') as directory:
            workspace = Path(directory) / 'product with spaces'
            shutil.copytree(ROOT / 'tests/fixtures/repo', workspace)
            env = dict(os.environ, XDG_CONFIG_HOME=str(Path(directory) / 'config'),
                       OPENSPEC_TELEMETRY='0')

            def run(*args):
                result = subprocess.run(args, cwd=workspace, env=env,
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout

            run('openspec', 'init', '--tools', 'codex', '--profile', 'core', '--no-animation')
            official = workspace / '.agents/skills'
            self.assertEqual((official / '.openspec-target').read_text().strip(), 'codex')
            for skill in ('openspec-propose', 'openspec-apply-change', 'openspec-archive-change'):
                self.assertTrue((official / skill / 'SKILL.md').is_file(), skill)
            self.assertFalse((workspace / '.codex/prompts').exists())
            self.assertFalse((workspace / '.claude').exists())

            run('bash', str(ROOT / 'scripts/install-skills.sh'), '--harness', 'codex',
                '--project', str(workspace))
            change = workspace / 'openspec/changes/case-added'
            # Existing fixtures intentionally omit CLI planning artifacts and normative
            # wording. Complete only this temporary copy; trace collection stays intact.
            (change / 'design.md').write_text('# Design\n\nUse the existing source layout.\n')
            (change / 'tasks.md').write_text('## 1. Implementation\n\n- [x] 1.1 Add the behavior\n')
            spec = change / 'specs/cap/spec.md'
            spec.write_text(spec.read_text().replace('Sources: REQ-T-001',
                            'Sources: REQ-T-001\n\nThe system SHALL support the new behavior.', 1))
            script = official / 'valkyrja-spec/tools/trace.py'
            trace = run(sys.executable, str(script), '.', 'case-added')
            self.assertRegex(trace, r'V5\.1\s+openspec validate --strict 通过')
            self.assertRegex(trace, r'V5\.2\s+required artifacts 齐备')
            self.assertNotIn('跳过（--skip-cli', trace)
            self.assertEqual(json.loads(run('openspec', 'status', '--change', 'case-added', '--json'))
                             ['isPlanningComplete'], True)


if __name__ == '__main__':
    unittest.main()
