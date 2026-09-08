"""Laptop regressions: real Git and test processes; model/sandbox adapters simulated."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import test_outcomes
import test_worker
from test_outcomes import AUTHOR, CHECK, REVIEW

from guardian_next import execution, integration, trees, worker, workflow


class LaptopTests(unittest.TestCase):
    setUp = test_outcomes.WorkflowTests.setUp
    prepare = test_outcomes.WorkflowTests.prepare
    result = test_worker.WorkerTests.result

    def test_snapshot_and_registration_avoid_unsupported_git_227_options(self):
        original = trees.git

        def old_git(repo, *args, **kwargs):
            if "-b" in args or "--path-format=absolute" in args:
                raise trees.Failure("environment", "Option unavailable in Git 2.27")
            return original(repo, *args, **kwargs)

        with patch("guardian_next.trees.git", side_effect=old_git):
            self.assertEqual(integration.common(self.repo), str((self.repo / ".git").resolve()))
            baseline = trees.capture(self.repo)
            snap = self.repo.parent / "snapshot"
            trees.snapshot(self.repo, baseline, baseline, snap)
            self.assertEqual(trees.capture(snap), baseline)

    def test_acceptance_sees_only_candidate_files_and_changes(self):
        baseline = trees.capture(self.repo)
        (self.repo / "app.py").write_bytes(b"def value(): return 2\n")
        task = {"base": baseline}
        suite = {
            "authored": {
                **AUTHOR,
                "test_code": """import subprocess, unittest
from pathlib import Path
from app import value
class Acceptance(unittest.TestCase):
    def test_result_and_scope(self):
        self.assertEqual(value(), 2)
        files = {p.name for p in Path.cwd().iterdir() if p.name != '.git'}
        self.assertEqual(files, {'app.py'})
        changed = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD']).decode().splitlines()
        untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard']).decode().splitlines()
        self.assertEqual(changed + untracked, ['app.py'])
