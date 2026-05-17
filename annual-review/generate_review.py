#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "tqdm",
# ]
# ///
"""
Read an annotated GitHub outputs CSV and produce a Markdown annual review template.
PRs and Releases are grouped by the Goal column, sorted by creation date.
Rows with no Goal are collected in an "Other" section at the end.
"""

import csv
import logging
import os
import sys
from collections import defaultdict
from datetime import date, datetime

import click
from tqdm import tqdm


def default_review_period() -> tuple[date, date]:
    today = date.today()
    if today.month < 4:
        start = date(today.year - 1, 4, 1)
        end = date(today.year, 3, 31)
    else:
        start = date(today.year, 4, 1)
        end = date(today.year + 1, 3, 31)
    return start, end


def fmt_date(iso: str) -> str:
    """Format an ISO date string as 'Mon D, YYYY' (no zero-padding on day)."""
    dt = datetime.fromisoformat(iso)
    return f"{dt.strftime('%b')} {dt.day}, {dt.year}"


def format_pr_line(row: dict) -> str:
    org = row["Organization"]
    repo = row["Repository"]
    num = row["Number"]
    title = row["Title"]
    url = row["URL"]
    status = row["Status"]
    closed = row["Closed/Merged"].strip()

    if status == "merged" and closed:
        disposition = f"merged {fmt_date(closed)}"
    elif status == "open":
        disposition = "in progress"
    elif status == "closed" and closed:
        disposition = f"closed {fmt_date(closed)}"
    else:
        disposition = status

    return f"- [{disposition}] {title} ({url})"


def format_release_line(row: dict) -> str:
    org = row["Organization"]
    repo = row["Repository"]
    tag = row["Number"]
    title = row["Title"]
    url = row["URL"]
    created = row["Created"].strip()

    date_str = fmt_date(created) if created else "unknown date"
    return f"- [released {date_str}] {title} ({url})"


def sort_key(row: dict) -> tuple:
    # Releases before PRs; within each type, sort by creation date ascending
    type_order = 0 if row.get("Type") == "Release" else 1
    try:
        dt = datetime.fromisoformat(row["Created"])
    except (ValueError, KeyError):
        dt = datetime.min
    return (type_order, dt)


@click.command()
@click.option("--input", "-i", "input_path", default="data/github_outputs.csv", show_default=True,
              help="Input CSV file (produced by get_github_outputs.py)")
@click.option("--output", "-o", default="data/annual_review.md", show_default=True,
              help="Output Markdown file")
@click.option("--start", "start_str", default=None, metavar="YYYY-MM-DD",
              help="Review period start (used in document title; default: current period)")
@click.option("--end", "end_str", default=None, metavar="YYYY-MM-DD",
              help="Review period end (used in document title; default: current period)")
@click.option("--log-level", default="INFO", show_default=True,
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
              help="Logging verbosity")
def main(input_path: str, output: str, start_str: str | None, end_str: str | None,
         log_level: str) -> None:
    """Generate a Markdown annual review template from an annotated GitHub outputs CSV."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    default_start, default_end = default_review_period()
    start = date.fromisoformat(start_str) if start_str else default_start
    end = date.fromisoformat(end_str) if end_str else default_end
    title_years = f"{start.year}–{end.year}"

    logging.info(f"Reading {input_path}")
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        logging.warning(f"No rows found in {input_path}")

    # Group rows by goal; blank goal → "Other"
    groups: dict[str, list] = defaultdict(list)
    goal_order: list[str] = []

    for row in tqdm(rows, desc="Grouping rows", unit=" rows"):
        goal = row.get("Goal", "").strip() or "Other"
        if goal not in groups:
            goal_order.append(goal)
        groups[goal].append(row)

    # Sort within each group by creation date
    for goal in goal_order:
        groups[goal].sort(key=sort_key)

    # Always put "Other" last
    ordered_goals = [g for g in goal_order if g != "Other"]
    if "Other" in groups:
        ordered_goals.append("Other")

    # Build Markdown
    lines: list[str] = [f"# Annual Review {title_years}", ""]

    for goal in ordered_goals:
        lines.append(f"## {goal}")
        lines.append("")
        lines.append("> [Your narrative here]")
        lines.append("")
        for row in groups[goal]:
            row_type = row.get("Type", "PR")
            if row_type == "Release":
                lines.append(format_release_line(row))
            else:
                lines.append(format_pr_line(row))
        lines.append("")

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")

    pr_count = sum(1 for r in rows if r.get("Type") == "PR")
    release_count = sum(1 for r in rows if r.get("Type") == "Release")
    named_goal_count = len([g for g in ordered_goals if g != "Other"])
    logging.info(
        f"Wrote {output}: {named_goal_count} goal section(s), "
        f"{'Other section, ' if 'Other' in groups else ''}"
        f"{pr_count} PRs, {release_count} releases"
    )


if __name__ == "__main__":
    main()
