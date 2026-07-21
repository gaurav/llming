---
name: wrap
description: Wrap up a piece of work — push outstanding branches, record durable lessons in the right agent/docs file, and suggest follow-up tests and issues. Use when the user says "wrap up", "/wrap", "we're done here", or is finishing a work session.
---

Wrap up the work done in this session. Three things to do, in any order.

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

## 3. Suggest follow-ups

Two short lists, suggestions only — do not create or write anything without approval:

- **Tests** worth adding for what changed: name the behavior that is currently uncovered, and where the test would go.
- **Follow-up issues**: loose ends, deferred fixes, things noticed but out of scope. One line each. Offer to file them with `gh issue create`.

Keep the whole output short. Bullets, not prose.
