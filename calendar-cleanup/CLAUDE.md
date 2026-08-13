# calendar-cleanup

## Overview

One of my calendars, coloured green and named "Tasks", doubles as a task list. Small things get
dropped onto it at a time that means something — either a good moment to do the work, or the
deadline it has to beat. Since I'm already checking the calendar for meetings, upcoming tasks are
in front of me without a separate tool to open. (The real work lives in Sunsama and a paper
journal; this is for the small stuff.)

Once or twice a week I scan back a week or two, delete what's done, and drag anything still live
into the current week. Tasks I miss on that pass just sit there. `list_events.py` prints every task
sorted by date so the stragglers are obvious.

## What the script does

### Input

An `.ics` export of the calendar, by default `data/Tasks.ics`. Export it from Calendar.app and drop
it there before each run; the script never talks to Calendar itself.

`data/` is gitignored, and the export must stay there — it holds a real task list, and this
repository is public.

### Output

One line per task on stdout, oldest first:

```
Found 53 tasks:
 - 888 days ago: [R] Replace the smoke alarm battery -- Sun, Mar 3, 2024 (all day) (recurring, series ended)
 - 34 days ago: Water the fern -- Sun, Jul 5, 2026 (all day)
 - Today: Call about the bicycle -- Sat, Aug 8, 2026 at 2:00pm EDT
 - In 12 days: Sharpen the kitchen knives -- Thu, Aug 20, 2026 (all day)
 - In 18 days: [R] Tidy the workbench -- Wed, Aug 26, 2026 from 8:00pm to 8:30pm EDT (recurring, next occurrence)
```

Anything reported as more than a couple of weeks ago is a candidate to delete or reschedule, which
is the whole point.

Progress messages go to stderr via `logging`, so piping stdout keeps the list clean.

### How it works

The interesting part is which date a recurring task is judged on. A weekly reminder created in 2023
has a `DTSTART` in 2023; reporting that would put it at the top of the list as "1250 days ago"
every single week, burying the tasks that genuinely need attention. So:

1. Read the calendar and note, per `UID`, whether that task has an `RRULE`. (Expanded occurrences
   don't carry `RRULE`, so this has to come from the original `VEVENT`s.)
2. Expand the whole calendar from its earliest `DTSTART` to `HORIZON_DAYS` past today.
3. Group the occurrences by `UID` and pick, for each task, **the next occurrence due — or, if the
   series has run out, the last one that ever happened.**

That second branch is deliberate. A repeating task whose `RRULE` ended in 2024 is precisely the
kind of leftover worth clearing, so it should surface as old rather than be hidden.

Non-recurring tasks fall out of the same rule for free: they expand to exactly one occurrence, so
there's no separate code path.

Where a single instance of a series was moved or renamed (`RECURRENCE-ID`), that instance's own
time and summary are shown.

### Technical details

- **Dependencies** (PEP 723 header, installed by `uv run`): `click` for the CLI, `icalendar` for
  parsing, `recurring-ical-events` for expansion.
- **Why a library for recurrence**: the calendar uses `EXDATE` heavily (skipped weeks accumulate on
  long-running habits), plus `RRULE ... UNTIL`, all-day versus timed events across two timezones,
  and a `RECURRENCE-ID` override. Hand-rolled `dateutil.rrule` code gets those subtly wrong.
- **`HORIZON_DAYS = 400`**: far enough ahead that any series recurring annually or more often has
  an instance inside the window. Widen it if a task ever repeats less often than yearly.
- **No `tqdm`**: about 50 tasks and a few hundred occurrences. There's no loop long enough to want
  a progress bar.
- **`--today`** overrides the current date. It exists so the tests can assert on fixed output
  rather than on whatever day they happen to run.

### Usage

```sh
uv run calendar-cleanup/list_events.py | tee calendar-cleanup/data/last-run.log
```

Against a different export:

```sh
uv run calendar-cleanup/list_events.py --input some-other-calendar.ics
```

## Tests

```sh
uv run pytest calendar-cleanup
```

`tests/fixtures/tasks.ics` is a hand-written synthetic calendar — invented tasks, no real people or
places — covering the cases the logic branches on: all-day and timed one-offs, a task with no
`DTEND`, a live weekly series with `EXDATE`s, a series whose `UNTIL` has passed, and a modified
instance. It lives under `tests/`, not `data/`, because `data/` is gitignored and a fixture has to
be committed to be useful.
