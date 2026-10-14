Use multiple commits any time it will be helpful for future developers.

Write and update PR titles and descriptions with the `update-pr` skill. The short version: a PR
title becomes a line in my release notes, so it says what the change does, not the stage of work;
and anything worth knowing after the PR merges goes in the repo (code comments, docs, `CLAUDE.md` /
`AGENTS.md`), not only in the description.

Don't open a pull request unless I ask for one or clearly imply it; running `/update-pr` on a
branch with no PR counts as asking. A PR is a record on GitHub that outlives the decision to open
it: the branch may end up folded into another PR, or stay a branch. When you do open one, open it
as a **draft** (`gh pr create --draft`) and leave it one. I review every PR myself before marking
it ready, so never run `gh pr ready`.

An approach that was tried and failed belongs in the commit messages, or, if someone is likely to
try it again, in the code or docs, so they don't go the same wrong way.

Don't merge a pull request that no human has reviewed: the merge is mine to make, after a review.
Suggesting that two PRs be combined, so one long session can review both, is fine.

When a page carrying facts I will act on (a deadline, an eligibility rule, a price, a licence term)
refuses or challenges scripted fetches (a 403, 429 or 503, or a 200 "checking your browser" page),
try it directly once, then ask me to save it from my browser and read that copy. Don't route such
text through a third-party fetch proxy (Jina Reader and the like) or read it from an archived copy
(the Wayback Machine, a search engine's cache): a clause misread through someone else's rendering,
or read from an out-of-date snapshot, is worse than a delay. When there's no one to ask, as in a
subagent or a scheduled run, report the page as unread rather than carrying on without it. Say where
a fact was read from.

A site that turns every script away has said it doesn't want scripted visitors, so don't keep trying
user agents or headers, and don't send a proxy in your place. A proxy is fine for bulk background
reading (news coverage, mirrors, discussion threads) from sites that don't turn scripts away, where
saving each page by hand is tedious and nothing read there decides anything on its own. If a fact
read that way comes to decide something, read it again from the site or a browser save first.
