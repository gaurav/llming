# audiobooks

Tools for making sense of my hand-maintained audiobook library — the Google Sheet that tracks every
audiobook I have bought across Audible, Libro.fm and Apple Books, along with its author, genre,
rating, listen count and how long it took me to get through. None of the three sellers will tell me
what I own, and the Sheet's PivotTables are fiddly to maintain, so the data comes into Python
instead.

The goal this is all pointed at: **what should I listen to next**. `recommend.py` answers that for
the two ways the library actually gets used — something new to listen to properly, or something
already known to have on in the background — and the rest of the directory exists to feed it:
the Sheet tidied into a DataFrame, the gaps in it filled from Audible's catalogue, and its
free-text genres pulled into one vocabulary.

The Sheet stays the only place anything is typed, and stays as easy to add a row to as it is now:
no dropdowns, no validation, nothing pasted back into it. Everything below happens on the way out.

## Running it

Set up `.env` once, with the Sheet's ID and the gid of its master tab, both taken from the Sheet's
own URL:

```bash
cp env.default .env
$EDITOR .env
```

The Sheet must be shared as "anyone with the link", because the download uses Google's public CSV
export endpoint rather than a service account.

Then the usual round, after buying or finishing something:

```bash
uv run download_sheet.py 2>&1 | tee data/last-run.log              # save the Sheet to data/audiobooks.csv
uv run enrich.py data/audiobooks.csv 2>&1 | tee data/last-run.log  # look up whatever is new on Audible
uv run recommend.py new data/audiobooks.csv                        # what to listen to properly
uv run recommend.py relisten data/audiobooks.csv                   # what to have on in the background
uv run recommend.py taste data/audiobooks.csv                      # which genres have gone down best
```

Every script takes the saved CSV as an optional argument and reads the live Sheet without it.

### Recommendations

```bash
uv run recommend.py new data/audiobooks.csv --genre fantasy --max-hours 12
uv run recommend.py new data/audiobooks.csv --genre detectives --non-fiction
uv run recommend.py relisten data/audiobooks.csv --min-hours 10
uv run recommend.py new data/audiobooks.csv --form "read by the author" --non-fiction
uv run recommend.py relisten data/audiobooks.csv --long-ago
```

- **`new`** lists what has not been heard — in any edition — best bet first. The next book of a
  series already under way leads, lifted or sunk by how the series has gone so far; after that it
  is how the author, the narrator and the genre have gone down before, in that order of weight.
  Books that were started and dropped stay in, slightly lower, marked `stalled since`.
- **`relisten`** lists what has been heard, fiction unless told otherwise, by how much it was
  liked and how often it has been returned to. The same favourites will top it every time, which
  is the point; **`--long-ago`** is for the second run, when none of them appeal — it favours
  whatever was last heard longest ago.
- `--genre` takes a genre from `genre_map.yaml` or any piece of an Audible category, so
  `--genre "sea adventures"` works even though that is nobody's idea of a genre here.
- `--form` takes one of the forms in `genre_map.yaml`: `radio drama` (anything performed — full
  cast, BBC serial, monologue), `short stories`, or `read by the author`. That last one is typed
  on seven books and true of 282: the loader fills it in wherever a book has no other form and its
  author is among its narrators.
- **`taste`** is the table behind the rankings rather than a ranking: every genre with its mean
  rating, how many ratings that rests on, how many books are owned and how many are still
  unheard. `score` is the mean pulled towards the library-wide one, so a genre with a single
  five-star book does not lead; sort by it, read `mean` beside it. `--by author`, `narrator`,
  `series` or `form` does the same for those, and `--fiction/--non-fiction` narrows it. This lives
  here and not in `genre_map.yaml` because it changes with every book rated, and the map is a
  hand-edited file that should not.
- The **why** column says what moved each book up or down. If a ranking looks wrong, that is
  where to look first. `--csv` prints every column instead, blurb included, which is the thing to
  hand to an LLM along with a mood ("something funny and short").

### Filling the gaps from Audible

`enrich.py` looks every book up in Audible's public catalogue and caches the answers in
`data/enrichment.csv`: series and position, narrators, runtime, Audible's categories and a short
blurb. A row with an Audible `url` is fetched by the ASIN in it; any other row — Libro.fm, Apple
Books, the old `From Audible` pastes — is searched for by title and author and accepted only on an
exact match. It only looks up what is not cached yet, so after the first twelve-minute run it
takes seconds. `--limit 30` for a trial, `--refresh` to start again.

