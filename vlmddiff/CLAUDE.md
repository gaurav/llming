# vlmddiff

## Overview

Diffs two HEAL VLMD (variable-level metadata) JSON files variable by variable, matching them on a
stable ID rather than on array position.

The problem this solves: generic JSON diff tools (jsondiff, jsondiff.com) compare the `fields` array
positionally. When the two files order or size their variable lists differently, everything after
the first insertion reads as changed and the real edits are buried. Both VLMD files key their
variables by `name`, so a much better diff is available — match on `name`, then compare property by
property.

The output is meant to be committed and reviewed on GitHub.

## What the Script Does

### Input

Two VLMD JSON files, each a document with a `fields` list of variable objects. Any VLMD-shaped file
works; nothing is hardcoded to a particular schema version, and `--id-key` allows a different
matching property.

**None of the real inputs or outputs are committed, and `--base`/`--revised` have no defaults.**
They are study data and this repo is public; `data/` is gitignored repo-wide, and unlike the other
script directories here nothing in it is force-added — not even `last-run.log`, whose file paths
carry the study ID. That is also why the script has no default input paths, breaking the convention
elsewhere in this repo that a script runs with no arguments: the defaults would have named the
study. The worked example in `tests/fixtures/` is synthetic and stands in for the real pair.

`data/` is organised one subdirectory per comparison, because the same study has been looked at
more than one way. The shared REDCap CSV both start from stays at `data/` root.

`data/vlmd-file-comparison/` is the pair this was written for: one study by two routes.

- **base** — a deterministic script produced the REDCap CSV, and the VLMD tool converted it.
- **revised** — a coworker took that same REDCap CSV, ran an LLM tool over it to fix problems, and
  emitted VLMD directly.

`data/input-file-comparison/` is for the other direction: the coworker's LLM tool also emits a
cleaned version of the REDCap CSV itself, so diffing that against the original shows what the LLM
changed before any VLMD was generated — the cleaning step, rather than its downstream effect. The
cleaned CSV was reconstructed *after* the LLM tool had already generated its VLMD, by asking the
agent to work backwards, so it was not literally the VLMD's input. That comparison is done by
`redcapdiff.py`, not `vlmddiff.py` (see below). The original CSV there is byte-identical to the one
at `data/` root.

`data/sdk-vlmd-comparison/` converts both CSVs to VLMD with heal-sdk and diffs the results, to make
the pipeline reproducible. There are three diffs: script VLMD vs SDK(original), which differ only in
whitespace; SDK(original) vs SDK(clean), which are byte-identical; and SDK(clean) vs the LLM VLMD.
`data/cleanup-summary.md` writes up what they show. In short, the cleaned CSV explains none of the
LLM VLMD's edits. To convert:

```bash
uvx --python 3.13 --from heal-sdk heal vlmd extract --file_type redcap \
    --input_file data/x/in.redcap.csv --title "..." --output_dir data/x/out
```

- **The PyPI package is `heal-sdk`, not `heal` or `heal-platform-sdk`.** `heal` on PyPI is an
  unrelated placeholder project that pulls in litellm. `heal-sdk` needs Python 3.13.
- **heal-sdk silently drops rows with an invalid REDCap field type** (`datetime`, `any`), which is
  why it produces 1457 variables from 1465 CSV rows.
- **heal-sdk ignores the choices of a `truefalse` field** and always emits `["0", "1"]`. It also
  parses bare choice codes and strips whitespace itself, which is why the cleaned CSV converts
  identically.

### Output

Two files sharing `--output-prefix`, which defaults to `vlmd-diff` in `--base`'s own directory —
there is no fixed default path, because one would write every comparison's report to the same place:

- **`<prefix>.md`** — the review artifact. Document-level property changes, added and removed
  variables with their full JSON, then one section per changed property.
- **`<prefix>.csv`** — the complete backing record, one untruncated row per field-level
  change: `variable, section, property, change, base_value, revised_value, category`.

The Markdown groups identical `old → new` value pairs into one entry with a count and the affected
variable names in a collapsed `<details>`. That grouping is the entire point: on the current pair,
349 variables make the same `constraints` rewrite, and reading it once beats reading it 349 times.

A property whose changes are all one-offs renders as a `variable | from | to` table instead.

Three properties go in an appendix as conversion-tool conventions rather than content edits
(configurable via `--artifact-property`):

- `title` — the VLMD tool copies `description` into it; the LLM tool omits it. On the current pair
  base's `title` equalled its own `description` on 1413 of 1457 variables, so nothing is lost.
- `custom` — the LLM tool preserves the raw REDCap columns here; the VLMD tool does not.
- `format` — every difference is the same `"any"` → absent.

An appendix property with more than `APPENDIX_MAX_PATTERNS` (20) distinct value pairs is summarised
rather than listed. Without that, `title` and `custom` alone contribute ~2400 unique values and push
the Markdown past 500 KB, which is where GitHub stops rendering it. Substantive properties are never
summarised.

`tests/fixtures/expected.md` and `expected.csv` are a committed worked example, generated from the
synthetic pair beside them. They exercise every rendering path except the >20-pattern summary.

### Usage

