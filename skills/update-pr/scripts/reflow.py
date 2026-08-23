#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Unwrap hard-wrapped Markdown so GitHub can reflow it.

GitHub renders a single newline inside a paragraph as a line break, so a body
wrapped at 80 columns keeps those wrap points on every screen width. This joins
each paragraph and each list item back into one continuous line.

    uv run scripts/reflow.py body.md      # rewrite in place
    uv run scripts/reflow.py --selftest   # check the tricky cases still hold

Left alone: fenced code blocks, indented (4-space) code blocks, headings —
both `#` and the underlined kind — blockquotes, table rows, and blank lines.
Each list item starts its own block, so bullets never merge, and a block keeps
the indentation of its first line, so nested lists stay nested. A line ending
in two spaces is an intentional break and ends its block.

Only needed for a body that is *already* wrapped — when writing a new one, just
don't wrap it.
"""

from __future__ import annotations

import re
import sys

BULLET = re.compile(r"^(\s*)([-*+]|\d+\.)\s")
SETEXT = re.compile(r"^ {0,3}(=+|-+)\s*$")  # the `Title` / `=====` heading underline


def reflow(text: str) -> str:
    out: list[str] = []
    buf: list[str] = []
    in_fence = False

    def flush() -> None:
        if buf:
            # buf[0] keeps its indent — it is what marks a nested list item.
            out.append(" ".join([buf[0]] + [part.strip() for part in buf[1:]]))
            buf.clear()

    def add(line: str) -> None:
        hard_break = line.endswith("  ")
        buf.append(line if hard_break else line.rstrip())
        if hard_break:
            flush()  # two trailing spaces are a deliberate line break

    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            flush()
            in_fence = not in_fence
            out.append(line)
        elif in_fence:
            out.append(line)
        elif not line.strip():
            flush()
            out.append("")
        elif line.lstrip().startswith(("#", ">", "|")) or SETEXT.match(line):
            flush()  # a setext underline lands right after the line it underlines
            out.append(line)
        elif BULLET.match(line):
            flush()  # a new list item is its own block
            add(line)
        elif not buf and line.startswith("    "):
            out.append(line)  # indented code block — only ever starts a block
        else:
            add(line)
    flush()
    return "\n".join(out)


def _selftest() -> None:
    src = (
        "## Heading\n\n"
        "Underlined heading\n===\n\n"
        "A paragraph that was\nwrapped across lines.\n\n"
        "- first bullet, itself\n  wrapped\n"
        "  - nested bullet, also\n    wrapped\n"
        "- second bullet\n\n"
        "    gh pr edit 1 \\\n        --body-file b.md\n\n"
        "```bash\ngh pr edit 1 \\\n    --body-file b.md\n```\n\n"
        "address line one  \naddress line two\n\n"
        "> quoted line\n"
    )
    got = reflow(src)
    assert "A paragraph that was wrapped across lines." in got
    assert "Underlined heading\n===" in got, "setext heading must not merge"
    assert "- first bullet, itself wrapped" in got
    assert "  - nested bullet, also wrapped" in got, "nesting must survive"
    assert "- second bullet" in got, "bullets must not merge"
    assert "    gh pr edit 1 \\\n        --body-file b.md" in got, "indented code"
    assert "gh pr edit 1 \\\n    --body-file b.md" in got, "fence must survive"
    assert "address line one  \naddress line two" in got, "hard break must survive"
    assert "> quoted line" in got
    assert reflow(got) == got, "reflow must be idempotent"
    print("ok")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--selftest"]:
        _selftest()
    elif not args:
        sys.exit("usage: reflow.py FILE... | --selftest")
    else:
        for path in args:
            with open(path) as handle:
                flat = reflow(handle.read())
            with open(path, "w") as handle:
                handle.write(flat)
