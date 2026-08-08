# vlmddiff

## Overview

Diffs two HEAL VLMD (variable-level metadata) JSON files variable by variable, matching them on a
stable ID rather than on array position.

The problem this solves: generic JSON diff tools (jsondiff, jsondiff.com) compare the `fields` array
positionally. When the two files order or size their variable lists differently, everything after the
first insertion reads as changed and the real edits are buried. Both VLMD files key their variables
by `name`, so a much better diff is available — match on `name`, then compare property by property.

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

The pair this was written for lives in `data/` and describes one study by two routes:

- **base** — a deterministic script produced a REDCap CSV, and the VLMD tool converted it.
- **revised** — a coworker took that same REDCap CSV, ran an LLM tool over it to fix problems, and
  emitted VLMD directly.

The shared REDCap CSV is in `data/` too, for reference. The script does not read it — see
Limitations.

### Output

Two files sharing `--output-prefix`:

- **`data/vlmd-diff.md`** — the review artifact. Document-level property changes, added and removed
  variables with their full JSON, then one section per changed property.
- **`data/vlmd-diff.csv`** — the complete backing record, one untruncated row per field-level
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
uv run vlmddiff.py --base data/a.json --revised data/b.json 2>&1 | tee data/last-run.log

uv run vlmddiff.py -b data/a.json -r data/b.json --output-prefix data/a-vs-b

# Treat nothing as a conversion artifact — everything lands in the main body.
uv run vlmddiff.py -b data/a.json -r data/b.json --artifact-property ''

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

## Known Issues & Limitations

- **No traceback to the REDCap CSV.** An earlier idea was to trace each VLMD variable back to its
  source row. It isn't needed: the revised file's `custom` block already carries the raw REDCap
  `Field Note` and `Text Validation Type OR Show Slider Number` columns, so "what did the source
  say?" is answerable from the revised file alone.
- **No schema validation.** The script does not check either file against the VLMD schema
  ([heal_json.json](https://github.com/uc-cdis/heal-platform-sdk/blob/master/heal/vlmd/schemas/heal_json.json),
  v0.3.2; the [older data-dictionary.json](https://github.com/HEAL/heal-metadata-schemas/blob/main/variable-level-metadata-schema/schemas/data-dictionary.json)
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
- `tests/test_vlmddiff.py`, `tests/conftest.py` — tests. `conftest.py` only puts the parent
  directory on `sys.path`, since `vlmddiff.py` is a plain script rather than an installed package.
- `tests/fixtures/base.json`, `revised.json` — the synthetic sample pair, used by every test.
- `tests/fixtures/expected.md`, `expected.csv` — the committed worked example, checked by
  `test_cli_output_matches_the_committed_example` so it can't go stale.

Not in git — study data, see above:

- `data/*.vlmd-generated-by-script.json` — base input.
- `data/*.vlmd-generated-by-llm-tool.json` — revised input.
- `data/*.redcap.csv` — the shared REDCap source, reference only.
- `data/vlmd-diff.md`, `data/vlmd-diff.csv` — the real outputs, for review elsewhere.
- `data/last-run.log` — output of the run that produced them.
