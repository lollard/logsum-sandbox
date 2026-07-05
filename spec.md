# logsum CLI — specification

## 1. Goal section
Tiny CLI that summarises synthetic events.csv logs

## 2. Inputs section
Expected CSV format: timestamp (timestamp), level (char24), service(char 4), message(chasr256), 

## 3. Group key
Each output row represents a unique `(date, level, service)` triple, where
`date` is the UTC calendar date (YYYY-MM-DD) extracted from `timestamp`.
`message` is intentionally excluded from the key.

## 4. Normalisation rules
| Field       | Rule |
|-------------|------|
| `timestamp` | Parse as ISO 8601 UTC. No timezone conversion. |
| `level`     | Strip whitespace, uppercase. `" warn "` → `"WARN"`. |
| `service`   | Strip whitespace, lowercase. `" Auth "` → `"auth"`. |
| `message`   | Not normalised; not part of the key. |

## 5. Output columns
`date, level, service, count, first_seen, last_seen`

`first_seen` and `last_seen` are ISO 8601 UTC strings of the earliest/latest
timestamps in the group.

## 6. Missing level
Treat as `"UNKNOWN"`. Row is counted normally.

## 7. Malformed timestamp
Skip the row; emit a warning to stderr including the 1-based row number.
Processing continues. Exit code is unaffected unless `--strict` is active.

## 8. Empty input
Write the header row only. Exit 0. No error or warning.

## 9. CLI flags and exit codes

```
logsum [--input FILE] [--output FILE] [--strict]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--input FILE`  | `data/events.csv` | Path to input CSV. |
| `--output FILE` | stdout            | Path to output CSV. |
| `--strict`      | off               | Treat malformed rows as fatal errors. |

| Code | Meaning |
|------|---------|
| 0 | Success (including empty input). |
| 1 | I/O error, or a bad row encountered under `--strict`. |
| 2 | Invalid CLI usage (unknown flag, missing required value). |

## 10. Out of scope
- Filtering by date range, level, or service.
- Deduplication or analysis of message text.
- Output formats other than CSV (JSON, Parquet, etc.).
- Streaming or chunked processing of very large files.
- Any database or external storage backend.

## 11. Signed off
Vladimir Ermishin, 7/3/2026

## 12. Implementation notes
No surprises