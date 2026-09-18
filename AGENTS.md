# Agent contract

The repository uses AI coding tools as accelerators, not as the verification authority.

Hard gates:
- Historical client fixtures are immutable to the code-generation loop.
- Generated operations may not escape the workspace.
- Model output cannot become a shell command.
- The same replay surface is run before and after repair.
- Unknown/ambiguous static call targets are reported as uncertainty rather than guessed.
- Measured results belong in `artifacts/`; targets and plans must not be presented as measured facts.
