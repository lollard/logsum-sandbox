# Provenance — logsum replay

## Model
`claude-sonnet-4-6`

## Context loaded before writing
All files were read by an Explore agent before any code was written:
- `spec.md` — sole source of truth for all behaviour
- `src/logsum.py` — prior implementation (read to understand what exists, not reused)
- `tests/test_logsum.py` — prior tests (same)
- `tests/fixtures/*.csv` — all five fixture files
- `.github/workflows/ci.yml`
- `CLAUDE.md`
- `data/sample_events.csv`, `data/summary.csv`
- `questions.md`

## Files written
Every file was produced as a full overwrite from `spec.md` alone.

| File | Nature |
|---|---|
| `src/logsum.py` | Full rewrite + in-place refactor |
| `tests/test_logsum.py` | Full rewrite |
| `tests/fixtures/normal.csv` | Overwrite (content unchanged) |
| `tests/fixtures/whitespace.csv` | Overwrite (content unchanged) |
| `tests/fixtures/missing_level.csv` | Overwrite (content unchanged) |
| `tests/fixtures/malformed_ts.csv` | Overwrite (content unchanged) |
| `tests/fixtures/empty.csv` | Overwrite (content unchanged) |
| `.github/workflows/ci.yml` | Overwrite (content unchanged) |
| `provenance.md` | Created new |

## Deviations from spec
One intentional omission: the prior `src/logsum.py` accepted two undocumented
positional arguments (`INPUT`, `OUTPUT`). These are not in `spec.md §9` and no
test relies on them. The replay removes them — the CLI now accepts only the four
flags the spec defines: `--input`, `--output`, `--strict`, `--min-count`.

## Refactor applied
**Target:** output-writing section of `main()`.

**Before:** two separate `if output_path` guards — one to open the file, one to
close it — with `out_fh` left open if `writerows` raised between them.

**After:** `contextlib.nullcontext` unifies file and stdout into a single `with`
block. The duplicated condition is gone and the file is always closed on exit,
including on `OSError`. `contextlib` is stdlib; no new dependency.

## Verification run

| Command | Result |
|---|---|
| `pytest tests/test_logsum.py -v` | 38/38 passed |
| `python -m src.logsum --input data/sample_events.csv` | 3 groups, 1 malformed-ts warning |
| `python -m src.logsum --input data/sample_events.csv --min-count 2` | 1 group (INFO/auth ×2) |
| `python -m src.logsum --min-count foo` | exit 2 |
| `python -m src.logsum --no-such-flag` | exit 2 |
| `ruff check .` | not run — `ruff` not on PATH in this shell session |
