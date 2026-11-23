`README.md` has the install steps and each tool's settings in words. This file has the specifics.

Every machine shares these docs, so don't describe one machine's state ("cloned on this machine",
"no JDK here yet"). Say what holds wherever the settings are installed, or leave it out.

That goes for the checkout's own path too. Write install and check commands relative to the
repository root (`cp settings/vim/vimrc ~/.vim/vimrc`), with a line saying to run them from
wherever the repo is cloned, never as `~/Developer/llming/...` or any other machine's path.

## Checking installed copies against the repo

Settings are installed as copies, so a machine's copy and this repo drift apart. **Before changing a
tool here, and before committing, diff the two:**

| Tool        | Repo                                  | Installed copy                   |
| ----------- | ------------------------------------- | -------------------------------- |
| oh-my-posh  | `settings/oh-my-posh/`                | `~/.config/oh-my-posh/`          |
| Vim         | `settings/vim/vimrc`                  | `~/.vim/vimrc`                   |
| Claude Code | `settings/claude-code/statusline.sh`  | `~/.claude/statusline.sh`        |
| Claude Code | `settings/claude-code/user-CLAUDE.md` | `~/.claude/CLAUDE.md`            |
| Git         | `settings/git/gitconfig`              | `~/.config/git/shared.gitconfig` |
| Git         | `settings/git/gitignore`              | `~/.gitignore`                   |
| Terminal    | `settings/terminal-app/*.terminal`    | Terminal's preferences, [not `diff`](#checking-a-profile-against-the-repo) |

`diff -r settings/oh-my-posh ~/.config/oh-my-posh`, and so on. For each difference, ask the
user which way it should go: bring the repo's version over, keep the machine's change only on that
machine, or commit it here. **This repo is public.** Before committing anything from a machine,
read all of it for tokens, hostnames, usernames, home-directory paths, internal tool or project
names, and anything else that shouldn't be published, and remove them. The first copy of the
status line had a comment naming a tool the user hadn't published.

## oh-my-posh

The config is `oh-my-posh/gaurav-custom.omp.json`, installed as a copy in `~/.config/oh-my-posh/`,
which is the path `~/.zshrc` points at. Editing the repo copy doesn't change the live prompt: copy
it over, or preview it with `--config` as below.

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

`print` can't show how prompts behave over time: the transient collapse, the blank line, the
cursor-position query. To check those without a human at a terminal, run `zsh -i` under Python's
`pty.fork()` and feed its output into a `pyte` screen (pip-install `pyte` into a throwaway venv).
Answer the query by setting `screen.write_process_input` to write back to the pty. Type commands
with `os.write(fd, b"cmd\r")`, wait a few seconds, and print `screen.display`.

The blank line comes from `"newline": true` on the first block. `enable_cursor_positioning` keeps it
off the top of a fresh window. It asks the terminal where the cursor is, and skips the newline in
column 0 of row 0. The transient prompt redraws from the start of the prompt, so the blank line
goes with it.

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

- **Every colour is a palette reference (`p:role`)**. There are no hex values in the blocks.
  `palettes.list` holds the named palettes, and `palettes.template` picks one from `$POSH_PALETTE`,
  falling back to the default. Top-level `palette` is a copy of the default, used when
  `$POSH_PALETTE` names a palette that doesn't exist. To add a palette, fill every role, and check
  contrast against both the bar and black (the frame, dots and `▶` sit on the terminal background).
  `preview-palettes.zsh` reads the palette names from the JSON.
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
- **In the git segment, `.Staging.Changed` and `.Working.Changed` don't mean a count is nonzero.**
  A merge conflict sets both, but oh-my-posh counts it only in `.Staging.Unmerged` and
  `.Working.Unmerged` (one per file in each), not in `Added`/`Modified`. Guarding on `Changed`
  printed `+0` during a merge, so each count is guarded on its own sum instead. `.Working.Added` is
  a file added with `git add -N`, counted under `!`. To see what oh-my-posh reports for a repo
  state, render a throwaway config whose git template prints every field.
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
  -o "settings/terminal-app/Solarized Darker.terminal" ~/Library/Preferences/com.apple.Terminal.plist
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

To make a new profile from an existing one without quitting Terminal:

1. Copy the `.terminal` dict in Python.
2. Swap colours by cloning an existing colour archive and replacing its `NSRGB` string.
3. Change `name`.
4. `open` the file. Terminal imports it (and opens a window with it).
5. Make it the default with AppleScript
   (`set default settings to settings set "…"`, and the same for `startup settings`).
6. Re-export Terminal's stored copy over the file. Terminal re-encodes the archives on import, so
   the bytes change but the values don't.

