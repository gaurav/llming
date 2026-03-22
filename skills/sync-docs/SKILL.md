---
name: sync-docs
description: Checks that the documentation files in a repository don't drift far from the source code. Also called a documentation audit.
---

This repository probably contains multiple documentation files in Markdown format with `.md` extension,
most of them in a `docs/` or `documentation/` folder as well as `README.md` files everywhere.

For every Markdown file, look for statements about how to use the software in this repository or
descriptions of how it works, then read the relevant parts of the source code to confirm that these
statements are still accurate. If not, modify the Markdown file so that it is accurate, although you
might want to warn the user first if the code might actually need to be fixed yet. You don't need
to check URLs or other resources outside of this repository.

If there are many Markdown files, it might make sense to spawn subagents to work on each Markdown file
separately.
