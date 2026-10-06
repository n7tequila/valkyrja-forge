"""Registered Codex skill names, rendered offline; never touches the user's Codex home."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ('valk', 'valk-tools')
NAME = re.compile(r'(?m)^- ((?:[a-z0-9-]+:)?[a-z0-9-]+): ')


def skill_names(plugin):
    return sorted(p.parent.name for p in (ROOT / plugin / 'skills').glob('*/SKILL.md'))


@unittest.skipUnless(shutil.which('codex'), 'Codex CLI not installed')
class CodexRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='valk-codex-names-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def codex(self, home, cwd, *args):
        result = subprocess.run(['codex', *args], cwd=cwd, env=dict(os.environ, CODEX_HOME=str(home)),
                                capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def registered(self, home, cwd):
        # prompt-input renders what the model would see; no model call, no login needed.
        items = json.loads(self.codex(home, cwd, 'debug', 'prompt-input', 'hi'))
        text = '\n'.join(part.get('text', '') for item in items
                         for part in item.get('content', []) if isinstance(part, dict))
        return set(NAME.findall(text))

    def test_plugin_install_registers_prefixed_names(self):
        market = self.root / 'market'
        (market / '.claude-plugin').mkdir(parents=True)
        shutil.copy2(ROOT / '.claude-plugin/marketplace.json', market / '.claude-plugin')
        for plugin in PLUGINS:
            shutil.copytree(ROOT / plugin, market / plugin,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
        home, workspace = self.root / 'home', self.root / 'workspace'
        home.mkdir()
        workspace.mkdir()
        self.codex(home, workspace, 'plugin', 'marketplace', 'add', str(market))
        for plugin in PLUGINS:
            self.codex(home, workspace, 'plugin', 'add', plugin + '@valkyrja-forge')
        names = self.registered(home, workspace)
        for plugin in PLUGINS:
            for skill in skill_names(plugin):
                with self.subTest(skill=plugin + ':' + skill):
                    self.assertIn(plugin + ':' + skill, names)

    def test_copy_install_registers_bare_names(self):
        home, project = self.root / 'home', self.root / 'product repo'
        home.mkdir()
        project.mkdir()
        subprocess.run(['git', 'init', '-q', str(project)], check=True)
        for plugin in PLUGINS:
            subprocess.run(['bash', str(ROOT / 'scripts/install-skills.sh'), '--harness', 'codex',
                            '--plugin', plugin, '--project', str(project)],
                           check=True, capture_output=True, text=True)
        names = self.registered(home, project)
        for plugin in PLUGINS:
            for skill in skill_names(plugin):
                with self.subTest(skill=skill):
                    self.assertIn(skill, names)
                    self.assertNotIn(plugin + ':' + skill, names)


if __name__ == '__main__':
    unittest.main()
