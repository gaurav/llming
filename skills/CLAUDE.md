# skills/

`README.md` here records why each skill exists, what it's for, and where it might go next — see the
root `CLAUDE.md` for the convention and the split between the two files.

Nothing enforces that it keeps up. When adding, removing or substantially rethinking a skill, check
`README.md` still matches: both the one-line summaries at the top and the section for the skill
below them, since the summary carries a compressed version of the same reasoning and will quietly
contradict its section. This is the file most likely to go stale, because a `SKILL.md` can be
edited from end to end without ever opening it.

## Commands inside a `SKILL.md` get run, not read

Prose in a skill is advice an agent weighs; a shell command in a fenced block is something it runs
and believes the output of. So the bar is different: check that each command actually answers the
question the sentence above it asks. Three in one block of `update-pr` didn't, and every one failed
silently rather than erroring — a commit count standing in for a containment test, a `gh` lookup
resolving against the clone's default repo instead of the PR's base, a grep dropping the
`owner/repo` qualifier and querying the wrong repository. Each returns a confident answer about
something else. Run them against a real case before committing, especially the ones whose output
feeds a decision the agent then acts on.
