"""Tests for vlmddiff.

Run with:  uv run --with pytest --with click pytest tests

The sample pair in fixtures/ is synthetic — the real dictionaries this tool was written for are
study data and are deliberately not in this repo. fixtures/expected.md and fixtures/expected.csv
double as the worked example in CLAUDE.md; regenerate them with:

    uv run vlmddiff.py -b tests/fixtures/base.json -r tests/fixtures/revised.json \
        -o tests/fixtures/expected
"""

import csv
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from vlmddiff import (
    MISSING,
    Change,
    code_span,
    diff_documents,
    group_by_pattern,
    index_fields,
    main,
    render_property_section,
    render_report,
    render_value,
    write_csv,
)

FIXTURES = Path(__file__).parent / "fixtures"
BASE = json.loads((FIXTURES / "base.json").read_text(encoding="utf-8"))
REVISED = json.loads((FIXTURES / "revised.json").read_text(encoding="utf-8"))


@pytest.fixture
def diff():
    return diff_documents(BASE, REVISED, "name")


# ---- indexing ----


def test_index_fields_keys_by_id():
    assert sorted(index_fields(BASE, "name", "base")) == [
        "AWAKE", "PAINSCORE", "RETIRED", "VISITDAT", "WEAR", "site",
    ]


def test_index_fields_rejects_duplicate_id():
    doc = {"fields": [{"name": "A"}, {"name": "A"}]}
    with pytest.raises(ValueError, match="duplicate"):
        index_fields(doc, "name", "base")


def test_index_fields_rejects_missing_id():
    doc = {"fields": [{"name": "A"}, {"label": "B"}]}
    with pytest.raises(ValueError, match="position 1"):
        index_fields(doc, "name", "base")


def test_index_fields_rejects_document_without_fields():
    with pytest.raises(ValueError, match="no `fields` list"):
        index_fields({"schemaVersion": "0.3.2"}, "name", "base")


# ---- diffing ----


def test_added_and_removed_variables(diff):
    _, added, removed, _ = diff
    assert added == ["CONSENTDAT"]
    assert removed == ["RETIRED"]


def test_unchanged_properties_produce_no_change(diff):
    changes, _, _, _ = diff
    assert not [c for c in changes if c.property in ("type", "section", "name")]


def test_unchanged_nested_property_produces_no_change(diff):
    """PAINSCORE's constraints object is deep-equal across both files."""
    changes, _, _, _ = diff
    assert not [c for c in changes if c.variable == "PAINSCORE" and c.property == "constraints"]


def test_change_kinds(diff):
    changes, _, _, _ = diff
    kinds = {(c.variable, c.property): c.kind for c in changes}
    assert kinds[("AWAKE", "enumLabels")] == "removed"
    assert kinds[("AWAKE", "constraints")] == "changed"
    assert kinds[("site", "custom")] == "added"
    assert kinds[("site", "format")] == "removed"


def test_change_carries_section_and_values(diff):
    changes, _, _, _ = diff
    change = next(c for c in changes if c.variable == "site" and c.property == "description")
    assert change == Change(
        "site", "Demographics", "description", "changed",
        "demographics: Site(blinded)", "Site(blinded)",
    )


def test_removed_property_has_missing_sentinel_not_none(diff):
    """A property that is absent must not be confused with one explicitly set to null."""
    changes, _, _, _ = diff
    change = next(c for c in changes if c.variable == "AWAKE" and c.property == "enumLabels")
    assert change.revised is MISSING


def test_explicit_null_differs_from_absent():
    base = {"fields": [{"name": "A", "format": None}]}
    revised = {"fields": [{"name": "A"}]}
    changes, _, _, _ = diff_documents(base, revised, "name")
    assert [(c.property, c.kind, c.base, c.revised) for c in changes] == [
        ("format", "removed", None, MISSING)
    ]


def test_added_and_removed_variables_contribute_no_field_changes(diff):
    changes, _, _, _ = diff
    assert not [c for c in changes if c.variable in ("RETIRED", "CONSENTDAT")]


def test_document_level_changes(diff):
    _, _, _, top_level = diff
    assert {c.property: c.kind for c in top_level} == {"title": "changed", "description": "added"}
    assert all(c.variable == "(document)" and c.section == "" for c in top_level)


def test_document_level_ignores_fields_list(diff):
    _, _, _, top_level = diff
    assert "fields" not in {c.property for c in top_level}


def test_identical_documents_produce_no_changes():
    assert diff_documents(BASE, BASE, "name") == ([], [], [], [])


def test_custom_id_key():
    base = {"fields": [{"varname": "A", "type": "string"}]}
    revised = {"fields": [{"varname": "A", "type": "integer"}]}
    changes, added, removed, _ = diff_documents(base, revised, "varname")
    assert (added, removed) == ([], [])
    assert changes[0].property == "type"


# ---- grouping: the reason this tool exists ----


