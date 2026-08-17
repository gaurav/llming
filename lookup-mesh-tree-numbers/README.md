# lookup-mesh-tree-numbers

Takes a TSV of MeSH identifiers (as exported from [CTD], in `MESH:D012345` form) and adds the
concept's position in the MeSH hierarchy, by querying the NLM MeSH API. The point is to be able to
group or filter a pile of CTD concepts by chemical/therapeutic class — "which of these are
antibiotics", "drop everything that isn't a disease" — which the bare identifiers don't let you do.

Five columns are added: `MESH_LABEL`, `MESH_TREE_NUMBERS` (e.g. `D04.345.566;D12.644.641`),
`MESH_TREE_LABELS`, `MESH_TREE_TOP_CODES` (e.g. `D04;D12`) and `MESH_TREE_TOP_LABELS`.

[CTD]: https://ctdbase.org/

## Running it

Run from inside this directory — the default paths are relative to the working directory.

```bash
cd lookup-mesh-tree-numbers
uv run enrich_mesh_types.py 2>&1 | tee data/last-run.log
```

Reads `data/ctd-mesh-ids.tsv` and writes `data/ctd-mesh-ids-enriched.csv` (note: CSV out, TSV in).
The input must have a column named exactly `CTD-ASSIGNED CONCEPT ID`, holding `MESH:D012345`-style
identifiers — any other CTD export shape produces a full-length output with all five new columns
blank and an exit code of 0, which looks like zero coverage rather than the wrong column name.

The input path is a positional argument; `-o/--output` sets the output. `--delay` (default 0.2s)
sleeps between *rows*, not between requests — a single row can fire the concept fetch, up to two
mapping fetches and a SPARQL query back to back — and `--log-level DEBUG` shows every API call.

Expect roughly 3 rows/second — a 773-row file takes about 4.5 minutes.

## Watch out for

- **Coverage is not complete.** On the 773-row CTD file, 98 rows (~13%) came back with no tree
  numbers. Almost all of them — 96 — are supplementary concept records (C-numbers) that *did*
  resolve through `preferredMappedTo` or `mappedTo`; the descriptor they map to simply has no tree
  numbers of its own, so they get a `MESH_LABEL` and four empty tree columns. Only 2 rows failed
  outright. An empty tree column means "we couldn't find one", *not* "this concept sits outside the
  hierarchy" — don't treat blanks as a meaningful category.
- **No retries and no resume.** A network blip mid-run fails that row, and there's no way to pick
  up where a killed run left off; you re-run the whole thing. Nothing is cached to disk between
  runs either.
- **It hammers the NLM API.** Every row is at least one request, plus a SPARQL query per distinct
  top-level code. Don't drop `--delay` much below the default on a large file.
- **The output overwrites in place** with no confirmation, so pass `-o` if you want to keep the
  previous run. Pointing `-o` at the input file is refused outright — input and output are opened
  together, so that would truncate the input before a single row was read.

## If I come back to this

The obvious wins, in order: batch the top-level SPARQL lookups into one query instead of one per
code; cache the label lookups to disk so re-runs are cheap; add retry-with-backoff. Writing the
96 label-only concepts to their own file would also make them easier to work through by hand —
they have a descriptor, it just isn't in the tree, so they may need placing by another route.

`CLAUDE.md` in this directory has the full notes on the MeSH API's response shapes and the
fallback logic, which is the fiddly part.
