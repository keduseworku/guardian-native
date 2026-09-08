"""Personal installation and registration; never write team repository configuration."""

import copy
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
import uuid
from pathlib import Path

from . import execution, trees
from .trees import Failure, digest, save
from .workflow import locked


def shell(argv):
    return subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)


def prefix(home):
    return [sys.executable, "-I", "-m", "guardian_next.cli", "--home", str(home)]


def settings(text, values):
    """Edit only simple owned settings, preserving every unrelated TOML line."""
    expected = copy.deepcopy(tomllib.loads(text))
    for section, key, value in values:
        target = expected.setdefault(section, {}) if section else expected
        if value is None:
            target.pop(key, None)
        else:
            target[key] = value
    lines = text.splitlines(keepends=True)
    for section, key, value in values:
        current, start, found = "", 0, None
        for i, line in enumerate(lines):
            match = re.match(r"^\s*\[{1,2}([^\[\]]+)\]{1,2}\s*(?:#.*)?$", line.strip())
            if match:
                if current == section:
                    break
                current = match[1].strip()
                if current == section:
                    start = i + 1
            if current == section and re.match(r"^\s*" + re.escape(key) + r"\s*=", line):
                found = i
        replacement = f"{key} = {json.dumps(value)}\n" if value is not None else ""
        if found is not None:
            lines[found] = replacement
        elif value is not None:
            if section and not any(
                re.match(r"^\s*\[" + re.escape(section) + r"\]\s*(?:#.*)?$", line.strip())
                for line in lines
            ):
                lines += [f"\n[{section}]\n", replacement]
            else:
                lines.insert(start if section else 0, replacement)
    result = "".join(lines)
    parsed = tomllib.loads(result)
    if parsed != expected:
        raise Failure(
            "environment", "Complex TOML settings need a targeted manual merge; original preserved"
        )
    for section, key, value in values:
        actual = parsed.get(section, {}).get(key) if section else parsed.get(key)
        if actual != value:
            raise Failure("environment", "Complex config setting needs manual merge: " + key)
    return result


def install(home, codex_home):
    home, codex_home = home.resolve(), codex_home.resolve()
    home.mkdir(parents=True, exist_ok=True)
    codex_home.mkdir(parents=True, exist_ok=True)
    with locked(home):
        manifest_path = home / "installation.json"
        if manifest_path.exists():
            return {"installed": True, "already_installed": True, "manifest": str(manifest_path)}
        hooks_path, config_path = codex_home / "hooks.json", codex_home / "config.toml"
        rule_path = codex_home / "rules/guardian-native.rules"
        if rule_path.exists():
            raise Failure(
                "environment",
                "Existing guardian-native.rules preserved; inspect prior installation",
            )
        original = {
            str(p): p.read_bytes() if p.exists() else None
            for p in (hooks_path, config_path, rule_path)
        }
        hooks = json.loads((original[str(hooks_path)] or b'{"hooks":{}}').decode("utf-8"))
        config = (original[str(config_path)] or b"").decode("utf-8")
        parsed = tomllib.loads(config)
        prior_settings = [
            ["", "model", parsed.get("model")],
            ["", "model_reasoning_effort", parsed.get("model_reasoning_effort")],
            ["features", "hooks", parsed.get("features", {}).get("hooks")],
        ]
        config = settings(
            config,
            [
                ("", "model", "gpt-5.6-sol"),
                ("", "model_reasoning_effort", "high"),
                ("features", "hooks", True),
            ],
        )
        commands = []
        for event in ("UserPromptSubmit", "Stop"):
            command = shell(prefix(home) + ["hook", event])
            commands.append(command)
            hooks.setdefault("hooks", {}).setdefault(event, []).append(
                {"hooks": [{"type": "command", "command": command, "timeout": 1800}]}
            )
        rules = "".join(
            "prefix_rule(pattern = "
            + json.dumps(prefix(home) + [action])
            + ', decision = "allow", justification = "Guardian personal task control.")\n'
            for action in ("prepare", "classify", "status")
        )
        backup = home / "backups" / uuid.uuid4().hex
        backup.mkdir(parents=True)
        for i, content in enumerate(original.values()):
            if content is not None:
                (backup / str(i)).write_bytes(content)
        try:
            save(hooks_path, hooks)
            config_path.write_text(config, encoding="utf-8")
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(rules, encoding="utf-8")
            save(
                manifest_path,
                dict(
                    codex_home=str(codex_home),
                    commands=commands,
                    backup=str(backup),
                    prior_settings=prior_settings,
                    paths=list(original),
                    absent=[p for p, b in original.items() if b is None],
                    installed={
                        str(p): digest(p.read_bytes()) for p in (hooks_path, config_path, rule_path)
                    },
                ),
            )
        except BaseException:
            for name, content in original.items():
                path = Path(name)
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)
            raise
    return {
        "installed": True,
        "manifest": str(manifest_path),
        "note": "Restart Codex; managed settings and task model overrides still require laptop acceptance.",
    }


def uninstall(home):
    with locked(home):
        path = home / "installation.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for i, name in enumerate(manifest["paths"]):
            target = Path(name)
            if not target.exists():
                continue
            if digest(target.read_bytes()) == manifest["installed"][name]:
                if name in manifest["absent"]:
                    target.unlink()
                else:
                    target.write_bytes((Path(manifest["backup"]) / str(i)).read_bytes())
            elif target.name == "hooks.json":
                hooks = json.loads(target.read_text(encoding="utf-8"))
                for event, groups in hooks.get("hooks", {}).items():
                    for group in groups:
                        group["hooks"] = [
                            h
                            for h in group.get("hooks", [])
                            if h.get("command") not in manifest["commands"]
                        ]
                    hooks["hooks"][event] = [g for g in groups if g.get("hooks")]
                save(target, hooks)
            elif target.name == "config.toml":
                text = target.read_text(encoding="utf-8")
                parsed = tomllib.loads(text)
                owned = {"model": "gpt-5.6-sol", "model_reasoning_effort": "high", "hooks": True}
                restore = [
                    v
                    for v in manifest["prior_settings"]
                    if (parsed.get(v[0], {}).get(v[1]) if v[0] else parsed.get(v[1])) == owned[v[1]]
                ]
                target.write_text(settings(text, restore), encoding="utf-8")
            else:
                raise Failure(
                    "environment",
                    "Modified Guardian rule preserved; remove its entries manually: " + name,
                )
        path.rename(home / "last-uninstall.json")
    return {"uninstalled": True, "evidence_retained": str(home)}


