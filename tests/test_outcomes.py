"""Regression evidence for exact delivery and separating code from workflow failures."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from guardian_next import spec, trees, workflow

CONTRACT = {
    "objective": "Return the requested constant",
    "design": "One function",
    "outcome": "Correct API",
    "milestone": "Implement",
    "task": "Constant",
    "allowed_paths": ["app.py", "tests"],
    "context_paths": ["app.py"],
    "acceptance": ["returns two"],
    "examples": [
        {
            "criterion": "returns two",
            "input": "value()",
            "expected": "2",
            "derivation": "Original requirement",
        }
    ],
    "edges": ["no arguments"],
}
AUTHOR = {
    "test_code": (
        "import unittest\nfrom app import value\nclass T(unittest.TestCase):\n"
        " def test_value(self): self.assertEqual(value(),2)\n"
    ),
    "reasoning": "Exact request",
    "example_checks": ["value() == 2"],
}
REVIEW = {
    "ready": True,
    "summary": "Meets request",
    "findings": [],
    "expected_values_checked": ["value() == 2"],
}
CHECK = {"passed": True, "exit_code": 0, "failed_tests": [], "log": "test.log"}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        (self.repo / "app.py").write_text("def value(): return 1\n")
        trees.git(self.repo, "init", "-b", "main")
        trees.git(self.repo, "add", ".")
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
            "baseline",
        )
        self.state = Path(self.tmp.name) / "state"
        self.state.mkdir()
        self.cfg = {
            "repo": str(self.repo),
            "python": "python",
            "checks": [],
            "hook_files": {},
            "research": str(Path(__file__).resolve().parents[1] / "src/guardian_next/resources"),
        }
        self.payload = {"cwd": str(self.repo), "session_id": "one", "prompt": "Return two"}

    def prepare(self):
        workflow.begin(self.cfg, self.state, self.payload)
        with (
            patch("guardian_next.execution.ask", return_value=AUTHOR),
            patch("guardian_next.execution.check", return_value=CHECK),
        ):
            workflow.prepare(self.cfg, self.state, "one", CONTRACT)

    def test_capture_preserves_staging_and_exact_dirty_bytes(self):
        (self.repo / "app.py").write_text("staged\n")
        trees.git(self.repo, "add", "app.py")
        index = (self.repo / ".git/index").read_bytes()
        (self.repo / "app.py").write_bytes(b"unstaged\r\n")
        (self.repo / "new.bin").write_bytes(b"\x00\xff")
        tree = trees.capture(self.repo)
        out = Path(self.tmp.name) / "export"
        trees.export(self.repo, tree, out)
        self.assertEqual((out / "app.py").read_bytes(), b"unstaged\r\n")
        self.assertEqual((out / "new.bin").read_bytes(), b"\x00\xff")
        self.assertEqual((self.repo / ".git/index").read_bytes(), index)
        self.assertEqual(trees.text_git(self.repo, "branch", "--show-current"), "main")

    def test_snapshot_contains_original_baseline_and_candidate(self):
        original_bytes = (self.repo / "app.py").read_bytes()
        base = trees.capture(self.repo)
        (self.repo / "app.py").unlink()
        (self.repo / "new.py").write_text("new\n")
        candidate = trees.capture(self.repo)
        out = Path(self.tmp.name) / "snapshot"
        trees.snapshot(self.repo, base, candidate, out)
        self.assertFalse((out / "app.py").exists())
        self.assertEqual(trees.git(out, "show", "HEAD:app.py"), original_bytes)
        self.assertEqual(trees.capture(out), candidate)

    def test_missing_expected_value_rejected_before_author(self):
        workflow.begin(self.cfg, self.state, self.payload)
        invalid = copy.deepcopy(CONTRACT)
        invalid["examples"][0]["expected"] = ""
        with patch("guardian_next.execution.ask") as ask, self.assertRaises(trees.Failure):
            workflow.prepare(self.cfg, self.state, "one", invalid)
        ask.assert_not_called()

    def test_preparation_preserves_original_baseline_contract_fields(self):
        workflow.begin(self.cfg, self.state, self.payload)
        contract = copy.deepcopy(CONTRACT)
        del contract["objective"]
        with self.assertRaises(trees.Failure):
            workflow.prepare(self.cfg, self.state, "one", contract)

    def test_structured_input_and_numeric_expected_are_valid_evidence(self):
        contract = copy.deepcopy(CONTRACT)
        contract["examples"][0].update(input=[], expected=2)
        self.assertEqual(spec.validate(contract)["examples"][0]["expected"], 2)

    def test_snapshot_preserves_ignored_tracked_file_and_directory_replacement(self):
        (self.repo / ".gitignore").write_text("app.py\n")
        (self.repo / "folder").mkdir()
        (self.repo / "folder/old.py").write_text("old\n")
        base = trees.capture(self.repo)
        (self.repo / "folder/old.py").unlink()
        (self.repo / "folder").rmdir()
        (self.repo / "folder").write_text("new\n")
        candidate = trees.capture(self.repo)
        out = Path(self.tmp.name) / "replacement"
        trees.snapshot(self.repo, base, candidate, out)
        self.assertEqual(trees.text_git(out, "rev-parse", "HEAD^{tree}"), base)
        self.assertEqual((out / "folder").read_text(), "new\n")

    def test_preparation_rejects_edits_already_started(self):
        workflow.begin(self.cfg, self.state, self.payload)
        (self.repo / "app.py").write_text("def value(): return 2\n")
        with patch("guardian_next.execution.ask") as ask, self.assertRaises(trees.Failure):
            workflow.prepare(self.cfg, self.state, "one", CONTRACT)
        ask.assert_not_called()

    def test_accepted_bytes_are_already_in_native_worktree(self):
        self.prepare()
        (self.repo / "app.py").write_text("def value(): return 2\n")
        index = (self.repo / ".git/index").read_bytes()
        with (
            patch("guardian_next.execution.ask", return_value=REVIEW),
            patch("guardian_next.execution.check", return_value=CHECK),
        ):
            result = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(trees.capture(self.repo), result["candidate"])
        self.assertEqual((self.repo / ".git/index").read_bytes(), index)
        with self.assertRaises(trees.Failure):
            workflow.finish(self.cfg, self.state, "one")

    def test_candidate_failures_repair_without_reauthoring(self):
        self.prepare()
        (self.repo / "app.py").write_text("def value(): return 3\n")
        log = self.state / "failed.log"
        log.write_text("AssertionError: 3 != 2")
        bad = {**CHECK, "passed": False, "failed_tests": ["test_value"], "log": str(log)}
        with (
            patch("guardian_next.execution.check", return_value=bad),
            patch(
                "guardian_next.execution.ask",
                return_value={
                    "classification": "code",
                    "reason": "value() returns 3, requires 2",
                    "corrected_expectation": "",
                },
            ) as ask,
        ):
            result = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual(
            (result["status"], result["repairs"], result["active"]), ("candidate", 1, True)
        )
        self.assertEqual(result["acceptance"], AUTHOR)
        self.assertEqual(ask.call_count, 1)

    def test_protocol_retry_does_not_consume_code_repair(self):
        self.prepare()
        (self.repo / "app.py").write_text("def value(): return 2\n")
        with (
            patch(
                "guardian_next.execution.ask",
                side_effect=[trees.Failure("protocol", "bad JSON"), REVIEW],
            ) as ask,
            patch("guardian_next.execution.check", return_value=CHECK),
        ):
            result = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual(ask.call_count, 2)
        self.assertEqual((result["status"], result["repairs"]), ("accepted", 0))

    def test_environment_failure_stops_without_code_repairs(self):
        self.prepare()
        with patch(
            "guardian_next.execution.check",
            side_effect=trees.Failure("environment", "sandbox missing"),
        ):
            result = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual(
            (result["status"], result["repairs"], result["active"]), ("environment", 0, False)
        )

    def test_native_mutation_during_review_cannot_be_accepted(self):
        self.prepare()
        (self.repo / "app.py").write_text("def value(): return 2\n")

        def mutate(*args):
            (self.repo / "app.py").write_text("def value(): return 99\n")
            return REVIEW

        with (
            patch("guardian_next.execution.ask", side_effect=mutate),
            patch("guardian_next.execution.check", return_value=CHECK),
        ):
            result = workflow.finish(self.cfg, self.state, "one")
        self.assertEqual(result["status"], "protocol")
        self.assertEqual(result["repairs"], 0)

    def test_review_summary_never_inlines_baseline_trace(self):
        prompt = spec.review_prompt("request", CONTRACT, [CHECK])
        self.assertNotIn("Traceback", prompt)
        self.assertIn("test.log", prompt)

    def test_competing_session_cannot_replace_active_task(self):
        workflow.begin(self.cfg, self.state, self.payload)
        with self.assertRaises(trees.Failure):
            workflow.begin(self.cfg, self.state, {**self.payload, "session_id": "two"})
        self.assertEqual(json.loads((self.state / "report.json").read_text())["session"], "one")


if __name__ == "__main__":
    unittest.main()
