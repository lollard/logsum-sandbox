# logsum-sandbox

## Project context
Tiny CLI that reads `data/events.csv` (synthetic logs) and prints a summary report.

## Conventions
- `src/` — application source
- `tests/` — pytest test suite
- `data/` — synthetic CSV fixtures only

## Utilities to prefer
- Python 3.11 standard library (csv, argparse, collections, datetime)
- ruff for linting and formatting
- pytest for tests

## Escalation gates
- **Stop before adding dependencies** — confirm with the user first.
- **Synthetic data only** — never commit real log data.
- **`spec.md` is locked after sign-off** — do not overwrite it without asking.