Near misses land in `data/enrichment-review.csv` with their three likeliest candidates. To settle
one, in the Sheet:

- if the row's `URL` cell is **blank**, paste the right Audible URL into it
  (`https://www.audible.com/pd/<ASIN>` is enough);
- if it already holds a Libro.fm or Apple Books link, **leave it** — that is the record of where
  the book was bought — and correct the `Title` to what Audible calls the book instead. A
  subtitle after a colon is fine: `ADHD Is Awesome: A Guide to (Mostly) Thriving with ADHD`.

Then download the Sheet again and rerun `enrich.py`, which retries everything unmatched each time.

**Worth keeping a copy in the Sheet.** The catalogue endpoint is undocumented and could close, and
`data/` is not in git, so the cache exists on one machine. Every so often, paste the whole of
`data/enrichment.csv` over a tab of its own (`File → Import → Replace current sheet` does it in one
step). Replacing a whole tab cannot misalign the way pasting a column into the master tab can. The
file carries each title exactly as the Sheet has it, so a `VLOOKUP` on title from the master tab
can show the series or Audible's categories beside a book, if that is ever wanted there. Nothing
reads that tab back yet; it is a backup, and restoring is saving it as `data/enrichment.csv`.

### The genre vocabulary

`genre_map.yaml` says what every value typed into `genre` or `grouping`, and every Audible
category, means: which genre, which form (radio drama, short stories, read by the author), and
whether it is fiction. Edit it like any other file — its header explains the rules, including why
the order of the entries matters. A genre typed into the Sheet that the map has never seen still
works; it passes through as typed and the loader logs it, as a reminder to file it.

### In code

```python
from audiobooks import load

df = load()                                     # live, from the Sheet ID in .env
df = load("data/audiobooks.csv")                # the downloaded copy, for working offline or fast
df = load("data/audiobooks.csv", enrich=False)  # the Sheet alone, exactly as typed
```

`load()` normalises the column names to snake_case (`Date Finished` becomes `date_finished`), drops
the blank padding rows and columns that Sheets adds to every export, parses the date columns, and
strips stray whitespace off text values. It turns the two columns the Sheet keeps as text into
numbers: `money` (`$3.75`) in place, and `duration` (`11:57:00`) into a new `duration_hours`.

Then, unless told `enrich=False`, it joins the Audible cache and settles the genres. **The Sheet
wins every disagreement**: Audible fills a blank `genre`, `narrator` or `duration_hours` and never
replaces a typed one. That adds `series`, `series_position`, `categories`, `summary`, `form`,
`fiction`, `genre_source` (`sheet` or `audible`), `genre_raw` (what was typed), and `last_started`
/ `last_finished` across all the listens. Running `uv run audiobooks.py data/audiobooks.csv` prints
a per-column summary of the result.

## Known issues

- **A genre Audible filled in is a good guess, not a fact.** It agrees with a typed genre a little
  under 6 times in 10 (see the end of this file). `genre_source` says which genres came from where,
  and typing a genre into the Sheet always settles it.
- **Audible cannot tell a biography from an autobiography**, and files both under one category.
  Nine in ten of those in this library are autobiographies or memoirs, so that is what a blank gets;
  roughly one in ten of the Audible-filled `Autobiography` rows is really a `Biography`.
- **About 20 books get nothing from Audible**: BBC radio collections sold under other names,
  titles whose top search hits are German or Spanish editions, and a couple of typos in the Sheet
  (`The Orchadist`). `data/enrichment-review.csv` lists the near misses with candidates; a URL
  pasted into the Sheet's `url` cell fixes any one of them.
- **The Audible lookup sends titles and authors to Audible**, unauthenticated, from wherever it is
  run. It is an undocumented public endpoint and could change or close without notice; everything
  else keeps working off the cache if it does.
- **An author is whatever the cell says.** `Terry Pratchett` and `Terry Pratchett, Neil Gaiman` are
  two different authors to the ranking, so a co-written book borrows nothing from either.
- **The ranking weights are judgement, not fitted**: author 3, narrator 1.5, genre 1, and a series
  pull of up to 2.5. With 169 ratings there is not enough to fit them on. They are constants at the
  top of `recommend.py`.
- **Date columns are recognised by name**, not by content: a column parses as dates only if its
  name contains `date`, `started`, `finished`, `purchased`, `bought`, `added` or `released`. A date
  column named something else stays as text. This is deliberate — sniffing every column's contents
  turns ratings and `3/5`-style values into timestamps — but it means renaming a column in the
  Sheet can silently change its type here.
