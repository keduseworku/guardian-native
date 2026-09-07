# Source and distribution provenance

This repository starts from a reviewed source snapshot of the existing Guardian tool.
It has a new Git repository with one initial source commit. Earlier Git history,
branches, tags, releases, experiment reports, private review correspondence and
deployment-specific notes are not imported. This describes the publication boundary;
it does not claim that the software was originally authored in this repository.

The runtime, installer, tests and generic guidance are distributed under the included
repository license. The expected worker-result adapter describes the interface it
validates; the distribution does not contain an external worker's implementation or
establish compatibility with a particular deployment.

The retained fixtures are synthetic or based on public cachetools code, with the
cachetools license retained. See tests/fixtures/PROVENANCE.md. Ponytail and the selected
Pocock methods retain their upstream attribution, licenses and pinned source identifiers
under src/guardian_next/resources. Adapted-file hashes identify the distributed methods.

This snapshot includes no account credentials or deployment source repository. The
runtime processes data supplied when it is used: local artifacts remain in selected
device locations, while Codex acceptance and review may process relevant source, prompts
and test evidence through the configured model service. See ACCOUNT-WORKFLOW.md.

Historical model-quality comparisons and development smoke receipts are not part of
this publication. Validation claims for this public release are limited to the checks
and evidence linked from VALIDATION.md and its release notes. Actual account, hook,
sandbox, team-environment and existing-worker acceptance must be completed on the
target device using the disposable-first sequence in LAPTOP-START.md.
