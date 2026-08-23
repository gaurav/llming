This repository holds two unrelated kinds of thing, and the conventions below differ for each:

- **One-off scripts** — small tools solving a single problem, each in its own top-level directory
  (`lookup-mesh-tree-numbers/`, `calendar-cleanup/`). Not worth a repo apiece. Most live on their
  own unmerged branch, so a top-level directory holding nothing but gitignored files — `data/`,
  `__pycache__/`, an emptied-out `tests/` — is a checked-out leftover, not an abandoned tool. Check
  `git branch -a` before concluding a tool is missing.
- **Coding agent skills** — everything under `skills/`, kept here so it can be shared across
  machines. These are prose instructions for an agent, not programs.

## README.md and CLAUDE.md

Both kinds of thing here are documented by a pair of files, and the split between them is the same
in each case.

`README.md` is the primary documentation, written for a human. It is allowed to get quite long, as
long as what someone needs first is at the top — what this is for, how to run it, what to be
careful about. `CLAUDE.md` takes the extraneous specifics that would bury that: API response
quirks, the shape of some fallback logic, and above all the gotchas that will save time on the next
visit. The test is roughly *when would I want to know this?* — before deciding to use the tool at
all, or only once already elbow-deep in the code. Neither file should restate the other.

## One-off scripts

When creating a Python script, create or update both files described above.
All Python scripts should be runnable with `uv run`.
Use click to provide a simple CLI.
Use logging to provide progress information.
Use tqdm to provide progress bars and completion estimates on long-running loops.
Input and output files should be stored in the `data/` subdirectory.
When running scripts, use tee to write the output into `data/last-run.log`.

Every script directory gets a `README.md` covering four things, in this order: what the tool is for,
how to run it (a copy-pasteable command line), any known issues or limitations to be careful about,
and possible next steps. Write it for someone returning to the tool after six months away — those
four should be readable in a couple of minutes, whatever else the file goes on to say.
Update it whenever the tool's behaviour or CLI changes.

Tests, where a script has them, go in its `tests/` subdirectory. pytest is a dev dependency in the
root `pyproject.toml`, so `uv run pytest` from the repo root runs everything. Keep test fixtures out
of `data/` — that path is gitignored, and anything a test needs has to be committed.

## Skills

A skill is a directory under `skills/` containing a `SKILL.md` with YAML frontmatter (`name` and a
`description` saying when to use it). The conventions above are for one-off scripts and do **not**
apply: a skill has no CLI, no `data/` directory, and no run log.

Skills do **not** get a README each — the frontmatter `description` already covers what the skill
does and when to use it, so a per-skill README would only restate it. Instead there is one shared
`skills/README.md` recording why each skill exists, what it's for, and where it might go next: the
things a `SKILL.md` has no room for because it is written for an agent, not for me. Add a section
there when adding a skill.

Prefer a skill that is only `SKILL.md`. Before adding a helper script, check whether an existing
tool already does the job — `gh api graphql --paginate` with a `--jq` filter replaced a 95-line
Python helper in `skills/copilot-review/`, and `npx prettier --prose-wrap never` replaced a
110-line Markdown unwrapper in `skills/update-pr/`. A script that wraps a flag is a script that can
rot, and both of those had already started to: the reimplementation loses on the edge cases the
real tool handles, which for anything file-shaped means silent corruption rather than a crash.
Reach for a script only when nothing installed does the job. If a skill does need one:

- Put it in the skill's `scripts/` subdirectory and make it runnable with `uv run`, declaring any
  dependencies in a PEP 723 header. Prefer the standard library so there are none.
- Reference it by a path relative to the skill directory. Never hardcode an install location like
  `~/.claude/skills/...` — the same skill gets used as a personal, project, and plugin skill.
- Skip click, logging, and tqdm. An agent invokes these non-interactively and reads stdout; plain
  arguments and plain output are easier for it to consume than a CLI framework's.
- Install skills onto a machine by symlinking the skill **directory** into `~/.claude/skills/`, not
  the `SKILL.md` inside it (`ln -s ~/code/llming/skills/update-pr ~/.claude/skills/update-pr`). A
  file symlink brings the prose and leaves the `scripts/` behind, so the skill's own relative path
  resolves to nothing on the machine that needs it. Editing through either path is the same file,
  so a script added on one machine is live everywhere the directory is linked.
