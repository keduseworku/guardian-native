# Release design and limits

Guardian provides user-scoped installation and registration, unique preparation inputs,
turn classification, independent acceptance, exact-candidate review and an expected
worker-result adapter. This public repository begins with a source snapshot of the
existing tool; see [provenance](PROVENANCE.md).

## Exact-candidate workflow

The user's original request and initial Git tree remain the task baseline. Git objects
are created through a temporary index, without altering staging or clean filters.
Independent disposable repositories serve authoring, checks and review. Implementation
remains in Codex's selected native checkout; Guardian never creates a second editing
root, commits there or pushes. Symlinks, submodules and special files are rejected by
this candidate's snapshot layer rather than silently omitted.

A unique UUID preparation file is issued under the OS temporary directory for each
task. The CLI verifies its binding to the session. Completed reports are archived by
task ID; author/reviewer receipts and check logs use unique evidence directories.

The implementation agent explicitly selects work, resume, clarify or discussion before
further edits. The hook instructs this automatically. Discussion must leave that turn's
bytes unchanged and preserves unfinished intent. Clarification appends the actual user
follow-up and freezes an additional suite before further edits. Valid earlier suites
remain required. A Stop continuation retains the existing task and repair count.

A generated acceptance failure receives separate read-only adjudication. A code defect
uses a repair opportunity; malformed output is a bounded protocol retry; unavailable
infrastructure or unresolved evidence stops unverified. A demonstrable test defect
permits one replacement by a separate author viewing the corresponding pre-edit
baseline, original request, contract and correction reason. The old suite and failure
remain. The replacement is checked, and final independent review remains necessary.
Team checks cannot be replaced or waived by model verdicts. There is no generic ready
override for failed requirements.

Approval is saved only for the candidate that was checked and reviewed with unchanged
native HEAD. Evaluation clears a previous review before running. Repairs default to
two; protocol retries do not spend that allowance. An interrupted or exhausted task
remains unverified and its files remain available.

## Personal integration

User hooks are added to the existing JSON arrays. Unregistered repositories return an
empty hook result, so Guardian does not suppress their other hooks. User settings and
owned rules are backed up; installation writes no project Guardian configuration.
Personal model defaults do not override managed policy or an existing task selection.
Other matching user/project hooks run too; duplicate controllers must be resolved in
laptop acceptance. Documentation checked against Codex CLI 0.153.4 and the current
[hook documentation](https://learn.chatgpt.com/docs/hooks).

Repository checks run through the native OS sandbox with network disabled and a
sanitized environment. Test plugins remain enabled; registration uses the actual team
interpreter and commands. A correctly configured sandbox is an operating-system
requirement. This is process isolation and audit evidence within one user account,
not a security boundary against a malicious operator or a guarantee that repository
tests cannot read every file available to that account.

## Methods and test quality

Ponytail is the complete supplied policy. Thirteen Pocock methods are pinned, attributed
adaptations, not a claim that every upstream skill is bundled. See the packaged
provenance table and licenses. Only relevant detailed methods are loaded.

Hypothesis support is conditional on task fit and the actual interpreter. Property
strategies need justified invariants; randomized generation does not create an oracle.
Deliberate negative controls run in disposable copies and must fail for the intended
reason. No mutation framework or WSL dependency is introduced. Import direction and
changed-line coverage use the team's actual contracts and thresholds; neither proves
semantic ownership or correctness. Gitleaks must be an explicit registered check.

Confirmed local corrections carry paths, an evidence reference and a regression
reference. Relevant corrections are loaded for authoring and review; reproduce the
failure and write a regression before persisting guidance. They do not replace user
requirements and are not written into team AGENTS.md. A focused independent challenge
may be arranged for unresolved evidence; the default is one Sol/high final reviewer.

## Explicit acceptance boundaries

Source regressions use simulated role outputs where stated. A real model smoke is a
bounded integration observation, not a comparative quality trial. Windows CI can check
Python, Git, packaging and PowerShell behavior without proving the corporate Codex
sandbox, hook activation, Conda fixtures or the actual worker. Those require the laptop.
Keep concrete post-adoption corrections, false rejections and missed defects locally;
use those observations to guide subsequent corrections.
