# Guardian Native

Guardian adds independent acceptance tests and review to ordinary Codex coding tasks.
It captures the request, prepares acceptance before edits, and checks the completed
code against the request and your repository's required checks. Corrections trigger
bounded repair. Implementation stays in the native checkout with staging preserved.

## Test the local repair candidate

This checkout is the **1.0.0rc5 local repair candidate**, pending a complete Windows
worker acceptance run. Use its built `guardian-native-1.0.0rc5-windows.zip` and follow
[ISOLATED-TRIAL.md](docs/ISOLATED-TRIAL.md). The trial uses a disposable repository and
temporary configuration; everyday-profile integration is a separate decision.

The [published releases](https://github.com/keduseworku/guardian-native/releases) may
contain an earlier version. Do not treat earlier CI results as verification of this candidate.

Setup needs a signed-in Codex installation with its CLI, Git 2.27+ and Python 3.11+.
The installer creates a separate Python environment and installs the bundled wheel
offline. Repository checks use your team's actual interpreter and commands.
Doctor checks tool selection, required commands and actual reviewer inspection access.
For a later, explicitly chosen everyday-profile installation, use [LAPTOP-START.md](docs/LAPTOP-START.md).

After setup, submit coding requests normally. Direct implementation, independent
acceptance and review use **Sol/high**. When a worker is used, its launcher explicitly
selects **Luna**. The [account workflow](docs/ACCOUNT-WORKFLOW.md) explains each stage,
follow-up requests, model settings, stored files and removal.

Guardian stores configuration and evidence in user-scoped locations. Acceptance and
review use the configured Codex model service and may process relevant source, prompts
and test evidence. Offline installation and network-disabled checks are separate from
model processing.

This release candidate includes eight runtime modules, on-demand engineering guidance,
installation/removal scripts and focused regression tests. See [validation](docs/VALIDATION.md)
for what is tested, [design](docs/DESIGN.md) for runtime behavior, and
[worker integration](docs/WORKER.md) for the result interface. [Licenses and attribution](docs/PROVENANCE.md)
identify the bundled third-party materials. Each release includes a complete file inventory
and checksums.
