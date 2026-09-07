# Guardian on the work Codex account

This release candidate is ready for a disposable laptop trial. The actual work account,
native Windows hooks/sandbox, team environment and existing worker still require that
trial. Start with [LAPTOP-START.md](LAPTOP-START.md); the source/CI checks are documented
in [VALIDATION.md](VALIDATION.md).

## What the download does

Download and extract `guardian-native-1.0.0rc3-windows.zip` outside the work repository.
The zip contains source, tests, guidance, an offline-installable wheel, PowerShell setup
and removal, checksums and validation evidence. You do not need the separate wheel or
source tarball when using this zip. It includes no account credentials or work-repository
source. Its retained test fixtures are public/synthetic; the worker adapter represents
an expected interface whose live compatibility remains to be tested.

Open the extracted folder in Codex on the work device and paste the laptop-start prompt.
Use the work account already signed in there. The package does not include
a login, conversations or development evidence from another device. Guardian launches the
installed Codex CLI for acceptance and review, using the authentication available through
that device's Codex home. It does not log in for you or select an organization/workspace.
Verify the effective account/provider during disposable acceptance: child roles omit
the user config file, so the main task's settings alone do not establish theirs.

The installer creates a separate Python 3.11+ virtual environment using an already
available interpreter. The bundled wheel installs offline with no third-party runtime
dependencies. Team tests still run with the team's registered interpreter and installed
tools; the Guardian environment does not replace Conda or provision all test dependencies.

## One-time acceptance sequence

1. Inspect the device's actual Codex version, login/configuration, hooks, Python/Git and
   team environment. Verify the release checksums. Install the user-scoped integration,
   preserve other hooks and restart Codex.
2. In a disposable synthetic repository, inspect one raw prompt-hook payload before
   registration. Verify `cwd`, `session_id` and a nonempty `prompt`. The runtime does not
   use a native turn ID. Remove the temporary probe after inspection. Stop setup if
   required capture is absent or incorrect.
3. Register that disposable repository and its real commands. Run doctor and an ordinary
   coding request through capture, pre-edit acceptance, implementation, required checks,
   final review and any bounded repair. Verify follow-ups, interruption, parallel native
   worktrees, existing hooks, effective model settings and unchanged staging.
4. Use the actual existing worker interface for one bounded synthetic leaf in the
   disposable repository. Dispatch Luna explicitly. Import the result and pass the
   integrated Guardian checks/review. Keep the actual receipt and provenance. A mock
   envelope is insufficient; an interface that cannot use a disposable repository is
   an unresolved acceptance limitation.
5. Only after those gates pass, inspect the intended work repository's actual guidance,
   examples, environment and required check commands. Store its registration outside
   the repository and run doctor on a disposable snapshot. Record real results locally.

Registration follows the repository's Git common directory and therefore applies to
its native worktrees. Doctor evidence is specific to each worktree/configuration; a new
worktree triggers doctor when needed. Another session cannot take over unfinished work
in the same checkout. Use separate native worktrees for concurrent tasks.

## Model assignments

| Role | Selection | How it is applied |
|---|---|---|
| Normal task/direct implementation | Sol, high reasoning | Installer sets local user defaults; existing task overrides require inspection |
| Independent acceptance author | Sol, high reasoning | Registered runtime invokes a separate Codex process explicitly |
| Acceptance-dispute adjudication and final review | Sol, high reasoning | Registered runtime invokes separate review roles explicitly |
| Existing worker execution | Luna only | The existing worker launcher must explicitly select it; the importer does not choose or verify the model |

Sol/high defaults apply to Codex tasks using this device's user configuration, including
unregistered repositories. This is a local configuration change, not an account-wide
change on every device. Existing task selections and managed settings may differ.
Worker Luna dispatch remains explicit. Separate model calls use the account's available
usage and may add several minutes; the package does not create a separate usage budget.

## A normal coding request

Describe the desired change in the registered work repository's Codex task. You should
not need to invoke Guardian methods or ask for each review yourself.

The prompt hook captures your request and initial candidate bytes. The implementation
agent reads the relevant guidance and examples, classifies the turn and writes a scoped
specification. Before implementation, a separate Sol/high author examines a disposable
baseline snapshot and produces acceptance tests. Those tests remain outside the editing
checkout; they are frozen before changes.

Codex implements in its selected native checkout using Sol/high. When a bounded leaf
uses the existing worker, that worker runs Luna in a separate worktree. Guardian checks
its result envelope, provenance, baseline and changed-file scope before importing its
code. Import is followed by the same integrated acceptance and review as direct work.

At completion, the Stop hook snapshots the current candidate, runs all registered team
checks and frozen acceptance, then requests an independent Sol/high review. Acceptance
is recorded only for those checked bytes with the native HEAD unchanged. Required
corrections request bounded repair; the default allowance is two. A later edit requires
fresh evaluation. This workflow does not automatically commit or push the work.

A demonstrable defect in generated acceptance can receive separate adjudication and one
replacement, with the original evidence retained. Required team checks are not waived.
Interrupted, unavailable or exhausted evaluation stays unverified. During setup, an
unverified hook/capture result is a defect to resolve before work-repository registration.

Discussion retains unfinished work. Resuming the same requirements retains acceptance;
new or corrected requirements need classification and additional pre-edit acceptance.
Relevant detailed methods load on demand. Negative-control guidance and the two retained
fixture tests do not mean every task automatically runs a mutation-testing stage.

## Files and data on the work device

| Location | Contents/effect |
|---|---|
| `%USERPROFILE%\.guardian-native\venv` | Installed Guardian Python environment and bundled guidance |
| `%USERPROFILE%\.guardian-native\registrations` | Repository command configurations and confirmed scoped corrections |
| `%USERPROFILE%\.guardian-native\worktrees` | Per-worktree reports, history, generated acceptance, role evidence, check logs and final patch |
| `%USERPROFILE%\.guardian-native\backups` | Copies of prior integration files for removal/recovery |
| Effective Codex home, usually `%USERPROFILE%\.codex` | Merged `hooks.json`, three changed `config.toml` settings and one owned rules file |
| OS temporary directory | Unique specification inputs and disposable snapshots; normal snapshot cleanup occurs when operations exit |
| Work repository's Git object store | Candidate blobs/trees created with a separate temporary index; normal staging is preserved |
| Native checkout | Requested implementation edits and imported worker code; no tracked Guardian configuration is installed |

Local evidence can contain source, prompts, specifications and test output. Store it in
the work device's permitted locations. Acceptance/review calls may process those materials
through the configured Codex model service. Network-disabled repository checks and
offline package installation do not imply offline model processing. The current runtime
does not provide automatic evidence redaction or a retention schedule.

Run `scripts/Uninstall-Guardian.ps1` to remove the owned integration, then restart Codex.
Unchanged installed configuration is restored byte-for-byte; later edits receive selective
restoration as described in the laptop guide. Runtime, backups and evidence remain for
inspection and separate cleanup. The work repository's implementation changes remain.
