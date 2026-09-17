#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["click"]
# ///
"""Diff two REDCap data dictionary CSVs row by row, and classify each change.

The sibling of vlmddiff.py, one step earlier in the pipeline: where that compares two VLMD
documents, this compares the REDCap CSVs they are generated from. Rows are matched on
`Variable / Field Name`, then compared column by column, and every change gets a category so
the report opens with a count per kind of edit ("349 choices filled in, 23 formatting only…").

Writes two files sharing --output-prefix:

  <prefix>.md   category counts, then one section per category with identical old -> new pairs
                grouped, exactly as vlmddiff.py groups them.
  <prefix>.csv  one untruncated row per changed cell:
                variable, form, column, base_value, revised_value, category
"""

import csv
import logging
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

import click

from vlmddiff import (
    Change,
    diff_documents,
    group_by_pattern,
    index_fields,
    render_property_section,
    render_variable_list,
)

DEFAULT_PREFIX_STEM = "redcap-diff"
ID_COLUMN = "Variable / Field Name"
FORM_COLUMN = "Form Name"
CHOICES_COLUMN = "Choices, Calculations, OR Slider Labels"

# Report order. classify() checks whitespace first, so "   " -> "" is whitespace, not emptied.
CATEGORIES = (
    "filled in",
    "emptied",
    "whitespace only",
    "choice formatting only",
    "content change",
)


def load_csv(path: Path) -> Dict[str, List[Dict[str, str]]]:
    """Load a REDCap CSV in the shape vlmddiff.diff_documents expects: {"fields": rows}."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return {"fields": list(csv.DictReader(handle))}


def parse_choices(text: str) -> List[tuple]:
    """Parse REDCap choices into (code, label) pairs. A bare item `x` means `x, x`."""
    pairs = []
    for item in text.split("|"):
        code, comma, label = item.partition(",")
        code = " ".join(code.split())
        pairs.append((code, " ".join(label.split()) if comma else code))
    return pairs


def show_whitespace(text: str) -> str:
    """Make any whitespace other than a plain space visible, e.g. NBSP as <U+00A0>."""
    return re.sub(r"[^\S ]", lambda m: f"<U+{ord(m.group()):04X}>", text)


def classify(change: Change) -> str:
    base, revised = change.base, change.revised
    # str.split() with no argument splits on any Unicode whitespace, NBSP included.
    if base.split() == revised.split():
        return "whitespace only"
    if not base.strip():
        return "filled in"
    if not revised.strip():
        return "emptied"
    if change.property == CHOICES_COLUMN and parse_choices(base) == parse_choices(revised):
        return "choice formatting only"
    return "content change"


def render_report(
    base_path: Path,
    revised_path: Path,
    base_index: Dict[str, Dict[str, str]],
    revised_index: Dict[str, Dict[str, str]],
    changes: List[Change],
    added: List[str],
    removed: List[str],
) -> str:
    categories = {c: classify(c) for c in changes}
    counts = Counter(categories.values())
    shared = set(base_index) & set(revised_index)
    touched = {c.variable for c in changes}
    columns = sorted({c.property for c in changes})

    lines = [
        "# REDCap data dictionary diff",
        "",
        f"- **base** — `{base_path}`",
        f"- **revised** — `{revised_path}`",
        "",
        f"{len(shared)} rows in common, {len(added)} added, {len(removed)} removed. "
        f"{len(touched)} of the shared rows differ, in {len(changes)} changed cells "
        f"across {len(columns)} column{'' if len(columns) == 1 else 's'}"
        + (": " + ", ".join(f"`{c}`" for c in columns) if columns else "")
        + ".",
        "",
        "| category | changes |",
        "|---|---|",
    ]
    lines += [f"| {category} | {counts[category]} |" for category in CATEGORIES if counts[category]]
    lines.append("")

    lines += render_variable_list("Rows added", added, revised_index)
    lines += render_variable_list("Rows removed", removed, base_index)

    for category in CATEGORIES:
        if not counts[category]:
            continue
        lines += [f"## {category.capitalize()} ({counts[category]})", ""]
        in_category = [c for c in changes if categories[c] == category]
        if category == "whitespace only":
            # Otherwise the two sides of a whitespace-only change render identically.
            in_category = [
                c._replace(base=show_whitespace(c.base), revised=show_whitespace(c.revised))
                for c in in_category
            ]
        grouped = group_by_pattern(in_category)
        for column in sorted(grouped):
            lines += render_property_section(column, grouped[column])

    return "\n".join(lines) + "\n"


def write_csv(path: Path, changes: List[Change]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["variable", "form", "column", "base_value", "revised_value", "category"])
        for change in sorted(changes, key=lambda c: (c.property, c.variable)):
            writer.writerow(
                [change.variable, change.section, change.property, change.base, change.revised,
                 classify(change)]
            )


@click.command()
@click.option(
    "-b", "--base", "base_path", required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="The REDCap CSV to diff from.",
)
@click.option(
    "-r", "--revised", "revised_path", required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="The REDCap CSV to diff to.",
)
@click.option(
    "-o", "--output-prefix", type=click.Path(dir_okay=False, path_type=Path), default=None,
    help=f"Writes <prefix>.md and <prefix>.csv.  [default: {DEFAULT_PREFIX_STEM}, beside --base]",
)
@click.option(
    "--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO", show_default=True,
)
def main(base_path: Path, revised_path: Path, output_prefix: Optional[Path], log_level: str) -> None:
    """Diff two REDCap data dictionary CSVs row by row, matching on `Variable / Field Name`."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    if output_prefix is None:
        output_prefix = base_path.parent / DEFAULT_PREFIX_STEM
    markdown_path = Path(f"{output_prefix}.md")
    csv_path = Path(f"{output_prefix}.csv")
    inputs = {base_path.resolve(), revised_path.resolve()}
    for output in (markdown_path, csv_path):
        if output.resolve() in inputs:
            raise click.UsageError(f"--output-prefix would overwrite an input file: {output}")

    logging.info("Reading %s and %s", base_path, revised_path)
    base = load_csv(base_path)
    revised = load_csv(revised_path)

    try:
        base_index = index_fields(base, ID_COLUMN, "base")
        revised_index = index_fields(revised, ID_COLUMN, "revised")
        changes, added, removed, _ = diff_documents(base, revised, ID_COLUMN)
    except ValueError as error:
        logging.error("%s", error)
        sys.exit(1)

    # diff_field looks for a VLMD `section`; a REDCap row's equivalent is its form.
    changes = [c._replace(section=base_index[c.variable].get(FORM_COLUMN, "")) for c in changes]

    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(
        render_report(base_path, revised_path, base_index, revised_index, changes, added, removed),
        encoding="utf-8",
    )
    write_csv(csv_path, changes)

    logging.info(
        "%d rows in common, %d added, %d removed, %d changed cells",
        len(set(base_index) & set(revised_index)), len(added), len(removed), len(changes),
    )
    counts = Counter(classify(c) for c in changes)
    for category in CATEGORIES:
        if counts[category]:
            logging.info("  %s: %d", category, counts[category])
    logging.info("Wrote %s and %s", markdown_path, csv_path)


if __name__ == "__main__":
    main()
