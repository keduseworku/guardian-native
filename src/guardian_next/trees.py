"""Byte-exact candidates without changing the user's index, branch, or files."""

import hashlib
import json
import os
import re
import shutil
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


def executable():
    selected = os.environ.get("GUARDIAN_GIT", "git")
    found = shutil.which(selected)
    if not found:
        raise Failure(
            "environment",
            f"Git executable unavailable: {selected}. Set GUARDIAN_GIT to its full path.",
        )
    return str(Path(found).absolute())


def git_info(repo):
    version = text_git(repo, "--version")
    match = re.search(r"git version (\d+)\.(\d+)", version)
    if not match or tuple(map(int, match.groups())) < (2, 27):
        raise Failure(
            "environment", f"Guardian requires Git 2.27+: {executable()} reports {version}"
        )
    return {"path": executable(), "version": version, "exit_code": 0}


def git(repo, *args, data=None, extra=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"})
    env.update(extra or {})
    result = subprocess.run(
        [executable(), "-c", "core.hooksPath=", *args],
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


def capture(repo, names=None, source=None):
    """Hash actual bytes, including untracked files; bypass git clean filters."""
    entries = []
    if names is None:
        names = git(repo, "ls-files", "-c", "-o", "--exclude-standard", "-z").split(b"\0")
    names = sorted(set(names))
    for raw in filter(None, names):
        name = raw.decode("utf-8")
        safe_path(name)
        path = (source or repo) / name
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
    git(destination, "init")
    git(destination, "symbolic-ref", "HEAD", "refs/heads/snapshot")
    git(destination, "config", "core.autocrlf", "false")
    (destination / ".git/info/attributes").write_text(
        "* -text -filter -ident -working-tree-encoding\n", encoding="utf-8"
    )
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


def checkout_baseline(repo, head):
    """Reconstruct Git's HEAD checkout bytes without touching any existing worktree/index.

    Only built-in checkout conversion is supported. Custom filters/encodings need a
    worker-specific baseline contract, not a permissive normalization comparison.
    """
    names = git(repo, "ls-tree", "-r", "--name-only", "-z", head)
    with tempfile.TemporaryDirectory(prefix="guardian-worker-base-") as temporary:
        destination = Path(temporary) / "files"
        destination.mkdir()
        env = {"GIT_INDEX_FILE": str(Path(temporary) / "index"), "GIT_WORK_TREE": str(destination)}
        git(repo, "read-tree", head, extra=env)
        attrs = git(
            repo,
            "check-attr",
            "--cached",
            "-z",
            "filter",
            "working-tree-encoding",
            "--stdin",
            data=names,
            extra=env,
        ).split(b"\0")
        if any(value not in {b"unspecified", b"unset"} for value in attrs[2::3]):
            raise Failure(
                "environment",
                "Worker baseline uses a custom filter or encoding; explicit adapter support required",
            )
        # Reject special entries before checkout can create links or consult submodules.
        for row in filter(None, git(repo, "ls-tree", "-rz", head).split(b"\0")):
            metadata, name = row.split(b"\t", 1)
            safe_path(name.decode())
            if metadata.split()[0] not in {b"100644", b"100755"}:
                raise Failure("environment", "Worker baseline contains an unsupported Git entry")
        git(repo, "checkout-index", "--all", "--force", extra=env)
        return capture(repo, names.split(b"\0"), source=destination)
