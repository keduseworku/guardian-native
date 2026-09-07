"""Check exact wheel payload, then install it offline into a fresh isolated interpreter."""

import json
import os
import subprocess
import tempfile
import venv
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
wheel = next((root / "dist").glob("guardian_native-1.0.0rc3-*.whl"))
source = root / "src/guardian_next"
with zipfile.ZipFile(wheel) as archive:
    expected = {p for p in source.rglob("*") if p.is_file() and p.suffix in {".py", ".md"}}
    for path in expected:
        name = "guardian_next/" + path.relative_to(source).as_posix()
        if archive.read(name) != path.read_bytes():
            raise SystemExit("Wheel differs from release source: " + name)
    if any("__pycache__" in n for n in archive.namelist()):
        raise SystemExit("Unexpected generated wheel payload")
with tempfile.TemporaryDirectory(prefix="guardian-artifact-") as temporary:
    home = Path(temporary)
    runtime = home / "runtime"
    venv.EnvBuilder(with_pip=True).create(runtime)
    python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--no-cache-dir",
            str(wheel),
        ],
        check=True,
        cwd=home,
    )
    probe = "from pathlib import Path; import guardian_next,json; p=Path(guardian_next.__file__).parent; print(json.dumps({'module':str(p),'methods':len(list((p/'resources/pocock').glob('*/METHOD.md'))),'ponytail':(p/'resources/PONYTAIL.md').is_file()}))"
    result = subprocess.run(
        [str(python), "-I", "-c", probe], check=True, cwd=home, capture_output=True, text=True
    )
    observed = json.loads(result.stdout)
    if (
        observed["methods"] != 13
        or not observed["ponytail"]
        or not Path(observed["module"]).resolve().is_relative_to(runtime.resolve())
    ):
        raise SystemExit(
            "Installed guidance/import isolation is incomplete: "
            + json.dumps({"observed": observed, "runtime": str(runtime)})
        )
    subprocess.run(
        [
            str(python),
            "-I",
            "-m",
            "guardian_next.cli",
            "--home",
            str(home / "personal"),
            "install",
            "--codex-home",
            str(home / "codex"),
        ],
        check=True,
        cwd=home,
    )
    subprocess.run(
        [
            str(python),
            "-I",
            "-m",
            "guardian_next.cli",
            "--home",
            str(home / "personal"),
            "uninstall",
        ],
        check=True,
        cwd=home,
    )
print(
    json.dumps(
        {
            "wheel": wheel.name,
            "exact_source_files": len(expected),
            "offline_install": True,
            "pocock_methods": 13,
            "isolated_personal_install_remove": True,
        }
    )
)
