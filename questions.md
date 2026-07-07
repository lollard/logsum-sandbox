# Repo Q&A

## Where is the grouping rule?

**Files read:** `spec.md`, `src/logsum.py`

Each output row represents one unique `(date, level, service)` triple
(`spec.md:9–12`). `date` is the UTC calendar date extracted from `timestamp`;
`message` is explicitly excluded from the key.

In code, the triple is assembled at `src/logsum.py:39–42`:

```python
date    = ts.date().isoformat()
level   = (row.get("level") or "").strip().upper() or "UNKNOWN"
service = (row.get("service") or "").strip().lower()
key     = (date, level, service)
```

`groups.setdefault(key, {...})` at `src/logsum.py:44` creates a new accumulator
the first time a key is seen and returns the existing one on subsequent rows —
that is the merge step. `count` is incremented at `src/logsum.py:52`, and
`first_seen`/`last_seen` are updated with `min`/`max` at `src/logsum.py:53–54`.

Nothing unverifiable here; spec and implementation agree.

---

## How is missing level handled?

**Files read:** `spec.md`, `src/logsum.py`

The spec rule is: treat a missing level as `"UNKNOWN"`; count the row normally
(`spec.md:28–29`). No warning is emitted for a missing level (the warning is only
for malformed timestamps, `spec.md:32–33`).

In code, `src/logsum.py:40` implements this in one expression:

```python
level = (row.get("level") or "").strip().upper() or "UNKNOWN"
```

`row.get("level")` returns `None` for an absent column or `""` for an empty
field; both are falsy, so `or ""` normalises them to an empty string, `.strip()`
removes whitespace, `.upper()` uppercases, and the trailing `or "UNKNOWN"` fires
when the result is still an empty string. The row then proceeds through normal
accumulation (`src/logsum.py:44–54`) with no branch for the missing-level case —
confirming it is counted normally and silently.

Nothing unverifiable here.

---

## How do I run tests and CI locally?

**Files read:** `CLAUDE.md`, `.github/workflows/ci.yml`

**Tests:**

```
pip install pytest
pytest -v
```

`CLAUDE.md:9` names pytest as the test runner. The CI workflow runs `pytest -v`
with no extra flags or environment variables (`.github/workflows/ci.yml:23`), so
the same bare command works locally.

**Lint (mirrors CI):**

```
pip install ruff
ruff check .
```

`CLAUDE.md:8` names ruff for linting. CI runs `ruff check .` at
`.github/workflows/ci.yml:20`; running the same command locally reproduces the CI
lint step exactly.

**CI workflow itself** (`.github/workflows/ci.yml:3`) triggers on `push` and
`pull_request` and pins Python to 3.11 (`.github/workflows/ci.yml:14`). To match
that precisely locally, use Python 3.11. There is no `requirements.txt`,
`pyproject.toml`, or `setup.py` in the repo; `ruff` and `pytest` are the only
install-time dependencies, and both are installed via a bare `pip install` in CI
(`.github/workflows/ci.yml:17`).

**Could not verify:** there is no `Makefile` or `tox.ini`; a search was not
performed for those files. If either exists they might provide convenience
targets, but no evidence of them was seen.

## Verification
Passed