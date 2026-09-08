# Isolated repair-candidate trial

Target: one complete accepted change in a disposable clone, a rejected invalid change,
automatic hooks in a temporary profile, and verified configuration removal. Keep these
four results separate. Manual hook calls do not demonstrate automatic desktop dispatch.

Use this prompt with the extracted **1.0.0rc5** bundle on the target laptop:

> Test this Guardian candidate in isolation. Use only a newly created temporary Guardian
> home, temporary Codex home, disposable repository clone, and separate worker state.
> Record all locations and exact versions before starting. Do not install hooks in my
> everyday Codex profile, register my actual work checkout, change system Git, or import
> worker results into a real project. Keep work-specific evidence local. Read this guide
> and WORKER.md, then execute the applicable stages. If an external worker prerequisite
> fails, preserve the evidence and stop that stage without changing the worker project
> or weakening validation. Report each stage as passed, failed, or not exercised.

## Prepare and record isolation

1. Create a unique trial directory outside every source repository. Use child directories
   for the Guardian home, Codex home, clone, worker state and evidence. Record the source
   commit, source status, wrapper path/hash, Guardian version, Python path/version and
   Git path/version. Stop concurrent edits to the test inputs; never reset another task's work.
2. Select a compatible installed Git. Guardian requires 2.27+ and avoids `git init -b`
   and `rev-parse --path-format=absolute`. `GUARDIAN_GIT` may select an absolute executable
   for this trial process. Do not change the machine's global PATH or Git configuration.
   Registration records the resolved executable and rejects subsequent path drift.
3. Clone the intended baseline into the trial directory with `git clone --no-local`.
   This copies the committed state, not uncommitted source edits. Verify the selected
   commit and checkout settings. Do not rewrite files to hide a baseline mismatch.
4. Verify the bundle's checksums. Invoke its PowerShell installer with **both** explicit
   `-GuardianHome` and `-CodexHome` paths inside the trial directory, plus the chosen
   Python 3.11+ executable. These parameters prevent the default everyday-profile targets.
   Record the temporary profile's pre-install configuration bytes or absence.

Example variables below are trial-specific. Substitute inspected executable/bundle paths:

```powershell
$TrialRoot = Join-Path $env:TEMP ('guardian-trial-' + [guid]::NewGuid().ToString('N'))
$TrialGuardian = Join-Path $TrialRoot 'guardian'
$TrialCodex = Join-Path $TrialRoot 'codex'
New-Item -ItemType Directory -Path $TrialRoot | Out-Null
# Supply actual paths to $Bundle and $TeamPython before this invocation.
& "$Bundle/scripts/Install-Guardian.ps1" -Python $TeamPython -GuardianHome $TrialGuardian -CodexHome $TrialCodex
if ($LASTEXITCODE -ne 0) { throw 'Temporary installation failed' }
$TrialPython = Join-Path $TrialGuardian 'venv/Scripts/python.exe'
```

## Exercise preparation, worker import and acceptance

1. Run Codex with the temporary Codex home and verify which profile the actual session
   uses. Changing a shell variable does not prove an already-running desktop session
   switched profiles. Authenticate the temporary profile through supported sign-in if
   required; do not copy credentials. If an isolated desktop launch cannot be established,
   manual CLI tests may proceed, but mark automatic desktop hooks **not exercised**.
   All model-invoking Guardian commands must inherit that same temporary `CODEX_HOME`.
   Guardian's `--home` selects its state directory; it does not select a Codex profile.
   Apply the profile environment only to trial processes and preserve the parent environment.
2. Register only the disposable clone, using `--home $TrialGuardian` and its real team
   interpreter and required argv commands. The configuration shape is documented in
   LAPTOP-START.md. Pass the same home explicitly to every Guardian command.
3. Run `doctor --repo <clone>`. Review its resolved tools, team checks and `review_preflight`
   evidence. The preflight uses the actual Sol/high read-only reviewer on a synthetic
   Git/byte challenge. A denied or incorrect inspection prevents preparation. Never
   loosen the reviewer sandbox merely to turn the result green.
4. Capture a bounded user request and complete classification and independent acceptance
   preparation through the hooks/session commands. Preserve the request, specification,
   session ID and frozen acceptance evidence. Start a new task with this candidate;
   do not reuse frozen tests authored for an earlier in-repository test layout.
5. Run `worker-preflight --repo <clone> --session <session>` before launching the worker.
   This tests the supported clean-HEAD baseline. It does not certify the external launcher.
6. Inspect and invoke the worker's actual outer coordinator with its supported disposable
   repository and separate state settings. Explicitly select Luna. Do not call a lower-level
   script, invent readiness/provenance, or replace required validation with synthetic results.
   If the installed wrapper has a missing helper, resolve that in a separately authorized
   worker task and re-record the installed wrapper hash before retrying.
7. Preserve the exit code and result. Import only into the disposable clone, then run the
   normal Stop evaluation: required team checks, frozen acceptance, independent review,
   and exact final candidate identity. Require `status=accepted` and completed inspection.
8. In a separate disposable task, exercise a known-invalid result and confirm rejection.
   Record the actual rejection gate. An environment failure is not evidence that a
   behavioral acceptance test discriminates correctly.

## Remove configuration and report boundaries

Invoke `Uninstall-Guardian.ps1 -GuardianHome $TrialGuardian`. Compare temporary profile
configuration with its pre-install state, confirm Guardian hooks/rules are removed, and
verify the original work checkout and everyday configuration against recorded baselines.
Keep unrelated concurrent edits intact and report any uncertain attribution.

Uninstall restores/removes owned integration configuration; it does **not** undo code
edits or imports, delete the runtime, or erase evidence/worker records. List retained
trial paths. Preserve evidence before optionally deleting the uniquely identified trial
directory. Do not run broad cleanup commands against shared repositories or homes.

Report the four target outcomes independently, including exact versions and any remaining
blocker. Full everyday-profile integration is a later user decision, even if this trial passes.
