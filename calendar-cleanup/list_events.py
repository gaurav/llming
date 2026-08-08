#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "click",
#   "icalendar",
#   "recurring-ical-events",
# ]
# ///

"""
List every task on a calendar, sorted by date, so stale ones are easy to spot.

Input is an .ics export of the calendar used as a task list (default
`data/Tasks.ics`). Output is one line per task on stdout:

    Found 53 tasks:
     - 34 days ago: Water the fern -- Sun, Jul 5, 2026 (all day)
     - In 18 days: [R] Tidy the workbench -- Wed, Aug 26, 2026 from 8:00pm to 8:30pm EDT (recurring, next occurrence)

Recurring tasks are reported at the occurrence that matters now -- the next one
due, or the last one that ever happened if the series has run out -- rather than
at the original DTSTART, which for a long-running weekly task is years in the
past and would swamp the genuinely stale entries.
"""

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import click
import recurring_ical_events
from icalendar import Calendar

# An occurrence this far ahead is far enough: the least frequent series here is
# semiannual, so every live series has an instance inside a year.
# ponytail: widen if a task ever recurs less often than annually.
HORIZON_DAYS = 400


def normalize_datetime(dt):
    """Convert a date to datetime for comparison purposes."""
    if dt is None:
        return datetime.min
    if isinstance(dt, datetime):
        # Remove timezone info for comparison
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    elif isinstance(dt, date):
        # Convert date to datetime at midnight
        return datetime.combine(dt, datetime.min.time())
    return datetime.min


def as_date(dt):
    """Reduce a date-or-datetime to a plain date."""
    return dt.date() if isinstance(dt, datetime) else dt


def calculate_days_until(dt, today):
    """Calculate days from today to the given date."""
    if dt is None:
        return None

    return (as_date(dt) - today).days


def format_days_until(days_until):
    """Phrase a day offset the way it reads best in a scan."""
    if days_until is None:
        return "Unknown"
    if days_until == 0:
        return "Today"
    if days_until == 1:
        return "Tomorrow"
    if days_until == -1:
        return "Yesterday"
    if days_until < 0:
        return f"{abs(days_until)} days ago"
    return f"In {days_until} days"


def format_event_datetime(start_dt, end_dt):
    """Format start and end times in short locale format."""
    if start_dt is None:
        return "Unknown date"

    # Check if it's a date-only event
    if not isinstance(start_dt, datetime):
        # All-day event
        return start_dt.strftime("%a, %b %-d, %Y (all day)")

    # Format: "Sat, Feb 23, 2026 from 2:30pm to 3:30pm EST"
    date_part = start_dt.strftime("%a, %b %-d, %Y")
    start_time = start_dt.strftime("%-I:%M%p").lower()
    tz_abbr = start_dt.strftime("%Z") if start_dt.tzinfo else ""

    # Expansion gives a task with no DTEND a zero-length one; that reads as a
    # moment, not a range.
    if isinstance(end_dt, datetime) and end_dt != start_dt:
        when = f"{date_part} from {start_time} to {end_dt.strftime('%-I:%M%p').lower()}"
    else:
        when = f"{date_part} at {start_time}"

    return f"{when} {tz_abbr}" if tz_abbr else when


def read_masters(cal):
    """Map each UID to its summary and whether it recurs.

    Expanded occurrences don't carry RRULE, so whether a task repeats has to be
    read off the original VEVENTs. A series with a modified instance has two
    VEVENTs sharing a UID; the one without RECURRENCE-ID is the master.
    """
    masters = {}
    for event in cal.walk("VEVENT"):
        uid = str(event.get("uid"))
        if uid in masters and event.get("recurrence-id") is not None:
            continue
        masters[uid] = {
            "summary": str(event.get("summary", "No title")),
            "recurring": event.get("rrule") is not None,
        }
    return masters


def pick_occurrence(occurrences, today):
    """The occurrence worth showing: the next one due, else the last one held."""
    occurrences.sort(key=lambda o: normalize_datetime(o.get("dtstart").dt))
    for occurrence in occurrences:
        if as_date(occurrence.get("dtstart").dt) >= today:
            return occurrence, True
    return occurrences[-1], False


def collect_tasks(ics_path, today):
    """Return one row per task, sorted by the date it should be judged on."""
    cal = Calendar.from_ical(Path(ics_path).read_bytes())
    masters = read_masters(cal)
    logging.info("Read %d tasks from %s", len(masters), ics_path)

    starts = [
        as_date(event.get("dtstart").dt)
        for event in cal.walk("VEVENT")
        if event.get("dtstart")
    ]
    if not starts:
        return []

    occurrences = recurring_ical_events.of(cal).between(
        min(starts), today + timedelta(days=HORIZON_DAYS)
    )
    logging.info("Expanded to %d occurrences", len(occurrences))

    by_uid = defaultdict(list)
    for occurrence in occurrences:
        by_uid[str(occurrence.get("uid"))].append(occurrence)

    rows = []
    for uid, master in masters.items():
        if not by_uid[uid]:
            # No occurrence in the window at all; fall back to nothing to show.
            logging.warning("No occurrence found for %r", master["summary"])
            continue
        occurrence, upcoming = pick_occurrence(by_uid[uid], today)
        dtend = occurrence.get("dtend")
        rows.append(
            {
                # A modified instance carries its own summary; prefer it.
                "summary": str(occurrence.get("summary", master["summary"])),
                "start": occurrence.get("dtstart").dt,
                "end": dtend.dt if dtend else None,
                "recurring": master["recurring"],
                "upcoming": upcoming,
            }
        )

    rows.sort(key=lambda row: normalize_datetime(row["start"]))
    return rows


def format_task(row, today):
    """Render one task as a single scannable line."""
    days_str = format_days_until(calculate_days_until(row["start"], today))
    date_str = format_event_datetime(row["start"], row["end"])
    line = f" - {days_str}: {row['summary']} -- {date_str}"
    if row["recurring"]:
        state = "next occurrence" if row["upcoming"] else "series ended"
        line += f" (recurring, {state})"
    return line


@click.command()
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=Path(__file__).parent / "data" / "Tasks.ics",
    show_default=True,
    help="Calendar export to read.",
)
@click.option(
    "--today",
    type=click.DateTime(["%Y-%m-%d"]),
    default=None,
    help="Treat this date as today (defaults to the actual date).",
)
def main(input_path, today):
    """List every task on the calendar, sorted by date."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    today = today.date() if today else date.today()
    rows = collect_tasks(input_path, today)

    print(f"Found {len(rows)} tasks:")
    for row in rows:
        print(format_task(row, today))


if __name__ == "__main__":
    main()
