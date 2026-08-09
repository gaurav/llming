# REDCap Choices Checker

## Overview

`check_choices.py` checks REDCap "Choices, Calculations, OR Slider Labels" strings
for formatting issues, on the assumption that each string should follow the convention:

    key=value|key=value|key=value...

## What the Script Does

### Input
Either:
- A plain text file with one Choices string per (non-empty) line, or
- A CSV/TSV file with a column whose header contains "choices" (case-insensitive),
  e.g. a full REDCap Data Dictionary export. `--choices-column` can be used to specify
  the column explicitly if auto-detection fails. If a "Variable / Field Name" (or
  `field_name`) column is present, it is used to label rows in the report.

### Output
A CSV report (`--output`) with one row per issue found:
`line_number, field_name, issue_type, detail, choices_raw`

### Checks Performed
- **malformed**: entry missing `=`, empty key, empty value, or empty entry from a
  stray/trailing `|`
- **duplicate_key**: the same key appears more than once within a field's Choices string
- **duplicate_value**: the same value (label) appears more than once within a field's
  Choices string

The script exits with status 1 if any issues are found (useful in CI/scripts).

### Usage

```bash
# Plain text input, one Choices string per line
uv run check_choices.py -i data/choices.txt -o data/choices-report.csv

# Full REDCap Data Dictionary CSV export (auto-detects the Choices column)
uv run check_choices.py -i data/data_dictionary.csv -o data/choices-report.csv

# Explicit column name, debug logging
uv run check_choices.py -i data/data_dictionary.csv -o data/choices-report.csv \
  --choices-column "Choices, Calculations, OR Slider Labels" --log-level DEBUG
```

## Known Limitations / Future Work

- This is a first pass focused only on the `key=value|key=value` convention.
  Real REDCap Choices strings actually use `code, label | code, label` (comma-separated,
  not `=`) — this script matches the convention the user is currently working with, and
  can be extended to also check the comma-delimited style.
- No whitespace/formatting checks yet (leading/trailing whitespace, smart quotes,
  non-breaking spaces).
- No validation of code type consistency with field type (e.g. numeric-only codes
  for certain field types).

## Related Files

- `data/` — put your input file(s) here (e.g. `data/choices.txt` or a Data Dictionary export)
- `check_choices.py` — main script
