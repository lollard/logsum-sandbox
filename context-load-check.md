From [CLAUDE.md](app://localhost/epitaxy/CLAUDE.md):

**Project context** — A tiny CLI that reads `data/events.csv` (synthetic logs) and prints a summary report.

**Conventions** — Source lives in `src/`, tests in `tests/`, CSV fixtures in `data/`. Uses Python 3.11 stdlib, ruff for linting/formatting, and pytest.

**Escalation gates** — Three hard stops: confirm before adding dependencies, never commit real log data, and don't overwrite `spec.md` after sign-off without asking.