```bash
# With no -o, the report lands beside --base, which is the subdirectory of the comparison it
# belongs to. Pass -o only to name it something other than vlmd-diff.
uv run vlmddiff.py -b data/vlmd-file-comparison/a.json -r data/vlmd-file-comparison/b.json \
    2>&1 | tee data/vlmd-file-comparison/last-run.log

# Treat nothing as a conversion artifact — everything lands in the main body.
uv run vlmddiff.py -b data/x/a.json -r data/x/b.json --artifact-property ''

uv run vlmddiff.py --help
```

Tests (the only directory here with any so far). pytest is a dev dependency in the repo-root
`pyproject.toml`, so no `--with` flags are needed:

```bash
uv run pytest              # from the repo root, runs every test in the repo
uv run pytest vlmddiff     # just this tool's

# Regenerate the committed worked example after changing the report format:
cd vlmddiff && uv run vlmddiff.py \
    -b tests/fixtures/base.json -r tests/fixtures/revised.json -o tests/fixtures/expected
```

### `redcapdiff.py`

It imports `diff_documents`, `index_fields`, `group_by_pattern`, `render_property_section` and
`render_variable_list` from `vlmddiff.py`, so changing those changes both reports. A CSV loads as
`{"fields": rows}`, and every cell is a string. `diff_field` only looks for a VLMD `section`, so
each change's section is filled from `Form Name` afterwards.

`classify()` checks in this order, and the first rule that matches wins:

1. **whitespace only** — `str.split()` gives the same tokens on both sides. It comes first so
   `"  "` → `""` doesn't count as emptied. `str.split()` also splits on NBSP, which is the one case
   the real pair has, and the report renders non-space whitespace as `<U+00A0>`, because otherwise
   both sides of the change would look identical.
2. **filled in** / **emptied** — one side is blank.
3. **choice formatting only** — only in `Choices, Calculations, OR Slider Labels`. Split on `|`,
   then on each item's first `,`. A bare `x` means `x, x`, which is how REDCap reads it.
4. **content change** — everything else.

On the real pair only the Choices column differs: 374 cells, split 349 filled in (every
`truefalse` field given `True, True | False, False`), 23 choice formatting, 1 whitespace and 1
content change. There are no tests with a committed expected output. The tests write tiny CSVs to
`tmp_path`.

## Known Issues & Limitations

- **No traceback to the REDCap CSV.** An earlier idea was to trace each VLMD variable back to its
  source row. It isn't needed: the revised file's `custom` block already carries the raw REDCap
  `Field Note` and `Text Validation Type OR Show Slider Number` columns, so "what did the source
  say?" is answerable from the revised file alone.
- **No schema validation.** The script does not check either file against the VLMD schema
  ([heal_json.json](https://github.com/uc-cdis/heal-platform-sdk/blob/master/heal/vlmd/schemas/heal_json.json),
  v0.3.2; the
  [older data-dictionary.json](https://github.com/HEAL/heal-metadata-schemas/blob/main/variable-level-metadata-schema/schemas/data-dictionary.json)
  is deprecated). It reports what differs, not what is valid.
- **Values compare exactly.** `{"enum": ["0","1"]}` vs `{"enum": ["1","0"]}` reads as a change even
  though both describe the same set. Fine for these files; worth revisiting if it produces noise.
- **Nested properties diff whole.** A one-key change inside `constraints` prints the whole object on
  both sides. Grouping makes this readable in practice, since the same whole-object change tends to
  repeat.
- **`--artifact-property` is judgement, not detection.** The defaults were chosen after inspecting
  this specific pair of files. A different pair of tools would need different values.
- No `tqdm`, unlike the other scripts in this repo: 1457 variables diff instantly, and the project
  convention asks for progress bars on long-running loops.

## Related Files

- `vlmddiff.py` — the script.
- `redcapdiff.py` — the REDCap CSV sibling, importing from `vlmddiff.py`.
- `tests/test_redcapdiff.py` — its tests.
- `tests/test_vlmddiff.py`, `tests/conftest.py` — tests. `conftest.py` only puts the parent
  directory on `sys.path`, since `vlmddiff.py` is a plain script rather than an installed package.
- `tests/fixtures/base.json`, `revised.json` — the synthetic sample pair, used by every test.
- `tests/fixtures/expected.md`, `expected.csv` — the committed worked example, checked by
  `test_cli_output_matches_the_committed_example` so it can't go stale.

Not in git — study data, see above:

- `data/*.redcap.csv` — the shared REDCap source both comparisons start from, reference only.
- `data/vlmd-file-comparison/*.vlmd-generated-by-script.json` — base input.
- `data/vlmd-file-comparison/*.vlmd-generated-by-llm-tool.json` — revised input.
- `data/vlmd-file-comparison/vlmd-diff.md`, `vlmd-diff.csv` — the real outputs, for review
  elsewhere.
- `data/vlmd-file-comparison/last-run.log` — output of the run that produced them.
- `data/input-file-comparison/*.redcap.csv`, `*_clean.redcap.csv` — the original and cleaned CSVs.
- `data/input-file-comparison/redcap-diff.md`, `redcap-diff.csv`, `last-run.log` — their comparison.
