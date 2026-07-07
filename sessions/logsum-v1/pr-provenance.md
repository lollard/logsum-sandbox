# PR provenance block — logsum v1

## Links

| Artefact | Path |
|---------|------|
| Spec (repo) | [`spec.md`](../../spec.md) |
| Session log | [`sessions/logsum-v1/session-log.md`](session-log.md) |
| Independent tests | [`tests/test_logsum.py`](../../tests/test_logsum.py) |
| Seven-lens review | [`reviews/pr-logsum-v1/review.md`](../../reviews/pr-logsum-v1/review.md) |
| Prior provenance | [`provenance.md`](../../provenance.md) |

## Test isolation tier

**Tier A** — tests generated in a context that had not seen `src/logsum.py`.
Confirmed by `test-notes.md` and `provenance.md`.

## Verification gate

| Check | Result |
|-------|--------|
| All ACs have ≥1 test | ✓ 9/9 ACs covered |
| All tests pass | ✓ 38/38 |
| Seven-lens review complete | ✓ all lenses run, findings named |
| Security-class findings | None — no escalation required |
| Spec version discrepancy | Noted (artefacts spec omits `--min-count`); repo spec is authoritative |

## Decisions NOT made here (human-owned)

- Architecture approvals
- The merge button
- Whether the artefacts spec or the repo spec governs for downstream consumers
