"""User lifecycle hooks and explicit, session-bound preparation commands."""

import argparse
import json
import os
import sys
from pathlib import Path

from . import execution, spec, trees, workflow
from . import integration as native
from .trees import Failure, save


def hook(cfg, state, home, event, payload):
    if event == "UserPromptSubmit":
        doctor_path = state / "doctor.json"
        doctor = json.loads(doctor_path.read_text(encoding="utf-8")) if doctor_path.exists() else {}
        if cfg.get("require_doctor") and (
            doctor.get("protocol") != execution.DOCTOR_PROTOCOL
            or not doctor.get("completed")
            or doctor.get("config_hash") != trees.digest(json.dumps(cfg, sort_keys=True).encode())
        ):
            doctor = native.doctor(home, cfg["repo"])
        task = workflow.begin(cfg, state, payload)
        args = native.prefix(home)
        binding = ["--repo", cfg["repo"], "--session", task["session"]]
        classify = native.shell(args + ["classify", *binding, "--mode"])
        prepare = native.shell(args + ["prepare", *binding, "--file", task["input"]])
        context = (
            "Guardian is active in this native checkout. Use Sol/high for direct implementation; "
            "the existing worker must explicitly dispatch Luna only. "
            "Read repository guidance and accepted callers/examples. Read the routing/practices at "
            + str(Path(cfg["research"]) / "WORKFLOW.md")
            + ". "
            "Before further edits classify this turn by running " + classify + " <mode> alone. "
            "Modes: work for initial implementation, resume for the SAME frozen requirements, "
            "clarify for new or corrected requirements, discussion for a discussion-only user request, "
            "waiting when implementation needs a missing user decision before it can proceed. "
            "Discussion retains unfinished intent; clarify requires new independent acceptance "
            "before further edits. Do not discard the original request. "
            "For work/clarify, derive examples and domain boundaries yourself using available "
            "evidence; ask the user only for missing business decisions. Write specification JSON "
            "to this exact unique path: " + task["input"] + ". Fields: objective, design, outcome, "
            "milestone, task (nonempty strings); allowed_paths, context_paths, acceptance (string "
            "arrays); examples (criterion matching acceptance, input, expected, derivation); "
            "edges (strings); kind (feature/fix/refactor). Include a justified worked example per "
            "criterion. Run " + prepare + " alone before edits. It freezes independent acceptance. "
            "Preparation can take several minutes: use a long-lived exec call (at least 900 seconds "
            "if the tool has a hard timeout), and poll its returned session until completion. "
            "An initial tool yield is not failure. Do not interrupt or rerun a still-active preparation. "
            "Use the selected methods returned by preparation. Resume keeps frozen acceptance. "
            "Keep changes task-proportionate and preserve the user's staging. The Stop hook "
            "checks and independently reviews exact native bytes, then requests bounded repair "
            "when needed. Do not modify Guardian state or read frozen tests; only write the bound "
            "spec input and use the commands. Do not commit or push as part of this workflow. "
            "Report unverified or interrupted work honestly; no previous approval covers later edits. "
            "A Stop continuation is already classified; follow its correction without reauthoring. "
            "Required checks: " + json.dumps(cfg["checks"]) + ". "
            "Original task request: " + task["request"]
        )
        if doctor and not doctor.get("passed"):
            context += (
                "\nBaseline checks failed. Inspect these results before planning; resolve missing environment prerequisites and preserve known code failures as regressions. These failures are not waived at completion: "
                + json.dumps(doctor["checks"])
            )
        if task["contract"]:
            context += "\nFrozen contract: " + json.dumps(task["contract"])
        context += spec.local_context(cfg, task["contract"])
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}
    task = workflow.finish(cfg, state, payload.get("session_id"))
    if task["status"] in {"accepted", "no_changes", "paused"}:
        return {
            "systemMessage": f"Guardian {task['status']}; exact candidate {task['candidate']}; report: {state / 'report.json'}"
        }
    detail = f"Guardian {task['status']}: {task.get('detail', '')}"
    if task["active"]:
        instruction = (
            "Repair the candidate"
            if task["status"] == "candidate"
            else "Resolve the precondition; retry the same evaluation"
        )
        reason = detail + "\n" + instruction + ". Then finish again."
        with workflow.locked(state):
            if workflow.load(state) != task:
                raise Failure(
                    "protocol", "Task changed before continuation; inspect current status"
                )
            task["continuation"] = reason
            save(state / "report.json", task)
        return {"decision": "block", "reason": reason}
    return {
        "continue": False,
        "systemMessage": detail + ". Completion UNVERIFIED; inspect the report.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", default=str(Path.home() / ".guardian-native"))
    commands = parser.add_subparsers(dest="action", required=True)
    install = commands.add_parser("install")
    install.add_argument(
        "--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
    )
    commands.add_parser("uninstall")
    register = commands.add_parser("register")
    register.add_argument("--repo", required=True)
    register.add_argument("--config", required=True)
    doctor = commands.add_parser("doctor")
    doctor.add_argument("--repo", required=True)
    hooks = commands.add_parser("hook")
    hooks.add_argument("event", choices=["UserPromptSubmit", "Stop"])
    for name in (
        "prepare",
        "classify",
        "status",
        "worker-import",
        "worker-preflight",
        "abandon",
        "correction",
    ):
        command = commands.add_parser(name)
        command.add_argument("--repo", required=True)
        command.add_argument("--session", required=True)
        if name in {"prepare", "worker-import", "correction"}:
            command.add_argument("--file", required=True)
        if name == "worker-import":
            command.add_argument("--exit-code", required=True, type=int)
        if name == "classify":
            command.add_argument(
                "--mode",
                choices=["work", "resume", "clarify", "discussion", "waiting"],
                required=True,
            )
    args = parser.parse_args()
    home = Path(args.home).resolve()
    try:
        if args.action == "install":
            result = native.install(home, Path(args.codex_home))
        elif args.action == "uninstall":
            result = native.uninstall(home)
        elif args.action == "register":
            result = native.register(
                home, Path(args.repo), json.loads(Path(args.config).read_text(encoding="utf-8"))
            )
        elif args.action == "doctor":
            result = native.doctor(home, Path(args.repo))
        else:
            payload = (
                json.loads(sys.stdin.buffer.read(128 * 1024)) if args.action == "hook" else None
            )
            cfg, state = native.resolve(home, payload["cwd"] if payload else args.repo)
            if cfg is None:
                if args.action != "hook":
                    raise Failure("environment", "Repository is not registered")
                result = {}
            elif args.action == "hook":
                result = hook(cfg, state, home, args.event, payload)
            elif args.action == "prepare":
                task = workflow.owned(state, args.session)
                if Path(args.file).resolve() != Path(task["input"]).resolve():
                    raise Failure(
                        "protocol", "Use the unique preparation path issued for this task"
                    )
                result = workflow.prepare(
                    cfg,
                    state,
                    args.session,
                    json.loads(Path(args.file).read_text(encoding="utf-8")),
                )
            elif args.action == "classify":
                task = workflow.classify(cfg, state, args.session, args.mode)
                result = {
                    "mode": task["mode"],
                    "prepared": bool(task["acceptance"]),
                    "input": task["input"],
                }
            elif args.action == "status":
                task = workflow.load(state)
                if task["session"] != args.session:
                    raise Failure("protocol", "Session does not own this task")
                result = {
                    k: task.get(k)
                    for k in ("status", "request", "input", "candidate", "repairs", "detail")
                }
            elif args.action == "abandon":
                with workflow.locked(state):
                    task = workflow.load(state)
                    if task["session"] != args.session:
                        raise Failure("protocol", "Only the owning session may abandon a task")
                    task.update(status="abandoned", active=False)
                    save(state / "report.json", task)
                result = {"abandoned": True, "files_preserved": True}
            elif args.action == "worker-preflight":
                from .worker import preflight

                result = preflight(cfg, state, args.session)
            elif args.action == "worker-import":
                from .worker import accept_result

                result = accept_result(
                    cfg,
                    state,
                    args.session,
                    json.loads(Path(args.file).read_text(encoding="utf-8")),
                    args.exit_code,
                )
            else:
                workflow.owned(state, args.session)
                correction = json.loads(Path(args.file).read_text(encoding="utf-8"))
                if correction.get("confirmed") is not True or not all(
                    correction.get(k) for k in ("paths", "rule", "evidence", "regression")
                ):
                    raise Failure(
                        "protocol", "Correction requires confirmed scope, evidence and regression"
                    )
                for path in correction["paths"]:
                    trees.safe_path(path)
                path = Path(cfg["corrections_file"])
                entries = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
                if correction not in entries:
                    entries.append(correction)
                save(path, entries)
                result = {"recorded": True}
    except (Failure, OSError, ValueError, KeyError, TypeError) as exc:
        if args.action == "hook":
            # Outside Git / unregistered projects must not interfere with other hooks.
            if (
                isinstance(exc, Failure)
                and args.action == "hook"
                and "not a git repository" in str(exc)
            ):
                result = {}
            else:
                result = {
                    "systemMessage": "Guardian unavailable; completion UNVERIFIED: " + str(exc)
                }
                if args.event == "Stop":
                    result["continue"] = False
        else:
            print(json.dumps({"error": str(exc), "kind": getattr(exc, "kind", "environment")}))
            return 1
    print(json.dumps(result))
    return 1 if args.action == "doctor" and not result.get("passed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
