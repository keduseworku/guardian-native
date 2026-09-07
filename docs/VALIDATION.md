# Validation scope

This public snapshot has 45 focused regression tests. Release verification runs those
tests, Ruff lint/format checks, source/wheel byte comparison, fresh offline wheel
installation and integration install/removal in disposable user directories.
The CI matrix repeats the checks on Windows, Linux and macOS with Python 3.11 and 3.12.
Both Windows jobs also extract the complete zip and execute the PowerShell installer
and removal scripts with temporary user directories.

Current results are linked from this repository's release notes and Actions page:
https://github.com/keduseworku/guardian-native/actions

Lifecycle tests cover unique inputs, native worktrees, original intent through follow-up
turns, interruption, stale evidence, bounded repairs, acceptance disputes and preservation
of required checks. Installer tests cover existing hooks, exact backup/restore when
unchanged, later unrelated edits and preservation of team configuration. Worker tests
use synthetic envelopes with actual temporary Git worktrees to check provenance, scope,
byte/staging preservation and rollback. They do not exercise an external worker launcher.

Role responses are simulated in these regression tests. Some subprocess tests also
simulate the Codex sandbox adapter. The two retained deliberate-defect fixtures verify
that specific probes reject their intended defects and accept targeted corrections.
These are regression controls, not comparative model-quality measurements or an
automatic mutation-testing stage for every user task.

The wheel contains eight runtime modules and 24 guidance/attribution documents, with
no third-party runtime dependencies. The source distribution also contains tests,
fixtures and packaging scripts. The Windows bundle includes the wheel and an internal
checksum manifest. FILE-INVENTORY.md and FILE-INVENTORY.json attached to the release
list the exact contents, line counts and sizes of all three packages.

No historical live-model receipt is represented as a test of this public snapshot.
The actual target account, native hooks/sandbox, interpreter/fixtures/check commands
and a real existing-worker leaf require the disposable laptop trial in LAPTOP-START.md.
Passing those checks provides evidence for that environment and candidate; it does not
guarantee that future code needs no correction.
