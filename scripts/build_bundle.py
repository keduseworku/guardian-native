"""Create the self-contained release zip from a built wheel; no network required."""

import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
version = "1.0.0rc3"
out = root / "dist"
wheels = list(out.glob(f"guardian_native-{version}-*.whl"))
if len(wheels) != 1:
    raise SystemExit("Build exactly one matching wheel first")
with tempfile.TemporaryDirectory(prefix="guardian-bundle-") as temporary:
    bundle = Path(temporary) / f"guardian-native-{version}"
    bundle.mkdir()
    for name in ("README.md", "LICENSE", "pyproject.toml", "MANIFEST.in", ".gitignore"):
        shutil.copy2(root / name, bundle / name)
    for name in ("src", "scripts", "tests", "docs", ".github"):
        shutil.copytree(
            root / name,
            bundle / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"),
        )
    (bundle / "dist").mkdir()
    shutil.copy2(wheels[0], bundle / "dist" / wheels[0].name)
    files = sorted(p for p in bundle.rglob("*") if p.is_file())
    (bundle / "SHA256SUMS.txt").write_text(
        "".join(
            hashlib.sha256(p.read_bytes()).hexdigest()
            + "  "
            + p.relative_to(bundle).as_posix()
            + "\n"
            for p in files
        ),
        encoding="utf-8",
    )
    with zipfile.ZipFile(
        out / f"guardian-native-{version}-windows.zip", "w", zipfile.ZIP_DEFLATED
    ) as archive:
        for path in sorted(p for p in bundle.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(bundle.parent))
print(out / f"guardian-native-{version}-windows.zip")
