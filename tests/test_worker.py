"""Synthetic tests for the retained worker envelope; not actual worker certification."""

import json
import unittest
from unittest.mock import patch

import test_outcomes
from test_outcomes import CHECK, REVIEW

from guardian_next import trees, worker, workflow


class WorkerTests(unittest.TestCase):
    setUp = test_outcomes.WorkflowTests.setUp
    prepare = test_outcomes.WorkflowTests.prepare

    def result(self):
        self.prepare()
        worktree = self.repo.parent / "worker"
        trees.git(self.repo, "worktree", "add", "-b", "codex/worker", str(worktree))
        (worktree / "app.py").write_text("def value(): return 2\n")
        return {
            "success": True,
            "execution_success": True,
            "work_product_created": True,
            "failure_classification": None,
            "validation_provenance": {
                "status": "verified",
                "before_snapshot_id": "test-snapshot",
                "after_snapshot_id": "test-snapshot",
            },
            "work_product": {
                "success": True,
                "worktree_path": str(worktree),
                "branch": "codex/worker",
                "changed_files": ["app.py"],
                "validation": [{"outcome": "passed"}],
            },
        }

    def test_import_preserves_index_then_requires_native_review(self):
        result = self.result()
        index = (self.repo / ".git/index").read_bytes()
        receipt = worker.accept_result(self.cfg, self.state, "one", result, 0)
        self.assertEqual((self.repo / "app.py").read_text(), "def value(): return 2\n")
        self.assertEqual((self.repo / ".git/index").read_bytes(), index)
        self.assertEqual(receipt["candidate"], trees.capture(self.repo))
        self.assertEqual(workflow.load(self.state)["status"], "prepared")
        with (
            patch("guardian_next.execution.ask", return_value=REVIEW),
            patch("guardian_next.execution.check", return_value=CHECK),
        ):
            self.assertEqual(workflow.finish(self.cfg, self.state, "one")["status"], "accepted")

    def test_bad_provenance_and_declared_files_never_copy(self):
        original = self.result()
        before = trees.capture(self.repo)
        for mutate in (
            lambda r: r["validation_provenance"].update(after_snapshot_id="different"),
            lambda r: r["work_product"].update(changed_files=["other.py"]),
        ):
            result = json.loads(json.dumps(original))
            mutate(result)
            with self.assertRaises(trees.Failure):
                worker.accept_result(self.cfg, self.state, "one", result, 0)
            self.assertEqual(trees.capture(self.repo), before)

    def test_native_drift_rejects_worker_baseline(self):
        result = self.result()
        (self.repo / "app.py").write_text("user edit\n")
        with self.assertRaises(trees.Failure):
            worker.accept_result(self.cfg, self.state, "one", result, 0)
        self.assertEqual((self.repo / "app.py").read_text(), "user edit\n")

    def test_failed_copy_rolls_back_only_our_bytes(self):
        result = self.result()
        actual = worker.write

        def fail_after_write(repo, name, content):
            actual(repo, name, content)
            raise OSError("simulated write failure")

        # A write can partially succeed before raising. Preserve/restore is checked below.
        with (
            patch("guardian_next.worker.write", side_effect=fail_after_write),
            self.assertRaises(OSError),
        ):
            worker.accept_result(self.cfg, self.state, "one", result, 0)
        self.assertEqual((self.repo / "app.py").read_text(), "def value(): return 1\n")
