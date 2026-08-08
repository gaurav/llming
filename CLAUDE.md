This repository holds two unrelated kinds of thing, and the conventions below differ for each:

- **One-off scripts** — small tools solving a single problem, each in its own top-level directory
  (`lookup-mesh-tree-numbers/`, `process-babel-slurm-rules/`). Not worth a repo apiece.
- **Coding agent skills** — everything under `skills/`, kept here so it can be shared across
  machines. These are prose instructions for an agent, not programs.

## One-off scripts

When creating a Python script, create or update the corresponding CLAUDE.md file explaining the script.
All Python scripts should be runnable with `uv run`.
Use click to provide a simple CLI.
Use logging to provide progress information.
Use tqdm to provide progress bars and completion estimates on long-running loops.
Input and output files should be stored in the `data/` subdirectory.
When running scripts, use tee to write the output into `data/last-run.log`.

Tests, where a script has them, go in its `tests/` subdirectory. pytest is a dev dependency in the
root `pyproject.toml`, so `uv run pytest` from the repo root runs everything. Keep test fixtures out
of `data/` — that path is gitignored, and anything a test needs has to be committed.

## Skills

A skill is a directory under `skills/` containing a `SKILL.md` with YAML frontmatter (`name` and a
`description` saying when to use it). The conventions above are for one-off scripts and do **not**
apply: a skill has no CLI, no `data/` directory, and no run log.

Prefer a skill that is only `SKILL.md`. Before adding a helper script, check whether an existing
tool already does the job — `gh api graphql --paginate` with a `--jq` filter replaced a 95-line
Python helper in `skills/copilot-review/`, and a script that wraps a flag is a script that can
rot. If a skill does need one:

- Put it in the skill's `scripts/` subdirectory and make it runnable with `uv run`, declaring any
  dependencies in a PEP 723 header. Prefer the standard library so there are none.
- Reference it by a path relative to the skill directory. Never hardcode an install location like
  `~/.claude/skills/...` — the same skill gets used as a personal, project, and plugin skill.
- Skip click, logging, and tqdm. An agent invokes these non-interactively and reads stdout; plain
  arguments and plain output are easier for it to consume than a CLI framework's.
