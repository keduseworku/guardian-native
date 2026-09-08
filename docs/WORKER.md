# Worker integration

Guardian imports bounded code changes from a worker running in a separate Git worktree.
The worker owns launching, proposals, execution and its result record. Guardian checks
the result and independently validates the integrated candidate.

Inspect the worker's interface on the target device and compare its result with the
envelope below. A mismatch requires an adapter change and regression before use.
Complete the real disposable worker trial to establish compatibility.

The worker launcher must explicitly select **Luna only**. Guardian's importer does not
launch the worker or verify its model. Retain the actual dispatch settings/receipt to
confirm that account-level Sol/high defaults did not change the worker's selection.
Independent acceptance and final review remain Sol/high.

Before registering the intended work repository, complete one bounded leaf through
the actual worker interface in a disposable repository with synthetic input. If the
interface cannot operate there, report that limitation and resolve the acceptance plan
before registering the work repository. Synthetic adapter tests do not satisfy this gate.

After Guardian acceptance is prepared, choose a bounded leaf whose proposal/provenance
process benefits from the existing worker. Launch through its established interface
from the exact current native candidate. The worker must use a separate registered Git
worktree of the same repository and leave its changes uncommitted relative to that
candidate baseline. Preserve its process exit code and JSON result locally.

Before dispatch, run `worker-preflight --repo ... --session ...` with the same
`--home` used for preparation. The current adapter requires a clean HEAD checkout:
it reconstructs Git's checkout bytes using a temporary index and directory, including
built-in LF/CRLF conversion, and compares them byte for byte with the native baseline.
It never rewrites native line endings. The worker must start at the exact prepared
commit and reconstruct the same checkout bytes. Import repeats the baseline check.

Working-file content changes, untracked starting files, changed checkout settings,
custom filters and working-tree encodings require explicit adapter support. Preserve
those files and use direct native implementation or a separately prepared disposable
baseline; do not discard edits to satisfy preflight. Staging itself is preserved.

The expected result requires `success`, `execution_success`, `work_product_created`
true; `failure_classification` null; `validation_provenance.status` verified with matching
nonempty before/after snapshot IDs. `work_product` must contain success true, a worktree
path, exact branch name, exact changed-file list and a nonempty validation list whose
entries have outcome passed. Claims are necessary but insufficient: Guardian independently
checks worktree identity, baseline tree, scope, file modes, byte bounds and stability.
Skipped entries remain rejected; optional validation needs an explicit adapter contract
before it can be distinguished from an omitted required check. Guardian always runs
its registered team checks after import. No result normalization may waive those checks.

Call the personal runtime's `worker-import --repo ... --session ... --file ...
--exit-code ...` command with the actual result. The importer accepts ordinary files
only and a maximum 16 MB delta. It preserves staging and rolls back its own copied bytes
on failure while avoiding overwriting concurrent user edits. Imported work is **not
approved**: the normal Stop hook must run required team checks, frozen acceptance and
independent review on the integrated native candidate.

Laptop acceptance must retain a real bounded worker leaf, original proposal/result,
provenance, actual process exit, native before/after trees, staging comparison, importer
receipt and final Guardian report. Until that passes, keep the deployment acceptance
task in its disposable repository. Do not fabricate worker results or manually mark the adapter accepted to make
setup appear complete.