def test_identical_value_pairs_collapse_into_one_pattern(diff):
    changes, _, _, _ = diff
    grouped = group_by_pattern(changes)
    assert len(grouped["constraints"]) == 1
    before, after, variables = grouped["constraints"][0]
    assert before == {"enum": ["0", "1"]}
    assert after == {"enum": ["True", "False"]}
    assert sorted(variables) == ["AWAKE", "WEAR"]


def test_distinct_value_pairs_stay_separate():
    changes = [
        Change("A", "", "type", "changed", "string", "integer"),
        Change("B", "", "type", "changed", "string", "number"),
    ]
    assert len(group_by_pattern(changes)["type"]) == 2


def test_patterns_sorted_by_count_descending():
    changes = [
        Change("A", "", "type", "changed", "string", "number"),
        Change("B", "", "type", "changed", "string", "integer"),
        Change("C", "", "type", "changed", "string", "integer"),
    ]
    counts = [len(variables) for _, _, variables in group_by_pattern(changes)["type"]]
    assert counts == [2, 1]


def test_grouping_distinguishes_absent_from_present():
    changes = [
        Change("A", "", "format", "removed", "any", MISSING),
        Change("B", "", "format", "changed", "any", "—"),
    ]
    assert len(group_by_pattern(changes)["format"]) == 2


# ---- rendering ----


def test_render_value_is_single_line_json():
    assert render_value({"b": 1, "a": [2, 3]}) == '{"a": [2, 3], "b": 1}'
    assert "\n" not in render_value({"note": "line one\nline two"})


def test_render_value_keeps_non_ascii_readable():
    assert render_value("awake time") == '"awake time"'


def test_render_value_of_missing():
    assert render_value(MISSING) == "—"


def test_code_span_widens_fence_around_backticks():
    assert code_span("a `b` c") == "``a `b` c``"


def test_code_span_pads_when_value_starts_or_ends_with_backtick():
    assert code_span("`x`") == "`` `x` ``"


def test_code_span_escapes_pipes_only_in_tables():
    assert code_span("a|b", in_table=True) == "`a\\|b`"
    assert code_span("a|b") == "`a|b`"


def test_code_span_truncates_long_values():
    rendered = code_span("x" * 5000)
    assert rendered.endswith(" …`") and len(rendered) < 400


def test_code_span_marks_absent_values():
    assert code_span("—") == "*(absent)*"


def test_summarises_a_property_with_too_many_distinct_patterns():
    """Enumerating a thousand unique one-off values is not skimmable; the CSV keeps them all."""
    entries = [(f"before {i}", None, [f"VAR{i}"]) for i in range(50)]
    text = "\n".join(render_property_section("title", entries, max_patterns=20))
    assert "50 distinct changes" in text
    assert "Too many distinct values to list; see the CSV" in text
    assert "VAR49" not in text
    assert text.count("- **1 variable**") == 3  # the largest 3, as promised


def test_enumerates_when_under_the_pattern_limit():
    entries = [("any", None, [f"VAR{i}" for i in range(102)])]
    text = "\n".join(render_property_section("format", entries, max_patterns=20))
    assert "Too many distinct" not in text
    assert "**102 variables**" in text and "VAR101" in text


def test_substantive_sections_are_never_summarised():
    """The point of the report is the substantive changes; they are always shown in full."""
    changes = [Change(f"VAR{i}", "", "description", "changed", f"old {i}", f"new {i}")
               for i in range(50)]
    text = render_report("a", "b", {}, {}, changes, [], [], [], ())
    assert "Too many distinct" not in text
    assert "VAR49" in text


def report(artifact_properties=("title", "custom", "format")):
    changes, added, removed, top_level = diff_documents(BASE, REVISED, "name")
    return render_report(
        "base.json", "revised.json",
        index_fields(BASE, "name", "base"), index_fields(REVISED, "name", "revised"),
        changes, added, removed, top_level, artifact_properties,
    )


def test_report_headline_counts():
    assert "5 variables in common, 1 added, 1 removed" in report()


def test_report_collapses_repeated_pattern():
    """The 2-variable constraints rewrite appears once, not once per variable."""
    text = report()
    assert text.count('{"enum": ["True", "False"]}') == 1
    assert "**2 variables**" in text


def test_report_uses_a_table_when_every_change_is_a_one_off():
    text = report()
    assert "| variable | from | to |" in text
    assert '| `site` | `"demographics: Site(blinded)"` | `"Site(blinded)"` |' in text


def test_report_separates_artifacts_into_appendix():
    body, appendix = report().split("## Appendix: conversion-tool conventions")
    assert "`description`" in body and "`constraints`" in body
    assert "`format`" in appendix and "`custom`" in appendix
    assert "`format`" not in body and "`custom`" not in body


def test_report_has_no_appendix_when_nothing_is_an_artifact():
    text = report(artifact_properties=())
    assert "## Appendix" not in text
    assert "`custom`" in text


def test_report_lists_added_and_removed_variables_with_json():
    text = report()
    assert "## Variables added (1)" in text and "<code>CONSENTDAT</code>" in text
    assert "## Variables removed (1)" in text and "<code>RETIRED</code>" in text
    assert '"name": "RETIRED"' in text


