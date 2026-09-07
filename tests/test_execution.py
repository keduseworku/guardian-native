"""Real subprocess checks with an explicitly simulated sandbox command adapter."""

import json
import os
import sys
import unittest
from unittest.mock import patch

import test_outcomes

from guardian_next import execution, trees


class ExecutionTests(unittest.TestCase):
    setUp = test_outcomes.WorkflowTests.setUp

    def run_without_os_sandbox(self, argv, **options):
        # CI has no authenticated Codex runtime. Only the command adapter is simulated.
        command = argv[argv.index("--") + 1 :]
        return self.real_run(command, **options)

    def test_source_mutating_check_cannot_certify_original_candidate(self):
        self.real_run = execution.bounded_run
        cfg = {**self.cfg, "codex": "simulated-codex", "python": sys.executable}
        with patch("guardian_next.execution.bounded_run", side_effect=self.run_without_os_sandbox):
            with self.assertRaises(trees.Failure) as failure:
                execution.check(
                    cfg,
                    self.repo,
                    [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('app.py').write_text('changed')",
                    ],
                    self.state / "check.log",
                )
        self.assertEqual(failure.exception.kind, "protocol")

    def test_checks_preserve_plugins_and_explicit_nonsecret_environment(self):
        self.real_run = execution.bounded_run
        cfg = {
            **self.cfg,
            "codex": "simulated-codex",
            "python": sys.executable,
            "check_env": {"TEAM_MODE": "test"},
        }
        program = "import os,json; print(json.dumps({k:os.environ.get(k) for k in ['TEAM_MODE','GUARDIAN_TEST_API_KEY','PYTEST_DISABLE_PLUGIN_AUTOLOAD']}))"
        with (
            patch.dict(os.environ, {"GUARDIAN_TEST_API_KEY": "synthetic-not-a-secret"}),
            patch("guardian_next.execution.bounded_run", side_effect=self.run_without_os_sandbox),
        ):
            result = execution.check(
                cfg, self.repo, [sys.executable, "-c", program], self.state / "check.log"
            )
        self.assertTrue(result["passed"])
        self.assertEqual(
            json.loads((self.state / "check.log").read_text()),
            {
                "TEAM_MODE": "test",
                "GUARDIAN_TEST_API_KEY": None,
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": None,
            },
        )

    def test_zero_test_discovery_is_protocol_failure(self):
        self.real_run = execution.bounded_run
        cfg = {**self.cfg, "codex": "simulated-codex", "python": sys.executable}
        with patch("guardian_next.execution.bounded_run", side_effect=self.run_without_os_sandbox):
            with self.assertRaises(trees.Failure) as failure:
                execution.check(
                    cfg,
                    self.repo,
                    [sys.executable, "-m", "unittest", "discover"],
                    self.state / "check.log",
                )
        self.assertEqual(failure.exception.kind, "protocol")

    def test_child_timeout_is_environment_failure(self):
        with self.assertRaises(trees.Failure) as failure:
            execution.bounded_run(
                [sys.executable, "-c", "import time; time.sleep(60)"],
                cwd=self.repo,
                env=execution.environment(self.repo),
                timeout=1,
            )
        self.assertEqual(failure.exception.kind, "environment")
