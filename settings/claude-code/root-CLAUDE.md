Use multiple commits any time it will be helpful for future developers.

PR titles eventually become the release notes for my programs, so a PR title must concisely explain what that PR does. Write it as the line a reader should see in a changelog: describe the change and its effect, not the branch or the stage of work. Avoid placeholder titles like "Initial implementation of X" or "WIP". Update the title if the scope of the PR changes.

Similarly, the PR description is intended to be a long-term record of the final decisions, outcomes, gotchas, and follow-on work of a PR — not everything that was tried and failed. Those failed attempts belong in the commits, unless they are likely to come up again in the future, in which case document them in the source code, the documentation, or the AGENTS.md/CLAUDE.md files to prevent future developers from going in the wrong direction.
