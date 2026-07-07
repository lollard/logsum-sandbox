# K 5.W.9 - By-hand vs by-agent comparison

## What both produced

Both approaches would arrive at the same six artefacts:
- `tests/test_logsum.py` — 38 spec-driven CLI tests
- `tests/fixtures/*.csv` — five fixture files derived from the spec
- `.github/workflows/ci.yml` — push/PR workflow running ruff and pytest
- A refactor of `summarise()` / `main()` in `src/logsum.py`
- A new `--min-count N` flag wired through argparse and the output filter
- Supporting documents (`questions.md`, `provenance.md`)

The end state is identical; the path and the audit trail are not.

## Where the agent saved time

**Parallel file writes.** All eight fixture and source files were submitted in
one message and written concurrently. By hand that is eight sequential
save-and-verify cycles.

**Boilerplate with no omissions.** The 38 tests were produced in one pass,
covering every section of the spec (grouping, normalisation, missing level,
malformed timestamp, empty input, exit codes, `--min-count`) without a
checklist. A developer writing by hand would draft a few cases and probably
miss the `first_seen == last_seen` singleton test or the `--min-count 99`
header-only edge case on the first pass.

**Exact citations on demand.** `questions.md` cited `spec.md:28–29`,
`src/logsum.py:40`, `.github/workflows/ci.yml:14` without needing to search.
By hand that means opening each file, counting lines, and copying the
reference manually.

**Plan as a checkpoint.** The planning phase for `--min-count` produced a
written spec-of-the-change (fixture map, test names, placement of the filter
line) before a single character of code was typed. The same artefact would
take 15–20 minutes to write by hand and most developers would skip it.

## Where the agent went wrong or came up short

**`ruff` was not verified.** The provenance note honestly records that `ruff`
was not on `PATH` in the shell session, so `ruff check .` was never run. The
plan listed it as a required verification step. A by-hand developer running
locally would have noticed the missing tool immediately and installed it.

**Filter placement was ambiguous.** The plan said to place the `--min-count`
filter "before the output section." The agent placed it before the
`if had_error and args.strict: return 1` guard, not after it. Both positions
produce identical runtime behaviour, but the plan's wording was not precise
enough to catch the discrepancy, and the provenance note only flagged it
retrospectively. A code review would have caught it on the diff.

**Positional args were removed without a direct user request.** The replay
removed the undocumented `input_pos`/`output_pos` arguments because they
were not in the spec. That was a defensible call, but it was a behaviour
change that a by-hand developer would have asked about first rather than
folded into a "replay from spec" justification.

## What the agent did better

**Consistency between spec and test.** Every test assertion maps to a named
section of `spec.md`. The `find_group` helper is used uniformly across all
grouping tests rather than each test using a different lookup idiom. By hand,
test style drifts between sections written at different times.

**The refactor was well-targeted.** The `contextlib.nullcontext` change
eliminated the duplicated `if output_path` guard and introduced correct
resource cleanup if `writerows` raised mid-write — a subtle correctness
improvement, not just a cosmetic one. By hand, the obvious fix would have been
to extract a helper function, which is heavier than a one-liner context
expression.

**The provenance note was honest.** It listed what was not run, named the
deviation, and explained why the filter placement differed from the plan. A
by-hand commit message would have said "add --min-count flag" and nothing
more.

## What I learned about supervised vs async

**Supervised (plan-then-approve) is appropriate when:**
- The change has a behaviour impact that is not fully reversible (removing
  undocumented CLI args, touching the spec).
- The requirements have more than one reasonable interpretation (filter before
  or after the strict-error check).
- The output will be reviewed by someone other than the person who triggered it.

The plan-approval gate forced ambiguities to be written down before execution.
The resulting plan document served as a micro-spec for `--min-count` that
outlasted the conversation.

**Async (fire-and-check) is appropriate when:**
- The task is well-scoped and the acceptance criterion is a binary test result.
- Parallel work is independent (writing five fixture files has no ordering
  dependency).
- The cost of a wrong answer is low and reversible (a fixture file with the
  wrong row is a one-line fix).

The test-writing and fixture-writing passes were effectively async: the agent
was given a spec and a constraint ("do not read the implementation") and
produced the output in one shot with no mid-task decisions to make.

**The gap between the two:** async agents do not interrupt to ask about edge
cases. The `ruff not on PATH` issue would have been surfaced immediately in a
supervised session where the developer was watching the terminal; in a fully
async run it would have been buried in the output log and reported as "not
verified" in the provenance note, which is exactly what happened.

## What I would do differently next time

1. **Pin the verification commands in the plan, not just list them.** Write
   them as `assert`-style acceptance criteria: "exit 0, stdout contains exactly
   three CSV rows, stderr is empty." Listing commands without expected output
   means the verify step is under-specified and easy to skip.

2. **Check for tool availability before writing the plan.** A single
   `ruff --version` at the start of the session would have caught the PATH
   issue before it appeared in the provenance note as an unrun step.

3. **Explicitly decide on undocumented behaviour before the replay, not
   during it.** Ask: "the current code has positional args not in the spec —
   keep or remove?" That is a one-line question that prevents a silent
   behaviour change from appearing in the diff.

4. **Use the provenance-note format from the start, not at the end.** The
   provenance note written after the replay was accurate because the session
   was linear and well-documented. In a longer or multi-session project the
   same information becomes hard to reconstruct after the fact.
