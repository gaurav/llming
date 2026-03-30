# annual-review

A two-script pipeline for generating an annual GitHub activity review. It downloads all PRs and software releases you were involved in during the review period (April 1 – March 31), lets you group them into goals, and produces a Markdown document ready to fill in with narrative.

## How it works

```
get_github_outputs.py  →  data/github_outputs.csv  →  [annotate goals]  →  generate_review.py  →  data/annual_review.md
```

1. **Fetch** — `get_github_outputs.py` queries GitHub for PRs where you are the author or assignee, and any GitHub Releases you published, during the review period. Results are written to `data/github_outputs.csv` sorted by date.

2. **Annotate** — Open the CSV and fill in the `Goal` column. Rows with the same goal name will be grouped together in the output document. Leave the column blank for low-priority items — they appear in an `## Other` section at the end.

3. **Generate** — `generate_review.py` reads the annotated CSV and produces `data/annual_review.md`: one section per goal, with a narrative placeholder and individual PRs/releases as bullet items.

4. **Write** — Fill in the narrative under each goal heading in the Markdown file.

## Setup

### Authentication

The scripts use your existing `gh` CLI credentials automatically:

```bash
gh auth login   # if not already authenticated
```

If you don't have the `gh` CLI, create a `.env` file instead:

```bash
cp .env.example .env
# Edit .env and set GITHUB_TOKEN and GITHUB_USERNAME
```

Required token scopes: `repo` (read), `read:org`.

### Goals config (optional)

Edit `goals.toml` to pre-populate the `Goal` column based on which repos a PR or release belongs to. This saves most of the manual annotation work.

```toml
[goals]
"Translator Infrastructure" = [
  "NCATSTranslator",           # matches all repos in this org
  "helxplatform/dug",          # matches one specific repo
]
"Phylogenetics" = [
  "phyloref/klados",
  "phyloref/phyx.js",
]
```

- An org name (no `/`) matches any repo in that org.
- A `org/repo` entry matches exactly that repo and takes priority over an org-level rule.
- Rows with a goal already set are never overwritten.

## Running the pipeline

```bash
cd annual-review/

# Step 1: download PRs and releases (defaults to current review period)
uv run get_github_outputs.py -u YOUR_GITHUB_USERNAME 2>&1 | tee data/last-run.log

# Step 2: apply goals.toml to pre-fill the Goal column
uv run get_github_outputs.py --apply-goals 2>&1 | tee data/last-run.log

# Step 3: open data/github_outputs.csv and fill in remaining Goal cells

# Step 4: generate the Markdown template
uv run generate_review.py 2>&1 | tee data/last-run.log

# Step 5: open data/annual_review.md and write narrative under each goal
```

Set `GITHUB_USERNAME` in `.env` to skip the `-u` flag on every run.

### Specifying a date range

The default period is automatically calculated: before April 1 it uses the just-ended April–March period; on or after April 1 it starts the new one. Override with:

```bash
uv run get_github_outputs.py --start 2024-04-01 --end 2025-03-31
uv run generate_review.py    --start 2024-04-01 --end 2025-03-31
```

### Updating goals without re-downloading

After editing `goals.toml`, apply the new mappings to the existing CSV in place — no GitHub API calls needed:

```bash
uv run get_github_outputs.py --apply-goals 2>&1 | tee data/last-run.log
```

### Testing releases only

To re-fetch releases without re-downloading all PRs (useful after fixing a bug):

```bash
uv run get_github_outputs.py --releases-only --releases-output data/github_releases.csv
```

## Output format

```markdown
# Annual Review 2025–2026

## Goal Name

> [Your narrative here]

- [org/repo#123: PR Title (merged Mar 5, 2026)](https://github.com/...)
- [org/repo v1.2.0: Release Title (released Nov 10, 2025)](https://github.com/...)

## Other

> [Your narrative here]

- ...
```

Within each goal section, releases are listed before PRs, both sorted oldest-to-newest.

## Files

| File | Description |
|------|-------------|
| `get_github_outputs.py` | Downloads PRs and releases from GitHub, writes CSV |
| `generate_review.py` | Reads annotated CSV, writes Markdown template |
| `goals.toml` | Repo-to-goal mapping config (edit this) |
| `.env.example` | Template for GitHub credentials |
| `data/github_outputs.csv` | Generated CSV — gitignored |
| `data/annual_review.md` | Generated Markdown — gitignored |
| `data/last-run.log` | Output from the most recent run — gitignored |
