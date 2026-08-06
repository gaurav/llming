#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["click"]
# ///
"""Diff two HEAL VLMD files variable by variable, matching on a stable ID.

Generic JSON diffs compare the `fields` array positionally, which is useless when the two files
order or size their variable lists differently. This matches variables by their `name` and then
compares property by property, so a change reads as "variable X's `constraints` went from A to B"
rather than "array element 412 differs".

Writes two files sharing --output-prefix:

  <prefix>.md   grouped review report. Identical old -> new value pairs collapse into one entry
                with a count and the list of variables affected, which is what makes a few
                thousand field-level changes reviewable in one sitting.
  <prefix>.csv  one untruncated row per field-level change:
                variable, section, property, change, base_value, revised_value, category
"""

import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

import click

DEFAULT_BASE = "data/eppic_net_EN20_01.vlmd-generated-by-script.json"
DEFAULT_REVISED = "data/HDP01050_eppic_net_EN20_01.vlmd-generated-by-llm-tool.json"
DEFAULT_PREFIX = "data/vlmd-diff"

# Properties that differ because the two conversion tools have different conventions, not because
# anyone edited the metadata. Reported in an appendix so they can be confirmed uniform and skipped.
DEFAULT_ARTIFACT_PROPERTIES = ("title", "custom", "format")

MAX_MARKDOWN_VALUE = 300

# An appendix property with more distinct value pairs than this is summarised rather than listed.
APPENDIX_MAX_PATTERNS = 20

# Sentinel for "this property is absent on this side", so that an explicit null can be told apart
# from a missing key.
MISSING = object()


class Change(NamedTuple):
    """One property of one variable differing between the two files."""

    variable: str
    section: str
    property: str
    kind: str  # added | removed | changed
    base: Any  # MISSING when the property is absent from the base file
    revised: Any  # MISSING when the property is absent from the revised file


# ---- diffing ----


def index_fields(doc: Dict[str, Any], id_key: str, label: str) -> Dict[str, Dict[str, Any]]:
    """Index a document's `fields` list by id_key. Raises ValueError on a missing or duplicate id."""
    fields = doc.get("fields")
    if not isinstance(fields, list):
        raise ValueError(f"{label}: no `fields` list")

    index: Dict[str, Dict[str, Any]] = {}
    for position, field in enumerate(fields):
        if not isinstance(field, dict) or id_key not in field:
            raise ValueError(f"{label}: field at position {position} has no `{id_key}`")
        variable = field[id_key]
        if variable in index:
            raise ValueError(f"{label}: duplicate `{id_key}` {variable!r}")
        index[variable] = field
    return index


def diff_field(variable: str, base: Dict[str, Any], revised: Dict[str, Any]) -> List[Change]:
    """Compare one variable's two representations, one Change per differing property."""
    section = base.get("section") or revised.get("section") or ""
    changes = []
    for prop in sorted(set(base) | set(revised)):
        before = base.get(prop, MISSING)
        after = revised.get(prop, MISSING)
        if before == after:
            continue
        kind = "added" if before is MISSING else "removed" if after is MISSING else "changed"
        changes.append(Change(variable, section, prop, kind, before, after))
    return changes


def diff_documents(
    base: Dict[str, Any], revised: Dict[str, Any], id_key: str
) -> Tuple[List[Change], List[str], List[str], List[Change]]:
    """Diff two whole VLMD documents.

    Returns (field changes, added variables, removed variables, top-level changes). Top-level
    changes reuse Change with the variable set to "(document)" and no section.
    """
    base_fields = index_fields(base, id_key, "base")
    revised_fields = index_fields(revised, id_key, "revised")

    top_level = diff_field(
        "(document)",
        {k: v for k, v in base.items() if k != "fields"},
        {k: v for k, v in revised.items() if k != "fields"},
    )
    # diff_field picks up `section` for a real variable; at the document level there is none.
    top_level = [c._replace(section="") for c in top_level]

    added = [v for v in revised_fields if v not in base_fields]
    removed = [v for v in base_fields if v not in revised_fields]

    changes = []
    for variable, field in base_fields.items():
        if variable in revised_fields:
            changes.extend(diff_field(variable, field, revised_fields[variable]))

    return changes, added, removed, top_level


def group_by_pattern(changes: Sequence[Change]) -> Dict[str, List[Tuple[Any, Any, List[str]]]]:
    """Group changes by property, then by identical (base, revised) value pair.

    This is the whole point of the tool: 349 variables making the same enum rewrite become one
    entry with a count instead of 349 lines to read.
    """
    buckets: Dict[str, Dict[Tuple[str, str], List[Change]]] = defaultdict(lambda: defaultdict(list))
    for change in changes:
        key = (render_value(change.base), render_value(change.revised))
        buckets[change.property][key].append(change)

    grouped = {}
    for prop, patterns in buckets.items():
        entries = [
            (group[0].base, group[0].revised, [c.variable for c in group])
            for group in patterns.values()
        ]
        # Biggest patterns first; ties broken by variable name so output is stable across runs.
        entries.sort(key=lambda e: (-len(e[2]), e[2][0]))
        grouped[prop] = entries
    return grouped


