# Vim

My Vim setup. It's small: syntax highlighting on, and colours chosen for a dark terminal. There's no
colour scheme, so Vim draws with the terminal's own 16 colours. That means it already matches
whichever [Terminal.app profile](../README.md#terminalapp-profile) is in use.

## Install

```bash
mkdir -p ~/.vim
cp ~/Developer/llming/settings/vim/vimrc ~/.vim/vimrc
```

**Vim only reads `~/.vim/vimrc` if there is no `~/.vimrc`**, so move any existing one out of the
way first. Open a new Vim to see the change.

## Known issues

- **Plugins aren't in the repo.** Anything installed as a Vim package is cloned into
  `~/.vim/pack/`, so a new machine needs the `git clone` from [Colour schemes](#colour-schemes)
  again.
- **Themes that need 24-bit colour may not work in Terminal.app.** Tokyo Night is one of them: it
  needs `set termguicolors`. Older versions of Terminal.app can't show 24-bit colour, and there
  the theme comes out garish or muddy. Check with the `printf` test in the
  [oh-my-posh known issues](../README.md#known-issues). Ghostty is fine.

## Preferences

What to reproduce on another machine, with or without this file:

- **Syntax highlighting on** (`syntax on`).
- **File-type detection, with per-language plugins and indentation** (`filetype plugin indent
  on`). This makes highlighting work for more files, and makes indentation follow each
  language's rules.
- **A dark background** (`set background=dark`). Every Terminal.app profile I use is dark. Without
  this line Vim assumes a light background and some colours are too dim to read.
- **No colour scheme.** Vim's default draws with the terminal's 16 ANSI colours, so it picks up
  the Terminal.app palette.

## Colour schemes

To try one, type `:colorscheme`, a space, and press Tab to cycle through the installed ones. Vim 9
comes with several, including `habamax`, `lunaperche`, `retrobox`, `sorbet`, `desert` and `slate`.
To keep one, add `colorscheme <name>` to `~/.vim/vimrc`, after `syntax on`.

A theme that is a single `.vim` file goes in `~/.vim/colors/`. A theme on GitHub is
usually a whole plugin, which goes in `~/.vim/pack/`, where Vim loads it at startup. For example,
[Tokyo Night](https://github.com/ghifarit53/tokyonight-vim), which matches the prompt's
*tokyo-night* palette:

```bash
git clone https://github.com/ghifarit53/tokyonight-vim ~/.vim/pack/themes/start/tokyonight-vim
```

Then add to `vimrc`, after `set background=dark`:

```vim
set termguicolors
let g:tokyonight_style = 'night'   " or 'storm'
colorscheme tokyonight
```

It's cloned on this machine but not turned on.

## Next steps

- Try Tokyo Night in Ghostty, where 24-bit colour works, and decide whether to turn it on.
- Solarized is also a Vim theme, if Vim should match the Solarized Darker profile more closely
  than the terminal's 16 colours already do.