- **The listen-session columns repeat with a duplicated header.** The Sheet has `Started 3`,
  `Finished 3` and `Time taken (days) 3` twice over; pandas keeps both by renaming the second set
  `started_3_1`. `last_started` and `last_finished` take the latest across all of them, so nothing
  is lost, but the labels in the Sheet are worth fixing.
- **`status` disagrees with the dates in places** — 24 books marked `Not started` have a `started`
  date, and 96 marked `Finished` have none. `--long-ago` treats a finished book with no date as
  heard long ago.
- **The whole thing depends on link sharing.** If the Sheet's access is tightened, the export
  endpoint answers with a sign-in page; `download_sheet.py` detects that and says so, but there is
  no authenticated fallback.
- **Only one tab is read**, the one named by `GOOGLE_SHEET_GID`. Other tabs, including the
  PivotTables, are ignored.

## Possible next steps

- **Sort the biographies from the memoirs.** The one genre call Audible cannot make is easy for an
  LLM given the title, author and blurb — *Red Comet* by Heather Clark is plainly a biography. A
  session over `recommend.py --csv`-style output could list the Audible-filled `Autobiography` rows
  that are not, to be typed into the Sheet.
- **What to buy next**: series where book N is finished and book N+1 is not owned. Audible's
  series listing would supply the missing half.
- **Audible's "similar titles"** (`/catalog/products/{asin}/sims`) for the favourites, intersected
  with the unread pile: because you loved X, and already own Y.
- **A lint report for the Sheet**: the status/date disagreements, the 16 titles that appear twice,
  the `Finished?` and `Reading` statuses, the doubled `Started 3` header.
- **An Open Library fallback** for the books Audible does not list — only worth it if the twenty
  become two hundred.
- **Write access to the Sheet** through a service account, if pasting single cells ever becomes a
  chore. It would also let the Sheet stop being link-shared.
- Replace the PivotTables with a handful of standing summaries — by genre, by author, by year — so
  the Sheet stops needing to maintain them.

## What is actually in there

**1,153 books.** The shape that matters for picking something to listen to next, as typed into the
Sheet and then as `load()` hands it back once Audible has filled the gaps:

| | in the Sheet | after `load()` |
|---|---|---|
| `genre` | 533 filled, 55 distinct values | 1,141 filled, 30 distinct |
| `narrator` | 700 | 1,129 |
| `duration_hours` | 613 | 1,123 |
| `series` | not a column at all | 230 books across 171 series |
| `fiction` | — | known for 1,107 |
| `form` | 97 tagged in `grouping`, 20 spellings | 406 tagged, 6 forms |

And what only the Sheet can say:

| | |
|---|---|
| `status` | 826 Not started, 205 Finished, 102 Started, 17 Returned, plus a `Finished?` and a `Reading` |
| `rating_0_5` | 169 filled, and generous: three quarters of what gets rated lands at 3.5 or above |
| `count` | times listened, 290 filled, `0.5` meaning a partial. 49 books have been heard twice or more |
| `grouping` | a second tag for *form* rather than subject — radio drama, full cast, read by the author — on 97 books |

`started`/`finished`/`time_taken_days` repeat seven times across the sheet, one triple per listen
through a book.

Things that fell out of looking at the whole library, each of which shaped the tools:

- **The buying and the enjoying are out of step.** History is the biggest unheard pile (130 books)
  and rates 3.5; Advice has 65 unheard and rates 2.7. Horror rates 4.2 and Literature 4.0, against
  a library mean of 3.7. `recommend.py taste` shows the current table, and the genre term in the
  ranking quietly corrects for it.
- **How fast a book gets finished says almost nothing about how it was rated** (r = 0.12 between
  `time_taken_days` and `rating_0_5`), so pace is not used as a stand-in for enjoyment anywhere.
- **Relistening is a rating.** The books heard twice or more that are also rated average 4.2, so
  an unrated relisten is scored at their median, 4.25. It rescues only five books — nearly
  everything relistened is rated already — but those five are favourites that would otherwise
  count for nothing.
- **Audible's idea of a book's genre matches the Sheet's a little under 6 times in 10**, measured on
  the 526 books that have both. Most of the rest is Audible being more specific (a typed
  `Literature` it calls Historical fiction, or a typed `Literature` it has no way to know is
  literary) or filing a history book under the person it is about. Good enough to fill 600 blanks;
  not good enough to overrule anything typed, which is why it never does.