""",
            }
        }
        real_run = execution.bounded_run

        def sandbox_adapter(argv, **options):
            return real_run(argv[argv.index("--") + 1 :], **options)

        cfg = {**self.cfg, "python": sys.executable, "codex": "simulated"}
        with patch("guardian_next.execution.bounded_run", side_effect=sandbox_adapter):
            result = workflow.snapshot_check(
                cfg,
                task,
                trees.capture(self.repo),
                workflow.acceptance_command(cfg),
                self.state / "acceptance.log",
                suite,
            )
        self.assertTrue(result["passed"], Path(result["log"]).read_text())

    def test_crlf_checkout_import_preserves_exact_worker_bytes_and_index(self):
        # Git's own checkout conversion is enabled even on Linux/macOS.
        trees.git(self.repo, "config", "core.autocrlf", "true")
        (self.repo / "app.py").write_bytes(b"def value(): return 1\r\n")
        result = self.result()
        worker_path = Path(result["work_product"]["worktree_path"])
        (worker_path / "app.py").write_bytes(b"def value(): return 2\r\n")
        before_index = (self.repo / ".git/index").read_bytes()
        receipt = worker.accept_result(self.cfg, self.state, "one", result, 0)
        self.assertEqual((self.repo / "app.py").read_bytes(), b"def value(): return 2\r\n")
        self.assertEqual((self.repo / ".git/index").read_bytes(), before_index)
        self.assertEqual(receipt["candidate"], trees.capture(self.repo))

    def test_crlf_conversion_never_accepts_dirty_or_untracked_start(self):
        trees.git(self.repo, "config", "core.autocrlf", "true")
        (self.repo / "app.py").write_bytes(b"def value(): return 1\r\n")
        self.prepare()
        self.assertTrue(worker.preflight(self.cfg, self.state, "one")["ready"])
        for name, data in (("app.py", b"user edit\r\n"), ("notes.txt", b"keep me\r\n")):
            with self.subTest(path=name):
                original = (self.repo / name).read_bytes() if (self.repo / name).exists() else None
                (self.repo / name).write_bytes(data)
                before = trees.capture(self.repo)
                with self.assertRaisesRegex(trees.Failure, "unchanged HEAD checkout"):
                    worker.preflight(self.cfg, self.state, "one")
                self.assertEqual(trees.capture(self.repo), before)
                if original is None:
                    (self.repo / name).unlink()
                else:
                    (self.repo / name).write_bytes(original)

    def test_checkout_attributes_binary_bytes_and_staging_are_preserved(self):
        trees.git(self.repo, "config", "core.autocrlf", "false")
        (self.repo / ".gitattributes").write_bytes(b"*.py text eol=crlf\n*.bin -text\n")
        (self.repo / "data.bin").write_bytes(b"\x00\xff\r\n\n")
        trees.git(self.repo, "add", ".gitattributes", "data.bin")
        trees.git(
            self.repo,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@localhost",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            "Checkout attributes",
        )
        (self.repo / "app.py").write_bytes(b"def value(): return 1\r\n")
        result = self.result()
        index = (self.repo / ".git/index").read_bytes()
        worker.accept_result(self.cfg, self.state, "one", result, 0)
        self.assertEqual((self.repo / "data.bin").read_bytes(), b"\x00\xff\r\n\n")
        self.assertEqual((self.repo / ".git/index").read_bytes(), index)

    def test_same_tree_at_different_worker_commit_is_rejected(self):
        result = self.result()
        worktree = Path(result["work_product"]["worktree_path"])
        trees.git(
            worktree,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@localhost",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--allow-empty",
            "-m",
            "Other HEAD",
        )
        before = trees.capture(self.repo)
        with self.assertRaisesRegex(trees.Failure, "Worker baseline differs"):
            worker.accept_result(self.cfg, self.state, "one", result, 0)
        self.assertEqual(trees.capture(self.repo), before)

    def test_import_keeps_preexisting_staged_content_when_working_bytes_match_head(self):
        result = self.result()
        native = (self.repo / "app.py").read_bytes()
        staged = b"user's separately staged edit\n"
        (self.repo / "app.py").write_bytes(staged)
        trees.git(self.repo, "add", "app.py")
        (self.repo / "app.py").write_bytes(native)
        index = (self.repo / ".git/index").read_bytes()
        worker.accept_result(self.cfg, self.state, "one", result, 0)
        self.assertEqual((self.repo / ".git/index").read_bytes(), index)
        self.assertEqual(trees.git(self.repo, "show", ":app.py"), staged)

    def test_custom_filters_are_rejected_without_running_them(self):
        (self.repo / ".gitattributes").write_bytes(b"app.py filter=custom\n")
        trees.git(self.repo, "add", ".gitattributes")
        trees.git(
            self.repo,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@localhost",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            "Filter contract",
        )
        trees.git(self.repo, "config", "filter.custom.smudge", "invalid-command-must-not-run")
        with self.assertRaisesRegex(trees.Failure, "custom filter"):
            trees.checkout_baseline(self.repo, "HEAD")

    def test_missing_and_old_git_have_actionable_diagnostics(self):
        with patch.dict(os.environ, {"GUARDIAN_GIT": str(self.state / "missing-git")}):
            with self.assertRaisesRegex(trees.Failure, "Git executable unavailable"):
                trees.git_info(self.repo)
        with patch("guardian_next.trees.text_git", return_value="git version 2.20.1.windows.1"):
            with self.assertRaisesRegex(trees.Failure, "requires Git 2.27"):
                trees.git_info(self.repo)

    def test_git_selection_is_recorded_and_path_drift_is_rejected(self):
        home = self.state / "home"
        integration.register(
            home,
            self.repo,
            {
                "python": sys.executable,
                "codex": sys.executable,
                "checks": [[sys.executable, "--version"]],
            },
        )
        cfg, _ = integration.resolve(home, self.repo)
        self.assertEqual(cfg["git"], trees.executable())
        registration = integration.registration_path(home, self.repo)
        saved = json.loads(registration.read_text())
        saved["git"] = str(self.state / "other-git")
        trees.save(registration, saved)
        with self.assertRaisesRegex(trees.Failure, "changed since registration"):
            integration.resolve(home, self.repo)

    def test_readonly_preflight_verifies_real_git_and_byte_outputs(self):
        cfg = {**self.cfg, "python": sys.executable}

        def simulated_model(cfg, cwd, prompt, schema, output, role):
            argv = json.loads(prompt.rsplit("\n", 1)[1])
            result = execution.bounded_run(
                argv, cwd=cwd, env=execution.environment(cwd, True), timeout=20
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

        with patch("guardian_next.execution.ask", side_effect=simulated_model):
            result = execution.review_preflight(cfg, self.state / "probe", self.state / "evidence")
        self.assertTrue(result["passed"])
        self.assertTrue((self.state / "evidence/verification.json").exists())

    def test_denied_preflight_stops_before_task_preparation(self):
        home = self.state / "home"
        integration.register(
            home,
            self.repo,
            {
                "python": sys.executable,
                "codex": sys.executable,
                "checks": [[sys.executable, "--version"]],
            },
        )
        with (
            patch("guardian_next.execution.check", return_value=CHECK),
            patch("guardian_next.execution.ask", return_value={"unavailable": True}),
        ):
            report = integration.doctor(home, self.repo)
        self.assertFalse(report["completed"])
        self.assertFalse(report["passed"])
        self.assertFalse(report["review_preflight"]["passed"])
        cfg, state = integration.resolve(home, self.repo)
        with self.assertRaisesRegex(trees.Failure, "Run doctor"):
            workflow.begin(cfg, state, self.payload)
        self.assertFalse((state / "report.json").exists())

    def test_later_review_access_failure_never_spends_code_repair(self):
        self.prepare()
        with (
            patch("guardian_next.execution.check", return_value=CHECK),
            patch(
                "guardian_next.execution.ask",
                return_value={
                    **REVIEW,
                    "inspection_complete": False,
                    "ready": False,
                    "summary": "Git denied",
                },
            ),
        ):
            task = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual((task["status"], task["repairs"]), ("environment", 0))

    def test_external_acceptance_source_mutation_is_still_rejected(self):
        path = workflow.write_suite(self.repo, AUTHOR)
        real_run = execution.bounded_run

        def sandbox_adapter(argv, **options):
            return real_run(argv[argv.index("--") + 1 :], **options)

        cfg = {**self.cfg, "python": sys.executable, "codex": "simulated"}
        with patch("guardian_next.execution.bounded_run", side_effect=sandbox_adapter):
            with self.assertRaisesRegex(trees.Failure, "modified the candidate or frozen test"):
                execution.check(
                    cfg,
                    self.repo,
                    [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path("
                        + repr(str(path))
                        + ").write_text('changed')",
                    ],
                    self.state / "mutation.log",
                    protected=[path],
                )

    def test_failed_worker_and_skipped_checks_never_import(self):
        result = self.result()
        before = trees.capture(self.repo)
        with self.assertRaisesRegex(trees.Failure, "execution failed before import"):
            worker.accept_result(self.cfg, self.state, "one", result, 7)
        result["work_product"]["validation"].append({"outcome": "skipped"})
        with self.assertRaisesRegex(trees.Failure, "optional checks need an explicit adapter"):
            worker.accept_result(self.cfg, self.state, "one", result, 0)
        self.assertEqual(trees.capture(self.repo), before)


if __name__ == "__main__":
    unittest.main()
