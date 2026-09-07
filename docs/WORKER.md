# Existing worker integration

Guardian contains a port of the older runtime's result importer. It does not invent a
worker launch CLI or replace the worker's proposal, execution, validation or ledger.
This adapter is intended for an existing worker whose actual interface is validated
on the deployment device. It does not contain that worker's source implementation.
The actual worker interface must be inspected on the laptop. Its result envelope below
is the adapter's current expectation; a mismatch needs an explicit adapter change and
regression before use. Synthetic tests alone do not establish real worker compatibility.

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

The expected result requires `success`, `execution_success`, `work_product_created`
true; `failure_classification` null; `validation_provenance.status` verified with matching
nonempty before/after snapshot IDs. `work_product` must contain success true, a worktree
path, exact branch name, exact changed-file list and a nonempty validation list whose
entries have outcome passed. Claims are necessary but insufficient: Guardian independently
checks worktree identity, baseline tree, scope, file modes, byte bounds and stability.

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
