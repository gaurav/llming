---
name: sync-docs
description: Checks that the documentation files in a repository don't drift far from the source code. Also called a documentation audit.
---

This repository probably contains multiple documentation files in Markdown format with `.md` extension,
most of them in a `docs/` or `documentation/` folder as well as `README.md` files everywhere.
This includes coding agent skills or agent instructions like CLAUDE.md or AGENTS.md.

For every Markdown file, look for statements about how to use the software in this repository or
descriptions of how it works, then read the relevant parts of the source code to confirm that these
statements are still accurate. If not, modify the Markdown file so that it is accurate, although you
might want to warn the user first if the code might actually need to be fixed yet. You don't need
to check URLs or other resources outside of this repository.

Think also about strategies for simplifying documentation synchronization in the future: for example,
it may not be important to record the exact number of tests or files in particular directories, as
these will need to be updated often.

If there are many Markdown files, it might make sense to spawn subagents to work on each Markdown file
separately. If there are lots of unrelated changes that need to be committed to source control, it
might make sense to commit them in groups of related changes.
