"""Bound child output and duration, including descendants that retain output handles."""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import threading
import time
from contextlib import suppress
from pathlib import Path

from .trees import Failure, capture, git, save


def GuardianError(message):
    return Failure("environment", message)


def _terminate(process: subprocess.Popen) -> None:
    if os.name == "nt":
        taskkill = Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "System32/taskkill.exe"
        subprocess.run(
            [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            timeout=10,
            check=False,
        )
    else:
        # A completed group may already have disappeared or been reaped by its host.
        with suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGKILL)
    if process.poll() is None:
        process.kill()
    process.wait(timeout=10)


def bounded_run(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float,
    max_bytes: int = 8 * 1024 * 1024,
    input_text: str | None = None,
) -> subprocess.CompletedProcess:
    """Each stream has a hard in-memory cap; excessive output is a failed operation."""
    if input_text is not None and len(input_text.encode("utf-8")) > 1024 * 1024:
        raise GuardianError("child input exceeds 1 MB")
    options = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **options,
    )
    buffers = [bytearray(), bytearray()]
    overflow = threading.Event()

    def drain(stream, output):
        try:
            while block := stream.read(8192):
                if len(output) + len(block) > max_bytes:
                    overflow.set()
                    return
                output.extend(block)
        finally:
            stream.close()

    threads = [
        threading.Thread(target=drain, args=(stream, output), daemon=True)
        for stream, output in zip((process.stdout, process.stderr), buffers, strict=True)
    ]
    if input_text is not None:

        def feed():
            try:
                process.stdin.write(input_text.encode("utf-8"))
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            finally:
                # Windows can reject the final flush after the child closes its input pipe.
                with suppress(OSError):
                    process.stdin.close()

        threads.append(threading.Thread(target=feed, daemon=True))
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + timeout
    try:
        while process.poll() is None or any(thread.is_alive() for thread in threads):
            if overflow.is_set():
                raise GuardianError(f"child output exceeded {max_bytes} bytes per stream")
            if time.monotonic() >= deadline:
                raise GuardianError(f"child timed out after {timeout}s")
            time.sleep(0.01)
        if overflow.is_set():
            raise GuardianError(f"child output exceeded {max_bytes} bytes per stream")
    except BaseException:
        _terminate(process)
        for thread in threads:
            thread.join(timeout=1)
        raise
    return subprocess.CompletedProcess(
        argv,
        process.returncode,
        buffers[0].decode("utf-8", errors="replace"),
        buffers[1].decode("utf-8", errors="replace"),
    )


def environment(cwd, authenticated=False):
    keep = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TMP", "TEMP", "TMPDIR"}
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    home = Path.home() if authenticated else cwd / ".runtime"
    env.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "CI": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "PIP_NO_INDEX": "1",
            "UV_OFFLINE": "1",
        }
    )
    if authenticated:
        env["CODEX_HOME"] = os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
    else:
        env["PYTHONPATH"] = os.pathsep.join([str(cwd / "src"), str(cwd)])
        home.mkdir(exist_ok=True)
        env.update({"TMPDIR": str(home), "TMP": str(home), "TEMP": str(home)})
    return env


def ask(cfg, cwd, prompt, schema, output, role):
    """One read-only role; invalid structured output is a protocol retry, not a code repair."""
    output.mkdir(parents=True, exist_ok=True)
    save(output / "schema.json", schema)
    (output / "prompt.txt").write_text(prompt, encoding="utf-8")
    argv = [
        cfg["codex"],
        "exec",
        "--ephemeral",
        "--ignore-rules",
        "--ignore-user-config",
        "--disable",
        "hooks",
        "--model",
        cfg[role + "_model"],
        "--sandbox",
        "read-only",
        "--json",
        "--output-schema",
        str(output / "schema.json"),
        "--output-last-message",
        str(output / "answer.json"),
        "-c",
        'model_reasoning_effort="high"',
        "-c",
        'approval_policy="never"',
        "-",
    ]
    start = time.monotonic()
    receipt = {"role": role, "model": cfg[role + "_model"], "usage": None}
    try:
        result = bounded_run(
            argv,
            cwd=cwd,
            env=environment(cwd, True),
            timeout=cfg.get("model_seconds", 600),
            input_text=prompt,
        )
        (output / "events.jsonl").write_text(result.stdout)
        (output / "stderr.txt").write_text(result.stderr)
        for line in result.stdout.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "turn.completed":
                receipt["usage"] = event.get("usage")
        if result.returncode:
            raise Failure("environment", f"{role} could not run: {result.stderr[-1200:]}")
        try:
            return json.loads((output / "answer.json").read_text())
        except (OSError, ValueError) as exc:
            raise Failure("protocol", f"{role} did not return structured output") from exc
    finally:
        receipt["seconds"] = round(time.monotonic() - start, 3)
        save(output / "receipt.json", receipt)


def check(cfg, cwd, argv, output):
    """Repository programs run only inside the native OS sandbox, never with auth env."""
    args = [
        cfg["codex"],
        "sandbox",
        "--permission-profile",
        "guardian-check",
        "-c",
        'permissions.guardian-check.filesystem={":root"="read",":workspace_roots"="write"}',
        "--cd",
        str(cwd),
        "--sandbox-state-disable-network",
        "-c",
        "permissions.guardian-check.network.enabled=false",
    ]
    if os.name == "nt":
        args += ["-c", 'windows.sandbox="unelevated"']
    args += ["--", *argv]
    env = environment(cwd)
    env.update(cfg.get("check_env", {}))
    # Conda DLLs and console scripts must resolve to the registered interpreter.
    python_dir = str(Path(cfg["python"]).parent)
    env["PATH"] = os.pathsep.join(
        [
            python_dir,
            str(Path(python_dir) / "Scripts"),
            str(Path(python_dir) / "Library/bin"),
            env.get("PATH", ""),
        ]
    )
    source_paths = git(cwd, "ls-files", "-c", "-o", "--exclude-standard", "-z").split(b"\0")
    before = capture(cwd, source_paths)
    result = bounded_run(args, cwd=cwd, env=env, timeout=cfg.get("test_seconds", 120))
    log = result.stdout + result.stderr
    output.write_text(log, encoding="utf-8")
    if capture(cwd, source_paths) != before:
        raise Failure(
            "protocol", "Check modified the candidate or frozen test source: " + str(output)
        )
    # Infrastructure failures are not actionable candidate defects.
    if any(
        s in log
        for s in (
            "sandbox-exec: sandbox_apply",
            "failed to create sandbox",
            "Operation not permitted: sandbox",
        )
    ):
        raise Failure("environment", "Native sandbox unavailable; see " + str(output))
    if result.returncode in cfg.get("environment_exit_codes", []):
        raise Failure("environment", "Configured infrastructure exit code: " + str(output))
    failures = re.findall(r"^(?:FAIL|ERROR): (.+)$", log, re.MULTILINE)
    if "Ran 0 tests" in log:
        raise Failure("protocol", "Test command discovered no tests: " + str(output))
    return {
        "passed": result.returncode == 0,
        "exit_code": result.returncode,
        "failed_tests": failures[:30],
        "log": str(output),
    }
