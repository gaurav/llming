Specifics about this tool that would get in the way of `README.md`. Read that first for what this
is and how to run it.

## The Sheet is read over the public CSV export endpoint

`https://docs.google.com/spreadsheets/d/<id>/export?format=csv&gid=<gid>`, no credentials. Two
things follow from that:

- **A sheet that is not link-shared returns HTTP 200 with a sign-in page**, not a 4xx. That is why
  `download_sheet.py` checks the `content-type` for `text/csv` before writing anything; without the
  check the saved "CSV" would be HTML and the failure would surface much later, as a parse error.
- **Only a gid selects the tab**, not a tab name. The `gviz/tq?sheet=<name>` endpoint does take
  names, but it guesses at header rows and retypes columns on the way out, so the faithful export
  plus a gid is the better trade.

`download_sheet.py` writes the response bytes straight to disk rather than round-tripping through
pandas, so the saved file is what Google sent and `load(path)` and `load()` see the same thing.

## Why the tidying is shaped the way it is

`tidy()` in `audiobooks.py` is deliberately conservative — it is the one place where a wrong guess
silently corrupts data:

- Date parsing is driven by `DATE_COLUMN_HINT` matching the *column name*. Content sniffing was the
  obvious alternative and is worse: a ratings column holding `3/5` parses cleanly as dates.
- Whitespace stripping maps `isinstance(v, str)` over every column instead of using
  `select_dtypes("object")`. The dtype names for strings have moved between pandas 2 and 3 and
  `select_dtypes` now warns about it; the isinstance version is version-proof and non-strings fall
  through untouched.
- Sheets exports pad with trailing blank rows and unnamed blank columns. Both are dropped, which is
  why `unnamed*` columns never reach the caller. The real export opens with two entirely blank rows
  and an unnamed first column; that is normal, not a broken download.
- `duration` is `HH:MM:SS` and runs past 24 hours (`28:28:00` is a real value), so it goes through
  `pd.to_timedelta`, which handles that, rather than anything clock-shaped that would wrap it.
  `duration_hours` is added alongside because `11:57:00` is the more readable form for a person.
- `money` converts in place by stripping everything but digits and a dot. Exactly one row holds
  `???` where the price was never recorded, and that is meant to land as NaN.

## The directory and the module share a name

`audiobooks/audiobooks.py`. `from audiobooks import load` resolves to the module rather than the
directory because the script's own directory comes first on `sys.path`, and the tests put it there
explicitly, so both work from the repo root. A future script importing this from somewhere else is
where that stops being true.

## Tests

`tests/test_audiobooks.py` covers `tidy()` against a miniature export held inline in the test file —
messy headers, a padding row, a padding column, padded values. Nothing touches the network. Run
from the repo root with `uv run pytest`; pandas and python-dotenv are in the root `pyproject.toml`
dev group for exactly that reason.
