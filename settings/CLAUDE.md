`README.md` has the install steps and each tool's settings in words. This file has the specifics.

## oh-my-posh

The config is `oh-my-posh/p10k-classic.omp.json`. `~/.config/oh-my-posh` is a symlink to the
`oh-my-posh/` directory (not to `settings/`), so `~/.zshrc` points at a stable path.

### Previewing a change

Inside a shell that already runs oh-my-posh, `oh-my-posh print … --config X` **silently ignores
`--config`**. A session (`$POSH_SESSION_ID`) is tied to the first config path it rendered, which is
whatever `.zshrc` loaded. Edits to *that* file are picked up at the next prompt, but any other
path is ignored. Drop the session variable to preview a different file:

```bash
C="$PWD/oh-my-posh/p10k-classic.omp.json"   # run from settings/
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
- **On the right, each optional segment carries its own trailing `\ue0b3` separator**, and the
  clock, which is always present, is last. That way a hidden segment never leaves a doubled or
  dangling separator.
- `status` appears twice. On the right it has the default `always_enabled: false`, so it only
  renders after a failure. On line 2 it has `always_enabled: true` and exists to colour the `❯`
  through `foreground_templates`.
- `executiontime` uses `"style": "round"` for p10k-like `4s` / `2m 5s`, and a 3000 ms `threshold`.

### Shell side

`ZSH_THEME` is emptied only when oh-my-posh will run. Emptying it unconditionally leaves
Terminal.app with zsh's bare `%` prompt, and leaving it set everywhere makes Oh My Zsh set up a
theme that oh-my-posh then overwrites. `oh-my-posh init zsh` reads `transient_prompt` from the
config and installs its zle hook itself, so no extra zsh code is needed for the transient prompt.
