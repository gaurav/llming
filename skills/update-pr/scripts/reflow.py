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

Left alone: fenced code blocks, headings, blockquotes, table rows, and blank
lines. Each list item starts its own block, so bullets never merge.

Only needed for a body that is *already* wrapped — when writing a new one, just
don't wrap it.
"""

from __future__ import annotations

import re
import sys

BULLET = re.compile(r"^(\s*)([-*+]|\d+\.)\s")


def reflow(text: str) -> str:
    out: list[str] = []
    buf: list[str] = []
    in_fence = False

    def flush() -> None:
        if buf:
            out.append(" ".join(part.strip() for part in buf))
            buf.clear()

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
        elif line.lstrip().startswith(("#", ">", "|")):
            flush()
            out.append(line)
        elif BULLET.match(line):
            flush()  # a new list item is its own block
            buf.append(line.rstrip())
        else:
            buf.append(line.rstrip())
    flush()
    return "\n".join(out)


def _selftest() -> None:
    src = (
        "## Heading\n\n"
        "A paragraph that was\nwrapped across lines.\n\n"
        "- first bullet, itself\n  wrapped\n- second bullet\n\n"
        "```bash\ngh pr edit 1 \\\n    --body-file b.md\n```\n\n"
        "> quoted line\n"
    )
    got = reflow(src)
    assert "A paragraph that was wrapped across lines." in got
    assert "- first bullet, itself wrapped" in got
    assert "- second bullet" in got, "bullets must not merge"
    assert "gh pr edit 1 \\\n    --body-file b.md" in got, "fence must survive"
    assert "> quoted line" in got
    assert reflow(got) == got, "reflow must be idempotent"
    print("ok")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "--selftest":
        _selftest()
    else:
        for path in args:
            with open(path) as handle:
                flat = reflow(handle.read())
            with open(path, "w") as handle:
                handle.write(flat)
