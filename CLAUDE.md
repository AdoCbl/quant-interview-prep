# CLAUDE.md

Interview-prep repo for Quant Researcher and Quant Developer roles. See README.md for layout.

## Commands
- Python: `uv sync`, `uv run pytest`, `uv run ruff check .`
- C++: `make -C cpp test` (C++20, clang++, header-only code in `cpp/src`, one test executable per `cpp/tests/*.cpp`)

## Conventions
- Notes live in `notes/<topic>/README.md`. Each problem: statement, solution, key insight, common follow-ups.
- Every implementation in `src/quantprep` or `cpp/src` gets a test that checks a known identity or
  closed form (e.g. put-call parity, MC vs analytic price), not just "runs without error".
- When helping practice: give hints before full solutions unless asked; for brainteasers, ask for
  the user's answer first.
- Prefer numpy-vectorised Python; seed RNGs (`np.random.default_rng(seed)`) in tests.
