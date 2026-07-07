# Seven-lens review — logsum v1

**Reviewer:** claude-sonnet-4-6 (engineering-logsum skill)
**Date:** 2026-07-07
**Artefacts reviewed:** `src/logsum.py`, `tests/test_logsum.py`, `spec.md`

---

## Lens 1 — Correctness

**Finding: none blocking.**

- `_parse_ts` converts trailing `Z` to `+00:00` before `fromisoformat`, then strips tzinfo with `.replace(tzinfo=None)`. Correct for UTC-only inputs as specified in §4.
- `enumerate(reader, start=2)` correctly numbers rows 1-based with the header as row 1.
- `return [], True` on `--strict` early-exit is correct; caller checks `had_error and args.strict` before writing output.
- `strftime("%Y-%m-%dT%H:%M:%SZ")` truncates sub-second precision — acceptable; spec does not require it.

**Note (non-blocking):** If a non-UTC ISO 8601 timestamp with explicit offset is provided (e.g., `2026-07-01T12:00:00+05:30`), the output `first_seen`/`last_seen` will carry a hardcoded `Z` suffix despite not being UTC. Spec §2 defines input as UTC, so this is a documented boundary assumption, not a bug.

---

## Lens 2 — Edge cases

**Finding: none blocking.**

- Missing columns (`timestamp`, `level`, `service` absent from CSV): `row.get()` returns `None`; `(None or "")` evaluates to `""`. Timestamp absence → skip with warning. Level absence → `UNKNOWN`. Service absence → empty string service. All handled gracefully.
- `--min-count 0`: not tested, but the filter `r["count"] >= 0` is always true, so all groups are included. Trivially correct.
- `--min-count` with empty input: tested (`test_min_count_with_empty_input_exits_zero`); exits 0 with header only. ✓

---

## Lens 3 — Security

**Finding: none.**

- All file I/O is local, via Python `open()`. No shell subprocess, no SQL, no network.
- `--input` and `--output` accept arbitrary paths — expected and correct for a local CLI tool.
- No sensitive data handling; no escalation needed.

---

## Lens 4 — Spec compliance

**Finding: spec version discrepancy (non-blocking, informational).**

All §3–§9 behaviours implemented correctly against the repo `spec.md`:

| Spec section | Implemented | Tested |
|---|---|---|
| §3 Group key | ✓ | ✓ |
| §4 Normalisation | ✓ | ✓ |
| §5 Output columns | ✓ | ✓ |
| §6 Missing level | ✓ | ✓ |
| §7 Malformed timestamp | ✓ | ✓ |
| §8 Empty input | ✓ | ✓ |
| §9 CLI flags + exit codes | ✓ | ✓ |

**Discrepancy:** The external artefacts spec (`…/500-wide/spec.md`) omits `--min-count` from §9. The repo `spec.md` includes it. Implementation follows the repo spec. If the artefacts copy is treated as the governing document, `--min-count` is an undocumented extension — not a violation, but worth a note to the spec owner.

---

## Lens 5 — Test coverage

**Finding: none.**

- 9/9 ACs covered by ≥1 test.
- 38/38 tests pass.
- Isolation tier: **A** — tests produced without access to `src/logsum.py` (confirmed by `test-notes.md` and `provenance.md`).
- All tests are spec-cited black-box tests; no implementation-aware tests.

---

## Lens 6 — Maintainability

**Finding: none.**

- `summarise()` cleanly separated from I/O in `main()`. Adding new output formats or input parsers requires no changes to business logic.
- `contextlib.nullcontext` eliminates the prior duplicated `if output_path` guard; file is always closed on any exception path.
- `_OUTPUT_FIELDS` tuple at module level makes column order change a one-liner.
- `--min-count` filtering in `main()` after `summarise()` is slightly surprising (one might expect it inside `summarise()`), but it is correct and keeps `summarise()` free of filter concerns.
- No new dependencies beyond stdlib. ✓

---

## Lens 7 — Adversarial

**Finding: none security-class.**

- Adversarial CSV: non-UTC timezone in timestamp → false `Z` label on output. No security impact; data integrity concern only, and spec defines UTC-only input.
- `--input` arbitrary path: intended; no privilege escalation possible since the process runs as the invoking user.
- Very large input: §10 explicitly scopes out streaming/chunked processing; OOM from a giant file is a known out-of-scope limitation.
- No injection vector in any code path.

No finding requires escalation.

---

## Summary

| Lens | Status | Findings |
|------|--------|----------|
| 1 Correctness | ✓ | Note: UTC-assumption for `Z` suffix in output (non-blocking) |
| 2 Edge cases | ✓ | Note: `--min-count 0` untested but trivially correct (non-blocking) |
| 3 Security | ✓ | None |
| 4 Spec compliance | ✓ | Note: artefacts spec vs repo spec diverge on `--min-count` (non-blocking) |
| 5 Test coverage | ✓ | None — 9/9 ACs, 38/38 pass, tier A |
| 6 Maintainability | ✓ | None |
| 7 Adversarial | ✓ | None security-class |

**Verdict: ready to merge.** No blocking findings. Three informational notes recorded above.
