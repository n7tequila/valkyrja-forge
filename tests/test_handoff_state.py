"""Read-only handoff fingerprints, exercised in isolated workspaces."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "valk-tools/skills/host-handoff/scripts/workspace_state.py"


class HandoffStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE)

    def init(self):
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        (self.root / "tracked.txt").write_text("base")
        self.git("add", ".")
        self.git("commit", "-qm", "baseline")

    def call(self, *args):
        proc = subprocess.run([os.sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)
        return proc.returncode, json.loads(proc.stdout)

    def snapshot(self, *paths):
        args = ["snapshot", self.root]
        for path in paths:
            args += ["--path", path]
        code, result = self.call(*args)
        self.assertEqual(code, 0, result)
        return result

    def verify(self, snapshot):
        path = Path(self.temp.name) / "snapshot.json"
        path.write_text(json.dumps(snapshot))
        return self.call("verify", self.root, path)

    def test_match_is_read_only(self):
        self.init()
        (self.root / "tracked.txt").write_text("dirty")
        before = self.git("status", "--porcelain=v1", "-z")
        index_before = (self.root / ".git/index").read_bytes()
        snapshot = self.snapshot()
        self.assertEqual(self.verify(snapshot)[0], 0)
        self.assertEqual(before, self.git("status", "--porcelain=v1", "-z"))
        self.assertEqual((self.root / "tracked.txt").read_text(), "dirty")
        self.assertEqual(index_before, (self.root / ".git/index").read_bytes())

    def test_dirty_content_changes(self):
        self.init()
        (self.root / "tracked.txt").write_text("one")
        snapshot = self.snapshot()
        (self.root / "tracked.txt").write_text("two")
        self.assertEqual(self.verify(snapshot)[0], 1)

    def test_staging_only_change(self):
        self.init()
        (self.root / "tracked.txt").write_text("staged")
        self.git("add", ".")
        (self.root / "tracked.txt").write_text("worktree")
        snapshot = self.snapshot()
        status_before = self.git("status", "--porcelain=v1", "-z")
        (self.root / "tracked.txt").write_text("different staged value")
        self.git("add", ".")
        (self.root / "tracked.txt").write_text("worktree")
        self.assertEqual(status_before, self.git("status", "--porcelain=v1", "-z"))
        code, result = self.verify(snapshot)
        self.assertEqual(code, 1)
        self.assertEqual(result["changed_paths"], [])
        self.assertEqual(result["changed_metadata"], ["git"])

    def test_head_change_without_worktree_change(self):
        self.init()
        snapshot = self.snapshot()
        self.git("commit", "--allow-empty", "-qm", "identity changed")
        self.assertEqual(self.verify(snapshot)[0], 1)

    def test_rename_with_newline_and_spaces(self):
        self.init()
        destination = "new name\nfile.txt"
        self.git("mv", "tracked.txt", destination)
        snapshot = self.snapshot()
        self.assertIn(destination, snapshot["paths"])
        self.assertIn("tracked.txt", snapshot["paths"])
        self.assertEqual(self.verify(snapshot)[0], 0)

    def test_workspace_root_with_newline_and_unicode(self):
        relocated = self.root.with_name("repo space\né")
        self.root.rename(relocated)
        self.root = relocated
        self.init()
        snapshot = self.snapshot()
        self.assertIsNotNone(snapshot["git"])
        self.assertEqual(self.verify(snapshot)[0], 0)

    def test_new_untracked_path_and_content(self):
        self.init()
        (self.root / "new.txt").write_text("one")
        snapshot = self.snapshot()
        (self.root / "new.txt").write_text("two")
        self.assertEqual(self.verify(snapshot)[0], 1)
        (self.root / "new.txt").write_text("one")
        (self.root / "extra.txt").write_text("extra")
        self.assertEqual(self.verify(snapshot)[0], 1)

    def test_deleted_tracked_path_has_missing_state(self):
        self.init()
        (self.root / "tracked.txt").unlink()
        snapshot = self.snapshot()
        self.assertEqual(snapshot["paths"]["tracked.txt"], {"kind": "missing"})
        self.assertEqual(self.verify(snapshot)[0], 0)

    def test_selected_directory_new_and_deleted_files(self):
        self.init()
        folder = self.root / "docs"
        folder.mkdir()
        (folder / "a.md").write_text("a")
        snapshot = self.snapshot("docs")
        (folder / "b.md").write_text("b")
        self.assertEqual(self.verify(snapshot)[0], 1)
        (folder / "b.md").unlink()
        (folder / "a.md").unlink()
        self.assertEqual(self.verify(snapshot)[0], 1)

    def test_missing_selected_path_created(self):
        self.init()
        snapshot = self.snapshot("future/file.md")
        (self.root / "future").mkdir()
        (self.root / "future/file.md").write_text("created")
        self.assertEqual(self.verify(snapshot)[0], 1)

    def test_ignored_junk_not_included(self):
        self.init()
        (self.root / ".gitignore").write_text("docs/junk\n")
        (self.root / "docs").mkdir()
        (self.root / "docs/junk").write_text("secret irrelevant")
        snapshot = self.snapshot("docs")
        self.assertNotIn("docs/junk", snapshot["paths"])
        (self.root / "docs/junk").write_text("changed")
        self.assertEqual(self.verify(snapshot)[0], 0)

    def test_sensitive_and_traversal_rejected(self):
        for path in ("../escape", "/tmp/escape", ".env", "config/auth.json", ".git/HEAD", ".claude/settings.json", ".codex/config.toml", "private-key.pem"):
            with self.subTest(path=path):
                self.assertEqual(self.call("snapshot", self.root, "--path", path)[0], 2)

    def test_sensitive_dirty_paths_omitted_not_read(self):
        self.init()
        (self.root / ".env").write_text("secret must not appear")
        snapshot = self.snapshot()
        self.assertNotIn(".env", snapshot["paths"])
        self.assertEqual(snapshot["omitted"][0]["path"], ".env")
        self.assertNotIn("secret must not appear", json.dumps(snapshot))
        self.assertEqual(self.verify(snapshot)[0], 0)

    def test_packet_exclusions_do_not_hide_other_changes(self):
        self.init()
        code, snapshot = self.call("snapshot", self.root, "--exclude", "handoff/packet.md", "--exclude", "handoff/state.json")
        self.assertEqual(code, 0)
        (self.root / "handoff").mkdir()
        (self.root / "handoff/packet.md").write_text("packet")
        (self.root / "handoff/state.json").write_text("fingerprints")
        self.assertEqual(self.verify(snapshot)[0], 0)
        (self.root / "handoff/packet.md").write_text("updated packet")
        self.assertEqual(self.verify(snapshot)[0], 0)
        (self.root / "tracked.txt").write_text("code drift")
        self.assertEqual(self.verify(snapshot)[0], 1)

    def test_excluded_packet_staging_still_invalidates(self):
        self.init()
        code, snapshot = self.call("snapshot", self.root, "--exclude", "packet.md")
        self.assertEqual(code, 0)
        (self.root / "packet.md").write_text("packet")
        self.git("add", "packet.md")
        self.assertEqual(self.verify(snapshot)[0], 1)

    def test_external_symlink_parent_rejected_leaf_not_followed(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "payload").write_text("must never read")
        (self.root / "link").symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.call("snapshot", self.root, "--path", "link/payload")[0], 2)
        snapshot = self.snapshot("link")
        self.assertEqual(snapshot["paths"]["link"]["kind"], "symlink")
        self.assertNotIn("must never read", json.dumps(snapshot))

    def test_internal_symlink_parent_not_followed(self):
        (self.root / "docs").mkdir()
        (self.root / "docs/file.md").write_text("inside")
        (self.root / "link").symlink_to("docs", target_is_directory=True)
        self.assertEqual(self.call("snapshot", self.root, "--path", "link/file.md")[0], 2)

    def test_forged_snapshot_rejected(self):
        snapshot = self.snapshot("note.md")
        for field in ("requested", "excluded", "paths"):
            forged = json.loads(json.dumps(snapshot))
            if field in ("requested", "excluded"):
                forged[field] = ["../outside"]
            else:
                forged[field]["../outside"] = {"kind": "missing"}
            self.assertEqual(self.verify(forged)[0], 2)
        snapshot["version"] = True
        self.assertEqual(self.verify(snapshot)[0], 2)

    def test_non_git_and_relocation(self):
        (self.root / "note.md").write_text("same")
        snapshot = self.snapshot("note.md")
        self.assertIsNone(snapshot["git"])
        self.assertEqual(snapshot["confidence"], "limited")
        snapshot["root"] = "/informational/old/location"
        self.assertEqual(self.verify(snapshot)[0], 0)


if __name__ == "__main__":
    unittest.main()
