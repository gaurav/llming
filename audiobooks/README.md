# audiobooks

Tools for making sense of my hand-maintained audiobook library — the Google Sheet that tracks every
audiobook I have bought across Audible, Libro.fm and Apple Books, along with its author, genre,
rating, listen count and how long it took me to get through. None of the three sellers will tell me
what I own, and the Sheet's PivotTables are fiddly to maintain, so the data comes into Python
instead.

The goal this is all pointed at: **what should I listen to next**, especially when I already have a
genre or a mood in mind. Right now the repo has the plumbing for that — the sheet, tidied, in a
DataFrame — and not yet the recommending.

## Running it

Set up `.env` once, with the Sheet's ID and the gid of its master tab, both taken from the Sheet's
own URL:

```bash
cp env.default .env
$EDITOR .env
```

The Sheet must be shared as "anyone with the link", because the download uses Google's public CSV
export endpoint rather than a service account.

Then either read the sheet live, or save a copy:

```bash
uv run audiobooks.py                                        # print what the live sheet holds
uv run download_sheet.py 2>&1 | tee data/last-run.log       # save it to data/audiobooks.csv
uv run audiobooks.py data/audiobooks.csv                    # print what the saved copy holds
```

Both print a per-column summary — dtype, how many rows are filled in, how many distinct values,
and an example — which is the quickest way to see what the loader made of the sheet.

In code, the loader is two lines:

```python
from audiobooks import load

df = load()                       # live, from the Sheet ID in .env
df = load("data/audiobooks.csv")  # the downloaded copy, for working offline or fast
```

`load()` normalises the column names to snake_case (`Date Finished` becomes `date_finished`), drops
the blank padding rows and columns that Sheets adds to every export, parses the date columns, and
strips stray whitespace off text values so `"Fantasy "` and `"Fantasy"` group together. It also
turns the two columns the Sheet keeps as text into numbers: `money` (`$3.75`) in place, and
`duration` (`11:57:00`) into a new `duration_hours` alongside the original. Everything else is left
exactly as the Sheet has it.

## What is actually in there

As of the first full load: **1,153 books, 43 columns**. The shape that matters for picking
something to listen to next:

| | |
|---|---|
| `status` | 826 Not started, 205 Finished, 102 Started, 17 Returned, plus a `Finished?` and a `Reading` |
| `genre` | filled on 533 of 1,153 — the biggest gap in the data. 55 distinct values, led by Literature (87), History (80), Autobiography (79), Fantasy (50), Advice (40) |
| `rating_0_5` | 169 filled, and generous: three quarters of what you rate lands at 3.5 or above |
| `count` | times listened, 290 filled, `0.5` meaning a partial |
| `duration_hours` | 613 filled, 1 to 100+ hours |
| `grouping` | a second tag for *form* rather than subject — radio drama, full cast, read by the author — on 97 books |

`started`/`finished`/`time_taken_days` repeat seven times across the sheet, one triple per listen
through a book.

Two things that fell out of the first look at the whole library, both of which shape what is worth
building next:

- **History is the biggest unread pile and the lowest-rated genre** — 64 unread, a 3.4 mean rating
  against 4.1 for Comedy, Horror and Literature. Autobiography is second-biggest unread at 48 and
  rates 3.8. The buying and the enjoying are out of step.
- **How fast a book gets finished says almost nothing about how it was rated** (r = 0.12 between
  `time_taken_days` and `rating_0_5`). Reading speed is not a usable stand-in for enjoyment, so
  anything that ranks books has to lean on the ratings that exist rather than infer taste from pace.

## Known issues

- **Date columns are recognised by name**, not by content: a column parses as dates only if its
  name contains `date`, `started`, `finished`, `purchased`, `bought`, `added` or `released`. A date
  column named something else stays as text. This is deliberate — sniffing every column's contents
  turns ratings and `3/5`-style values into timestamps — but it means renaming a column in the
  Sheet can silently change its type here.
- **Genre is missing on more than half the library**, which is the main thing standing between the
  data and "find me a fantasy novel I have not read". The 55 values also need tidying: `Fiction` and
  `Literature` overlap, `Radio drama` and `Radio Drama` differ only in case, and some rows carry two
  genres in one cell (`Advice, Politics`).
- **The listen-session columns repeat with a duplicated header.** The Sheet has `Started 3`,
  `Finished 3` and `Time taken (days) 3` twice over; pandas keeps both by renaming the second set
  `started_3_1`. The column *order* is still correct, so the seven triples read left to right as
  listens one to seven, but the labels in the Sheet are worth fixing.
- **`status` disagrees with the dates in places** — 24 books marked `Not started` have a `started`
  date, and 96 marked `Finished` have none.
- **The whole thing depends on link sharing.** If the Sheet's access is tightened, the export
  endpoint answers with a sign-in page; `download_sheet.py` detects that and says so, but there is
  no authenticated fallback.
- **Only one tab is read**, the one named by `GOOGLE_SHEET_GID`. Other tabs, including the
  PivotTables, are ignored.

## Possible next steps

- Decide what "what should I listen to next" means as a query: unlistened books in a given genre,
  ranked by something — author affinity, how well past books of that genre scored, length against
  the time available.
- Work out which columns actually carry signal, and clean the ones that nearly do: genre spellings
  that differ by a word, authors written two ways, ratings left blank.
- Replace the PivotTables with a handful of standing summaries — by genre, by author, by year — so
  the Sheet stops needing to maintain them.
