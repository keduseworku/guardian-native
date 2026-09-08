# Prefer the isolated trial first

For the local repair candidate, start with [ISOLATED-TRIAL.md](ISOLATED-TRIAL.md).
The setup below targets everyday-profile integration and requires that separate user
decision after isolated acceptance. It is not needed to continue testing.

# Laptop start

Download the complete Windows zip linked from README.md. Extract it into a user folder
outside the target repository. Open the extracted folder in Codex and paste the prompt
below to install Guardian and validate it with a disposable task. After setup, normal
coding requests run the workflow automatically. Store local artifacts in the work device's
permitted locations. Acceptance and review use the configured Codex model service and may process relevant source, prompts
and test evidence; local artifact storage does not mean offline model processing.
The runtime and methods discover the target interpreter and check commands.
Compatibility with an existing worker must be established on the target device.

> Install and validate Guardian Native on this Windows laptop. Read README.md and
> docs/ACCOUNT-WORKFLOW.md, docs/DESIGN.md and docs/WORKER.md. Inspect the Codex CLI/version,
> user and managed configuration, user/project hooks and rules, Git, Python installations and
> the team's active Python environment (including Conda if used). Preserve configuration
> and team files.
> Use the work account signed in on this device. Confirm which account/provider the child
> model roles actually use, since they omit user config; report a mismatch before using work source.
> Use an existing standard-user Python 3.11+ for Guardian's separate runtime, and the
> actual team interpreter for repository checks; these may be different interpreters.
> Verify release checksums and run scripts/Install-Guardian.ps1 with the detected Python
> path. Do not install WSL or request administrator rights. If corporate policy blocks
> a needed step, report the concrete restriction. Verify that each Guardian hook is
> installed once and preserve other configured hooks.
>
> In a disposable repository with synthetic input first, capture one raw UserPromptSubmit
> payload in a local temporary file before repository registration. Confirm cwd, session_id
> and a nonempty prompt are present and correctly identify that prompt. Record any native
> turn ID separately; this runtime does not consume it. If required capture fails, stop
> setup and report the defect; unverified capture is not an accepted operating mode.
> Use the installed CLI's supported hook configuration/trust flow for this temporary probe,
> preserve other hooks and remove the probe after inspection. Then register a configuration
> using the actual Codex executable and interpreter, run doctor, and verify a prompt through real
> UserPromptSubmit and Stop hooks: capture, pre-edit acceptance, implementation, required
> checks, independent Sol/high review and bounded repair. Also verify discussion/resume,
> interruption, distinct native worktrees in parallel, existing-hook coexistence, and
> unchanged staging. Confirm that model and sandbox settings are effective. Before any
> target-repository registration, follow docs/WORKER.md and complete one bounded synthetic leaf through
> the actual existing worker interface in the disposable repository. Its launcher
> must explicitly use Luna only; retain the dispatch evidence, original proposal/result,
> process exit code, provenance, staging comparison and integrated Guardian checks/review.
> Do not claim worker acceptance from synthetic adapter tests. If the worker cannot operate
> in the disposable repository, report that limitation and resolve this gate before proceeding.
> Only after the disposable workflow and real worker leaf pass, inspect
> the target repository's existing guidance, CI/check configuration, imports, plugins, fixtures and
> accepted examples. Register its actual commands outside the repository and run doctor
> on an exact disposable snapshot. Include the team's import contracts, coverage gates
> and secret scan when available; do not invent rules or make every optional tool mandatory.
> For meaningful numerical/parser/stateful work, verify Hypothesis in that environment.
> Record results and concrete blockers locally. Treat this request as authorization for reversible personal setup
> and acceptance work. Do not publish corporate files or alter shared team configuration.

## Direct commands, when useful

Run PowerShell from the extracted bundle. Supply the actual interpreter discovered on
this laptop; an example path is intentionally not substituted for environment discovery.

```powershell
.\scripts\Install-Guardian.ps1 -Python $DetectedPython
```

If the corporate execution policy rejects the script, retain that failure and follow
approved local policy. The installer does not change execution policy. It creates
`$env:USERPROFILE\.guardian-native\venv`, installs the bundled wheel offline, merges
user hooks, writes one owned user rule file and backs up changed personal files.
Restart Codex after installation. Existing task-specific model selections may need
switching to Sol/high. Keep the existing worker's explicit Luna dispatch; that requirement is
independent of the account default. See [the complete account workflow](ACCOUNT-WORKFLOW.md).

Create a personal JSON configuration outside the repository. These fields are required:

```json
{
  "python": "<absolute team Python executable>",
  "codex": "<absolute Codex executable>",
  "checks": [
    ["<absolute team Python executable>", "-m", "pytest", "<actual team test path>"]
  ],
  "test_seconds": 300
}
```

The commands above are a schema example, not commands for any specific repository. Replace them from
the team's existing configuration. Checks are argv arrays, never shell strings. Use
absolute executable paths; all run in disposable copies with networking disabled.
Required test plugins are enabled. Commands must inspect the working snapshot, including
untracked candidate files; a check that scans only committed HEAD would inspect the
baseline. For example, select the supported working-directory secret-scan mode rather
than assuming a Git-history scan covers new files. `check_env` can carry explicit nonsecret settings
needed by the team environment. Credentials and home/import redirection are rejected.
An installed dependency that imports the original editable checkout instead of the
snapshot must be corrected or excluded before treating validation as meaningful.

```powershell
$GuardianPython = Join-Path $env:USERPROFILE '.guardian-native\venv\Scripts\python.exe'
& $GuardianPython -I -m guardian_next.cli register --repo $RepositoryPath --config $PersonalConfig
& $GuardianPython -I -m guardian_next.cli doctor --repo $RepositoryPath
```

Registration follows Git's common directory, so it applies to native worktrees of the
same repository. Doctor evidence belongs to each worktree/configuration. The first prompt in a new worktree runs doctor automatically when evidence is missing
or configuration has changed. Baseline check failures are shown for investigation;
they remain required completion checks. This permits fixing a reproducible existing
bug without pretending the baseline is green. Sandbox/command launch failures block
activation until the environment is corrected.

Doctor reports interpreter and Codex versions, Git, Conda availability, Python test-tool
availability, the exact registered commands and sandboxed check results. It does not
install optional test packages automatically. No generic unittest, Gitleaks, import
contract, Hypothesis, or changed-line coverage gate is silently enabled.

## Removal and recovery

```powershell
.\scripts\Uninstall-Guardian.ps1
```

Removal restores unchanged installed files byte-for-byte. If unrelated configuration
was changed later, it removes only owned hooks and restores owned settings that still
match the installed values. A modified Guardian rule is preserved for inspection.
Backups, runtime and local task evidence remain; removal does not delete company work.
Restart Codex. After inspecting the retained evidence, the personal runtime/state can
be removed separately if desired.

An interrupted evaluation is unverified. Inspect the report before retrying; never turn a stale report into approval. Task
locks use the operating system and release when their owning process exits. A yielded
preparation command must be polled to completion, not restarted while still active. Another
session cannot take over unfinished work in the same checkout. Resume the owning task,
use a separate native worktree, or explicitly abandon the unfinished Guardian task while
preserving its files. Changes to requirements use clarify and retain earlier valid
acceptance. Contradictory requirements need an explicit resolved specification; an
ordinary ready verdict does not erase them.
