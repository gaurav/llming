# vlmddiff

Diffs two HEAL VLMD (variable-level metadata) JSON files variable by variable and writes a report
meant to be read on GitHub. It matches variables on `name` rather than on position in the `fields`
array, which is what makes it more useful than a generic JSON differ: jsondiff and friends compare
the array index by index, so one inserted variable makes everything after it read as changed and
the edits that matter are buried.

The report's real work is grouping. Identical `old → new` value pairs collapse into a single entry
with a count and the affected variables tucked into a `<details>`, so a rewrite that 349 variables
all made is something you read once. On the pair this was written for, 3885 field-level changes
came out as a 570-line document.

Two files are written, sharing a prefix: `<prefix>.md` is the report, `<prefix>.csv` is the
complete untruncated record behind it, one row per field-level change.

## Running it

```bash
cd vlmddiff
uv run vlmddiff.py -b data/<comparison>/base.json -r data/<comparison>/revised.json \
    2>&1 | tee data/<comparison>/last-run.log
```

`--base` and `--revised` are required and have no defaults — these are study data and this repo is
public, so a default would have named the study in the source. For the same reason `data/` is
gitignored here with nothing force-added, not even the run log.

With no `-o/--output-prefix`, the report is written as `vlmd-diff.md`/`.csv` beside `--base`.
`data/` holds one subdirectory per comparison, so that puts each report in with the files it
describes. Pass `-o` to name it something else.

Worth knowing: `--id-key` matches on a property other than `name`; `--artifact-property` sets which
properties are relegated to the appendix as conversion-tool noise rather than content edits, and
defaults to `title`, `custom`, `format`. `uv run vlmddiff.py --help` has the rest.

Tests run from the repo root with `uv run pytest`, or `uv run pytest vlmddiff` for just this one.
The pair in `tests/fixtures/` is synthetic and stands in for the real files.

## Watch out for

- **It diffs VLMD documents, not CSVs.** The REDCap CSV both dictionaries derive from is in `data/`
  for reference only; pointing this at two CSVs will not work.
- **Values compare exactly.** `{"enum": ["0","1"]}` against `{"enum": ["1","0"]}` reads as a change
  although both describe the same set, and a one-key edit inside `constraints` prints the whole
  object on both sides. Tolerable here because grouping collapses the repeats.
- **The appendix properties are a judgement call**, made by inspecting one specific pair of files.
  A different pair of conversion tools would need different `--artifact-property` values, and
  getting them wrong hides real edits in the appendix.
- **No schema validation.** The report says what differs between two files, never whether either is
  a valid VLMD document.
- **Large appendix sections are summarised, not listed** — over 20 distinct value pairs and you get
  a count instead. Without that the Markdown ran past the ~500 KB where GitHub stops rendering it.
  Substantive properties are never summarised, so this only ever hides conversion noise.

## If I come back to this

The open question is the input-file comparison: the LLM tool also emits a cleaned version of the
REDCap CSV, and diffing that against the original would show what the cleaning step did before any
VLMD was generated. That needs either a CSV differ this tool isn't, or a pass that converts the
cleaned CSV to VLMD first and reuses this — they answer different questions and the choice hasn't
been made.

After that: comparing `enum` values as sets rather than sequences, and diffing inside nested
objects instead of whole, would both cut noise if a future pair produces more of it than this one
did.

`CLAUDE.md` in this directory has the details — why each appendix property is there, the output
format, and the `data/` layout.