# ---- rendering ----


def render_value(value: Any) -> str:
    """Render a property value as single-line JSON. Absent properties render as an em dash."""
    if value is MISSING:
        return "—"
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def code_span(text: str, in_table: bool = False) -> str:
    """Wrap text in a Markdown code span, fenced wide enough to survive backticks inside it."""
    text = text if len(text) <= MAX_MARKDOWN_VALUE else text[:MAX_MARKDOWN_VALUE] + " …"
    if text == "—":  # an absent property, not code
        return "*(absent)*"
    if in_table:
        text = text.replace("|", "\\|")
    longest_run = 0
    run = 0
    for char in text:
        run = run + 1 if char == "`" else 0
        longest_run = max(longest_run, run)
    fence = "`" * (longest_run + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def render_property_section(
    prop: str, entries: List[Tuple[Any, Any, List[str]]], max_patterns: Optional[int] = None
) -> List[str]:
    """Render one property's patterns: a table when every pattern is a one-off, else a bullet list.

    With max_patterns set, a property whose changes are mostly one-offs is summarised instead of
    enumerated — the appendix exists to be skimmed, and listing 1233 unique values is not skimmable.
    The CSV always holds every one of them.
    """
    total = sum(len(variables) for _, _, variables in entries)
    plural = "" if total == 1 else "s"
    lines = [f"### `{prop}` — {total} variable{plural}, {len(entries)} distinct change{'' if len(entries) == 1 else 's'}", ""]

    if max_patterns is not None and len(entries) > max_patterns:
        lines += [
            f"Too many distinct values to list; see the CSV. The largest {min(3, len(entries))}:",
            "",
        ]
        for before, after, variables in entries[:3]:
            lines.append(
                f"- **{len(variables)} variable{'' if len(variables) == 1 else 's'}** — "
                f"{code_span(render_value(before))} → {code_span(render_value(after))}"
            )
        lines.append("")
        return lines

    if all(len(variables) == 1 for _, _, variables in entries):
        lines += ["| variable | from | to |", "|---|---|---|"]
        for before, after, variables in entries:
            lines.append(
                f"| `{variables[0]}` | {code_span(render_value(before), in_table=True)} "
                f"| {code_span(render_value(after), in_table=True)} |"
            )
        lines.append("")
        return lines

    for before, after, variables in entries:
        count = len(variables)
        lines.append(
            f"- **{count} variable{'' if count == 1 else 's'}** — "
            f"{code_span(render_value(before))} → {code_span(render_value(after))}"
        )
        if count == 1:
            lines.append(f"  - `{variables[0]}`")
        else:
            lines.append("  <details><summary>variables</summary>")
            lines.append("")
            lines.append("  " + ", ".join(f"`{v}`" for v in sorted(variables)))
            lines.append("")
            lines.append("  </details>")
        lines.append("")
    return lines


def render_variable_list(heading: str, variables: List[str], index: Dict[str, Dict[str, Any]]) -> List[str]:
    lines = [f"## {heading} ({len(variables)})", ""]
    if not variables:
        lines += ["*(none)*", ""]
        return lines
    for variable in sorted(variables):
        lines.append(f"<details><summary><code>{variable}</code></summary>")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(index[variable], indent=2, sort_keys=True, ensure_ascii=False))
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    return lines


def render_report(
    base_path: Path,
    revised_path: Path,
    base_index: Dict[str, Dict[str, Any]],
    revised_index: Dict[str, Dict[str, Any]],
    changes: List[Change],
    added: List[str],
    removed: List[str],
    top_level: List[Change],
    artifact_properties: Sequence[str],
) -> str:
    grouped = group_by_pattern(changes)
    substantive = {p: e for p, e in grouped.items() if p not in artifact_properties}
    artifacts = {p: e for p, e in grouped.items() if p in artifact_properties}
    shared = sorted(set(base_index) & set(revised_index))
    touched = {c.variable for c in changes}
    patterns = sum(len(e) for e in grouped.values())

    lines = [
        "# VLMD diff",
        "",
        f"- **base** — `{base_path}`",
        f"- **revised** — `{revised_path}`",
        "",
        f"{len(shared)} variables in common, {len(added)} added, {len(removed)} removed. "
        f"{len(touched)} of the shared variables differ, in {len(changes)} field-level changes "
        f"across {patterns} distinct old → new patterns.",
        "",
        "## Document-level properties",
        "",
    ]
    if top_level:
        lines += ["| property | from | to |", "|---|---|---|"]
        for change in top_level:
            lines.append(
                f"| `{change.property}` | {code_span(render_value(change.base), in_table=True)} "
                f"| {code_span(render_value(change.revised), in_table=True)} |"
            )
        lines.append("")
    else:
        lines += ["*(identical)*", ""]

    lines += render_variable_list("Variables added", added, revised_index)
    lines += render_variable_list("Variables removed", removed, base_index)

    lines += ["## Changed properties", ""]
    if substantive:
        for prop in sorted(substantive, key=lambda p: -sum(len(e[2]) for e in substantive[p])):
            lines += render_property_section(prop, substantive[prop])
    else:
        lines += ["*(none)*", ""]

    if artifacts:
        lines += [
            "## Appendix: conversion-tool conventions",
            "",
            "These properties differ because the two tools that produced these files write metadata "
            "differently, not because the content was edited. They are listed so their uniformity "
            "can be confirmed, then skipped.",
            "",
        ]
        for prop in sorted(artifacts, key=lambda p: -sum(len(e[2]) for e in artifacts[p])):
            lines += render_property_section(prop, artifacts[prop], max_patterns=APPENDIX_MAX_PATTERNS)

    return "\n".join(lines) + "\n"


