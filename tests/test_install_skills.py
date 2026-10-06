"""Offline installer regressions; all source and destination writes are isolated."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
VALK_SKILLS = {"valkyrja-prd", "valkyrja-arch", "valkyrja-spec"}
TOOLS_SKILLS = {"context-handoff", "host-handoff", "merge-pr", "refactor-review"}


class InstallSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="valk-installer-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        (self.source / "scripts").mkdir(parents=True)
        self.script = self.source / "scripts/install-skills.sh"
        shutil.copy2(REPO / "scripts/install-skills.sh", self.script)
        for plugin in ("valk", "valk-tools"):
            shutil.copytree(REPO / plugin, self.source / plugin)
        self.project = self.root / "consumer project"
        self.project.mkdir()
        self.user_home = self.root / "isolated user"
        self.user_home.mkdir()

    def run_installer(self, *args, success=True):
        env = dict(os.environ, HOME=str(self.user_home))
        result = subprocess.run(
            ["bash", str(self.script), *map(str, args)],
            cwd=self.project, env=env, text=True, capture_output=True,
        )
        output = result.stdout + result.stderr
        if success:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
        return output

    def installed_names(self, root):
        return {p.parent.name for p in (root / "skills").glob("*/SKILL.md")}

    def test_claude_default_installs_three_skills_and_commands(self):
        self.run_installer("--project", self.project)
        target = self.project / ".claude"
        self.assertEqual(self.installed_names(target), VALK_SKILLS)
        self.assertEqual(
            {p.stem for p in (target / "commands/valk").glob("*.md")},
            {"prd", "arch", "spec"},
        )

    def test_codex_installs_skills_only(self):
        self.run_installer("--harness", "codex", "--project", self.project)
        self.assertEqual(self.installed_names(self.project / ".agents"), VALK_SKILLS)
        self.assertFalse((self.project / ".agents/commands").exists())
        self.assertFalse((self.project / ".claude").exists())

    def test_codex_tools_plugin(self):
        self.run_installer("--harness", "codex", "--plugin", "valk-tools")
        self.assertEqual(self.installed_names(self.project / ".agents"), TOOLS_SKILLS)
        self.assertFalse((self.project / ".agents/commands").exists())

    def test_claude_tools_plugin_has_no_commands(self):
        self.run_installer("--plugin", "valk-tools")
        self.assertEqual(self.installed_names(self.project / ".claude"), TOOLS_SKILLS)
        self.assertFalse((self.project / ".claude/commands").exists())

    def test_cross_host_handoff_is_self_contained_when_installed_alone(self):
        for harness, folder in (("claude", ".claude"), ("codex", ".agents")):
            with self.subTest(harness=harness):
                self.run_installer("--harness", harness, "--plugin", "valk-tools", "host-handoff")
                skill = self.project / folder / 'skills/host-handoff'
                self.assertEqual(self.installed_names(self.project / folder), {'host-handoff'})
                self.assertTrue((skill / 'scripts/workspace_state.py').is_file())
                self.assertTrue((skill / 'templates/handoff.md').is_file())
                self.assertFalse((self.project / folder / 'commands').exists())

    def test_system_destinations_use_isolated_home(self):
        for harness, folder in (("claude", ".claude"), ("codex", ".agents")):
            with self.subTest(harness=harness):
                self.run_installer("--harness", harness, "--system", "valkyrja-prd")
                self.assertEqual(self.installed_names(self.user_home / folder), {"valkyrja-prd"})
        self.assertEqual(list(self.project.iterdir()), [])

    def test_dry_run_does_not_create_destinations(self):
        for harness in ("claude", "codex"):
            with self.subTest(harness=harness):
                output = self.run_installer("--harness", harness, "--dry-run", "--force")
                self.assertIn("dry-run", output)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_selective_installs_have_no_commands(self):
        for harness, folder in (("claude", ".claude"), ("codex", ".agents")):
            with self.subTest(harness=harness):
                self.run_installer("--harness", harness, "valkyrja-prd")
                self.assertEqual(self.installed_names(self.project / folder), {"valkyrja-prd"})
                self.assertFalse((self.project / folder / "commands").exists())

    def test_reinstall_skips_without_force(self):
        self.run_installer("--harness", "codex", "valkyrja-prd")
        marker = self.project / ".agents/skills/valkyrja-prd/local-note"
        marker.write_text("preserve me")
        self.run_installer("--harness", "codex", "valkyrja-prd")
        self.assertEqual(marker.read_text(), "preserve me")

    def test_force_backup_preserves_data_outside_codex_discovery(self):
        self.run_installer("--harness", "codex", "valkyrja-prd")
        marker = self.project / ".agents/skills/valkyrja-prd/local-note"
        marker.write_text("old data")
        self.run_installer("--harness", "codex", "--force", "valkyrja-prd")
        self.assertFalse(marker.exists())
        backups = list((self.project / ".agents/.valkyrja-backup/skills").glob("*/local-note"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "old data")
        self.assertEqual(len(list((self.project / ".agents/skills").rglob("SKILL.md"))), 1)

    def test_repeated_backups_do_not_merge_old_versions(self):
        self.run_installer("--harness", "codex", "valkyrja-prd")
        marker = self.project / ".agents/skills/valkyrja-prd/local-note"
        for data in ("version one", "version two"):
            marker.write_text(data)
            self.run_installer("--harness", "codex", "--force", "valkyrja-prd")
        backups = list((self.project / ".agents/.valkyrja-backup/skills").glob("*/local-note"))
        self.assertEqual({p.read_text() for p in backups}, {"version one", "version two"})

    def test_claude_retains_existing_backup_location(self):
        self.run_installer("valkyrja-prd")
        marker = self.project / ".claude/skills/valkyrja-prd/local-note"
        marker.write_text("old Claude data")
        self.run_installer("--force", "valkyrja-prd")
        backups = list((self.project / ".claude/skills/.backup").glob("*/local-note"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "old Claude data")

    def test_no_backup_overrides_without_backup(self):
        self.run_installer("--harness", "codex", "valkyrja-prd")
        marker = self.project / ".agents/skills/valkyrja-prd/local-note"
        marker.write_text("old")
        self.run_installer("--harness", "codex", "--force", "--no-backup", "valkyrja-prd")
        self.assertFalse(marker.exists())
        self.assertFalse((self.project / ".agents/.valkyrja-backup").exists())

    def test_junk_is_scrubbed_and_assets_retained(self):
        source_skill = self.source / "valk/skills/valkyrja-prd"
        (source_skill / "__pycache__").mkdir(exist_ok=True)
        for path in (source_skill / ".DS_Store", source_skill / "cached.pyc", source_skill / "__pycache__/cached.pyc"):
            path.write_text("junk")
        (source_skill / "fixture-asset.txt").write_text("keep")
        self.run_installer("--harness", "codex", "valkyrja-prd")
        dest = self.project / ".agents/skills/valkyrja-prd"
        self.assertFalse(list(dest.rglob(".DS_Store")))
        self.assertFalse(list(dest.rglob("*.pyc")))
        self.assertFalse(list(dest.rglob("__pycache__")))
        self.assertEqual((dest / "fixture-asset.txt").read_text(), "keep")

    def test_invalid_arguments_fail_before_writing(self):
        for args in (
            ("--harness", "unknown"), ("--plugin", "unknown"),
            ("--harness",), ("--plugin",),
            ("valkyrja-prd", ".."), ("../valkyrja-prd",),
            ("/tmp",), ("valkyrja-prd/../valkyrja-arch",),
            (".",), ("valkyrja-prd/",),
        ):
            with self.subTest(args=args):
                self.run_installer(*args, success=False)
                self.assertEqual(list(self.project.iterdir()), [])

    def test_list_is_read_only_and_omits_codex_commands(self):
        self.run_installer("--harness", "codex", "valkyrja-prd")
        output = self.run_installer("--harness", "codex", "--list")
        self.assertIn("valkyrja-prd", output)
        self.assertNotIn("斜杠命令", output)
        self.assertFalse((self.project / ".agents/commands").exists())


if __name__ == "__main__":
    unittest.main()
