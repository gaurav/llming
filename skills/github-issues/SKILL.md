---
name: github-issues
description: Rules for changing a GitHub issue — when to edit an issue rather than comment on it, and whose issues must never be edited. Use before editing, retitling, relabelling, closing or commenting on any GitHub issue, and whenever an issue turns out to be out of date, superseded or partly done.
---

# github-issues

An issue is read later by someone deciding what to do, and they act on what it says. A correcting
comment three screens below a wrong description usually isn't read at all — so where the text can
be made right, making it right beats appending to it. That only applies to text that is mine to
rewrite, which is the other half of this rule.

## Establish authorship first

Before changing anything:

```bash
gh issue view <N> --repo <owner>/<repo> --json author,title,body,createdAt,url
gh api user --jq .login
```

Compare `author.login` against the logged-in user rather than against a name written down here —
that way a second GitHub account errs toward treating an issue as someone else's, which is the safe
direction. The user is `gaurav` on github.com.

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
text rather than adding to it.

## The issue is anyone else's

Never edit the body, the title or the labels. Not when the repository belongs to the user, not with
admin rights, not when the correction is obviously right. Leave a comment instead.

Write access is permission to administer the repository; it is not permission to rewrite what
someone else wrote. The same goes for the issues of a bot or of a former colleague whose account is
inactive — nobody is around to disagree with the edit, which is a reason for more caution, not less.
