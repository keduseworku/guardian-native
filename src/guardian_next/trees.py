"""Byte-exact candidates without changing the user's index, branch, or files."""

import hashlib
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path, PurePosixPath


class Failure(Exception):
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args, data=None, extra=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"})
    env.update(extra or {})
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=", *args],
        cwd=repo,
        input=data,
        capture_output=True,
        env=env,
        timeout=120,
    )
    if result.returncode:
        raise Failure("environment", result.stderr.decode(errors="replace")[-2000:])
    return result.stdout


def text_git(repo, *args):
    return git(repo, *args).decode().strip()


def root(path):
    return Path(text_git(path, "rev-parse", "--show-toplevel")).resolve()


def safe_path(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ".." in p.parts or "\\" in name or ":" in name:
        raise Failure("protocol", f"Not a repository-relative path: {name!r}")
    if ".git" in p.parts:
        raise Failure("protocol", "Git internals are not task paths")
    return p


def capture(repo, names=None):
    """Hash actual bytes, including untracked files; bypass git clean filters."""
    entries = []
    if names is None:
        names = git(repo, "ls-files", "-c", "-o", "--exclude-standard", "-z").split(b"\0")
    names = sorted(set(names))
    for raw in filter(None, names):
        name = raw.decode("utf-8")
        safe_path(name)
        path = repo / name
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(mode):
            raise Failure(
                "environment", f"Symlink/submodule/special file needs explicit support: {name}"
            )
        oid = git(repo, "hash-object", "-w", "--stdin", data=path.read_bytes()).strip()
        gitmode = b"100755" if mode & stat.S_IXUSR else b"100644"
        entries.append(gitmode + b" " + oid + b"\t" + raw + b"\0")
    with tempfile.TemporaryDirectory(prefix="guardian-index-") as temporary:
        env = {"GIT_INDEX_FILE": str(Path(temporary) / "index")}
        git(repo, "read-tree", "--empty", extra=env)
        git(repo, "update-index", "-z", "--index-info", data=b"".join(entries), extra=env)
        return git(repo, "write-tree", extra=env).decode().strip()


def export(repo, tree, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for row in git(repo, "ls-tree", "-rz", tree).split(b"\0"):
        if not row:
            continue
        metadata, raw = row.split(b"\t", 1)
        mode, kind, oid = metadata.split()
        if kind != b"blob" or mode not in {b"100644", b"100755"}:
            raise Failure("environment", "Candidate contains unsupported Git entry")
        name = raw.decode()
        safe_path(name)
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(git(repo, "cat-file", "blob", oid.decode()))
        if mode == b"100755":
            path.chmod(0o755)


def snapshot(repo, base, candidate, destination):
    """Independent disposable repository, with the original baseline as HEAD."""
    export(repo, base, destination)
    git(destination, "init", "-b", "snapshot")
    names = git(repo, "ls-tree", "-r", "--name-only", "-z", base).split(b"\0")
    git(destination, "read-tree", capture(destination, names))
    git(
        destination,
        "-c",
        "user.name=Guardian",
        "-c",
        "user.email=guardian@localhost",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--allow-empty",
        "-m",
        "Task baseline",
    )
    for path in sorted(destination.rglob("*"), reverse=True):
        if ".git" in path.relative_to(destination).parts:
            continue
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    export(repo, candidate, destination)


def changed(repo, base, candidate):
    return [
        s.decode()
        for s in git(repo, "diff", "--name-only", "-z", base, candidate).split(b"\0")
        if s
    ]
