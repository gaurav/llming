---
name: copilot-review
description: Work through the GitHub Copilot code-review comments on a pull request — triage each one, fix what's worth fixing, reply where a note is useful, and resolve the threads. Use when asked to address/handle/clear a Copilot review, go through Copilot's PR comments, or resolve Copilot review threads.
---

# copilot-review

Go through every **unresolved** GitHub Copilot review comment on a pull request. For each one:
decide whether it should be fixed, fix it if so, leave a reply when a reply would help a future
reader, and resolve the thread once it's handled. Copilot's review comments are inline
*pull-request review threads* (not issue comments), authored by the bot login
`copilot-pull-request-reviewer`.

## Operating mode

Work **autonomously** — don't ask the user to confirm routine fix/won't-fix decisions. Reserve the
escape hatches below for genuinely unclear cases, and don't over-engineer: apply the smallest
change that addresses the comment.

When a comment is genuinely ambiguous or would need a design decision you can't infer from the code
and PR context, do **not** stop to ask. Instead pick one:
- **Open a follow-up issue** describing the question, and reply to the thread linking it (`Tracked
  in #NNN.`). Resolve the thread only if the code question is now deferred deliberately.
- **Leave the thread unresolved** with a short reply explaining what's undecided, so the user can
  look at it later.

Only ask the user directly if you are hard-blocked (e.g. missing auth, can't determine the PR).

## Prerequisites

- `gh` authenticated (`gh auth status`). All GitHub reads/writes go through `gh api`.
- A local checkout on the PR's head branch (needed for the commit-and-push step). If the working
  tree is on a different branch or dirty in a conflicting way, sort that out first.

## Step 1 — Identify the PR and repo

- If the user passed a PR URL or number, use it. Otherwise use the PR for the current branch:
  `gh pr view --json number,url,headRefName,title,body`.
- Derive `OWNER` and `REPO` from the URL, or `gh repo view --json owner,name -q '.owner.login, .name'`.
- Read the PR **title and body** now. They record the author's intent and deliberate design
  decisions — a Copilot comment that contradicts a stated decision is usually a won't-fix.

## Step 2 — Fetch unresolved Copilot threads

Run the bundled script that lives next to this SKILL.md. It calls `gh api graphql`, pages through
all review threads, and prints one block per **unresolved Copilot** thread — each with the thread's
GraphQL node id, the top comment's `databaseId`, path, line, the `outdated` flag, the url, and the
full comment text plus any replies. Invoke it by its absolute path (the working directory is the
repo you're reviewing, not this skill's directory):

```bash
python3 ~/.claude/skills/copilot-review/scripts/list_copilot_threads.py "$OWNER" "$REPO" "$PR"
```

It already filters to `copilot-pull-request-reviewer` threads that are not resolved, and prints
`No unresolved Copilot review threads.` when there's nothing to do. An `isOutdated: true` thread
points at code that has since changed — read the *current* code to see whether it's still an issue
before acting; often it's already addressed, in which case resolve it (with a one-line reply only
if the reason isn't obvious).

## Step 3 — Triage each comment

Read the referenced file and the surrounding code. Classify as:

- **Fix** — a real correctness, clarity, safety, or maintainability improvement that fits the
  codebase's conventions and the PR's intent. Also fix trivially-correct nits (misleading log
  message, wrong variable name, missing guard).
- **Won't-fix** — the comment is wrong, guarded elsewhere, out of scope for this PR, purely
  stylistic against the repo's established convention, or contradicts a deliberate decision stated
  in the PR body or code comments.
- **Unclear** — needs a judgment call you can't ground in the code/PR. Use an escape hatch from
  *Operating mode* (open an issue, or leave unresolved with a note).

Prefer the smallest change that resolves the concern. Check the repo's `CLAUDE.md`/`AGENTS.md` for
conventions before choosing an approach. If Copilot raises the same issue in several threads, fix
the root cause once and resolve each thread (reply where the connection isn't obvious).

## Step 4 — Apply fixes and verify

- Make the edits. If a fix warrants a regression test and the repo has a test suite, add one.
- Verify before committing: run the repo's fast checks (tests for the touched area, linter,
  formatter) as documented in its `CLAUDE.md`. Don't resolve a thread whose fix doesn't pass.

## Step 5 — Commit & push

- Commit the fixes, following the repo's commit conventions (message style, required trailers). Use
  **multiple commits** when the fixes are independent — one per comment or per closely-related
  cluster — so each change is traceable to the comment that prompted it.
- Match any `Co-Authored-By` trailer to the model actually running this skill (not a default).
- Push to the PR's head branch so the PR reflects the fixes before you resolve threads.

## Step 6 — Reply (only when useful)

Reply when it helps a future reader — i.e. when **declining** a fix (state the reason), when the
resolution is **non-obvious** from the diff, or to **link a follow-up issue**. Stay silent when the
pushed fix speaks for itself. Post a reply with the thread's top-comment `databaseId`:

```bash
gh api --method POST \
  "/repos/$OWNER/$REPO/pulls/$PR/comments/$TOP_COMMENT_DB_ID/replies" \
  -f body="Your reply here."
```

Keep replies short and specific (what you changed and why, or why not).

## Step 7 — Resolve threads

Resolve a thread once it's handled: fixed-and-pushed, or a won't-fix you've replied to, or an
outdated thread you've confirmed is moot. Do **not** resolve threads you deliberately left open for
the user.

```bash
gh api graphql \
  -f query='mutation($threadId:ID!){ resolveReviewThread(input:{threadId:$threadId}){ thread{ id isResolved } } }' \
  -F threadId="$THREAD_ID"
```

## Step 8 — Summary

Report a compact per-thread summary: for each Copilot comment, whether it was **fixed** (with the
commit), **declined** (with the reason), **deferred** (issue link), or **left open**, and confirm
the push succeeded. Note any thread you couldn't resolve automatically.

## Notes

- Replies use the REST `.../comments/{id}/replies` endpoint keyed by the top comment's
  **`databaseId`** (an integer), while resolving uses the thread's **GraphQL node id** (the
  `PRRT_...` string). Don't mix them up.
- If Step 2 returns no unresolved Copilot threads, say so and stop — nothing to do.
- This skill only touches Copilot's threads. Leave human reviewers' comments alone unless the user
  says otherwise.
