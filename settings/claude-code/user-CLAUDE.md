Use multiple commits any time it will be helpful for future developers.

Write and update PR titles and descriptions with the `update-pr` skill. The short version: a PR
title becomes a line in my release notes, so it says what the change does, not the stage of work;
and anything worth knowing after the PR merges goes in the repo (code comments, docs, `CLAUDE.md` /
`AGENTS.md`), not only in the description.

An approach that was tried and failed belongs in the commit messages, or, if someone is likely to
try it again, in the code or docs, so they don't go the same wrong way.

Don't merge a pull request that no human has reviewed: the merge is mine to make, after a review.
Suggesting that two PRs be combined, so one long session can review both, is fine.
