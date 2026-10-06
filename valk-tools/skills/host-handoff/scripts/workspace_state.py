#!/usr/bin/env python3
"""Read-only, scoped workspace fingerprints. A match is not execution authority."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys


LOCAL_STATE = {".git", ".claude", ".codex"}
HEX = re.compile(r"^[0-9a-f]{64}$")


def sensitive(path):
    parts = PurePosixPath(path).parts
    name = parts[-1].lower()
    return (any(part.lower() in LOCAL_STATE for part in parts)
            or name.startswith(".env")
            or name in {"auth.json", "credentials", "credentials.json", "credentials.yaml", "credentials.yml", ".netrc", ".npmrc", ".pypirc", ".git-credentials", "id_rsa", "id_ed25519", "id_dsa", "id_ecdsa"}
            or name.startswith(("private-key", "private_key", "service-account"))
            or name.endswith((".pem", ".key", ".p12", ".pfx")))


def safe_path(root, value, allow_sensitive=False):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ValueError("invalid relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or any(p in {".", ".."} for p in value.split("/")):
        raise ValueError("path must be canonical and relative")
    ancestor = root
    for part in path.parts[:-1]:
        ancestor = ancestor / part
        if ancestor.is_symlink():
            raise ValueError("symlink parent is not traversable")
    try:
        (root / value).parent.resolve().relative_to(root)
    except ValueError:
        raise ValueError("symlink parent escapes workspace")
    if sensitive(value) and not allow_sensitive:
        raise ValueError("sensitive or agent-local path is not selectable")
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args, input_data=None, allowed=(0,)):
    proc = subprocess.run(["git", "--no-optional-locks", "-C", str(root), *args],
                          input=input_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode not in allowed:
        raise ValueError("Git inspection failed")
    return proc


def excluded(path, exclusions):
    return any(path == item or path.startswith(item + "/") for item in exclusions)


def git_identity(root, exclusions):
    try:
        prefix = git(root, "rev-parse", "--show-prefix", allowed=(0, 128))
    except FileNotFoundError:
        return None, []
    if prefix.returncode == 128 or prefix.stdout not in (b"", b"\n"):
        return None, []
    head = git(root, "rev-parse", "--verify", "HEAD", allowed=(0, 128))
    branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD", allowed=(0, 1))
    raw = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout.split(b"\x00")
    records = []
    i = 0
    while i < len(raw) and raw[i]:
        entry = raw[i]
        if len(entry) < 4 or entry[2:3] != b" ":
            raise ValueError("invalid Git status record")
        record = {"status": entry[:2].decode("ascii"), "path": os.fsdecode(entry[3:])}
        i += 1
        if "R" in record["status"] or "C" in record["status"]:
            if i >= len(raw) or not raw[i]:
                raise ValueError("invalid Git rename record")
            record["original"] = os.fsdecode(raw[i])
            i += 1
        names = [record["path"]] + ([record["original"]] if "original" in record else [])
        if not all(excluded(name, exclusions) for name in names):
            records.append(record)
    records.sort(key=lambda item: (item["path"], item.get("original", ""), item["status"]))
    index = git(root, "ls-files", "--stage", "-z").stdout
    result = {"head": head.stdout.decode("ascii").strip() if head.returncode == 0 else None,
              "branch": os.fsdecode(branch.stdout.rstrip(b"\n")) if branch.returncode == 0 else None,
              "index_sha256": digest(index), "status": records}
    dirty = set()
    for record in records:
        dirty.add(record["path"])
        if "original" in record:
            dirty.add(record["original"])
    return result, sorted(dirty)


def ignored(root, path, has_git):
    return has_git and git(root, "check-ignore", "-q", "--", path, allowed=(0, 1)).returncode == 0


def capture(root, requested, exclusions, additional=()):
    identity, dirty = git_identity(root, exclusions)
    states = {}
    omitted = {}

    def inspect(path, explicit=False):
        safe_path(root, path, allow_sensitive=not explicit)
        if excluded(path, exclusions):
            return
        if sensitive(path):
            omitted[path] = "sensitive or agent-local; contents not inspected"
            return
        if path in states:
            return
        target = root / path
        try:
            info = target.lstat()
        except FileNotFoundError:
            states[path] = {"kind": "missing"}
            return
        if stat.S_ISLNK(info.st_mode):
            states[path] = {"kind": "symlink", "sha256": digest(os.fsencode(os.readlink(str(target))))}
        elif stat.S_ISREG(info.st_mode):
            fingerprint = hashlib.sha256()
            descriptor = os.open(str(target), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(descriptor, "rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    fingerprint.update(block)
            states[path] = {"kind": "file", "sha256": fingerprint.hexdigest(), "executable": bool(info.st_mode & 0o111)}
        elif stat.S_ISDIR(info.st_mode):
            entries = []
            for child in sorted(target.iterdir(), key=lambda item: item.name):
                child_path = path + "/" + child.name
                if excluded(child_path, exclusions) or ignored(root, child_path, identity is not None):
                    continue
                if sensitive(child_path):
                    omitted[child_path] = "sensitive or agent-local; contents not inspected"
                    continue
                entries.append(child.name)
                inspect(child_path)
            states[path] = {"kind": "directory", "entries": entries}
        else:
            raise ValueError("unsupported special file in scope")

    for path in requested:
        inspect(path, explicit=True)
    for path in sorted(set(dirty) | set(additional)):
        inspect(path)
    return {"version": 1, "root": str(root), "confidence": "git" if identity else "limited",
            "git": identity, "requested": requested, "excluded": exclusions,
            "paths": dict(sorted(states.items())),
            "omitted": [{"path": path, "reason": reason} for path, reason in sorted(omitted.items())]}


def validate_snapshot(root, snapshot):
    fields = {"version", "root", "confidence", "git", "requested", "excluded", "paths", "omitted"}
    if not isinstance(snapshot, dict) or set(snapshot) != fields or type(snapshot["version"]) is not int or snapshot["version"] != 1:
        raise ValueError("unsupported snapshot schema")
    if not isinstance(snapshot["root"], str) or snapshot["confidence"] not in {"git", "limited"}:
        raise ValueError("invalid snapshot metadata")
    for field in ("requested", "excluded"):
        if not isinstance(snapshot[field], list) or not all(isinstance(p, str) for p in snapshot[field]):
            raise ValueError("invalid snapshot scope")
        for path in snapshot[field]:
            safe_path(root, path, allow_sensitive=field == "excluded")
    if not isinstance(snapshot["paths"], dict) or not isinstance(snapshot["omitted"], list):
        raise ValueError("invalid snapshot paths")
    for path, state in snapshot["paths"].items():
        safe_path(root, path)
        if not isinstance(state, dict) or state.get("kind") not in {"missing", "file", "directory", "symlink"}:
            raise ValueError("invalid path state")
        kind = state["kind"]
        expected = {"kind"} | ({"sha256", "executable"} if kind == "file" else {"sha256"} if kind == "symlink" else {"entries"} if kind == "directory" else set())
        if set(state) != expected:
            raise ValueError("invalid path state fields")
        if kind in {"file", "symlink"} and (not isinstance(state["sha256"], str) or not HEX.fullmatch(state["sha256"])):
            raise ValueError("invalid path fingerprint")
        if kind == "file" and type(state["executable"]) is not bool:
            raise ValueError("invalid executable metadata")
        if kind == "directory":
            if not isinstance(state["entries"], list) or not all(isinstance(p, str) and p and "/" not in p and p not in {".", ".."} and "\x00" not in p for p in state["entries"]):
                raise ValueError("invalid directory entries")
    for item in snapshot["omitted"]:
        if not isinstance(item, dict) or set(item) != {"path", "reason"} or not isinstance(item["reason"], str):
            raise ValueError("invalid omitted-path metadata")
        safe_path(root, item["path"], allow_sensitive=True)
        if not sensitive(item["path"]):
            raise ValueError("non-sensitive path cannot be omitted")
    identity = snapshot["git"]
    if identity is not None:
        if not isinstance(identity, dict) or set(identity) != {"head", "branch", "index_sha256", "status"}:
            raise ValueError("invalid Git metadata")
        if identity["head"] is not None and (not isinstance(identity["head"], str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", identity["head"])):
            raise ValueError("invalid Git identity")
        if identity["branch"] is not None and not isinstance(identity["branch"], str):
            raise ValueError("invalid Git branch")
        if not isinstance(identity["index_sha256"], str) or not HEX.fullmatch(identity["index_sha256"]) or not isinstance(identity["status"], list):
            raise ValueError("invalid Git index or status")
        for record in identity["status"]:
            if not isinstance(record, dict) or set(record) not in ({"path", "status"}, {"path", "status", "original"}) or not isinstance(record["status"], str) or len(record["status"]) != 2:
                raise ValueError("invalid Git status record")
            for field in ("path", "original"):
                if field in record:
                    safe_path(root, record[field], allow_sensitive=True)
    if (identity is None) != (snapshot["confidence"] == "limited"):
        raise ValueError("inconsistent confidence metadata")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot_parser = commands.add_parser("snapshot")
    snapshot_parser.add_argument("root")
    snapshot_parser.add_argument("--path", action="append", default=[])
    snapshot_parser.add_argument("--exclude", action="append", default=[])
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("root")
    verify_parser.add_argument("snapshot_json")
    args = parser.parse_args()
    try:
        root = Path(args.root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("workspace root is not a directory")
        if args.command == "snapshot":
            requested = sorted(set(safe_path(root, p) for p in args.path))
            exclusions = sorted(set(safe_path(root, p, allow_sensitive=True) for p in args.exclude))
            if any(excluded(p, exclusions) for p in requested):
                raise ValueError("requested path is also excluded")
            result = capture(root, requested, exclusions)
            code = 0
        else:
            with open(args.snapshot_json, encoding="utf-8") as stream:
                previous = json.load(stream)
            validate_snapshot(root, previous)
            current = capture(root, previous["requested"], previous["excluded"], previous["paths"])
            changed = sorted(path for path in set(previous["paths"]) | set(current["paths"]) if previous["paths"].get(path) != current["paths"].get(path))
            metadata = [field for field in ("git", "confidence", "omitted") if previous[field] != current[field]]
            result = {"match": not changed and not metadata, "changed_paths": changed, "changed_metadata": metadata,
                      "confidence": current["confidence"], "omitted": current["omitted"], "excluded": current["excluded"]}
            code = 0 if result["match"] else 1
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return code
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
