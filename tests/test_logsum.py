"""
Spec-driven tests for the logsum CLI.
All behaviour is derived from spec.md; src/logsum.py is treated as a black box.

Fixture layout (tests/fixtures/):
  normal.csv        – valid rows covering multiple groups
  whitespace.csv    – level/service with surrounding whitespace
  missing_level.csv – empty level field
  malformed_ts.csv  – one bad timestamp surrounded by good rows
  empty.csv         – header row only
"""

import csv
import io
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"

OUTPUT_COLUMNS = {"date", "level", "service", "count", "first_seen", "last_seen"}


# ── helpers ───────────────────────────────────────────────────────────────────


def run_logsum(*extra_args, input_file=None):
    cmd = [sys.executable, "-m", "src.logsum"]
    if input_file is not None:
        cmd += ["--input", str(input_file)]
    cmd += list(extra_args)
    return subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )


def parse_output(text):
    return list(csv.DictReader(io.StringIO(text)))


def find_group(rows, *, date, level, service):
    return next(
        (r for r in rows if r["date"] == date and r["level"] == level and r["service"] == service),
        None,
    )


# ── output schema ─────────────────────────────────────────────────────────────


def test_output_columns_present():
    result = run_logsum(input_file=FIXTURES / "normal.csv")
    assert result.returncode == 0
    rows = parse_output(result.stdout)
    assert rows
    assert set(rows[0].keys()) == OUTPUT_COLUMNS


# ── grouping ──────────────────────────────────────────────────────────────────
# normal.csv groups:
#   (2026-07-01, INFO, auth)  count=2  first=10:00  last=10:05
#   (2026-07-01, WARN, api)   count=1
#   (2026-07-02, INFO, auth)  count=1


def test_rows_sharing_date_level_service_are_merged():
    result = run_logsum(input_file=FIXTURES / "normal.csv")
    rows = parse_output(result.stdout)
    grp = find_group(rows, date="2026-07-01", level="INFO", service="auth")
    assert grp is not None
    assert grp["count"] == "2"


def test_different_dates_produce_separate_groups():
    result = run_logsum(input_file=FIXTURES / "normal.csv")
    rows = parse_output(result.stdout)
    assert find_group(rows, date="2026-07-01", level="INFO", service="auth") is not None
    assert find_group(rows, date="2026-07-02", level="INFO", service="auth") is not None


def test_different_levels_produce_separate_groups():
    result = run_logsum(input_file=FIXTURES / "normal.csv")
    rows = parse_output(result.stdout)
    assert find_group(rows, date="2026-07-01", level="INFO", service="auth") is not None
    assert find_group(rows, date="2026-07-01", level="WARN", service="api") is not None


def test_message_is_excluded_from_group_key():
    # The two INFO/auth rows on 2026-07-01 have different messages; they must merge.
    result = run_logsum(input_file=FIXTURES / "normal.csv")
    rows = parse_output(result.stdout)
    grp = find_group(rows, date="2026-07-01", level="INFO", service="auth")
    assert grp is not None
    assert int(grp["count"]) == 2


def test_first_seen_is_earliest_timestamp_in_group():
    result = run_logsum(input_file=FIXTURES / "normal.csv")
    rows = parse_output(result.stdout)
    grp = find_group(rows, date="2026-07-01", level="INFO", service="auth")
    assert grp["first_seen"] == "2026-07-01T10:00:00Z"


def test_last_seen_is_latest_timestamp_in_group():
    result = run_logsum(input_file=FIXTURES / "normal.csv")
    rows = parse_output(result.stdout)
    grp = find_group(rows, date="2026-07-01", level="INFO", service="auth")
    assert grp["last_seen"] == "2026-07-01T10:05:00Z"


def test_first_seen_equals_last_seen_for_singleton_group():
    result = run_logsum(input_file=FIXTURES / "normal.csv")
    rows = parse_output(result.stdout)
    grp = find_group(rows, date="2026-07-01", level="WARN", service="api")
    assert grp["first_seen"] == grp["last_seen"]


