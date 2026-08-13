"""Tests for list_events, run against a synthetic fixture calendar.

Every date is asserted relative to a fixed TODAY so the output never depends on
when the suite runs.
"""

from datetime import date, datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from list_events import (
    calculate_days_until,
    collect_tasks,
    format_days_until,
    format_event_datetime,
    format_task,
    main,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tasks.ics"
TODAY = date(2026, 8, 8)


@pytest.fixture
def rows():
    return collect_tasks(FIXTURE, TODAY)


@pytest.fixture
def by_summary(rows):
    return {row["summary"]: row for row in rows}


def test_every_task_appears_once(rows):
    """Seven UIDs in the fixture; the modified instance must not add an eighth."""
    assert len(rows) == 7
    assert len({row["summary"] for row in rows}) == 7


def test_rows_are_sorted_by_date(rows):
    starts = [
        row["start"].date() if isinstance(row["start"], datetime) else row["start"]
        for row in rows
    ]
    assert starts == sorted(starts)


def test_one_off_tasks_keep_their_own_date(by_summary):
    assert by_summary["Water the fern"]["start"] == date(2026, 7, 5)
    assert by_summary["Return the library book"]["start"].date() == date(2026, 7, 30)
    assert not by_summary["Water the fern"]["recurring"]


def test_live_series_reports_next_occurrence_not_dtstart(by_summary):
    """The weekly series starts in Aug 2025; showing that would be the old bug."""
    row = by_summary["[R] Tidy the workbench"]
    assert row["recurring"] and row["upcoming"]
    assert row["start"].date() == date(2026, 8, 26)


def test_exdates_are_skipped(by_summary):
    """Aug 12 and Aug 19 are excluded, so Aug 26 is the next one due."""
    start = by_summary["[R] Tidy the workbench"]["start"].date()
    assert start not in (date(2026, 8, 12), date(2026, 8, 19))


def test_expired_series_reports_its_last_occurrence(by_summary):
    row = by_summary["[R] Replace the smoke alarm battery"]
    assert row["recurring"] and not row["upcoming"]
    assert row["start"] == date(2024, 3, 3)


def test_modified_instance_wins(by_summary):
    """The override moves the Aug 13 instance to 4pm and renames it."""
    row = by_summary["[R] Water the tomatoes (moved later)"]
    assert row["start"].date() == date(2026, 8, 13)
    assert row["start"].hour == 16


def test_task_without_dtend_reads_as_a_moment(by_summary):
    line = format_task(by_summary["Call about the bicycle"], TODAY)
    assert "at 2:00pm" in line
    assert "from" not in line


def test_all_day_task_is_labelled(by_summary):
    assert "(all day)" in format_task(by_summary["Water the fern"], TODAY)


def test_recurring_suffixes(by_summary):
    assert format_task(by_summary["[R] Tidy the workbench"], TODAY).endswith(
        "(recurring, next occurrence)"
    )
    assert format_task(
        by_summary["[R] Replace the smoke alarm battery"], TODAY
    ).endswith("(recurring, series ended)")
    assert "recurring" not in format_task(by_summary["Water the fern"], TODAY)


@pytest.mark.parametrize(
    "offset,expected",
    [(0, "Today"), (1, "Tomorrow"), (-1, "Yesterday"), (-9, "9 days ago"), (12, "In 12 days")],
)
def test_day_phrasing(offset, expected):
    assert format_days_until(offset) == expected


def test_day_phrasing_handles_missing_date():
    assert format_days_until(None) == "Unknown"
    assert calculate_days_until(None, TODAY) is None


def test_days_until_counts_from_a_date_or_datetime():
    assert calculate_days_until(date(2026, 8, 1), TODAY) == -7
    assert calculate_days_until(datetime(2026, 8, 20, 23, 0), TODAY) == 12


def test_format_event_datetime_without_a_start():
    assert format_event_datetime(None, None) == "Unknown date"


def test_cli_runs_and_lists_every_task():
    result = CliRunner().invoke(
        main, ["--input", str(FIXTURE), "--today", "2026-08-08"]
    )
    assert result.exit_code == 0
    assert result.output.startswith("Found 7 tasks:")
    assert "Water the fern" in result.output


def test_cli_rejects_a_missing_file():
    result = CliRunner().invoke(main, ["--input", "does-not-exist.ics"])
    assert result.exit_code != 0