That's how `Tokyo Night Darker` was made from `Solarized Darker`.

**Install the font before Terminal starts, or set it again after importing.** A `.terminal` file
imported while Terminal is running, when its font was installed after Terminal started, comes in
with no font at all. Terminal doesn't complain. Set the font afterwards with AppleScript
(`set font name of settings set "…" to "MesloLGMNF-Regular"`, and `font size` to 12).

### Checking a profile against the repo

`diff` and `cmp` can't do it. Terminal re-encodes the colour and font archives whenever it stores
a profile, so an exported profile's bytes differ from the repo's even when every value matches.
Decode the archives and compare those instead. Read Terminal's settings through
`defaults export`, not from `~/Library/Preferences/com.apple.Terminal.plist`: right after an
AppleScript change, the file on disk can still hold the old values while `cfprefsd` has the new
ones. Run this from the repository root. It prints the name of each setting that differs, and
nothing if the profile matches:

```bash
P="Solarized Darker"   # the profile to check
T=$(mktemp -d)
defaults export com.apple.Terminal "$T/installed.plist"
plutil -extract "Window Settings.$P" xml1 -o "$T/installed.terminal" "$T/installed.plist"
python3 - "settings/terminal-app/$P.terminal" "$T/installed.terminal" <<'EOF'
import plistlib, sys
def tree(v):  # decode a keyed archive (colours, font) into plain values
    if not (isinstance(v, bytes) and v.startswith(b"bplist")):
        return v
    a = plistlib.loads(v)
    def r(x):
        if isinstance(x, plistlib.UID): return r(a["$objects"][x.data])
        if isinstance(x, dict): return {k: r(y) for k, y in x.items()}
        if isinstance(x, list): return [r(y) for y in x]
        return x
    return r(a["$top"])
repo, installed = (plistlib.load(open(p, "rb")) for p in sys.argv[1:])
for k in sorted(repo.keys() | installed.keys()):
    if tree(repo.get(k)) != tree(installed.get(k)):
        print(k)
EOF
```

`defaults read com.apple.Terminal "Default Window Settings"` (and `"Startup Window Settings"`)
names the profile in use, which is the one to check.

## Vim

`~/.vim/vimrc` is only read when `~/.vimrc` doesn't exist. If an edit to `~/.vim/vimrc` has no
effect, look for a stray `~/.vimrc` first. `:echo $MYVIMRC` names the file Vim loaded.

**If Vim acts as if `defaults.vim` never ran** (`scrolloff=0`, no restore-cursor, no `incsearch`),
`skip_defaults_vim` is set. macOS's system vimrc (`/usr/share/vim/vimrc`) sets it, and
`defaults.vim` quietly does nothing, so the `unlet!` has to come before the `source`.
`:scriptnames` shows whether `defaults.vim` was loaded at all. Homebrew's Vim has no system vimrc,
so a vimrc that works there can still fail in `/usr/bin/vim`, which is what `git commit` often
opens. Check both.

**To check the vimrc without a human at a terminal**, copy it into a throwaway `$HOME` made
by `mktemp -d` and run Vim under a pty, writing options to a file:

```bash
H=$(mktemp -d)   # then copy the vimrc to $H/.vim/vimrc
HOME=$H TERM=tmux-256color script -q /dev/null /usr/bin/vim \
  -c "redir! > $H/out.txt | silent set mouse? ttymouse? scrolloff? | redir END | qa!" </dev/null
```

`vim -es` won't do: silent Ex mode skips the vimrc. Vary `TERM`, because `defaults.vim` and Vim's
own `ttymouse` detection both branch on it.

## Git

`git/gitconfig` is installed as `~/.config/git/shared.gitconfig` and pulled in by an `[include]`
at the top of `~/.gitconfig`. It is **not** the machine's `~/.gitconfig`, and must never be
replaced with a copy of one: that file also holds the name, email, signing key and the signing
program's path, none of which belong in a public repo. To bring a machine's change back here, copy
the one setting across.

- **`git config --global` doesn't follow the include.** Naming a file (`--global`, `--file`)
  turns includes off, so `git config --global --get merge.conflictstyle` prints nothing on a
  correctly installed machine. Add `--includes`, or drop `--global`.
- **`git config --global --includes --list --show-origin` names the file each value came from.**
  Use it to find a setting that is in both files, or one that the machine has and the shared file
  doesn't. A setting in both is harmless but hides drift, because the machine's copy wins.
- **The include has to come first.** Git reads the included file where the `[include]` line is,
  and the last value wins. An include at the bottom of `~/.gitconfig` makes the shared file
  override the machine's own settings.