# ── normalisation ─────────────────────────────────────────────────────────────
# whitespace.csv: " warn " / " Auth " and "WARN" / "auth" → single group count=2


def test_level_is_uppercased():
    result = run_logsum(input_file=FIXTURES / "whitespace.csv")
    rows = parse_output(result.stdout)
    assert all(r["level"] == r["level"].upper() for r in rows)


def test_level_whitespace_is_stripped():
    result = run_logsum(input_file=FIXTURES / "whitespace.csv")
    rows = parse_output(result.stdout)
    assert all(r["level"] == r["level"].strip() for r in rows)


def test_service_is_lowercased():
    result = run_logsum(input_file=FIXTURES / "whitespace.csv")
    rows = parse_output(result.stdout)
    assert all(r["service"] == r["service"].lower() for r in rows)


def test_service_whitespace_is_stripped():
    result = run_logsum(input_file=FIXTURES / "whitespace.csv")
    rows = parse_output(result.stdout)
    assert all(r["service"] == r["service"].strip() for r in rows)


def test_padded_and_canonical_values_merge_into_same_group():
    # " warn " normalises to "WARN", " Auth " to "auth" → same group as row 2
    result = run_logsum(input_file=FIXTURES / "whitespace.csv")
    rows = parse_output(result.stdout)
    assert len(rows) == 1
    assert rows[0]["count"] == "2"


# ── missing level ─────────────────────────────────────────────────────────────
# missing_level.csv: two rows with empty level field


def test_missing_level_becomes_unknown():
    result = run_logsum(input_file=FIXTURES / "missing_level.csv")
    rows = parse_output(result.stdout)
    assert any(r["level"] == "UNKNOWN" for r in rows)


def test_missing_level_row_is_counted_normally():
    result = run_logsum(input_file=FIXTURES / "missing_level.csv")
    rows = parse_output(result.stdout)
    grp = find_group(rows, date="2026-07-01", level="UNKNOWN", service="auth")
    assert grp is not None
    assert int(grp["count"]) == 2


def test_missing_level_exits_zero():
    result = run_logsum(input_file=FIXTURES / "missing_level.csv")
    assert result.returncode == 0


def test_missing_level_emits_no_warning():
    result = run_logsum(input_file=FIXTURES / "missing_level.csv")
    assert result.stderr == ""


# ── malformed timestamp ───────────────────────────────────────────────────────
# malformed_ts.csv: good / BAD / good  (bad row is file line 3)


def test_malformed_ts_row_is_skipped():
    # Only the two valid rows remain → one group with count=2.
    result = run_logsum(input_file=FIXTURES / "malformed_ts.csv")
    rows = parse_output(result.stdout)
    assert len(rows) == 1
    assert rows[0]["count"] == "2"


def test_malformed_ts_processing_continues_for_subsequent_rows():
    # The valid row *after* the bad row must appear in output.
    result = run_logsum(input_file=FIXTURES / "malformed_ts.csv")
    rows = parse_output(result.stdout)
    assert rows  # non-empty → rows after the bad one were processed


def test_malformed_ts_emits_warning_to_stderr():
    result = run_logsum(input_file=FIXTURES / "malformed_ts.csv")
    assert result.stderr.strip() != ""


def test_malformed_ts_warning_includes_row_number():
    result = run_logsum(input_file=FIXTURES / "malformed_ts.csv")
    # Bad row is file line 3 (1-based incl. header) or data row 2; either is valid.
    assert re.search(r"\b[23]\b", result.stderr), (
        f"expected a row number (2 or 3) in stderr, got: {result.stderr!r}"
    )


def test_malformed_ts_exit_code_zero_without_strict():
    result = run_logsum(input_file=FIXTURES / "malformed_ts.csv")
    assert result.returncode == 0


def test_malformed_ts_strict_flag_exits_one():
    result = run_logsum("--strict", input_file=FIXTURES / "malformed_ts.csv")
    assert result.returncode == 1


