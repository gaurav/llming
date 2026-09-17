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

## Nothing is ever bulk-pasted into the master tab

New rows go on *top* of the Sheet, and adding one has to stay effortless — no validation, no
dropdowns. So a script-generated column pasted back in misaligns silently the moment a book is
bought between the download and the paste. Everything here is shaped by avoiding that:

- Normalisation happens on load (`genre_map.yaml`), never at entry.
- Machine-derived data lives in `data/enrichment.csv`, keyed by `book_key()` — the ASIN out of the
  row's Audible `url`, else squashed `title|author` — and is joined in `enriched()`.
- The Sheet wins every disagreement. Audible fills blank `genre`, `narrator` and `duration_hours`
  and never overrides a typed one; `genre_raw` keeps what was typed.
- The one hand edit the tools ask for is a single cell, for a book `enrich.py` could not match:
  an Audible URL pasted into a *blank* `url`, which changes the row's key to the ASIN so the next
  run fetches it directly — or, where `url` already holds a Libro.fm or Apple Books link, a
  corrected `title`. Never suggest pasting over an existing `url`: it is the only record of where
  the book was bought. (That advice was given once, for two Libro.fm rows, before anyone looked.)

Fixing a typo in a title changes a `title|author` key, which orphans that row's cache entry. It
heals itself — the next `enrich.py` run looks the new key up — so the cache is never edited by hand.

## Audible's catalogue API

`https://api.audible.com/1.0/catalog/products`, no credentials, no documented rate limit;
`enrich.py` sleeps half a second between requests anyway. Quirks that cost time:

- **`response_groups` decides which fields exist at all.** `title` and `subtitle` come from
  `product_desc`; without it a search result's title is `null`, not absent.
- **An ASIN Audible no longer sells answers 200** with a product holding nothing but the `asin`.
  `look_up()` treats a missing title as not found.
- **A search for the first book of a series returns the rest of the series too, often ahead of
  it.** Never take the first hit. `pick_match()` wants an exact title and a shared author, and the
  near misses go to `data/enrichment-review.csv`.
- **Subtitles live on either side.** The Sheet has `Babel: Or the Necessity of Violence…`, Audible
  has `Babel`. `titles_match()` lets one side be shortened to its pre-colon part but never both —
  shorten both and `Star Wars: Thrawn` matches every Star Wars book by the same author.
- **Category ladders come back alphabetically**, not by importance, which puts
  `Literature & Fiction` ahead of nearly everything. Hence row order in `genre_map.yaml` being the
  priority, rather than "first ladder wins".
- `merchandising_summary` (in `product_attrs`) is a two-sentence blurb. `publisher_summary` is the
  full HTML one and needs `product_extended_attrs`; not fetched, because it would dominate the CSV.

`enrich.py` saves every 50 rows as well as in a `finally`: a full run is twelve minutes of requests,
and a kill signal skips `finally` entirely — the first full run lost everything that way.

## Literature is a judgement, Fiction is the catch-all

`Literature` in the Sheet means the literary shelf, not fiction in general, so it cannot simply
absorb Audible's `Literature & Fiction`. The map sends only `… > Genre Fiction > Literary Fiction`
and `… > Classics` to Literature — books typed Literature carry those ladders 58% and 52% of the
time, the best Audible offers — and everything else under that top level to `Fiction`. Telling the
two apart needs three ladder levels, which is why `ladder_entries()` matches on the longest prefix
the map lists rather than a fixed depth.

## How the ranking is built

`recommend.py` exists for two situations, and they want opposite things: `relisten` is for having
something on in the background, so it only offers books already heard and defaults to fiction;
`new` is for listening properly, so it offers only the unheard, and a series already under way
outranks everything.

- **Liking** is `rating_0_5`, else 4.25 for an unrated book with `count >= 2`. That number is the
  median rating of the books that are both rated and relistened, not a guess. It rescues only a
  handful of unrated books — most relistened books are rated — so it is a calibration, not a
  second data source.
- **Author, narrator, genre and series affinities** are means shrunk towards the library-wide
  mean by `SHRINKAGE` imaginary average books, and each book's own rating is left out of its own
  groups. Without the leave-one-out every finished book recommends itself in `relisten`.
- `next_in_series` marks only the *earliest* unheard book of a series with a heard one. Book three
  is not next until book two is heard.
- `--long-ago` is off by default on purpose: the usual favourites are the right first answer, and
  the flag is for the second run, when none of them appeal.
- The `why` column is not decoration. A ranking nobody can audit gets ignored; every term that
  moves a score has to be able to say so there.

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

`tests/test_download_sheet.py` drives the CLI through click's `CliRunner` with `requests.get`
stubbed, so the content-type guard is covered without the network — and its CSV case writes into a
`tmp_path` subdirectory that does not exist yet, which is what keeps the fresh-clone `mkdir` honest.

`tests/test_enrich.py` covers the matcher with canned catalogue products and a fake session — the
sequel-listed-first case, subtitles and bracketed notes on one side only, credentials on either
side of an author's name. Every case in it is one the real library produced.

The genre tests in `tests/test_audiobooks.py` run against a miniature map written to `tmp_path`,
not the committed `genre_map.yaml`, so reordering the real vocabulary cannot break them; one test
checks only that the committed file loads, which is also what catches a value listed twice.
`tests/test_recommend.py` builds its library inline. `enriched()` reads `ENRICHMENT_CSV` from
beside the module, so on a machine with a real cache the download test quietly joins it — harmless,
since nothing matches, but monkeypatch `audiobooks.ENRICHMENT_CSV` in any test where it matters.

The download and loader tests stub `audiobooks.load_dotenv` out before setting `GOOGLE_SHEET_ID`.
`load_dotenv()` does not override variables already in the environment, so `monkeypatch.setenv`
would win anyway; the stub is what stops a developer's own `.env` from being consulted at all.