def test_report_shows_document_level_changes():
    text = report()
    assert '`"An Example Study of Something"`' in text
    assert "*(absent)*" in text  # description is added at the document level


def test_report_of_identical_documents():
    changes, added, removed, top_level = diff_documents(BASE, BASE, "name")
    index = index_fields(BASE, "name", "base")
    text = render_report("a.json", "a.json", index, index, changes, added, removed, top_level, ())
    assert "6 variables in common, 0 added, 0 removed" in text
    assert "*(identical)*" in text
    assert "## Variables added (0)" in text


# ---- csv ----


def test_csv_has_one_row_per_change(tmp_path):
    changes, _, _, _ = diff_documents(BASE, REVISED, "name")
    path = tmp_path / "diff.csv"
    write_csv(path, changes, ("title", "custom", "format"))
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(changes)

    row = next(r for r in rows if r["variable"] == "site" and r["property"] == "description")
    assert row["section"] == "Demographics"
    assert row["change"] == "changed"
    assert row["base_value"] == '"demographics: Site(blinded)"'
    assert row["category"] == "substantive"

    assert next(r for r in rows if r["property"] == "custom")["category"] == "artifact"


def test_csv_leaves_absent_values_empty(tmp_path):
    changes, _, _, _ = diff_documents(BASE, REVISED, "name")
    path = tmp_path / "diff.csv"
    write_csv(path, changes, ())
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    row = next(r for r in rows if r["variable"] == "AWAKE" and r["property"] == "enumLabels")
    assert row["revised_value"] == "" and row["base_value"] != ""


def test_csv_values_are_not_truncated(tmp_path):
    long = "x" * 5000
    path = tmp_path / "diff.csv"
    write_csv(path, [Change("A", "", "description", "changed", long, "short")], ())
    with path.open(encoding="utf-8") as handle:
        assert long in list(csv.DictReader(handle))[0]["base_value"]


def test_csv_uses_lf_endings(tmp_path):
    """The committed example is in git; CRLF would make git rewrite it on every checkout."""
    path = tmp_path / "diff.csv"
    write_csv(path, [Change("A", "", "description", "changed", "old", "new")], ())
    assert b"\r\n" not in path.read_bytes()


# ---- cli ----


def test_cli_writes_both_outputs(tmp_path):
    result = CliRunner().invoke(
        main,
        ["-b", str(FIXTURES / "base.json"), "-r", str(FIXTURES / "revised.json"),
         "-o", str(tmp_path / "out" / "diff")],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "out" / "diff.md").exists()
    assert (tmp_path / "out" / "diff.csv").exists()


def test_cli_output_matches_the_committed_example(tmp_path):
    """fixtures/expected.* is the worked example in CLAUDE.md; keep it from going stale."""
    out = tmp_path / "expected"
    result = CliRunner().invoke(
        main,
        ["-b", str(FIXTURES / "base.json"), "-r", str(FIXTURES / "revised.json"), "-o", str(out)],
    )
    assert result.exit_code == 0, result.output
    for suffix in (".md", ".csv"):
        expected = (FIXTURES / f"expected{suffix}").read_text(encoding="utf-8")
        # The report names its inputs, and the test runs them from a different directory.
        assert Path(f"{out}{suffix}").read_text(encoding="utf-8").replace(
            str(FIXTURES) + "/", "tests/fixtures/"
        ) == expected


def test_cli_appends_to_the_prefix_rather_than_replacing_its_suffix(tmp_path):
    result = CliRunner().invoke(
        main,
        ["-b", str(FIXTURES / "base.json"), "-r", str(FIXTURES / "revised.json"),
         "-o", str(tmp_path / "example.v2")],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "example.v2.md").exists()
    assert not (tmp_path / "example.md").exists()


def test_cli_refuses_to_overwrite_an_input(tmp_path):
    # A prior report handed back as an input: -o .../report then writes report.md over it.
    report_input = tmp_path / "report.md"
    report_input.write_text(json.dumps(REVISED), encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["-b", str(FIXTURES / "base.json"), "-r", str(report_input), "-o", str(tmp_path / "report")],
    )
    assert result.exit_code != 0
    assert "would overwrite an input file" in result.output
    assert json.loads(report_input.read_text(encoding="utf-8")) == REVISED


def test_cli_exits_nonzero_on_duplicate_ids(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"fields": [{"name": "A"}, {"name": "A"}]}), encoding="utf-8")
    result = CliRunner().invoke(
        main, ["-b", str(bad), "-r", str(FIXTURES / "revised.json"), "-o", str(tmp_path / "diff")]
    )
    assert result.exit_code == 1


def test_cli_artifact_property_is_configurable(tmp_path):
    out = tmp_path / "diff"
    result = CliRunner().invoke(
        main,
        ["-b", str(FIXTURES / "base.json"), "-r", str(FIXTURES / "revised.json"),
         "-o", str(out), "--artifact-property", "description"],
    )
    assert result.exit_code == 0, result.output
    body, appendix = out.with_suffix(".md").read_text(encoding="utf-8").split("## Appendix")
    assert "`description`" in appendix and "`custom`" in body
