"""Import the expected existing-worker result envelope; launching remains worker-owned."""

import json
import uuid
from pathlib import Path

from . import integration, trees, workflow
from .trees import Failure

MAX_BYTES = 16 * 1024 * 1024


def content(repo, name):
    trees.safe_path(name)
    path = repo / name
    if path.is_symlink() or not path.resolve().is_relative_to(repo.resolve()):
        raise Failure("protocol", "Worker path escapes through a symlink")
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise Failure("protocol", "Worker file is not a bounded regular file")
    return path.read_bytes()


def write(repo, name, data):
    path = repo / name
    if data is None:
        path.unlink(missing_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(".guardian-worker-" + uuid.uuid4().hex)
        try:
            temporary.write_bytes(data)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def accept_result(cfg, state, session, result, exit_code):
    with workflow.locked(state):
        task = workflow.owned(state, session)
        if (
            not task["acceptance"]
            or task.get("needs_amendment")
            or task.get("pending_prompt")
            or task.get("mode") == "discussion"
        ):
            raise Failure("protocol", "Worker integration requires prepared, current acceptance")
        if type(exit_code) is not int or exit_code != 0:
            raise Failure("environment", "Worker process did not exit successfully")
        for field in ("success", "execution_success", "work_product_created"):
            if result.get(field) is not True:
                raise Failure("protocol", "Worker does not confirm " + field)
        if result.get("failure_classification", "missing") is not None:
            raise Failure("protocol", "Worker failure classification is not null")
        provenance = result.get("validation_provenance", {})
        if (
            provenance.get("status") != "verified"
            or not provenance.get("before_snapshot_id")
            or provenance["before_snapshot_id"] != provenance.get("after_snapshot_id")
        ):
            raise Failure("protocol", "Worker provenance is absent or inconsistent")
        product = result.get("work_product", {})
        if product.get("success") is not True or not isinstance(product.get("worktree_path"), str):
            raise Failure("protocol", "Worker result lacks a successful worktree")
        repo = Path(cfg["repo"])
        worker = Path(product["worktree_path"]).resolve()
        registered = [
            Path(s[len("worktree ") :]).resolve()
            for s in trees.text_git(repo, "worktree", "list", "--porcelain").splitlines()
            if s.startswith("worktree ")
        ]
        if (
            worker == repo.resolve()
            or worker not in registered
            or integration.common(worker) != integration.common(repo)
        ):
            raise Failure("protocol", "Worker is not a separate worktree of this repository")
        branch = trees.text_git(worker, "branch", "--show-current")
        if not branch or branch != product.get("branch"):
            raise Failure("protocol", "Worker branch differs from result")
        baseline = trees.capture(repo)
        worker_head = trees.text_git(worker, "rev-parse", "HEAD")
        if trees.text_git(worker, "rev-parse", "HEAD^{tree}") != baseline:
            raise Failure("protocol", "Worker baseline differs from native candidate; redispatch")
        if trees.text_git(repo, "rev-parse", "HEAD") != task["head"]:
            raise Failure("protocol", "Native HEAD changed since preparation")
        candidate = trees.capture(worker)
        changed = trees.changed(worker, baseline, candidate)
        declared = product.get("changed_files")
        allowed = task["contract"]["allowed_paths"]
        if (
            not isinstance(declared, list)
            or not all(isinstance(p, str) for p in declared)
            or set(changed) != set(declared)
            or not changed
        ):
            raise Failure("protocol", "Worker changed-file set differs from its result")
        if any(
            not any(n == p or n.startswith(p.rstrip("/") + "/") for p in allowed) for n in changed
        ):
            raise Failure("protocol", "Worker delta exceeds authorized scope")
        checks = product.get("validation")
        if (
            not isinstance(checks, list)
            or not checks
            or not all(isinstance(c, dict) and c.get("outcome") == "passed" for c in checks)
        ):
            raise Failure("protocol", "Worker validation is missing or failed")
        for line in trees.text_git(worker, "diff", "--raw", baseline, candidate).splitlines():
            old, new = line.split()[:2]
            if old.lstrip(":") not in {"000000", "100644"} or new not in {"000000", "100644"}:
                raise Failure("protocol", "Worker import supports ordinary file modes only")
        before = {p: content(repo, p) for p in changed}
        after = {p: content(worker, p) for p in changed}
        if sum(len(b or b"") for b in after.values()) > MAX_BYTES:
            raise Failure("protocol", "Worker delta exceeds 16 MB")
        if (
            trees.capture(repo) != baseline
            or trees.capture(worker) != candidate
            or trees.text_git(worker, "rev-parse", "HEAD") != worker_head
        ):
            raise Failure("protocol", "Worker/native source drifted during inspection")
        applied = []
        try:
            for name in changed:
                if content(repo, name) != before[name]:
                    raise Failure("protocol", "Native destination changed before application")
                applied.append(name)
                write(repo, name, after[name])
            if (
                trees.capture(repo) != candidate
                or trees.text_git(repo, "rev-parse", "HEAD") != task["head"]
            ):
                raise Failure("protocol", "Imported bytes differ from worker candidate")
        except BaseException:
            for name in reversed(applied):
                if content(repo, name) == after[name]:
                    write(repo, name, before[name])
            raise
        receipt = dict(
            worker_task_id=result.get("task_id"),
            worker_branch=branch,
            worker_head=worker_head,
            baseline=baseline,
            candidate=candidate,
            result_sha256=trees.digest(json.dumps(result, sort_keys=True).encode()),
            changed_files=changed,
            validation=checks,
            usage=result.get("usage"),
            note="Imported, not approved; native acceptance and review are still required.",
        )
        task.setdefault("worker_imports", []).append(receipt)
        task.update(status="prepared", candidate=candidate)
        task.pop("review", None)
        trees.save(state / "report.json", task)
        return receipt
