# settings

Settings for the tools I use, kept here so a setup that works on one machine can be recreated on
another. Each tool's config files live in a subdirectory named after the tool, which is symlinked
into wherever that tool reads its config (or imported, for tools like Terminal.app that can't
read a file in place). So far there are two:

- [`oh-my-posh/`](#shell-prompt-oh-my-posh): my zsh prompt.
- [`terminal-app/`](#terminalapp-profile): my Terminal.app profile.

## Shell prompt (oh-my-posh)

My terminal prompt, `gaurav-custom` (a working name until it settles), as an
[oh-my-posh](https://ohmyposh.dev/) theme. It started as powerlevel10k's two-line "classic" layout
and is being tweaked from there. I moved because p10k is no longer getting new features
and is hard to configure by hand, while oh-my-posh is one JSON file. The
[Preferences](#preferences) section describes the prompt without any oh-my-posh syntax, so it can
be rebuilt in p10k or in whatever tool comes next.

```text
╭─ ~/D/llming/settings   main ⇡1 +1 !2 ?1 ······ took 2m 10s, finished 2:03:43am   ✘ 1   3.9.6 ─╮
╰─ ▸
```

It's not used on every machine yet. Machines where p10k already works keep it for now.

### Install

```bash
brew install jandedobbeleer/oh-my-posh/oh-my-posh
ln -s ~/Developer/llming/settings/oh-my-posh ~/.config/oh-my-posh
```

Then in `~/.zshrc`, set `ZSH_THEME=""` so Oh My Zsh doesn't draw a prompt of its own, and add
this at the end:

```zsh
eval "$(oh-my-posh init zsh --config ~/.config/oh-my-posh/gaurav-custom.omp.json)"
```

Open a new tab to see it. Editing the JSON takes effect at the next prompt, with no reload needed.
The glyphs need a [Nerd Font](https://www.nerdfonts.com/). Ghostty has the symbols built in.
Terminal.app needs one set as the profile's font (I use MesloLGS Nerd Font:
`brew install --cask font-meslo-lg-nerd-font`).

### Known issues

- **The colours need a 24-bit colour terminal.** Ghostty is one. Older versions of Terminal.app
  aren't, and there the hex colours come out approximated. If the grey-blue bar looks wrong in
  Terminal.app, check with `printf '\e[48;2;84;110;122m  #546E7A  \e[0m\n'`.
- **No instant prompt or background git status.** p10k draws a cached prompt before `.zshrc` has
  finished loading, and gets git status from a background daemon. oh-my-posh does neither: it runs
  `git status` before every prompt. That's quick in the repos I use, but it might not be in a huge
  one. The fix is the top-level `"async": true`, which draws the prompt at once and fills in
  slow segments afterwards.
- **The Python version can be the wrong one in uv projects.** The segment asks pyenv, then
  whichever `python3` is on the `PATH`. It never looks at a project's `.venv`, so a uv project
  pinned to another Python shows the system version instead.
- **The Java segment is untested.** There is no JDK on this machine yet, and macOS's
  `/usr/bin/java` placeholder may pop up an "install Java" dialog when the prompt runs it. That
  only happens in a folder with Java files.
- **On a narrow window, line 1's right side disappears** when it doesn't fit beside the left side.
  The red `▸` still shows that a command failed.
- **Testing changes from a shell that already runs oh-my-posh** needs care: see `CLAUDE.md`.

### Preferences

These are what to reproduce, whatever the tool.

**Line 1, left**, opening with a `╭─` frame:

1. A lightning bolt, only when running as root.
2. The current path, with `~` for home. Past 30 columns, the leading folders shrink to their first
   letter (`~/D/llming/settings/oh-my-posh`). The current folder is bold.
3. Git: branch, then `⇣n` behind / `⇡n` ahead, `*n` stashes, `+n` staged, `!n` unstaged, `?n`
   untracked. Each count is hidden when it is zero. The branch is green when the tree is clean and
   amber when there are changes.

The segments share one dark slate background. They are divided by small text-height angles, `›`
on the left and `‹` on the right (U+203A and U+2039). The full-height Nerd Font powerline arrows
looked too big. The left group ends in a solid powerline arrow (U+E0B0), and the right group
begins with its mirror image (U+E0B2).

**The gap** between the two sides is filled with dots (`·`) in a lighter grey-blue, the same as the
frame.

**Line 1, right**, from left to right:

1. How long the previous command took, which is always shown instead of a clock. A quick command
   shows just a dim duration (`450ms`). One taking **3 seconds or more** shows in amber, with its
   finish time: `took 2m 10s, finished 2:03:43am`.
2. `✘ n`, the exit code, only after a failed command.
3. The Python, Node or Java version, only inside a project in that language, with no virtualenv
   name.
4. `user@host`, only over SSH or as root.

A `─╮` frame closes the right side. If line 1 doesn't fit the window, the right side is hidden.

**Line 2**: `╰─ ▸`, a small filled triangle (a full-height `❯` is too tall). It is green, and red
after a failed command. The cursor goes after it.

**Transient prompt**: once a command runs, its two-line prompt collapses to just `▸ command`, so
the scrollback holds commands and output rather than repeated status lines.

**Colours**:

| Colour     | Hex       | Used for                                                 |
| ---------- | --------- | -------------------------------------------------------- |
| slate      | `#37474F` | segment background                                       |
| grey-blue  | `#546E7A` | frame, filler dots                                       |
| grey       | `#78909C` | separators                                               |
| soft cyan  | `#80DEEA` | path                                                     |
| near-white | `#ECEFF1` | current folder, `user@host`                              |
| green      | `#9CCC65` | clean git branch, staged count, `▸`                      |
| amber      | `#FFD54F` | changed git branch, unstaged count, slow duration, root  |
| dim grey   | `#90A4AE` | quick duration                                           |
| light blue | `#81D4FA` | untracked count                                          |
| red        | `#FF6E6E` | exit code, `▸` after a failure                           |
| brand      | various   | Python `#FFE873`, Node `#8CC84B`, Java `#F89820`         |

**In p10k**, `p10k configure` gets the layout close with these choices: *Classic* style,
*Unicode*, *Angled* separators, *Sharp* heads, *Flat* tails, *Two lines*, *Dotted* connection,
*Full* frame, *Transient prompt: Yes*, and no time. The rest needs `~/.p10k.zsh` edits:

- `POWERLEVEL9K_COMMAND_EXECUTION_TIME_THRESHOLD=0` to always show the duration.
- `POWERLEVEL9K_PROMPT_CHAR_OK_VIINS_CONTENT_EXPANSION='▸'` for the triangle.
- `POWERLEVEL9K_SHORTEN_STRATEGY=truncate_to_unique` for path shortening. It is close to, but not
  the same as, the first-letter shortening here.
- The colours above.

### Next steps

- Find the theme a real name to replace `gaurav-custom`.
- Bring over the `~/.p10k.zsh` from the Terminal.app machines, so both versions sit side by side.
- Once a JDK or a Python version manager is installed, check that the Java and Python segments
  report the right versions.

## Terminal.app profile

`terminal-app/Solarized Darker.terminal` is the Terminal.app profile I use with the prompt above:
Solarized colours on a black background, with MesloLGM Nerd Font 12 pt so the prompt's icons
render. Two colours differ from stock Solarized, because it assumes its own dark blue background
rather than black. Bright black is Solarized's base01 grey (`#586E75`) instead of the background
tone, which vanished on black. The selection is a lighter teal (`#2E4F5A`) so selected text
stands out. The window opens at 120×32, because line 1 of the prompt hides its right side when it
doesn't fit, which happened often at the default 80 columns. Inactive windows turn slightly
see-through and blurred.

`terminal-app/Solarized Dark.terminal` is the profile it was derived from, kept for comparison and
as a fallback. Solarized Darker differs from it in:

- the black background, replacing Solarized's `#042029`
- inactive windows at 70% opacity, not 50%
- the window size, cursor, bright black and selection colours described above

### Install

Install MesloLGM Nerd Font (`brew install --cask font-meslo-lg-nerd-font`), then double-click the
`.terminal` file. Terminal imports it and opens a window with it. To make it the default, go to
Terminal ▸ Settings ▸ Profiles, select it, and click **Default**.

### Known issues

- **Colours in the prompt look slightly darker than their hex values**, e.g. `#546E7A` measured
  as RGB(72, 99, 110). It's still the same hue, so it isn't the 256-colour fallback. It's most
  likely macOS colour management or the inactive-window transparency.

### Next steps

- Rename the profile if it drifts far from Solarized Darker.
