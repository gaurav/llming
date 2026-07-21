---
name: wrap
description: Wrap up a piece of work — push outstanding branches, record durable lessons in the right agent/docs file, add missing tests, and suggest follow-up issues. Use when the user says "wrap up", "/wrap", "we're done here", or is finishing a work session.
---

Wrap up the work done in this session. Four things to do, in any order.

## 1. Push outstanding branches

Check every branch touched this session: `git status`, `git branch -vv`, and `git log --oneline @{u}..` for unpushed commits.

- Uncommitted changes that belong to the work: report them and ask whether to commit; do not commit silently.
- Committed but unpushed: push it, unless the user has said not to push unasked — in that case, report the branch and the commit count and stop.
- If a branch has no upstream, say so and ask before creating one.

## 2. Record durable lessons

Ask: did this session turn up something a future agent would need to be told again? Only non-obvious things — not what the code, git history, or existing docs already say.

Where it goes, in order of preference:

1. A `docs/` file for the source/subsystem, referenced from an agent file if it isn't already.
2. The nearest directory-specific `CLAUDE.md`.
3. The root `AGENTS.md` / `CLAUDE.md` — for repo-wide rules, and for information needed to understand how the code in this repo works that doesn't belong to any one directory.

Keep agent files small: prefer one line pointing at a docs file over a paragraph inline. If nothing durable came up, say so and move on — do not invent a lesson.

## 3. Add missing tests

Find the behavior this session changed that no test covers, and **write those tests** — this is work to do, not a list to propose. Run them.

- Default to writing them. Follow the repo's existing test conventions and put each one where that repo's layout says it goes.
- Ask first only when a test is genuinely large or complicated — it needs a heavyweight fixture, a full pipeline run, network access, or a big refactor to make the code testable. Name what makes it expensive and let the user decide.
- Skip a test whose only form would be flaky or meaningless — a timing benchmark with an arbitrary threshold, an assertion that just restates the implementation. Say you skipped it and why; don't write a bad test to fill the slot.
- If everything that changed is already covered, say so and move on.

## 4. Suggest follow-up issues

Loose ends, deferred fixes, things noticed but out of scope. One line each.

**Suggestions only — assume none of these will be done.** Do not file, create, or start any of them. Offer `gh issue create` and wait for the user to name the specific ones they want.

Keep the whole output short. Bullets, not prose.
