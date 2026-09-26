---
name: github-issues
description: Rules for changing a GitHub issue — when to edit an issue rather than comment on it, whose issues must never be edited, and when and how an issue may be closed. Use before filing, editing, retitling, relabelling, closing, reopening or commenting on any GitHub issue, and whenever an issue turns out to be out of date, superseded or partly done.
---

# github-issues

An issue is read later by someone deciding what to do, and they act on what it says. A correcting
comment three screens below a wrong description usually isn't read at all — so where the text can
be made right, making it right beats appending to it. That only applies to text that is mine to
rewrite, which is the other half of this rule.

These are rules for what to do unasked, not limits on the user. Where following one would leave the
open issues less usable than breaking it — a clear-cut duplicate is the usual case — put it to the
user and let them decide. An override is theirs to give, for that one issue; never infer it from
permissions or from an earlier yes.

## Establish authorship first

Before changing anything:

```bash
gh issue view <N> --repo <owner>/<repo> --json author,title,body,createdAt,url
gh api user --jq .login
```

Compare `author.login` against the logged-in user rather than against a name from anywhere else —
this file, a memory, the repository owner. That way a second GitHub account errs toward treating an
issue as someone else's, which is the safe direction. The `gh api user` comparison decides: if the
two logins differ, the issue is someone else's, even when the author is an account the user is
known to own.

## Before filing a new issue

Look for one that already covers it, closed ones included:

```bash
gh issue list --repo <owner>/<repo> --state all --search "<key terms> in:title,body" \
  --json number,state,title,author --jq '.[] | "#\(.number) \(.state) @\(.author.login) \(.title)"'
```

A match turns "file an issue" into "change an issue", and the rest of this skill decides how: edit
it if it is the user's, comment if it is not, reopen it if it was closed and the matter is live
again. A second issue about the same thing is the duplicate problem below, made on purpose.

Whether a new issue goes on a milestone, and which one, is decided by the `github-milestones`
skill — load it before filing.

## The issue is the user's own, and out of date

Edit the body so it is accurate. Do not append a comment that contradicts it, and do not narrate
the correction inside the body either — GitHub keeps the edit history, so the previous wording is
not lost and does not need preserving in the text.

Anything the issue still asks for that is *not* the same matter comes out into a new issue that
links back, rather than being left buried in a description now mostly about something else.
Splitting is the point: the edit is for what the issue is *about*, the new issue is for what is
left over.

Whether to ask first depends on the size of the edit, and that is a judgement to make, not a rule to
look up:

- **A minor edit — go ahead.** A correction, a note that part of it already happened in a named PR,
  more detail added to what is there. The issue still asks for the same thing once you are done.
  Make the edit, then tell the user in a line what changed.
- **A major edit — ask first.** The issue is about something different afterwards: investigation
  showed the bug has another shape than the one described, or a broad issue is becoming several
  narrower ones. Say what you are about to change and get the user's agreement before running
  `gh issue edit`. Anything split out into a new issue is on this side by definition, so describe
  the `gh issue create` alongside the edit and the user agrees to both halves at once.

An edit is visible to everyone watching the repository, and unlike a comment it replaces text rather
than adding to it, so when the size is a close call, ask.

## The issue is anyone else's

Never edit the body or the title. Not when the repository belongs to the user, not with admin
rights, not when the correction is obviously right. Leave a comment instead. Closing it is
restricted too — see *Closing an issue*.

Triage is fine: labels, assignees, the milestone, the project. It is what write access is for, it
is easy to undo, and it shows in the issue's timeline, so an author who thinks their bug has been
filed as unimportant can see that and say so. Reopening is fine on the same grounds, for an issue
or an unmerged pull request: the worst a wrong reopen does is put something back on the list, where
it gets looked at again — the opposite of what a wrong close does. Which milestone is the right one
is a separate question, answered by the `github-milestones` skill.

Write access is permission to administer the repository; it is not permission to rewrite what
someone else wrote. The same goes for the issues of a bot or of a former colleague whose account is
inactive — nobody is around to disagree with the edit, which is a reason for more caution, not less.

## Closing an issue

Whoever wrote the issue, the best way to close it is a closing keyword — `Closes #N` — in the
description of the pull request that resolves it. The claim that the issue is done then sits in
front of a reviewer next to the change that is supposed to have done it, the close happens only
when that PR merges, and the issue links to the PR that closed it. A direct close has none of that:
if it is wrong, nobody is placed to notice, and the issue is ignored until someone rediscovers it.

GitHub only acts on the keyword when the PR merges into the repository's default branch
(`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`). In a stacked PR or one aimed at
a release branch it closes nothing, so the keyword belongs on the PR that will eventually land on
the default branch; if there is none yet, tell the user the issue will need closing later.

Being asked to do the work that finishes an issue is not being asked to close it — the rules below
still decide how. Being told to close it is.

### The user's own issue

- **The work is in an unmerged PR — add the keyword, without asking.** Put `Closes #N` in that PR's
  description and tell the user in a line. That holds when it is a different PR from the one you
  are working on: an issue whose last item landed on another branch closes through that branch's
  PR. Never close the issue directly while the work is unmerged — if the PR is abandoned, the issue
  stays closed and nobody notices. A PR someone else opened is their text, as an issue would be:
  comment on it suggesting the keyword instead.
- **The work is already merged — close it with a comment.** This is the catch-up case: something
  finished the issue and nobody connected the two. If it came in through one of the user's own PRs
  that should have said `Fixes #N` and didn't, add the keyword to that PR's description so the fix
  names its issue — but GitHub only acts on the keyword at merge, so the issue still has to be
  closed by hand. Close it with a comment naming the commit or PR that finished it and why that
  finishes it, then tell the user in a line: the report is easy to miss, and the comment is the
  record. Go ahead when the case is straightforward — the issue asks for one thing and the merged
  change visibly does it. When it isn't — several asks, a fix you are inferring rather than seeing
  — say what you found and ask the user to confirm first. An issue that is only partly done gets a
  minor edit saying so, not a close.
- **Any other reason — ask first.** Obsolete, won't-do, superseded, a duplicate: these are judgement
  calls, and a wrong one hides the issue. Say why it should close and let the user decide. Only in
  a very obvious case — the code or feature the issue is about no longer exists — close it with a
  comment giving the reason and tell the user in a line.

### Anyone else's issue

Never close it directly — no `gh issue close`, no close button, not as a duplicate, not as
superseded, not as already fixed. The closing keyword is the only route. If there is no PR — the
issue looks obsolete, or fixed by something already merged — comment saying so and leave it open
for its author or the user to close. Adding a keyword to a merged PR is not a way around this: it
closes nothing.

### Duplicates

The issue that stays open is the most useful one, whoever wrote it. Never close the user's own
issue in favour of a thinner one merely because theirs is the one that may be closed. Comment on
the other issue suggesting it be closed in favour of the better one, with a link, and leave the
decision to its author or the user — or, if the case is clear-cut, ask the user whether to close it
now.
