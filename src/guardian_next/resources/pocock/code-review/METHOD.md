> Guardian adaptation of Matt Pocock’s pinned methods; see [provenance](../PROVENANCE.md).

# Code review: standards and specification

Guardian's single independent final arbiter evaluates both axes against the immutable
candidate, original baseline, original requests, selected spec and repository standards.
Keep the findings distinct so passing style cannot hide incorrect behavior. There is
no second automatic review-agent cascade. Code already checked mechanically needs no
duplicate style finding. Identify correctness, compatibility, state ownership, missing
behavioral coverage, performance and maintainability defects with concrete evidence.
Repository standards override generic smell heuristics. Treat smells as judgments,
not automatic requirements for new abstractions.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

Report missing or incorrect requirements under the spec axis and violations
of actual repository standards under the standards axis. Flag speculative scope and
preserved legacy debt separately. Return one final acceptance decision; preserve the
actual independent execution evidence and explicit limitations.
