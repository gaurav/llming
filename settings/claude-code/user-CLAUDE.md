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
