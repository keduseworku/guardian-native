"""Native task lifecycle, frozen acceptance and exact-candidate review."""

import json
import os
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

from . import execution, spec, trees
from .trees import Failure, capture, changed, save, snapshot


@contextmanager
def locked(state):
    """OS-owned advisory lock: interruption releases ownership, never leaves a stale lock."""
    state.mkdir(parents=True, exist_ok=True)
    with (state / "operation.lock").open("a+b") as handle:
        if handle.seek(0, 2) == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise Failure(
                "environment", "Another operation owns this task lock; wait for the active command"
            ) from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load(state):
    try:
        return json.loads((state / "report.json").read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Failure("protocol", "No prompt captured; task is unverified") from exc


def owned(state, session):
    task = load(state)
    if task["session"] != session or not task["active"]:
        raise Failure("protocol", "No active request for this session")
    return task


def begin(cfg, state, payload):
    repo = trees.root(Path(payload["cwd"]))
    if repo != Path(cfg["repo"]).resolve():
        raise Failure("environment", "Hook invoked for a different worktree")
    if cfg.get("require_doctor"):
        doctor = (
            json.loads((state / "doctor.json").read_text(encoding="utf-8"))
            if (state / "doctor.json").exists()
            else {}
        )
        if not doctor.get("completed") or doctor.get("config_hash") != trees.digest(
            json.dumps(cfg, sort_keys=True).encode()
        ):
            raise Failure(
                "environment",
                "Run doctor for this registered configuration and worktree first",
            )
    session, request = payload.get("session_id"), payload.get("prompt")
    if not session or not isinstance(request, str) or not request.strip():
        raise Failure("protocol", "Prompt requires a session and original request")
    with locked(state):
        old = load(state) if (state / "report.json").exists() else None
        unfinished = old and old["status"] not in {"accepted", "no_changes", "abandoned"}
        if unfinished and old["session"] != session:
            raise Failure(
                "environment", "Another session owns unfinished work; use a native worktree"
            )
        if unfinished:
            if request == old.get("continuation"):
                old.pop("continuation", None)
                save(state / "report.json", old)
                return old
            old.update(active=True, pending_prompt=request, turn_base=capture(repo), mode=None)
            old["protocol_retries"] = 0
            save(state / "report.json", old)
            return old
        if old:
            save(state / "history" / (old["id"] + ".json"), old)
        task_id = uuid.uuid4().hex
        base = capture(repo)
        task = dict(
            id=task_id,
            session=session,
            request=request,
            base=base,
            turn_base=base,
            head=trees.text_git(repo, "rev-parse", "HEAD"),
            active=True,
            status="needs_spec",
            repairs=0,
            protocol_retries=0,
            candidate=None,
            contract=None,
            acceptance=None,
            suites=[],
            mode=None,
            pending_prompt=request,
            input=str(
                Path(tempfile.gettempdir()) / "guardian-native-inputs" / task_id / "spec.json"
            ),
        )
        Path(task["input"]).parent.mkdir(parents=True, exist_ok=True)
        save(state / "report.json", task)
        return task


def classify(cfg, state, session, mode):
    with locked(state):
        task = owned(state, session)
        if capture(Path(cfg["repo"])) != task["turn_base"]:
            raise Failure("protocol", "Classify the turn before further implementation edits")
        if mode == "resume" and not task["acceptance"]:
            raise Failure("protocol", "No frozen task to resume; prepare work first")
        pending = task.pop("pending_prompt", None)
        if mode in {"work", "clarify"} and pending and pending != task["request"]:
            task["request"] += "\n\nUSER FOLLOW-UP:\n" + pending
            task["needs_amendment"] = bool(task["acceptance"])
        task["implementation_intent"] = (
            task.get("implementation_intent", False) or mode != "discussion"
        )
        task["mode"] = mode
        save(state / "report.json", task)
        return task


def retry_protocol(call):
    for attempt in range(2):
        try:
            return call(attempt)
        except Failure as exc:
            if exc.kind != "protocol" or attempt:
                raise


def evidence_dir(state, task):
    path = state / "evidence" / task["id"] / uuid.uuid4().hex
    path.mkdir(parents=True)
    return path


def acceptance_command(cfg):
    return [cfg["python"], "-m", "unittest", "discover", "-s", ".guardian_checks", "-v"]


def write_suite(snap, suite):
    tests = snap / ".guardian_checks"
    tests.mkdir(exist_ok=True)
    (tests / "test_acceptance.py").write_text(suite["test_code"], encoding="utf-8", newline="\n")


def author_suite(cfg, state, task, contract, base, correction=None):
    output = evidence_dir(state, task)
    with tempfile.TemporaryDirectory(prefix="guardian-author-") as temporary:
        snap = Path(temporary) / "repo"
        snapshot(Path(cfg["repo"]), base, base, snap)
        prompt = spec.author_prompt(task["request"], contract) + spec.local_context(cfg, contract)
        if correction:
            prompt += (
                "\nIndependently investigate and correct this acceptance defect. Keep all valid requirements.\n"
                + json.dumps(correction)
            )
        authored = retry_protocol(
            lambda attempt: spec.validate_author(
                execution.ask(
                    cfg, snap, prompt, spec.AUTHOR_SCHEMA, output / f"author-{attempt}", "author"
                )
            )
        )
        write_suite(snap, authored)
        baseline = execution.check(cfg, snap, acceptance_command(cfg), output / "baseline.log")
    return dict(
        authored=authored,
        baseline=baseline,
        base=base,
        contract=contract,
        sha256=trees.digest(authored["test_code"].encode()),
        disposition="required",
    )


def prepare(cfg, state, session, contract):
    with locked(state):
        task = owned(state, session)
        repo = Path(cfg["repo"])
        spec.validate(contract)
        if task.get("mode") is None:
            if task["acceptance"]:
                raise Failure(
                    "protocol", "Classify follow-up as resume, clarify or discussion first"
                )
            task.update(mode="work", pending_prompt=None, implementation_intent=True)
        if task["mode"] == "discussion":
            raise Failure("protocol", "Discussion cannot prepare implementation")
        expected = task["turn_base"] if task.get("needs_amendment") else task["base"]
        if task["acceptance"] and not task.get("needs_amendment"):
            if contract != task["contract"]:
                raise Failure("protocol", "Changed requirements need a pre-edit clarify turn")
            return {"prepared": True, "methods": spec.context(cfg, contract)}
        if capture(repo) != expected:
            raise Failure(
                "protocol", "Implementation changed before independent acceptance; preserve work"
            )
        attempts = task.get("preparation_runs", 0)
        if attempts >= 2:
            raise Failure(
                "environment",
                "Preparation restart limit reached; inspect interrupted/failed evidence",
            )
        task.update(status="authoring", preparation_runs=attempts + 1)
        save(state / "report.json", task)
        try:
            suite = author_suite(cfg, state, task, contract, expected)
        except Failure as exc:
            task.update(status=exc.kind, detail=str(exc), active=exc.kind == "protocol")
            save(state / "report.json", task)
            raise
        if capture(repo) != expected:
            raise Failure("protocol", "Worktree changed during authoring")
        task["suites"].append(suite)
        task.update(
            contract=contract,
            acceptance=suite["authored"],
            baseline=suite["baseline"],
            status="prepared",
            needs_amendment=False,
            preparation_runs=0,
        )
        save(state / "report.json", task)
        return {
            "prepared": True,
            "baseline": suite["baseline"],
            "methods": spec.context(cfg, contract),
        }


def snapshot_check(cfg, task, candidate, command, output, suite=None):
    with tempfile.TemporaryDirectory(prefix="guardian-check-") as temporary:
        snap = Path(temporary) / "repo"
        snapshot(Path(cfg["repo"]), task["base"], candidate, snap)
        if suite:
            write_suite(snap, suite["authored"])
        return execution.check(cfg, snap, command, output)


def adjudicate(cfg, state, task, candidate, index, failure):
    """A failed generated test may be corrected only by a separate baseline-only author."""
    suite = task["suites"][index]
    out = evidence_dir(state, task)
    with tempfile.TemporaryDirectory(prefix="guardian-dispute-") as temporary:
        snap = Path(temporary) / "repo"
        snapshot(Path(cfg["repo"]), task["base"], candidate, snap)
        write_suite(snap, suite["authored"])
        prompt = (
            "Investigate this failed acceptance against the ORIGINAL REQUEST. Read code and "
            "test, independently derive expected behavior. Classify code, tests, environment, "
            "or unclear. A tests verdict requires a concrete demonstrable test defect and "
            "corrected expectation. Never excuse incorrect code or weaken a requirement.\n"
            + json.dumps(
                dict(
                    request=task["request"],
                    contract=suite["contract"],
                    failure=failure,
                    test=suite["authored"],
                    failure_log=Path(failure["log"]).read_text(encoding="utf-8")[-24000:],
                )
            )
        )
        verdict = retry_protocol(
            lambda attempt: spec.validate_dispute(
                execution.ask(
                    cfg, snap, prompt, spec.DISPUTE_SCHEMA, out / f"dispute-{attempt}", "review"
                )
            )
        )
    task.setdefault("disputes", []).append(dict(suite=index, failure=failure, verdict=verdict))
    save(state / "report.json", task)
    if verdict["classification"] in {"environment", "unclear"}:
        raise Failure("environment", "Acceptance needs investigation: " + verdict["reason"])
    if verdict["classification"] == "code":
        raise Failure("candidate", verdict["reason"])
    if suite.get("replacement_for") is not None:
        raise Failure(
            "environment", "Replacement acceptance remains disputed; bounded reauthoring exhausted"
        )
    replacement = author_suite(
        cfg,
        state,
        task,
        suite["contract"],
        suite["base"],
        dict(original=suite["authored"], adjudication=verdict),
    )
    replacement["replacement_for"] = index
    suite["disposition"] = "replaced_after_independent_dispute"
    task["suites"].append(replacement)
    task["acceptance"] = replacement["authored"]
    save(state / "report.json", task)
    return replacement


def evaluate(cfg, state, task, candidate):
    repo, contract = Path(cfg["repo"]), task["contract"]
    contracts = [s["contract"] for s in task["suites"]]
    allowed = {p for c in contracts for p in c["allowed_paths"]}
    modified = changed(repo, task["base"], candidate)
    if any(not any(n == p or n.startswith(p.rstrip("/") + "/") for p in allowed) for n in modified):
        raise Failure("candidate", "Changes outside allowed paths: " + ", ".join(modified))
    for name in contract["context_paths"]:
        if name in modified and name not in contract["allowed_paths"]:
            raise Failure("candidate", "Read-only context changed: " + name)
    out = evidence_dir(state, task)
    task["checks"] = []
    # Every command sees a fresh candidate, without build artifacts from another check.
    for index, command in enumerate(cfg["checks"]):
        result = snapshot_check(cfg, task, candidate, command, out / f"team-{index}.log")
        task["checks"].append(result)
        if not result["passed"]:
            raise Failure("candidate", "Required team check failed: " + json.dumps(result))
    for index, suite in list(enumerate(task["suites"])):
        if suite["disposition"] != "required":
            continue
        result = snapshot_check(
            cfg, task, candidate, acceptance_command(cfg), out / f"acceptance-{index}.log", suite
        )
        task["checks"].append(result)
        if not result["passed"]:
            replacement = adjudicate(cfg, state, task, candidate, index, result)
            result["disposition"] = "replaced_after_independent_dispute"
            result = snapshot_check(
                cfg,
                task,
                candidate,
                acceptance_command(cfg),
                out / f"replacement-{index}.log",
                replacement,
            )
            task["checks"].append(result)
            if not result["passed"]:
                raise Failure(
                    "candidate", "Corrected required acceptance failed: " + json.dumps(result)
                )
    with tempfile.TemporaryDirectory(prefix="guardian-review-") as temporary:
        snap = Path(temporary) / "repo"
        snapshot(repo, task["base"], candidate, snap)
        prompt = spec.review_prompt(task["request"], contract, task["checks"])
        prompt += "\nAll retained acceptance contracts:\n" + json.dumps(contracts)
        prompt += spec.local_context(cfg, contract, review=True)
        verdict = retry_protocol(
            lambda attempt: spec.validate_review(
                execution.ask(
                    cfg, snap, prompt, spec.REVIEW_SCHEMA, out / f"review-{attempt}", "review"
                )
            )
        )
        task["review"] = verdict
        if not verdict["ready"]:
            raise Failure("candidate", json.dumps(verdict))
    if capture(repo) != candidate or trees.text_git(repo, "rev-parse", "HEAD") != task["head"]:
        raise Failure("protocol", "Native candidate changed during evaluation; approval is stale")


def finish(cfg, state, session):
    with locked(state):
        task = owned(state, session)
        repo = Path(cfg["repo"])
        candidate = capture(repo)
        task.update(candidate=candidate, status="evaluating")
        task.pop("review", None)
        save(state / "report.json", task)  # Interrupted evaluations are visibly unverified.
        try:
            if task.get("mode") in {"discussion", "waiting"}:
                if candidate != task["turn_base"]:
                    raise Failure("protocol", "Discussion turn changed implementation")
                task["status"] = "paused" if task.get("implementation_intent") else "no_changes"
                task["active"] = task["status"] == "paused"
            elif task.get("mode") is None and candidate == task["base"] and not task["acceptance"]:
                task.update(status="no_changes", active=False)
            else:
                if (
                    task.get("pending_prompt")
                    or not task["acceptance"]
                    or task.get("needs_amendment")
                ):
                    raise Failure(
                        "protocol", "Missing pre-edit classification/specification/acceptance"
                    )
                evaluate(cfg, state, task, candidate)
                task.update(status="accepted", active=False)
                (state / "change.patch").write_bytes(
                    trees.git(repo, "diff", "--binary", task["base"], candidate)
                )
        except Failure as exc:
            task.update(status=exc.kind, detail=str(exc))
            if exc.kind == "candidate":
                task["repairs"] += 1
                task["active"] = task["repairs"] <= cfg.get("repairs", 2)
            elif exc.kind == "protocol":
                task["protocol_retries"] += 1
                task["active"] = task["protocol_retries"] <= 1
            else:
                task["active"] = False
        save(state / "report.json", task)
        return task
