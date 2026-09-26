# settings

Settings for the tools I use, kept here so a setup that works on one machine can be recreated on
another. Each tool's config files live in a subdirectory named after the tool, which is symlinked
into wherever that tool reads its config. So far there is one:

- [`oh-my-posh/`](#shell-prompt-oh-my-posh): my zsh prompt.

## Shell prompt (oh-my-posh)

My terminal prompt, `gaurav-custom` (a working name until it settles), as an
[oh-my-posh](https://ohmyposh.dev/) theme. It started as powerlevel10k's two-line "classic" layout
and is being tweaked from there. I moved because p10k is no longer getting new features
and is hard to configure by hand, while oh-my-posh is one JSON file. The
[Preferences](#preferences) section describes the prompt without any oh-my-posh syntax, so it can
be rebuilt in p10k or in whatever tool comes next.

```text
╭─  ~/Developer/llming   main ⇡1 +1 !2 ?1 ··················· ✘ 1  4s   14:02:11  ─╮
╰─ ❯
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
- **Durations are rounded.** A command that takes 3600.5 s shows as `1h`.
- **Testing changes from a shell that already runs oh-my-posh** needs care: see `CLAUDE.md`.

### Preferences

These are what to reproduce, whatever the tool.

**Line 1, left**, opening with a `╭─` frame:

1. The OS icon.
2. A lightning bolt, only when running as root.
3. The full current path, with `~` for home.
4. Git: branch, then `⇣n` behind / `⇡n` ahead, `*n` stashes, `+n` staged, `!n` unstaged, `?n`
   untracked. Each count is hidden when it is zero.

The segments share one dark grey-blue background, divided by thin powerline separators (Nerd
Font U+E0B1 on the left side, U+E0B3 on the right). The left group ends in a solid powerline
arrow (U+E0B0), and the right group begins with its mirror image (U+E0B2).

**The gap** between the two sides is filled with dots (`·`) in that same grey-blue.

**Line 1, right**, from left to right:

1. `✘ n`, the exit code, only after a failed command.
2. The previous command's duration, only if it took **3 seconds or more**. It uses the largest
   units that fit: `4s`, `2m 5s`, `1h`.
3. `user@host`, only over SSH or as root.
4. A 24-hour `HH:MM:SS` clock.

A `─╮` frame closes the right side.

**Line 2**: `╰─ ❯`. The `❯` is yellow-green, and red after a failed command. The cursor goes after
it.

**Transient prompt**: once a command runs, its two-line prompt collapses to just `❯ command`, so
the scrollback holds commands and output rather than repeated status lines.

**Colours**:

| Colour               | Hex       | Used for                                                  |
| -------------------- | --------- | --------------------------------------------------------- |
| grey-blue            | `#546E7A` | segment background, frame, filler dots                    |
| cyan                 | `#26C6DA` | OS icon, path, clock, separators                          |
| yellow-green         | `#D4E157` | git branch and ahead/behind, `❯`, `user@host`             |
| amber                | `#FFD54F` | staged and unstaged counts, duration, root bolt           |
| light blue           | `#81D4FA` | untracked count                                           |
| red                  | `#FF5252` | exit code, `❯` after a failure                            |

**In p10k**, `p10k configure` gets close with these choices: *Classic* style, *Unicode*, *Dark*
colour, *24-hour* time, *Angled* separators, *Sharp* heads, *Flat* tails, *Two lines*, *Dotted*
connection, *Full* frame, *Transient prompt: Yes*. The status segment and 3 s duration
threshold are p10k's defaults already.

### Next steps

- Try path shortening. The `powerlevel` path style with a `max_width` (both are options on the
  `path` segment) should truncate deep paths the way p10k does.
- Bring over the `~/.p10k.zsh` from the Terminal.app machines, so both versions sit side by side.
- Add language segments (Python virtualenv, Node version) to the right side if I miss them. p10k
  shows these by default.
