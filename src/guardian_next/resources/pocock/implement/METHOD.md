> Guardian adaptation of Matt Pocock’s pinned methods; see [provenance](../PROVENANCE.md).

# Implement

Implement the selected spec/task as one useful vertical slice, using the established
interfaces and vocabulary. Use [tdd](../tdd/METHOD.md) for behavior changes at the
interfaces already agreed in the request/spec. Run narrow tests during edits, type
checking when interfaces change, and the full configured checks at completion.
Guardian's final review applies [code-review](../code-review/METHOD.md). Leave the
verified change in the native Codex worktree. The completion hook reviews those exact
bytes; no export command or second editing directory is needed.