def write_csv(path: Path, changes: List[Change], artifact_properties: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["variable", "section", "property", "change", "base_value", "revised_value", "category"]
        )
        for change in sorted(changes, key=lambda c: (c.property, c.variable)):
            writer.writerow(
                [
                    change.variable,
                    change.section,
                    change.property,
                    change.kind,
                    "" if change.base is MISSING else render_value(change.base),
                    "" if change.revised is MISSING else render_value(change.revised),
                    "artifact" if change.property in artifact_properties else "substantive",
                ]
            )


# ---- CLI ----


@click.command()
@click.option(
    "-b", "--base", "base_path", type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=DEFAULT_BASE, show_default=True, help="The VLMD file to diff from.",
)
@click.option(
    "-r", "--revised", "revised_path", type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=DEFAULT_REVISED, show_default=True, help="The VLMD file to diff to.",
)
@click.option(
    "-o", "--output-prefix", type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_PREFIX, show_default=True, help="Writes <prefix>.md and <prefix>.csv.",
)
@click.option("--id-key", default="name", show_default=True, help="Field property used to match variables.")
@click.option(
    "--artifact-property", multiple=True, default=DEFAULT_ARTIFACT_PROPERTIES, show_default=True,
    help="Property to relegate to the appendix as a conversion-tool convention. Repeatable.",
)
@click.option(
    "--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO", show_default=True,
)
def main(
    base_path: Path,
    revised_path: Path,
    output_prefix: Path,
    id_key: str,
    artifact_property: Tuple[str, ...],
    log_level: str,
) -> None:
    """Diff two HEAL VLMD files variable by variable, matching on --id-key."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    # Append rather than with_suffix, which would turn a prefix of `foo.diff` into `foo.md`.
    markdown_path = Path(f"{output_prefix}.md")
    csv_path = Path(f"{output_prefix}.csv")
    inputs = {base_path.resolve(), revised_path.resolve()}
    for output in (markdown_path, csv_path):
        if output.resolve() in inputs:
            raise click.UsageError(f"--output-prefix would overwrite an input file: {output}")

    logging.info("Reading %s and %s", base_path, revised_path)
    base = json.loads(base_path.read_text(encoding="utf-8"))
    revised = json.loads(revised_path.read_text(encoding="utf-8"))

    try:
        changes, added, removed, top_level = diff_documents(base, revised, id_key)
        base_index = index_fields(base, id_key, "base")
        revised_index = index_fields(revised, id_key, "revised")
    except ValueError as error:
        logging.error("%s", error)
        sys.exit(1)

    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(
        render_report(base_path, revised_path, base_index, revised_index, changes, added, removed,
                      top_level, artifact_property),
        encoding="utf-8",
    )
    write_csv(csv_path, changes, artifact_property)

    grouped = group_by_pattern(changes)
    shared = set(base_index) & set(revised_index)
    logging.info(
        "%d variables in common, %d added, %d removed", len(shared), len(added), len(removed)
    )
    logging.info(
        "%d field-level changes across %d distinct patterns, %d document-level changes",
        len(changes), sum(len(e) for e in grouped.values()), len(top_level),
    )
    for prop in sorted(grouped, key=lambda p: -sum(len(e[2]) for e in grouped[p])):
        counts = defaultdict(int)
        for change in changes:
            if change.property == prop:
                counts[change.kind] += 1
        summary = ", ".join(f"{n} {kind}" for kind, n in sorted(counts.items()))
        marker = " (appendix)" if prop in artifact_property else ""
        logging.info("  %s: %s%s", prop, summary, marker)
    logging.info("Wrote %s and %s", markdown_path, csv_path)


if __name__ == "__main__":
    main()
