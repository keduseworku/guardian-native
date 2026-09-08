# Guardian Native

Guardian adds independent acceptance tests and review to ordinary Codex coding tasks.
It captures the request, prepares acceptance before edits, and checks the completed
code against the request and your repository's required checks. Corrections trigger
bounded repair. Implementation stays in the native checkout with staging preserved.

## Start on Windows

1. Download `guardian-native-1.0.0rc4-windows.zip` from the
   [release page](https://github.com/keduseworku/guardian-native/releases/tag/native-1.0.0rc4).
2. Extract it into a user folder outside the repository you want to work on.
3. Open the extracted folder in Codex and paste the setup prompt from
   [LAPTOP-START.md](docs/LAPTOP-START.md).

Setup needs a signed-in Codex installation with its CLI, Git and Python 3.11+.
The installer creates a separate Python environment and installs the bundled wheel
offline. Repository checks use your team's actual interpreter and commands.
The guide validates the workflow in a disposable repository before registering work.

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
