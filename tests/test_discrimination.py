"""Known numerical and cache-ownership controls, separate from controller correctness."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


class DiscriminationTests(unittest.TestCase):
    def run_probe(self, folder, program):
        return subprocess.run(
            [sys.executable, "-c", program],
            cwd=folder,
            env={**os.environ, "PYTHONPATH": str(folder), "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_huge_integer_identity_rejects_retained_seed_accepts_exact_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(FIXTURES / "weighted-seed", root)
            probe = (
                "from aggregate import weighted_mean; n=10**400; assert weighted_mean([n],[1]) == n"
            )
            bad = self.run_probe(root, probe)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("OverflowError", bad.stderr)
            source = root / "aggregate.py"
            old = "    return float(weighted_total / total_weight)"
            new = "    result = weighted_total / total_weight\n    try:\n        return float(result)\n    except OverflowError:\n        return result"
            self.assertEqual(source.read_text().count(old), 1)
            source.write_text(source.read_text().replace(old, new))
            good = self.run_probe(root, probe)
            self.assertEqual(good.returncode, 0, good.stderr)

    def test_stacked_cache_ownership_rejects_seed_accepts_local_owner_fix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(FIXTURES / "cache-seed", root)
            probe = """from cachetools import cached
inner_cache, outer_cache = {}, {}
@cached(inner_cache)
def inner(x): return x * 2
outer = cached(outer_cache)(inner)
outer(3)
assert outer.cache_invalidate(3) is True
assert not outer_cache, "outer cache must own invalidation"
assert inner_cache == {(3,):6}, "inner cache must be preserved"
"""
            bad = self.run_probe(root, probe)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("outer cache must own invalidation", bad.stderr)
            source = root / "cachetools/_cached.py"
            text = source.read_text()
            marker = "    wrapper.cache = cache"
            self.assertEqual(text.count(marker), 1)
            text = text.replace(marker, "    functools.update_wrapper(wrapper, func)\n" + marker)
            text = text.replace(
                "    return functools.update_wrapper(wrapper, func)", "    return wrapper"
            )
            source.write_text(text)
            good = self.run_probe(root, probe)
            self.assertEqual(good.returncode, 0, good.stderr)
