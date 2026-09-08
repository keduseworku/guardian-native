"""Regressions for release integration defects; model calls are explicitly simulated."""

import copy
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import test_outcomes
from test_outcomes import AUTHOR, CHECK, CONTRACT, REVIEW

from guardian_next import cli, integration, spec, trees, workflow


class ReleaseTests(unittest.TestCase):
    setUp = test_outcomes.WorkflowTests.setUp
    prepare = test_outcomes.WorkflowTests.prepare

    def test_process_death_releases_lock_without_manual_state_edit(self):
        program = (
            "from guardian_next.workflow import locked; from pathlib import Path; import sys,time; "
            + "\nwith locked(Path(sys.argv[1])):\n print('locked',flush=True)\n time.sleep(60)"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", program, str(self.state)],
            stdout=subprocess.PIPE,
            text=True,
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        )
        try:
            self.assertEqual(process.stdout.readline().strip(), "locked")
            with self.assertRaises(trees.Failure):
                with workflow.locked(self.state):
                    pass
            process.kill()
            process.wait(timeout=10)
            with workflow.locked(self.state):
                self.assertTrue((self.state / "operation.lock").exists())
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            process.stdout.close()

    def test_settings_preserve_array_table_models(self):
        text = 'model = "gpt-5.6-sol"\n[[custom]]\nmodel = "keep-me"\n'
        result = integration.settings(
            text, [("", "model", "gpt-5.6-sol"), ("features", "hooks", True)]
        )
        self.assertIn('model = "keep-me"', result)

    def test_preparation_failure_is_recorded_without_spending_code_repair(self):
        workflow.begin(self.cfg, self.state, self.payload)
        with (
            patch(
                "guardian_next.execution.ask",
                side_effect=trees.Failure("environment", "author unavailable"),
            ),
            self.assertRaises(trees.Failure),
        ):
            workflow.prepare(self.cfg, self.state, "one", CONTRACT)
        task = workflow.load(self.state)
        self.assertEqual(
            (task["status"], task["repairs"], task["active"]), ("environment", 0, False)
        )

    def test_frozen_acceptance_bytes_match_recorded_code_on_every_platform(self):
        workflow.write_suite(self.repo, AUTHOR)
        self.assertEqual(
            (self.repo.parent / ".guardian_checks/test_acceptance.py").read_bytes(),
            AUTHOR["test_code"].encode("utf-8"),
        )

    def test_unique_input_and_retained_completed_evidence(self):
        first = workflow.begin(self.cfg, self.state, self.payload)
        workflow.finish(self.cfg, self.state, "one")
        second = workflow.begin(self.cfg, self.state, self.payload)
        self.assertNotEqual(first["input"], second["input"])
        self.assertTrue(Path(first["input"]).parent.exists())
        self.assertTrue((self.state / "history" / (first["id"] + ".json")).exists())

    def test_discussion_resume_retains_original_request_and_suite(self):
        self.prepare()
        (self.repo / "app.py").write_text("def value(): return 2\n")
        workflow.begin(self.cfg, self.state, {**self.payload, "prompt": "Why use a function?"})
        workflow.classify(self.cfg, self.state, "one", "discussion")
        paused = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual(paused["status"], "paused")
        self.assertEqual(paused["request"], "Return two")
        self.assertEqual(paused["acceptance"], AUTHOR)
        workflow.begin(self.cfg, self.state, {**self.payload, "prompt": "Continue"})
        workflow.classify(self.cfg, self.state, "one", "resume")
        with (
            patch("guardian_next.execution.ask", return_value=REVIEW),
            patch("guardian_next.execution.check", return_value=CHECK),
        ):
            result = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual(result["status"], "accepted")

    def test_missing_business_decision_preserves_original_unprepared_task(self):
        workflow.begin(self.cfg, self.state, self.payload)
        workflow.classify(self.cfg, self.state, "one", "waiting")
        task = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual(task["status"], "paused")
        workflow.begin(
            self.cfg, self.state, {**self.payload, "prompt": "Use the existing integer API"}
        )
        task = workflow.classify(self.cfg, self.state, "one", "clarify")
        self.assertIn("Return two", task["request"])
        self.assertIn("existing integer API", task["request"])

    def test_standalone_discussion_releases_the_checkout(self):
        workflow.begin(self.cfg, self.state, self.payload)
        workflow.classify(self.cfg, self.state, "one", "discussion")
        self.assertEqual(workflow.finish(self.cfg, self.state, "one")["status"], "no_changes")
        workflow.begin(self.cfg, self.state, {**self.payload, "session_id": "another"})

    def test_registered_native_worktrees_have_distinct_state_and_input(self):
        home = self.state / "home"
        cfg = {
            "python": sys.executable,
            "codex": sys.executable,
            "checks": [[sys.executable, "--version"]],
        }
        integration.register(home, self.repo, cfg)
        other = self.repo.parent / "parallel-worktree"
        trees.git(self.repo, "worktree", "add", "-b", "codex/parallel", str(other))
        paths = []
        for repo, session in ((self.repo, "one"), (other, "two")):
            config, state = integration.resolve(home, repo)
            config.pop(
                "require_doctor"
            )  # This test covers registration/lifecycle, not sandbox health.
            task = workflow.begin(
                config, state, {"cwd": str(repo), "session_id": session, "prompt": "Return two"}
            )
            paths.append((state, task["input"]))
        self.assertNotEqual(paths[0][0], paths[1][0])
        self.assertNotEqual(paths[0][1], paths[1][1])

    def test_discussion_with_edits_is_unverified(self):
        self.prepare()
        workflow.begin(self.cfg, self.state, {**self.payload, "prompt": "Explain"})
        workflow.classify(self.cfg, self.state, "one", "discussion")
        (self.repo / "app.py").write_text("changed")
        self.assertEqual(workflow.finish(self.cfg, self.state, "one")["status"], "protocol")

    def test_clarification_refreezes_before_new_edits_and_retains_old_suite(self):
        self.prepare()
        (self.repo / "app.py").write_text("def value(): return 2\n")
        workflow.begin(self.cfg, self.state, {**self.payload, "prompt": "Also add a label"})
        workflow.classify(self.cfg, self.state, "one", "clarify")
        amended = copy.deepcopy(CONTRACT)
        amended["task"] = "Add a label as well"
        with (
            patch("guardian_next.execution.ask", return_value=AUTHOR),
            patch("guardian_next.execution.check", return_value=CHECK),
        ):
            workflow.prepare(self.cfg, self.state, "one", amended)
        task = workflow.load(self.state)
        self.assertEqual(len(task["suites"]), 2)
        self.assertEqual(task["suites"][0]["contract"], CONTRACT)
        self.assertIn("Also add a label", task["request"])
        self.assertEqual(task["suites"][0]["disposition"], "required")

    def test_stop_continuation_does_not_restart_task(self):
        self.prepare()
        original = workflow.load(self.state)
        original["continuation"] = "Repair exact failure"
        trees.save(self.state / "report.json", original)
        resumed = workflow.begin(
            self.cfg, self.state, {**self.payload, "prompt": original["continuation"]}
        )
        self.assertEqual(resumed["id"], original["id"])
        self.assertEqual(resumed["mode"], "work")
        self.assertEqual(resumed["acceptance"], AUTHOR)

    def test_interruption_clears_stale_approval(self):
        self.prepare()
        task = workflow.load(self.state)
        task["review"] = REVIEW
        trees.save(self.state / "report.json", task)
        with (
            patch("guardian_next.execution.check", side_effect=KeyboardInterrupt),
            self.assertRaises(KeyboardInterrupt),
        ):
            workflow.finish(self.cfg, self.state, "one")
        current = workflow.load(self.state)
        self.assertEqual(current["status"], "evaluating")
        self.assertNotIn("review", current)
        self.assertFalse((self.state / "busy").exists())

    def test_faulty_test_is_replaced_by_baseline_author_and_rechecked(self):
        self.prepare()
        (self.repo / "app.py").write_text("def value(): return 2\n")
        log = self.state / "wrong.log"
        log.write_text("AssertionError: expected 3 but request requires 2")
        bad = {**CHECK, "passed": False, "log": str(log)}
        dispute = {
            "classification": "tests",
            "reason": "Test contradicts original constant two",
            "corrected_expectation": "2",
        }
        author_bases = []

        def ask(cfg, snap, prompt, schema, output, role):
            if schema == spec.DISPUTE_SCHEMA:
                return dispute
            if schema == spec.AUTHOR_SCHEMA:
                author_bases.append((snap / "app.py").read_text())
                return AUTHOR
            return REVIEW

        with (
            patch("guardian_next.execution.ask", side_effect=ask),
            patch("guardian_next.execution.check", side_effect=[bad, CHECK, CHECK]),
        ):
            task = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual(task["status"], "accepted")
        self.assertEqual(author_bases, ["def value(): return 1\n"])
        self.assertEqual(task["suites"][0]["authored"], AUTHOR)
        self.assertEqual(task["suites"][0]["disposition"], "replaced_after_independent_dispute")
        self.assertEqual(task["suites"][1]["replacement_for"], 0)
        self.assertEqual(task["repairs"], 0)

    def test_team_failure_never_reaches_model_override(self):
        self.prepare()
        self.cfg["checks"] = [[sys.executable, "team_check.py"]]
        with (
            patch("guardian_next.execution.check", return_value={**CHECK, "passed": False}),
            patch("guardian_next.execution.ask") as ask,
        ):
            task = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual(task["status"], "candidate")
        ask.assert_not_called()

    def test_environment_dispute_never_spends_code_repair(self):
        self.prepare()
        log = self.state / "missing.log"
        log.write_text("Required fixture unavailable")
        with (
            patch(
                "guardian_next.execution.check",
                return_value={**CHECK, "passed": False, "log": str(log)},
            ),
            patch(
                "guardian_next.execution.ask",
                return_value={
                    "classification": "environment",
                    "reason": "Missing external fixture",
                    "corrected_expectation": "",
                },
            ),
        ):
            task = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual((task["status"], task["repairs"]), ("environment", 0))

    def test_contradictory_review_is_protocol_failure(self):
        with self.assertRaises(trees.Failure) as caught:
            spec.validate_review({**REVIEW, "findings": [{"required_correction": True}]})
        self.assertEqual(caught.exception.kind, "protocol")

    def test_personal_install_coexists_and_uninstall_restores_exact_bytes(self):
        home, codex = self.state / "personal", self.state / "codex"
        codex.mkdir()
        config = b'# keep\nmodel = "old-model"\n[features]\nother = true\n'
        hooks = b'{"hooks":{"Stop":[{"hooks":[{"type":"command","command":"team-check"}]}]}}\n'
        (codex / "config.toml").write_bytes(config)
        (codex / "hooks.json").write_bytes(hooks)
        before = trees.capture(self.repo)
        integration.install(home, codex)
        installed = json.loads((codex / "hooks.json").read_text())
        self.assertEqual(installed["hooks"]["Stop"][0]["hooks"][0]["command"], "team-check")
        self.assertEqual(trees.capture(self.repo), before)
        integration.uninstall(home)
        self.assertEqual((codex / "config.toml").read_bytes(), config)
        self.assertEqual((codex / "hooks.json").read_bytes(), hooks)
        self.assertFalse((codex / "rules/guardian-native.rules").exists())

    def test_uninstall_preserves_later_unrelated_settings_and_hooks(self):
        home, codex = self.state / "personal", self.state / "codex"
        integration.install(home, codex)
        config = codex / "config.toml"
        config.write_text(config.read_text() + "\n[unrelated]\nkeep = 42\n")
        hookpath = codex / "hooks.json"
        hooks = json.loads(hookpath.read_text())
        hooks["hooks"]["Stop"][0]["hooks"].append({"type": "command", "command": "later-team-hook"})
        trees.save(hookpath, hooks)
        integration.uninstall(home)
        self.assertIn("keep = 42", config.read_text())
        remaining = json.loads(hookpath.read_text())
        self.assertEqual(remaining["hooks"]["Stop"][0]["hooks"][0]["command"], "later-team-hook")
        self.assertNotIn("guardian_next", hookpath.read_text())

    def test_registration_needs_actual_checks_and_preserves_venv_path(self):
        with self.assertRaises(trees.Failure):
            integration.register(
                self.state / "home",
                self.repo,
                {"python": sys.executable, "codex": sys.executable, "checks": []},
            )
        result = integration.register(
            self.state / "home",
            self.repo,
            {
                "python": sys.executable,
                "codex": sys.executable,
                "checks": [[sys.executable, "-m", "unittest"]],
            },
        )
        cfg = json.loads(Path(result["configuration"]).read_text())
        self.assertEqual(cfg["python"], str(Path(sys.executable).absolute()))
        self.assertTrue(cfg["require_doctor"])

    def test_unregistered_hook_returns_empty_and_does_not_suppress_other_hooks(self):
        from io import StringIO

        args = ["guardian", "--home", str(self.state / "home"), "hook", "Stop"]
        payload = json.dumps(self.payload).encode()

        class Input:
            import io

            buffer = io.BytesIO(payload)

        with (
            patch.object(sys, "argv", args),
            patch.object(sys, "stdin", Input()),
            patch.object(sys, "stdout", StringIO()) as output,
        ):
            self.assertEqual(cli.main(), 0)
        self.assertEqual(json.loads(output.getvalue()), {})


if __name__ == "__main__":
    unittest.main()
