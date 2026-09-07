# Engineering practices, selected by task

Read the request and relevant repository code before deciding how much process it needs.
The original request controls; repository conventions and real expected-result fixtures
provide the local engineering context. Skills supply a method, not an extra bureaucracy.

## Before editing

For unclear product intent or a substantial new feature, use `pocock/grill-with-docs` or
`pocock/grilling`, then `pocock/to-spec`. Resolve questions through code/docs first; ask
the owner only about missing intent or decisions that cannot be inferred. There is no
mandatory interview duration. Record the design and acceptance without restating the request.

Read callers, state owners, accepted patterns and relevant architectural decisions.
Use `pocock/codebase-design` when boundaries or state ownership need design. Decompose a
large change with `pocock/to-tickets`; do not build a graph or install a planning system.

For each behavioral requirement, derive a concrete input/expected-output pair from an
authoritative fixture, donor-system result, exact arithmetic, or a worked specification
example. State how it was derived. Enumerate applicable empty, invalid, extreme, overflow,
underflow, mutation, aliasing and failure-recovery boundaries. In numerical work, separate
intermediate representation failure from the mathematical final result. In ingestion,
follow values through parsers as well as arithmetic. Do not invent business expectations.

Independent acceptance is authored from that evidence before implementation and stays
outside the editing root. A regression should reject the old defect. A check that passes
an almost-correct implementation needs a stronger input or assertion, not another label.

## During implementation

Use `pocock/implement` and `pocock/tdd`: one useful vertical slice, tests at public seams,
then the minimum adequate implementation. Use `pocock/diagnosing-bugs` for uncertain
failures. Run focused checks, then the repository's actual completion commands.
Direct implementation, acceptance and review use Sol/high. When using the existing
worker, its launcher must select Luna explicitly; the result importer does not choose
or verify the worker's model. Keep that worker exception when applying account defaults.

Keep Ponytail `full` behavior from PONYTAIL.md: understand the whole affected flow first;
reuse existing code, standard library and native platform features; fix the root cause;
avoid speculative abstractions. Retain required validation and protection against data
loss. Few lines are useful only when they implement the full requirement correctly.

Karpathy-derived core discipline: think before coding, prefer simplicity, make surgical
changes, and work toward explicit verifiable outcomes. Boris/Cherny-derived instruction
discipline: keep instructions concise and retain confirmed corrections in personal Guardian state;
load detailed references only for the task that needs them.

## At completion

Use `pocock/code-review` for one independent final judgment of behavior and engineering
quality. The candidate lives in the native worktree; tests/review use disposable copies
of immutable Git trees. Passing tests never substitutes for reading the integrated diff.

Apply pstack's named practices selectively: interrogate assumptions when evidence conflicts;
remove unnecessary abstractions after correctness; reflect after an actual failure by
recording a small actionable correction. These are local adaptations of the researched
practices, not a claim that unavailable upstream skill bodies were bundled verbatim.
Use concise wording for routine handoff, never to omit a requested explanation.

Use `pocock/handoff` and `pocock/writing-for-agents` when useful. Custom exec-plan, fix-ci,
review-pr, add-migration and doc-garden remain task categories: use existing repository
procedures rather than auto-generating files or installing overlapping workflow packs.

Provision repository-appropriate checks for the language and task. Complexity is reported to the reviewer; it does not consume a repair attempt.

## Source boundary

The Pocock methods here were preserved from the prior pinned, attributed adaptations.
This native release removes their obsolete daemon, graph and export instructions. See
`pocock/PROVENANCE.md` and its license for upstream attribution. PONYTAIL.md preserves
the complete supplied policy. Only the selected method resources and their attribution are distributed.

## Registered tools and local feedback

Use the actual registered team environment and checks. For numerical, parser or stateful
work, use Hypothesis when installed and appropriate; justify invariants and strategies.
Demonstrate that tests reject meaningful near misses using deliberate faulty implementations
in disposable copies. Record why they failed. An established compatible mutation runner
may help; no WSL or homegrown mutation framework is required.

Use the team's import contracts and coverage configuration when available. Report
uncovered changed behavior; enforce team thresholds rather than a universal 100% rule.
Do not add suppressions just to turn a report green. Import direction does not determine
semantic ownership. Gitleaks runs only when registered as an actual check.

After a reproduced and confirmed mistake, add a regression first. Retain a scoped rule,
evidence and regression reference using the personal correction command. Do not turn
every reviewer comment into a permanent rule or edit shared instructions for this purpose.
One Sol/high reviewer is the default. A focused independent challenge is useful for
unresolved evidence; findings still require validation. Different model names do not
establish independent errors.