- **A machine set up before `git/` existed has these settings inline in `~/.gitconfig`**, with
  no include, so there is nothing at `~/.config/git/shared.gitconfig` to diff. Compare values
  instead: `git config --file settings/git/gitconfig --list` against `git config --global --list`.
- **`~/.config/git/ignore` is also read**, as Git's default global ignore file, but only while
  `core.excludesfile` is unset. With the shared file installed, `~/.gitignore` is the only one
  used, and anything listed only in `~/.config/git/ignore` stops being ignored.
- **Check a version claim against Git's release notes** (`Documentation/RelNotes/` in
  [git/git](https://github.com/git/git)) before putting it in the README. The article's own
  comment on `zdiff3` says "git version < 2.3", where 2.35 is meant.
  The release notes don't name every new setting (`push.autoSetupRemote` isn't in 2.37's). When
  they don't, compare `Documentation/config/<section>.adoc` (`.txt` before 2.49) at two tags with
  `gh api 'repos/git/git/contents/<path>?ref=v2.37.0'`.
- **To test the install steps**, use a throwaway `HOME` (`HOME=$(mktemp -d)`), follow
  the README there, and read the result with `git config --global --includes --list
  --show-origin`.

## Claude Code

`claude-code/statusline.sh` is installed as a copy at `~/.claude/statusline.sh`, which is where
`/statusline` and its agent edit it. Changes made that way have to be copied back here, which is
the main way this one drifts. Claude Code runs it after each message, passing a JSON payload on
stdin.
[The status line docs](https://code.claude.com/docs/en/statusline) list its fields; the ones used
here are `workspace.current_dir`, `context_window.used_percentage` and `.total_input_tokens`,
`rate_limits.{five_hour,seven_day}.{used_percentage,resets_at}` (`resets_at` in epoch seconds),
`model.display_name` and `effort.level`.

**Test with a fake payload**, not by waiting for Claude Code to redraw:

```bash
N=$(date +%s)
jq -n --argjson now "$N" '{workspace: {current_dir: "'"$PWD"'"},
  context_window: {used_percentage: 42, total_input_tokens: 84000},
  rate_limits: {five_hour: {used_percentage: 4, resets_at: ($now + 13920)},
                seven_day: {used_percentage: 20, resets_at: ($now + 277200)}},
  model: {display_name: "Opus 5.5"}, effort: {level: "high"}}' \
  | bash settings/claude-code/statusline.sh | cat -v
```

Also try a quota with no `resets_at` (`five_hour: {used_percentage: 4}`). The docs say Claude Code
sends both fields or drops the window, but the script is meant to show just the percentage, not
`until  (now)`. Likewise try a context window with no `total_input_tokens`, a zero one, or one
small enough to round to `0k` (`total_input_tokens: 400`): each should show `ctx 42%`, not
`ctx 0k (42%)`.

`cat -v` shows the escape codes, which is the only way to check colours without a human looking.
Strip them with `perl -pe 's/\e\[[0-9;]*m//g'` to read the text. For git states, make throwaway
repos (a bare remote plus clones that are clean, dirty, ahead and behind) and point
`current_dir` at each.

The `statusline-setup` agent that `/statusline` launches has no shell, so it can't run the script.
Test its edits from the main session.

**Don't rename `user-CLAUDE.md` to `CLAUDE.md`**, although that is its installed name. Claude Code
loads a file called `CLAUDE.md` from any directory it reads files in, so under that name it would
become instructions for every agent working in `claude-code/` rather than a file they're editing.

### Colours and glyphs

- **Solarized's *bright* ANSI colours are mostly greys** (bright green, yellow and blue) or other
  hues (bright red is orange, bright magenta is violet). Only bright white is a brighter version of
  its base colour. Use 24-bit colour for a lighter tint instead.
- **Don't brighten with bold.** The profile has `UseBrightBold` and `UseBoldFonts` off, so bold
  does nothing visible in Terminal.app, and a terminal with bright-bold on would shift the hue.
- **Check a glyph's vertical position before using it.** Many geometric shapes (`◆`, `●`, `■`,
  `▰`) sit well below the middle of capital letters in Meslo. `♦`, `•` and `◦` are centred.
  Measure with fontTools:
  `uv run --with fonttools python` → load `~/Library/Fonts/MesloLGMNerdFont-Regular.ttf`, draw the
  glyph into a `BoundsPen`, and compare its vertical centre with `H`'s. A glyph missing from the
  font renders from a fallback font, at whatever size and height that font uses.
- Keep glyphs as `$'\xNN'` byte escapes with the character named in a comment, as in the
  oh-my-posh JSON.
