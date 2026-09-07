> Guardian adaptation of Matt Pocock’s pinned methods; see [provenance](../PROVENANCE.md).

# Design it twice

For a consequential interface decision, sketch two substantially different adequate
interfaces from the same requirements. Compare caller burden, state ownership,
locality, error modes, compatibility and testability; choose the simpler adequate one.
Use [DEEPENING.md](DEEPENING.md) when dependency placement is the problem. The supervisor
normally performs this comparison. Independent parallel design exploration is optional
when explicitly authorized and its value justifies the cost. Routine edits need no
alternative-design ceremony.
