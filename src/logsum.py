"""Summarise synthetic event logs into a CSV report."""
from __future__ import annotations

import argparse
import contextlib
import csv
import sys
from datetime import datetime


_OUTPUT_FIELDS = ("date", "level", "service", "count", "first_seen", "last_seen")


def _parse_ts(value: str) -> datetime | None:
    v = value.strip()
    if not v:
        return None
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(v).replace(tzinfo=None)
    except ValueError:
        return None


def summarise(reader: csv.DictReader, strict: bool) -> tuple[list[dict], bool]:
    groups: dict[tuple, dict] = {}
    had_error = False

    for row_idx, row in enumerate(reader, start=2):  # row 1 is the header
        ts_raw = (row.get("timestamp") or "").strip()
        ts = _parse_ts(ts_raw)
        if ts is None:
            sys.stderr.write(f"WARNING: row {row_idx}: malformed timestamp {ts_raw!r}, skipping\n")
            had_error = True
            if strict:
                return [], True
            continue

        date = ts.date().isoformat()
        level = (row.get("level") or "").strip().upper() or "UNKNOWN"
        service = (row.get("service") or "").strip().lower()
        key = (date, level, service)

        group = groups.setdefault(key, {
            "date": date,
            "level": level,
            "service": service,
            "count": 0,
            "first_seen": ts,
            "last_seen": ts,
        })
        group["count"] += 1
        group["first_seen"] = min(group["first_seen"], ts)
        group["last_seen"] = max(group["last_seen"], ts)

    output_rows = [
        {
            "date": g["date"],
            "level": g["level"],
            "service": g["service"],
            "count": g["count"],
            "first_seen": g["first_seen"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "last_seen": g["last_seen"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for g in groups.values()
    ]
    return output_rows, had_error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="logsum", description="Summarise event log CSV files.")
    parser.add_argument("--input", default=None, help="Input CSV file. Default: data/events.csv")
    parser.add_argument("--output", default=None, help="Output CSV file. Default: stdout")
    parser.add_argument("--strict", action="store_true", help="Treat malformed rows as fatal.")
    parser.add_argument("--min-count", type=int, default=None, metavar="N",
                        help="Only output groups with count >= N.")

    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2

    input_path = args.input or "data/events.csv"
    output_path = args.output  # None → stdout

    try:
        in_fh = open(input_path, newline="", encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1

    with in_fh:
        rows, had_error = summarise(csv.DictReader(in_fh), args.strict)

    if args.min_count is not None:
        rows = [r for r in rows if r["count"] >= args.min_count]

    if had_error and args.strict:
        return 1

    out_ctx = (
        open(output_path, "w", newline="", encoding="utf-8")
        if output_path
        else contextlib.nullcontext(sys.stdout)
    )
    try:
        with out_ctx as out_fh:
            writer = csv.DictWriter(out_fh, fieldnames=_OUTPUT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    except OSError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
