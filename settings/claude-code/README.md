# Claude Code

My [Claude Code](https://claude.com/claude-code) status line: one line under the input box showing
the git branch, how full the context window is, how much of the 5-hour and 7-day quotas is left,
and which model and effort level are running.

<!-- rumdl-disable MD013 -->

```text
main ⇡1 ♦ ctx 42% (84k) ♦ 5h: 96% until 6:10pm (3h 52m) ♦ 7d: 80% until Tue 8pm (3d 5h) ♦ Opus 5.5 [high]
```

<!-- rumdl-enable MD013 -->

## Install

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
- **Without a reset time, the quota clock shows a nonsense time** (the start of 1970, in local
  time). Claude Code has always sent one so far.

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

**Context**: `ctx 42% (84k)`, the share of the context window used, then the tokens used. No
maximum: the percentage already says it.

**Quotas**: `5h: 96% until 6:10pm (3h 52m)`, then the same for `7d:` with a day in place of the
time (`until Tue 8pm (3d 5h)`). The percentage is what's **left**, not what's used.

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
text (`(84k)`, `until …`) is dimmed. Every percentage is coloured by how much has been **used**:
green under 50%, yellow to 75%, orange to 90%, red above. That's true even where the number
shown is what's left, so the colour warns as the quota runs out.

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
