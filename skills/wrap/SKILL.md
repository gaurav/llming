---
name: wrap
description: Wrap up a piece of work — record durable lessons in the right agent/docs file, add missing tests, commit and push outstanding branches, and suggest follow-up issues. Use when the user says "wrap up", "/wrap", "we're done here", or is finishing a work session.
---

Wrap up the work done in this session. Four things to do, **in this order** — sections 1 and 2
write files, so committing before them would leave that work stranded.

## 1. Record durable lessons

Ask: did this session turn up something a future agent would need to be told again? Only
non-obvious things — not what the code, git history, or existing docs already say.

Where it goes, in order of preference:

1. A `docs/` file for the source/subsystem, referenced from an agent file if it isn't already.
2. The nearest directory-specific `CLAUDE.md`.
3. The root `AGENTS.md` / `CLAUDE.md` — for repo-wide rules, and for information needed to
   understand how the code in this repo works that doesn't belong to any one directory.

Keep agent files small: prefer one line pointing at a docs file over a paragraph inline. If nothing
durable came up, say so and move on — do not invent a lesson.

## 2. Add missing tests

Find the behavior this session changed that no test covers, and **write those tests** — this is work
to do, not a list to propose. Run them.

- Default to writing them. Follow the repo's existing test conventions and put each one where that
  repo's layout says it goes.
- Ask first only when a test is genuinely large or complicated — it needs a heavyweight fixture, a
  full pipeline run, network access, or a big refactor to make the code testable. Name what makes it
  expensive and let the user decide.
- Skip a test whose only form would be flaky or meaningless — a timing benchmark with an arbitrary
  threshold, an assertion that just restates the implementation. Say you skipped it and why; don't
  write a bad test to fill the slot.
- If everything that changed is already covered, say so and move on.

## 3. Commit and push

Do this **after** sections 1 and 2, so the lessons and tests they wrote are included.

Survey the repo with `git status` and `git branch -vv`. The latter lists every local branch with its
upstream and ahead/behind counts; a branch showing no `[origin/...]` marker simply has no upstream.
Only ask git for unpushed commits on branches that have one — `git log --oneline @{u}..` exits 128
with `fatal: no upstream configured` otherwise.

Invoking this skill is authorization to commit and push **the work of this session**:

- Commit the session's outstanding changes, following the repo's commit conventions, and push.
- **Anything not from this session** — stray edits, unrelated files, a dirty tree you didn't cause —
  gets reported and left alone. Ask before touching it.
- **Never push to `main` or the repo's default branch without asking**, even for session work. Say
  what would be pushed and wait.
- If a branch has no upstream, say so and ask before creating one.
- If the user has said not to push unasked, honour that: report each branch and its unpushed commit
  count, and stop.

## 4. Suggest follow-up issues

Loose ends, deferred fixes, things noticed but out of scope. One line each, numbered, so we can
reference them in follow-up conversation.

Naming something as a follow-up is a thinking tool, not a prediction — plenty of these turn out to
belong in the current PR once written down, and that's a good outcome, not a scope failure. Write
each one so it works either way: specific enough to file as an issue, specific enough to just do.

For each, say where it probably belongs, using the same bar as the `copilot-review` skill: fold it
into the current PR unless it is genuinely unrelated to this work, or needs enough design thinking
that doing it here would swamp the PR. "Somewhat awkward to do here" does not qualify.

**Do not file, create, or start any of them.** Offer `gh issue create` for the ones the user wants
tracked, and wait to be told which. If the user pulls one into the current PR instead, that is new
work — do it, then run section 3 again.

Keep the whole output short. Bullets, not prose.
