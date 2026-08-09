#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "click",
#     "tqdm",
# ]
# ///
"""
Check REDCap "Choices, Calculations, OR Slider Labels" strings for formatting issues.

Each choices string is expected to follow one of two conventions:

    comma:  code, label | code, label | code, label...   (REDCap's actual convention)
    equals: key=value|key=value|key=value...

The format is auto-detected per file by default (majority vote across entries),
or can be forced with --format.

This script flags, per line/field:
- Malformed entries (missing delimiter, empty key/code, empty value/label,
  empty entries from stray '|')
- Duplicate keys/codes within a field
- Duplicate values/labels within a field
"""

import csv
import logging
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional

import click
from tqdm import tqdm

logger = logging.getLogger("check_choices")


class Issue(NamedTuple):
    line_number: int
    field_name: str
    choices_raw: str
    issue_type: str
    detail: str


def find_choices_column(header: List[str]) -> Optional[int]:
    for i, col in enumerate(header):
        if "choices" in col.lower():
            return i
    return None


def find_field_name_column(header: List[str]) -> Optional[int]:
    for i, col in enumerate(header):
        normalized = col.lower()
        if "variable" in normalized or normalized.strip() == "field_name":
            return i
    return None


def load_records(input_path: Path, choices_column: Optional[str]) -> List[tuple]:
    """Return a list of (field_name, choices_raw) tuples read from the input file."""
    suffix = input_path.suffix.lower()

    if suffix in (".csv", ".tsv"):
        delimiter = "\t" if suffix == ".tsv" else ","
        with input_path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=delimiter)
            header = next(reader)

            if choices_column:
                matches = [i for i, col in enumerate(header) if col == choices_column]
                if not matches:
                    raise click.ClickException(
                        f"Column '{choices_column}' not found in header: {header}"
                    )
                choices_idx = matches[0]
            else:
                choices_idx = find_choices_column(header)
                if choices_idx is None:
                    raise click.ClickException(
                        "Could not auto-detect a 'Choices' column. "
                        "Pass --choices-column to specify it explicitly."
                    )

            field_idx = find_field_name_column(header)

            records = []
            for row in reader:
                if not row or choices_idx >= len(row):
                    continue
                choices_raw = row[choices_idx].strip()
                if not choices_raw:
                    continue
                field_name = row[field_idx].strip() if field_idx is not None else ""
                records.append((field_name, choices_raw))
            return records

    # Plain text: one choices string per non-empty line.
    with input_path.open(encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # REDCap Data Dictionary exports sometimes retain the column header when the
    # Choices column is copied out into its own text file; drop it if present.
    if lines and "choices" in lines[0].lower() and "calculations" in lines[0].lower():
        logger.info("Dropping header-like first line: %r", lines[0])
        lines = lines[1:]

    return [("", line) for line in lines]


def detect_format(records: List[tuple]) -> str:
    """Guess whether Choices strings use 'code, label' or 'key=value' delimiters."""
    comma_votes = 0
    equals_votes = 0
    for _, choices_raw in records:
        first_entry = choices_raw.split("|", 1)[0]
        if "," in first_entry:
            comma_votes += 1
        if "=" in first_entry:
            equals_votes += 1
    return "equals" if equals_votes > comma_votes else "comma"


def check_choices_string(
    line_number: int, field_name: str, choices_raw: str, format_: str
) -> List[Issue]:
    issues: List[Issue] = []
    entries = choices_raw.split("|")
    delimiter = "=" if format_ == "equals" else ","
    key_label = "key" if format_ == "equals" else "code"
    value_label = "value" if format_ == "equals" else "label"

    seen_keys = {}
    seen_values = {}

    for entry in entries:
        if not entry.strip():
            issues.append(Issue(
                line_number, field_name, choices_raw, "malformed",
                "empty entry (stray or trailing '|')",
            ))
            continue

        if delimiter not in entry:
            issues.append(Issue(
                line_number, field_name, choices_raw, "malformed",
                f"entry missing '{delimiter}': '{entry.strip()}'",
            ))
            continue

        key, _, value = entry.partition(delimiter)
        key, value = key.strip(), value.strip()

        if not key:
            issues.append(Issue(
                line_number, field_name, choices_raw, "malformed",
                f"empty {key_label} in entry: '{entry.strip()}'",
            ))
        elif key in seen_keys:
            issues.append(Issue(
                line_number, field_name, choices_raw, "duplicate_key",
                f"{key_label} '{key}' appears more than once",
            ))
        else:
            seen_keys[key] = value

        if not value:
            issues.append(Issue(
                line_number, field_name, choices_raw, "malformed",
                f"empty {value_label} in entry: '{entry.strip()}'",
            ))
        elif value in seen_values:
            issues.append(Issue(
                line_number, field_name, choices_raw, "duplicate_value",
                f"{value_label} '{value}' appears more than once "
                f"({key_label}s '{seen_values[value]}' and '{key}')",
            ))
        else:
            seen_values[value] = key

    return issues


@click.command()
@click.option(
    "--input", "-i", "input_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Input file: plain text (one Choices string per line) or CSV/TSV with a Choices column.",
)
@click.option(
    "--output", "-o", "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
    help="Output CSV report path.",
)
@click.option(
    "--choices-column",
    default=None,
    help="Name of the Choices column in a CSV/TSV input (auto-detected if omitted).",
)
@click.option(
    "--format", "-f", "format_",
    type=click.Choice(["auto", "comma", "equals"], case_sensitive=False),
    default="auto",
    help="Choices string convention: 'comma' (code, label) or 'equals' (key=value). "
         "'auto' detects it from the data.",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Logging verbosity.",
)
def main(
    input_path: Path, output_path: Path, choices_column: Optional[str],
    format_: str, log_level: str,
):
    """Check REDCap Choices strings for formatting issues and write a report."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if input_path.resolve() == output_path.resolve():
        raise click.ClickException("--input and --output must not be the same file.")

    logger.info("Loading records from %s", input_path)
    records = load_records(input_path, choices_column)
    logger.info("Loaded %d Choices strings", len(records))

    resolved_format = detect_format(records) if format_ == "auto" else format_
    logger.info("Using '%s' format for parsing", resolved_format)

    all_issues: List[Issue] = []
    for line_number, (field_name, choices_raw) in enumerate(
        tqdm(records, desc="Checking Choices strings"), start=1
    ):
        all_issues.extend(
            check_choices_string(line_number, field_name, choices_raw, resolved_format)
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["line_number", "field_name", "issue_type", "detail", "choices_raw"])
        for issue in all_issues:
            writer.writerow([
                issue.line_number, issue.field_name, issue.issue_type,
                issue.detail, issue.choices_raw,
            ])

    fields_with_issues = len({(i.line_number) for i in all_issues})
    logger.info(
        "Found %d issue(s) across %d field(s) (out of %d checked). Report written to %s",
        len(all_issues), fields_with_issues, len(records), output_path,
    )

    if all_issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
