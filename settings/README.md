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
╰─ ▶
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
Terminal.app needs one set as the profile's font (I use MesloLGM Nerd Font:
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
  The red `▶` still shows that a command failed.
- **Testing changes from a shell that already runs oh-my-posh** needs care: see `CLAUDE.md`.

### Preferences

These are what to reproduce, whatever the tool.

**A blank line** comes before the prompt, separating it from the last command's output. It goes
when the prompt collapses (see *Transient prompt*), and a new window doesn't start with one.

**Line 1, left**, opening with a `╭─` frame:

1. A lightning bolt, only when running as root.
2. The current path, with `~` for home. Past 30 columns, the leading folders shrink to their first
   letter (`~/D/llming/settings/oh-my-posh`). The current folder is bold.
3. Git: branch, then `⇣n` behind / `⇡n` ahead, `*n` stashes, `+n` staged, `!n` unstaged, `?n`
   untracked. Each count is hidden when it is zero.

The segments share one background bar. They are divided by small text-height angles, `›`
on the left and `‹` on the right (U+203A and U+2039). The full-height Nerd Font powerline arrows
looked too big. The left group ends in a solid powerline arrow (U+E0B0), and the right group
begins with its mirror image (U+E0B2).

**The gap** between the two sides is filled with dots (`·`) in the frame colour.

**Line 1, right**, from left to right:

1. How long the previous command took, which is always shown instead of a clock. A quick command
   shows just the duration (`450ms`). One taking **3 seconds or more** is highlighted and gains its
   finish time: `took 2m 10s, finished 2:03:43am`.
2. `✘ n`, the exit code, only after a failed command.
3. The Python, Node or Java version, only inside a project in that language, with no virtualenv
   name.
4. `user@host`, only over SSH or as root.

A `─╮` frame closes the right side. If line 1 doesn't fit the window, the right side is hidden.

**Line 2**: `╰─ ▶`, a filled triangle. `❯` was too tall, and the small `▸` hard to spot. It is
in the prompt colour (orange in every palette), used nowhere else so the live prompt stands out,
and in the error colour after a failed command.
The cursor goes after it.

**Transient prompt**: once a command runs, its two-line prompt collapses to just `▶ command` in
muted green, or muted red if it failed. The blank line before it goes too. The scrollback holds
commands and output rather than repeated status lines, and only the live prompt is bright, while the
colour still makes old prompts easy to find.

**Colours** are chosen by role. All text on the bar is **one colour**. Colour is kept for things
worth noticing:

| Role       | Used for                                                            |
| ---------- | ------------------------------------------------------------------- |
| `bar`      | segment background                                                  |
| `text`     | everything on the bar: path, branch, duration, versions, user@host  |
| `sep`      | the `›` / `‹` separators                                            |
| `frame`    | `╭─`, `─╮`, `╰─` and the filler dots                                |
| `prompt`   | the live `▶`                                                        |
| `error`    | exit code, live `▶` after a failure                                 |
| `warn`     | slow duration, unstaged count, root bolt                            |
| `ok`       | staged count                                                        |
| `info`     | untracked count                                                     |
| `old_ok`   | `▶` in the scrollback                                               |
| `old_err`  | `▶` in the scrollback after a failure                               |

The theme has several palettes that fill these roles, all meant for a black background. The
default is *tokyo-night*. The others are *charcoal* (neutral greys), *gruvbox* (warm),
*catppuccin* (pastel) and *lean* (no bar, text straight on black). `export POSH_PALETTE=<name>`
switches the current shell to another, from its next prompt.
`zsh ~/.config/oh-my-posh/preview-palettes.zsh` draws the prompt in every palette so they can be
compared.

**In p10k**, `p10k configure` gets the layout close with these choices: *Classic* style,
*Unicode*, *Angled* separators, *Sharp* heads, *Flat* tails, *Two lines*, *Dotted* connection,
*Full* frame, *Transient prompt: Yes*, and no time. The rest needs `~/.p10k.zsh` edits:

- `POWERLEVEL9K_COMMAND_EXECUTION_TIME_THRESHOLD=0` to always show the duration.
- `POWERLEVEL9K_PROMPT_CHAR_OK_VIINS_CONTENT_EXPANSION='▶'` for the triangle.
- `POWERLEVEL9K_SHORTEN_STRATEGY=truncate_to_unique` for path shortening. It is close to, but not
  the same as, the first-letter shortening here.
- The colours above.

### Next steps

- Find the theme a real name to replace `gaurav-custom`.
- Live with *tokyo-night* for a while. It was the clear first pick, but if it stops working for
  me, *charcoal* and *gruvbox* were the runners-up to try next (`export POSH_PALETTE=charcoal`).
- Check the git segment's speed in a large repo. If it lags, set the top-level `"async": true`.
- Bring over the `~/.p10k.zsh` from the Terminal.app machines, so both versions sit side by side.
- Once a JDK or a Python version manager is installed, check that the Java and Python segments
  report the right versions.

## Terminal.app profile

`terminal-app/Tokyo Night Darker.terminal` is the Terminal.app profile I use, and the default. Its
16 colours match the prompt's default *tokyo-night* palette, so `ls`, `git diff` and the like look
consistent with the prompt. The colours come from
[tokyonight.nvim](https://github.com/folke/tokyonight.nvim)'s "night" terminal colours, on a
black background. As with Solarized below, bright black is changed: Tokyo Night's `#414868`
nearly vanishes on black, so it uses the comment grey `#565F89` instead. The selection is
`#33467C`, and text and cursor are `#C0CAF5`. Everything else (font, size, transparency) is
copied from Solarized Darker.

`terminal-app/Solarized Darker.terminal` was the first profile I used with the prompt, and is kept
as a fallback:
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

Install MesloLGM Nerd Font (`brew install --cask font-meslo-lg-nerd-font`), then double-click a
`.terminal` file. Terminal imports it and opens a window with it. To make it the default, go to
Terminal ▸ Settings ▸ Profiles, select it, and click **Default**.

### Known issues

- **Colours in the prompt look slightly darker than their hex values**, e.g. `#546E7A` measured
  as RGB(72, 99, 110). It's still the same hue, so it isn't the 256-colour fallback. It's most
  likely macOS colour management or the inactive-window transparency.

### Next steps

- Decide whether to keep the Solarized profiles now that Tokyo Night Darker is the default.
- Give Tokyo Night Darker a better name if it drifts from Tokyo Night. If I switch prompt palette,
  make a matching Terminal profile the same way (see `CLAUDE.md`).
