Use multiple commits any time it will be helpful for future developers.

Write and update PR titles and descriptions with the `update-pr` skill. The short version: a PR
title becomes a line in my release notes, so it says what the change does, not the stage of work;
and anything worth knowing after the PR merges goes in the repo (code comments, docs, `CLAUDE.md` /
`AGENTS.md`), not only in the description.

An approach that was tried and failed belongs in the commit messages, or, if someone is likely to
try it again, in the code or docs, so they don't go the same wrong way.

Don't merge a pull request that no human has reviewed: the merge is mine to make, after a review.
Suggesting that two PRs be combined, so one long session can review both, is fine.

When a page carrying facts I will act on (a deadline, an eligibility rule, a price, a licence term)
refuses scripted fetches, try it directly once, then ask me to save it from my browser and read that
copy. Don't route such text through a third-party fetch proxy (Jina Reader and the like): a clause
misread through someone else's rendering is worse than a delay. A site that answers every script
with 403 has said it doesn't want scripted visitors, so don't keep trying user agents or headers
either. A proxy is fine for bulk background reading (news coverage, mirrors, discussion threads)
where saving each page by hand is tedious and nothing read there decides anything on its own. Say
where a fact was read from.