# ── empty input ───────────────────────────────────────────────────────────────


def test_empty_input_exits_zero():
    result = run_logsum(input_file=FIXTURES / "empty.csv")
    assert result.returncode == 0


def test_empty_input_outputs_header_row():
    result = run_logsum(input_file=FIXTURES / "empty.csv")
    # stdout must contain exactly the header – DictReader returns zero data rows.
    assert "date" in result.stdout
    rows = parse_output(result.stdout)
    assert rows == []


def test_empty_input_emits_no_stderr():
    result = run_logsum(input_file=FIXTURES / "empty.csv")
    assert result.stderr == ""


# ── CLI flags and exit codes ──────────────────────────────────────────────────


def test_missing_input_file_exits_one():
    result = run_logsum(input_file=FIXTURES / "does_not_exist.csv")
    assert result.returncode == 1


def test_unknown_flag_exits_two():
    result = run_logsum("--no-such-flag")
    assert result.returncode == 2


def test_output_flag_writes_to_file(tmp_path):
    out = tmp_path / "result.csv"
    result = run_logsum("--output", str(out), input_file=FIXTURES / "normal.csv")
    assert result.returncode == 0
    assert out.exists()
    rows = list(csv.DictReader(out.open()))
    assert rows  # file is non-empty


def test_output_flag_file_contains_correct_columns(tmp_path):
    out = tmp_path / "result.csv"
    run_logsum("--output", str(out), input_file=FIXTURES / "normal.csv")
    rows = list(csv.DictReader(out.open()))
    assert set(rows[0].keys()) == OUTPUT_COLUMNS


def test_output_flag_stdout_is_empty(tmp_path):
    out = tmp_path / "result.csv"
    result = run_logsum("--output", str(out), input_file=FIXTURES / "normal.csv")
    assert result.stdout == ""


# ── --min-count filter ───────────────────────────────────────────────────────
# normal.csv groups: auth/INFO/2026-07-01 count=2, api/WARN/2026-07-01 count=1,
#                    auth/INFO/2026-07-02 count=1


def test_min_count_hides_groups_below_threshold():
    result = run_logsum("--min-count", "2", input_file=FIXTURES / "normal.csv")
    assert result.returncode == 0
    rows = parse_output(result.stdout)
    assert all(int(r["count"]) >= 2 for r in rows)
    assert len(rows) == 1


def test_min_count_keeps_group_at_exact_threshold():
    result = run_logsum("--min-count", "2", input_file=FIXTURES / "normal.csv")
    rows = parse_output(result.stdout)
    grp = find_group(rows, date="2026-07-01", level="INFO", service="auth")
    assert grp is not None
    assert int(grp["count"]) == 2


def test_min_count_one_includes_all_groups():
    result = run_logsum("--min-count", "1", input_file=FIXTURES / "normal.csv")
    rows = parse_output(result.stdout)
    assert len(rows) == 3


def test_min_count_above_all_counts_outputs_header_only():
    result = run_logsum("--min-count", "99", input_file=FIXTURES / "normal.csv")
    assert result.returncode == 0
    rows = parse_output(result.stdout)
    assert rows == []
    assert "date" in result.stdout


def test_min_count_non_integer_exits_two():
    result = run_logsum("--min-count", "foo", input_file=FIXTURES / "normal.csv")
    assert result.returncode == 2


def test_min_count_with_empty_input_exits_zero():
    result = run_logsum("--min-count", "2", input_file=FIXTURES / "empty.csv")
    assert result.returncode == 0
    assert parse_output(result.stdout) == []
    assert result.stderr == ""


def test_default_input_path_is_data_events_csv():
    # Invoke without --input; the CLI must attempt data/events.csv.
    # We only assert it does NOT exit with code 2 (usage error) –
    # exit 0 (file exists) or 1 (file missing) both indicate the default was used.
    result = run_logsum()
    assert result.returncode in (0, 1)
