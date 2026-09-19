---
name: github-issues
description: Rules for changing a GitHub issue — when to edit an issue rather than comment on it, whose issues must never be edited, and how someone else's issue may be closed. Use before editing, retitling, relabelling, closing or commenting on any GitHub issue, and whenever an issue turns out to be out of date, superseded or partly done.
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

## The issue is the user's own, and out of date

Edit the body so it is accurate. Do not append a comment that contradicts it, and do not narrate
the correction inside the body either — GitHub keeps the edit history, so the previous wording is
not lost and does not need preserving in the text.

Anything the issue still asks for that is *not* the same matter comes out into a new issue that
links back, rather than being left buried in a description now mostly about something else.
Splitting is the point: the edit is for what the issue is *about*, the new issue is for what is
left over.

Say what you are about to change and get the user's agreement before running `gh issue edit`. An
edit to an issue is visible to everyone watching the repository, and unlike a comment it replaces
text rather than adding to it. The split-out issue needs the same agreement before
`gh issue create`: describe it alongside the edit, so the user agrees to both halves at once.

## The issue is anyone else's

Never change anything on it: not the body, the title or the labels, and not the assignees, the
milestone, the project or whether it is open — closing has its own section below, and reopening is
no different. Not when the repository belongs to the user, not with admin rights, not when the
correction is obviously right. Leave a comment instead.

Write access is permission to administer the repository; it is not permission to rewrite what
someone else wrote. The same goes for the issues of a bot or of a former colleague whose account is
inactive — nobody is around to disagree with the edit, which is a reason for more caution, not less.

## Closing an issue

Never close anyone else's issue directly — no `gh issue close`, no close button, not as a
duplicate, not as superseded, not as already fixed. A direct close is a silent one: if it is wrong,
nobody is placed to notice, and the bug is ignored until someone rediscovers it.

The way to close someone else's issue is a closing keyword — `Closes #N` — in the description of
the pull request that resolves it. The claim that the issue is done then sits in front of a
reviewer next to the change that is supposed to have done it, the close happens only when that PR
merges, and the issue links to the PR that closed it. If there is no PR — the issue looks
obsolete, or fixed by something already merged — comment saying so and leave it open for its author
or the user to close.

With duplicates, the issue that stays open is the most useful one, whoever wrote it. Never close
the user's own issue in favour of a thinner one merely because theirs is the one that may be
closed. Comment on the other issue suggesting it be closed in favour of the better one, with a
link, and leave the decision to its author or the user — or, if the case is clear-cut, ask the user
whether to close it now.

The user's own issue may be closed directly, on the same terms as an edit: say why it is finished
and get agreement first. A closing keyword in a PR is still the better route when a PR exists.
