"""Cross-host packaging checks; no model calls or personal installation."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_each_plugin_identity_and_version_match_all_manifests(self):
        marketplace = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        entries = {entry['name']: entry for entry in marketplace['plugins']}
        self.assertEqual(set(entries), {'valk', 'valk-tools'})
        for name, entry in entries.items():
            with self.subTest(plugin=name):
                portable = json.loads((ROOT / name / 'plugin.json').read_text())
                claude = json.loads((ROOT / name / '.claude-plugin/plugin.json').read_text())
                self.assertEqual(portable['name'], name)
                self.assertEqual(claude['name'], name)
                self.assertEqual(portable['version'], claude['version'])
                self.assertEqual(portable['version'], entry['version'])
                self.assertEqual(entry['source'], './' + name)
                self.assertEqual(portable['$schema'],
                                 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json')

    def test_all_skills_have_discoverable_frontmatter(self):
        for plugin, count in (('valk', 3), ('valk-tools', 4)):
            paths = sorted((ROOT / plugin / 'skills').glob('*/SKILL.md'))
            self.assertEqual(len(paths), count)
            for path in paths:
                with self.subTest(skill=path.parent.name):
                    content = path.read_text()
                    match = re.match(r'\A---\n(.*?)\n---\n', content, re.S)
                    self.assertIsNotNone(match)
                    fields = match.group(1)
                    self.assertRegex(fields, r'(?m)^name: ' + re.escape(path.parent.name) + r'\s*$')
                    self.assertRegex(fields, r'(?m)^description: \S')

    def test_consumer_guard_is_one_template_carried_by_each_skill(self):
        paths = sorted((ROOT / 'valk/skills').glob('*/templates/guard-block.md'))
        self.assertEqual(len(paths), 3)
        contents = [path.read_text() for path in paths]
        self.assertEqual(len(set(contents)), 1)
        self.assertIn('<!-- valkyrja:begin', contents[0])
        self.assertEqual(contents[0].count('<!-- valkyrja:begin'), 1)
        self.assertEqual(contents[0].count('<!-- valkyrja:end -->'), 1)
        self.assertEqual(list((ROOT / 'valk/skills').glob('*/templates/*-guard-block.md')), [])

    def test_every_skill_points_at_the_guard_template(self):
        for path in sorted((ROOT / 'valk/skills').glob('*/SKILL.md')):
            with self.subTest(skill=path.parent.name):
                self.assertIn('templates/guard-block.md', path.read_text())
        shipped = list((ROOT / 'valk').rglob('*.md')) + [ROOT / 'README.md', ROOT / 'README.zh-CN.md']
        for path in shipped:
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotRegex(path.read_text(), r'(claude|agents)-guard-block')

    def test_shared_skill_passages_are_identical(self):
        # 三个技能可独立安装，只能各带一份；逐字一致由这里守，不靠人工 md5。
        starts = {'宿主适配': '## 宿主适配（共享协议）\n',
                  '回显可读性': '**回显可读性（代号不裸奔）**',
                  '消费仓宿主治理块': '**消费仓宿主治理块**'}
        texts = {path.parent.name: path.read_text()
                 for path in sorted((ROOT / 'valk/skills').glob('*/SKILL.md'))}
        self.assertEqual(len(texts), 3)
        for label, start in starts.items():
            with self.subTest(passage=label):
                passages = set()
                for name, text in texts.items():
                    self.assertEqual(text.count(start), 1, name)
                    begin = text.index(start)
                    end = text.find('\n## ' if start.startswith('##') else '\n\n', begin + len(start))
                    passages.add(text[begin:end])
                self.assertEqual(len(passages), 1)

    def test_documented_invocation_names_exist(self):
        skills = {plugin: {p.parent.name for p in (ROOT / plugin / 'skills').glob('*/SKILL.md')}
                  for plugin in ('valk', 'valk-tools')}
        commands = {p.stem for p in (ROOT / 'valk/commands').glob('*.md')}
        bare = skills['valk'] | skills['valk-tools']
        docs = [ROOT / 'README.md', ROOT / 'README.zh-CN.md', ROOT / 'CLAUDE.md',
                ROOT / 'evals/README.md', ROOT / 'valk-tools/README.md']
        docs += sorted((ROOT / 'valk').rglob('*.md')) + sorted((ROOT / 'valk-tools').rglob('*.md'))
        pattern = re.compile(r'(?<![\w-])([$/]?)(valk-tools|valk):([a-z][a-z0-9-]*)')
        for path in docs:
            text = path.read_text()
            for prefix, plugin, name in pattern.findall(text):
                with self.subTest(path=str(path.relative_to(ROOT)), name=plugin + ':' + name):
                    known = skills[plugin] | (commands if plugin == 'valk' and prefix != '$' else set())
                    self.assertIn(name, known)
            for name in re.findall(r'(?<![\w$])\$((?:valkyrja|host|context|merge|refactor|claude)-[a-z0-9-]+)', text):
                with self.subTest(path=str(path.relative_to(ROOT)), name='$' + name):
                    self.assertIn(name, bare)

    def test_trace_is_bundled_once_with_the_spec_skill(self):
        self.assertTrue((ROOT / 'valk/skills/valkyrja-spec/tools/trace.py').is_file())
        self.assertEqual(list((ROOT / 'valk').rglob('trace.py')),
                         [ROOT / 'valk/skills/valkyrja-spec/tools/trace.py'])


if __name__ == '__main__':
    unittest.main()
