# Guardian Native — 1.0.0rc3

User-scoped acceptance and review for ordinary Codex coding requests. This repository starts from a reviewed source snapshot of the existing Guardian tool.
Direct implementation, independent acceptance and final review use **Sol/high**.
An existing worker, when used, dispatches **Luna only**. The complete
Ponytail policy and thirteen pinned Pocock method adaptations are included on demand.

**Start on the target laptop with [LAPTOP-START.md](docs/LAPTOP-START.md).** Download the
`guardian-native-1.0.0rc3-windows.zip` asset from this repository's GitHub release. It contains
source, a dependency-free wheel, PowerShell installation/removal, licenses, checksums
and validation instructions. No administrator rights or WSL are part of this setup.

After one-time personal installation and repository registration, a normal request
captures intent, prepares independent acceptance before edits, uses the native checkout,
and checks/reviews an exact snapshot. Required corrections trigger bounded repair.
Discussion retains unfinished work. A failed generated test can be independently
investigated and replaced with preserved evidence; required team checks remain gates.

Guardian stores its runtime, reports and configuration in user-scoped directories.
Acceptance and review invoke the configured Codex model service and may process relevant
source, prompts and test evidence. Offline installation and network-disabled test
commands do not make model processing offline. The workflow uses the account and
configuration available on the work device; the package does not include a login.
It does not add Guardian files to the team repository or alter the user's staging.
Existing hooks are merged, backed up and preserved during removal. Installation sets
personal model/reasoning defaults to Sol/high; managed policy and task overrides still
need local verification. The implementation agent classifies turns and prepares the
spec automatically; the owner need not invoke methods or reviewers for each task.

This is a **release candidate for laptop acceptance**, not a claim of zero-correction
code. Source/CI validation, actual Windows Codex sandbox behavior, corporate environment
compatibility and integration with the intended existing worker are separate facts. See
[validation evidence](docs/VALIDATION.md), [design and limits](docs/DESIGN.md), and the
[worker contract](docs/WORKER.md). This repository contains one initial source snapshot;
earlier Git history and releases are not imported. See [provenance](docs/PROVENANCE.md).

The fixtures in this release are public/synthetic. The proposed worker adapter is
documented separately from its pending local compatibility test. Deployment-specific
names and setup details belong in the [laptop guide](docs/LAPTOP-START.md).
For the account setup, normal task sequence and stored artifacts, read
[ACCOUNT-WORKFLOW.md](docs/ACCOUNT-WORKFLOW.md).

Local development uses Python 3.11+ with no runtime dependencies:

```console
python -m pip install --no-deps .
python -m unittest discover -s tests -v
python -m build
python scripts/verify_artifact.py
python scripts/build_bundle.py
```

The installed package retains the internal module name `guardian_next`; its distribution
and command are `guardian-native`. Runtime source, guidance, test fixtures and historical
experiment evidence are counted separately in the validation report.
