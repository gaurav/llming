`README.md` has the install steps and each tool's settings in words. This file has the specifics.

## oh-my-posh

The config is `oh-my-posh/gaurav-custom.omp.json`. `~/.config/oh-my-posh` is a symlink to the
`oh-my-posh/` directory (not to `settings/`), so `~/.zshrc` points at a stable path.

### Previewing a change

Inside a shell that already runs oh-my-posh, `oh-my-posh print … --config X` **silently ignores
`--config`**. A session (`$POSH_SESSION_ID`) is tied to the first config path it rendered, which is
whatever `.zshrc` loaded. Edits to *that* file are picked up at the next prompt, but any other
path is ignored. Drop the session variable to preview a different file:

```bash
C="$PWD/oh-my-posh/gaurav-custom.omp.json"   # run from settings/
env -u POSH_SESSION_ID oh-my-posh print primary --config "$C" \
  --shell zsh --plain -w 100 --execution-time 4200 --status 1
env -u POSH_SESSION_ID oh-my-posh print transient --config "$C" --shell zsh --plain --status 1
```

`--execution-time` is in milliseconds. `--plain` removes the ANSI colours so the output can be read
as text. A JSON syntax error doesn't fail: it exits 0 and renders the default theme with a
`CONFIG PARSE ERROR` segment, which is easy to miss in a real terminal.

### Editing the JSON

- **Keep glyphs as `\uXXXX` escapes.** Nerd Font icons are private-use code points that most
  editors (and diffs) show as blanks. Some tools, including agent file-writing tools, write the raw
  characters even when given escapes. Re-serialise afterwards with
  `json.dumps(config, indent=2, ensure_ascii=True)`.
- **The schema for the installed version is local**, at
  `/opt/homebrew/opt/oh-my-posh/themes/schema.json`, and outranks remembered examples: config
  version 4 calls segment settings `options` (older themes online say `properties`), and the git
  segment has no `fetch_status` any more. It fetches status whenever the template uses it.
- The bundled `powerlevel10k_*.omp.json` themes in the same directory were the starting point.
  `powerlevel10k_classic` has the colours but no duration, filler, frame or transient prompt.

### How the layout works

- The prompt is three blocks: left-aligned line 1, right-aligned line 1 (which carries the
  `filler` dots, which only work on a right-aligned block), and a `"newline": true` block for
  line 2. `transient_prompt` is a top-level key, not a block.
- All the segments are `plain` style. The coloured bar comes from a shared `background`, with the
  arrows and frame drawn by `text` segments on a transparent background. Powerline style
  would put an arrow between every pair of segments. p10k classic uses thin separators within a
  group instead.
- **On the right, `executiontime` is first and always renders** (`always_enabled`, threshold 0),
  and every segment after it starts with its own leading `\u2039` (`‹`) separator. That way a hidden
  segment never leaves a doubled or dangling separator. Anything placed before `executiontime`, or
  a change that lets it hide, breaks this.
- The "took …, finished …" wording is decided in the template (`if ge .Ms 3000`), not by the
  segment's `threshold`. The finish time is sprig's `now`, which works inside any template, and
  Go's `3:04:05pm` layout.
- `executiontime` uses `"style": "austin"`: `450ms`, `4.2s`, `2m 10s`, `1h 2m 5s`. To compare
  the other styles, render each one at a few `--execution-time` values. The names don't tell you
  much.
- `status` appears twice. On the right it has the default `always_enabled: false`, so it only
  renders after a failure. On line 2 it has `always_enabled: true` and exists to colour the `▶`
  through `foreground_templates`.
- The right-aligned block has `"overflow": "hide"`. Without it, a line 1 that doesn't fit spills
  the right side onto a wrapped line.
- The path uses `"style": "powerlevel"` with `max_width` 30. `right_format` bolds and colours the
  last folder. The `display_root` option is off, so outside `~`, the leading `/` is dropped
  (`o/h/C/…`).
- The language segments use `display_mode: files`, so they only run in project folders. Python has
  `fetch_virtual_env: false`, because I don't want the venv name shown.

### Shell side

`ZSH_THEME` is empty, because oh-my-posh now draws the prompt in every terminal, Terminal.app
included. Leaving an Oh My Zsh theme set makes both set up a prompt, and oh-my-posh's overwrites
the other. `oh-my-posh init zsh` reads `transient_prompt` from the config and installs its zle
hook itself, so no extra zsh code is needed for the transient prompt.

## Terminal.app

The profile lives in `~/Library/Preferences/com.apple.Terminal.plist` under `Window Settings`.
The `.terminal` file here is that one dictionary, extracted as it is:

```bash
plutil -extract "Window Settings.Solarized Darker" xml1 \
  -o "terminal-app/Solarized Darker.terminal" ~/Library/Preferences/com.apple.Terminal.plist
```

Re-export after every change and commit it. Colours and the font are keyed archives stored as
base64 `<data>`, so a diff of the file shows nothing readable. To see what changed, decode it with
`plistlib`: each colour's archive has an `NSRGB` string of 0–1 floats.

**Change the profile through AppleScript while Terminal is running**, not by editing the plist
behind its back. Terminal keeps its profiles in memory and may write them back over the edit.
AppleScript changes save straight away:

```bash
osascript -e 'tell application "Terminal"' \
  -e 'set number of columns of settings set "Solarized Darker" to 120' -e 'end tell'
```

The scriptable properties are the window size, font name and size, antialiasing, and the cursor,
background, normal text and bold text colours (as 16-bit `{r, g, b}`). **The 16 ANSI colours and
the selection colour are not scriptable.** Change those in Terminal ▸ Settings, or quit Terminal
and round-trip the whole domain through `defaults`: `defaults export com.apple.Terminal x.plist`,
edit the colour archive's `NSRGB` string with `plistlib`, then `defaults import com.apple.Terminal
x.plist`. That goes through the preferences daemon (`cfprefsd`), whereas writing
`~/Library/Preferences/com.apple.Terminal.plist` directly can be undone by its cached copy.
