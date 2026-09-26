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

The mirror image is prose promising a check the commands under it don't perform, or perform and
then walk past. `wrap`'s step 0 promised a `[origin/x: gone]` marker a plain `git fetch` cannot
produce; `update-pr`'s step 1 promised to catch a diverged head, first with commands that compared
nothing and then, once they did, with no instruction to stop. Prose reads as true because it
describes an intention, and an agent following it will narrate the check it was told about rather
than the one it ran. Read the block as if the surrounding sentences weren't there: what would it
actually tell you, and what does the skill do differently on each answer?

## Checking whether a skill fires

Session transcripts record every skill load as a `Skill` tool call, so a fire check is two greps:
sessions that did the thing the skill covers, and sessions that loaded the skill. A session in the
first list and not the second is a miss. The first grep only sees the `gh` CLI — an issue changed
through `gh api` or an MCP tool is not counted — so that list is a floor.

```bash
cd ~/.claude/projects
# github-issues
grep -lrE --include='*.jsonl' \
  '"command":"([^"]|\\")*gh issue (create|edit|close|reopen|comment)' . | sort
grep -lr --include='*.jsonl' '"skill":"github-issues"' . | sort
# github-milestones; repos/<owner>/<repo>/ keeps the gaurav/milestones repo itself from matching
grep -lrE --include='*.jsonl' \
  -e '"command":"([^"]|\\")*gh issue (create|edit)([^"]|\\")*(--milestone|-m )' \
  -e '"command":"([^"]|\\")*gh api ([^"]|\\")*repos/[^/" ]+/[^/" ]+/milestones' . | sort
grep -lr --include='*.jsonl' '"skill":"github-milestones"' . | sort
# pipe any list through this for each session's start time
while read -r f; do
  echo "$(grep -o -m1 -- '"timestamp":"[^"]*"' "./$f" | cut -d'"' -f4) $f"
done
```

- **Only sessions *started* after the install count.** The first run of the `github-issues` grep
  found about thirty sessions, all from before the skill existed. A file's mtime is the wrong date:
  it is when the session last wrote, and a session running across the install picks the skill up
  mid-session yet acted on plans made before it existed. Use each session's first timestamp.
- **Count per machine.** Transcripts stay on the machine that ran the session, and so does the
  install date, so run the greps on every machine against its own cutoff and add them up.
- **The paths come back as `-Users-…/<id>.jsonl`** with no leading `./`, so any command handed one
  bare reads it as an option: `xargs ls -lt` errors, and `grep` prints nothing, which looks like a
  session with no timestamp. Hence the `--` and the `./`.
- **`([^"]|\\")*`, not `[^"]*`.** The command field can contain a quoted argument before the `gh`
  call — a heredoc into `"$S/issue.md"`, a `sed -i '' 's/…/…/' "$f"` on the line above. A plain
  `[^"]*` stops at the first escaped quote and silently drops the session, which looks exactly like
  a session where the skill correctly had nothing to fire on. It was missing about a third of them.