def common(repo):
    directory = Path(trees.text_git(repo, "rev-parse", "--git-common-dir"))
    return str((Path(repo) / directory).resolve())


def registration_path(home, repo):
    return home / "registrations" / (digest(common(repo).encode()) + ".json")


def register(home, repo, cfg):
    git_tool = trees.git_info(repo)
    repo = trees.root(repo)
    if home.resolve().is_relative_to(repo):
        raise Failure("environment", "Guardian home must be outside the editing repository")
    for key in ("python", "codex"):
        found = shutil.which(cfg.get(key, ""))
        if not found:
            raise Failure("environment", "Executable unavailable: " + key)
        cfg[key] = str(Path(found).absolute())
    if not isinstance(cfg.get("checks"), list) or not cfg["checks"]:
        raise Failure(
            "protocol", "Register the actual required team checks; no implicit unittest default"
        )
    for command in cfg["checks"]:
        if (
            not isinstance(command, list)
            or not command
            or any(not isinstance(a, str) or not a for a in command)
        ):
            raise Failure("protocol", "Each check must be an argv array")
    forbidden = {"HOME", "USERPROFILE", "CODEX_HOME", "PYTHONPATH"}
    if any(
        k.upper() in forbidden
        or any(s in k.upper() for s in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))
        for k in cfg.get("check_env", {})
    ):
        raise Failure(
            "protocol", "Check environment may not contain credentials or redirect homes/imports"
        )
    cfg.update(
        git=git_tool["path"],
        require_doctor=True,
        author_model="gpt-5.6-sol",
        review_model="gpt-5.6-sol",
        research=str(Path(__file__).parent / "resources"),
        git_common=common(repo),
    )
    path = registration_path(home, repo)
    cfg["corrections_file"] = str(path.with_suffix(".corrections.json"))
    save(path, cfg)
    return {"registered": str(repo), "configuration": str(path), "doctor_required": True}


def resolve(home, cwd):
    repo = trees.root(Path(cwd))
    path = registration_path(home, repo)
    if not path.exists():
        return None, None
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if cfg.get("git") and cfg["git"] != trees.executable():
        raise Failure(
            "environment",
            "Git executable changed since registration. Set GUARDIAN_GIT to "
            + cfg["git"]
            + " or re-register and run doctor with the intended Git.",
        )
    cfg["repo"] = str(repo)
    state = home / "worktrees" / digest(str(repo).encode())
    state.mkdir(parents=True, exist_ok=True)
    return cfg, state


def doctor(home, repo):
    cfg, state = resolve(home, repo)
    if cfg is None:
        raise Failure("environment", "Repository is not registered")
    import tempfile

    report = {
        "platform": sys.platform,
        "tools": {},
        "team_files_written": False,
        "protocol": execution.DOCTOR_PROTOCOL,
    }
    for key in ("python", "codex"):
        run = execution.bounded_run(
            [cfg[key], "--version"], cwd=Path(repo), env=os.environ.copy(), timeout=30
        )
        report["tools"][key] = {
            "path": cfg[key],
            "version": (run.stdout + run.stderr).strip(),
            "exit_code": run.returncode,
        }
    report["tools"]["git"] = trees.git_info(Path(repo))
    report["conda"] = shutil.which("conda")
    run = execution.bounded_run(
        [
            cfg["python"],
            "-c",
            "import importlib.util,json; print(json.dumps({n:importlib.util.find_spec(n) is not None for n in ['pytest','hypothesis','coverage','importlinter']}))",
        ],
        cwd=Path(repo),
        env=os.environ.copy(),
        timeout=30,
    )
    report["python_capabilities"] = json.loads(run.stdout)
    report["gitleaks"] = shutil.which("gitleaks")
    report["configured_checks"] = cfg["checks"]
    report["checks"] = []
    report["review_preflight"] = {"passed": False, "detail": "Not run"}
    try:
        with tempfile.TemporaryDirectory(prefix="guardian-doctor-") as temporary:
            baseline = trees.capture(Path(repo))
            for i, command in enumerate(cfg["checks"]):
                snap = Path(temporary) / f"check-{i}"
                trees.snapshot(Path(repo), baseline, baseline, snap)
                report["checks"].append(
                    execution.check(cfg, snap, command, state / f"doctor-{i}.log")
                )
            report["review_preflight"] = execution.review_preflight(
                cfg, Path(temporary) / "review-probe", state / "doctor-review" / uuid.uuid4().hex
            )
    except (Failure, OSError) as exc:
        report["error"] = str(exc)
        report["failure_kind"] = getattr(exc, "kind", "environment")
    report["completed"] = (
        not report.get("error")
        and report["review_preflight"]["passed"]
        and all(t["exit_code"] == 0 for t in report["tools"].values() if isinstance(t, dict))
    )
    report["passed"] = report["completed"] and all(c["passed"] for c in report["checks"])
    report["config_hash"] = digest(json.dumps(cfg, sort_keys=True).encode())
    save(state / "doctor.json", report)
    return report
