# Claude Code

My [Claude Code](https://claude.com/claude-code) setup, in two files:

- `statusline.sh`, my status line: one line under the input box showing the git branch, how full
  the context window is, how much of the 5-hour and 7-day quotas is left, and which model and
  effort level are running.
- `user-CLAUDE.md`, the instructions I give Claude Code in every session on every machine: use
  several commits where they help, write PRs with the `update-pr` skill, leave merging a PR to me,
  after a human has reviewed it, and read a page I will act on from the site or my browser save,
  never through a fetch proxy. Installed as `~/.claude/CLAUDE.md`.

<!-- rumdl-disable MD013 -->

```text
main ⇡1 ♦ ctx 84k (42%) ♦ 5h: 96% until 6:10pm (3h 52m) ♦ 7d: 80% until Tue 8:00pm (3d 5h) ♦ Opus 5.5 [high]
```

<!-- rumdl-enable MD013 -->

## Install

The status line:

```bash
cp ~/Developer/llming/settings/claude-code/statusline.sh ~/.claude/statusline.sh
```

Then add this to `~/.claude/settings.json`, which isn't committed because it also holds
permissions and other per-machine settings:

```json
"statusLine": {
  "type": "command",
  "command": "bash ~/.claude/statusline.sh"
}
```

It needs `jq` and `git`. The status line updates after Claude's next message.

My instructions:

```bash
cp -i ~/Developer/llming/settings/claude-code/user-CLAUDE.md ~/.claude/CLAUDE.md
```

Claude Code reads `~/.claude/CLAUDE.md` at the start of every session, in every project, alongside
the project's own `CLAUDE.md`, so it takes effect in the next session. `-i` asks before overwriting:
a machine may already have one with additions of its own, so compare the two first.

## Known issues

- **The colours are tuned for my Solarized Darker Terminal.app profile** (see
  [`settings/README.md`](../README.md#terminalapp-profile)). Most of them are the terminal's own
  ANSI colours, so they follow whichever profile is in use. The model colours are 24-bit, so the
  terminal must support that.
- **Two yellows mean different things in a quota.** A yellow percentage means over half of it is
  used. A yellow countdown means it's being used faster than time is passing. Both can show at
  once. Pace colouring is on trial, and may yet be dropped or get its own colour or symbol.
- **The branch colour runs `git status` on every update.** That's quick in the repos I use, but
  might not be in a huge one.
- **`user-CLAUDE.md` defers to the [`update-pr`](../../skills/update-pr/SKILL.md) skill** on PR
  titles and descriptions, keeping only a two-line summary for a machine without it. Changing the
  skill's rules means checking that summary still agrees.

## Preferences

What to reproduce on another machine, with or without this script. Every part is separated by a
bright white `♦` (U+2666), which sits at the same height as capital letters in Meslo, unlike `◆`.

**Branch**, first. Its colour shows git state, since this is the only place I see it while Claude
is working:

| State                         | Shown as                                    |
| ----------------------------- | ------------------------------------------- |
| nothing uncommitted           | branch name in cyan                         |
| uncommitted changes           | branch name in yellow                       |
| commits not pushed / behind   | `⇡2` / `⇣1` after the name, in bright white |
| not a git repository          | `no branch`, dimmed                         |

No PR number: Claude Code already shows it.

**Context**: `ctx 84k (42%)`, the tokens used, then the share of the context window that is,
rounded to a whole percent. No maximum: the percentage already says it. Without a token count, or
with one small enough to round to `0k`, just the percentage (`ctx 42%`), since a count of `0k` would
be wrong: every session has some context.

**Quotas**: `5h: 96% until 6:10pm (3h 52m)`, then the same for `7d:` with the day before the
time (`until Tue 8:00pm (3d 5h)`). The percentage is what's **left**, not what's used. Without a
reset time, just the percentage.

**Pace**: the countdown in brackets turns yellow when I'm using a quota faster than its window is
passing, so at this rate it would run out before the reset. Precisely: when the percentage used is
more than 10 points above the percentage of the window gone. Without the margin it would fire on
the first few messages of every window. Otherwise the countdown is dimmed like the rest.

**Model and effort**: `Opus 5.5 [high]`. The model name is coloured by family, in lighter tints of
the Solarized colours (the originals were too dark): Opus pink `#E86AA0`, Sonnet blue `#62A4E6`,
Fable violet `#9696EB`, Haiku in plain text, anything else dimmed. `[high]` is my usual effort
level, so it takes the model's colour. **Any other level is bright white**, so an accidental change
stands out.

**Colours**, by role. The headers (`ctx`, `5h:`, `7d:`) and the `♦` are bright white. Supporting
text (`84k`, the brackets, `until …`) is dimmed. Every percentage is coloured by how much has been
**used**: green under 50%, yellow to 75%, orange to 90%, red above. That's true even where the
number shown is what's left, so the colour warns as the quota runs out.

Tried and rejected:

- **A background-coloured bar**, matching the oh-my-posh prompt, with the warning colours as
  chips. It looked worse than plain text on black.
- **Gold separators.** They were mistaken for warnings.
- **Effort as a row of dots** (`•••◦◦`). They looked nice, but I only ever use `high`, so all I need
  is to notice when it isn't.
- **A clickable PR link** (OSC 8). It works in Ghostty but not in Terminal.app, and Claude Code
  shows the PR anyway.

## Next steps

- Decide whether pace colouring is worth keeping, and whether it needs its own colour.
- Check the branch segment's speed in a large repo.
