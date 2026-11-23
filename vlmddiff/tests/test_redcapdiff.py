"""Tests for redcapdiff. Inputs are tiny synthetic CSVs written to tmp_path, not study data."""

import csv

import pytest
from click.testing import CliRunner

from redcapdiff import CHOICES_COLUMN, classify, main, parse_choices, show_whitespace
from vlmddiff import Change

HEADER = ["Variable / Field Name", "Form Name", "Field Type", CHOICES_COLUMN]


def change(base, revised, column=CHOICES_COLUMN):
    return Change("VAR", "Form", column, "changed", base, revised)


def test_parse_choices_treats_bare_items_as_code_and_label():
    assert parse_choices("Y | N") == parse_choices("Y, Y | N, N") == [("Y", "Y"), ("N", "N")]
    assert parse_choices("1,1|2,Two, or more") == [("1", "1"), ("2", "Two, or more")]


@pytest.mark.parametrize(
    "base, revised, column, expected",
    [
        ("", "True, True | False, False", CHOICES_COLUMN, "filled in"),
        ("1, Yes | 2, No", "", CHOICES_COLUMN, "emptied"),
        ("1, \xa0Less", "1, Less", CHOICES_COLUMN, "whitespace only"),
        ("   ", "", CHOICES_COLUMN, "whitespace only"),
        ("0,0|1,1", "0, 0 | 1, 1", CHOICES_COLUMN, "choice formatting only"),
        ("Y | N", "Y, Y | N, N", CHOICES_COLUMN, "choice formatting only"),
        ("4, Other | 4, Unknown", "4, Unknown | 4, Unknown", CHOICES_COLUMN, "content change"),
        # Choice parsing only applies to the choices column.
        ("a,b", "a, b", "Field Label", "content change"),
    ],
)
def test_classify(base, revised, column, expected):
    assert classify(change(base, revised, column)) == expected


def test_show_whitespace_marks_nbsp_but_not_spaces():
    assert show_whitespace("1, \xa0Less") == "1, <U+00A0>Less"


def write(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)


def test_cli_counts_each_category(tmp_path):
    write(tmp_path / "base.csv", [
        ["A", "F1", "truefalse", ""],
        ["B", "F1", "truefalse", ""],
        ["C", "F2", "radio", "0|1"],
        ["D", "F2", "radio", "1, \xa0Yes | 2, No"],
        ["E", "F2", "radio", "4, Other | 4, Unknown"],
        ["F", "F2", "text", ""],
    ])
    write(tmp_path / "revised.csv", [
        ["A", "F1", "truefalse", "True, True | False, False"],
        ["B", "F1", "truefalse", "True, True | False, False"],
        ["C", "F2", "radio", "0, 0 | 1, 1"],
        ["D", "F2", "radio", "1, Yes | 2, No"],
        ["E", "F2", "radio", "4, Unknown | 4, Unknown"],
        ["G", "F2", "text", ""],
    ])
    result = CliRunner().invoke(
        main, ["-b", str(tmp_path / "base.csv"), "-r", str(tmp_path / "revised.csv")]
    )
    assert result.exit_code == 0, result.output

    report = (tmp_path / "redcap-diff.md").read_text(encoding="utf-8")
    assert "| filled in | 2 |" in report
    assert "| whitespace only | 1 |" in report
    assert "| choice formatting only | 1 |" in report
    assert "| content change | 1 |" in report
    assert "## Rows added (1)" in report and "## Rows removed (1)" in report
    assert "<U+00A0>" in report

    with (tmp_path / "redcap-diff.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 5
    assert {r["form"] for r in rows} == {"F1", "F2"}
