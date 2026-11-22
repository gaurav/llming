# Git

My Git settings, the same on every machine. They follow Scott Chacon's
[How Core Git Developers Configure Git](https://blog.gitbutler.com/how-git-core-devs-configure-git/),
which collects the settings Git's own developers use and explains each one. I use all of them,
including the ones the article calls a matter of taste.

There are two files. `gitconfig` holds the settings. `gitignore` lists the files Git should ignore
in every repository. Neither holds a name, an email address or a signing key: those are set on
each machine, as described in [Per-machine setup](#per-machine-setup).

## Install

Run these from the root of this repository, wherever it is cloned on the computer being set up:

```bash
mkdir -p ~/.config/git
cp settings/git/gitconfig ~/.config/git/shared.gitconfig
[ -e ~/.gitignore ] || cp settings/git/gitignore ~/.gitignore
```

The last line leaves an existing `~/.gitignore` alone. It tests for the file rather than using
`cp -n`, which newer GNU coreutils warn about or treat as a failure when the file already exists.
If the machine has one already, add the lines from `gitignore` to it by hand. If it has a
`~/.config/git/ignore`, move its lines into `~/.gitignore` too: Git stops reading that file once
the shared settings point it at `~/.gitignore`.

Then put this at the **top** of `~/.gitconfig`, above everything else in it:

```ini
[include]
    path = ~/.config/git/shared.gitconfig
```

Git reads the included file at the point where the `[include]` appears, and a later value
replaces an earlier one. With the include at the top, anything else in `~/.gitconfig` overrides
the shared settings, which is how one machine can differ from the rest.

If `~/.gitconfig` already has some of these settings, delete them once the include is in place, so
that each setting comes from one file only. One needs care first: if it sets `core.excludesfile`
to another file, such as `~/.gitignore_global`, move that file's lines into `~/.gitignore` before
deleting the setting, or Git stops ignoring everything listed there.

To check that it worked:

```bash
git config --show-origin --get merge.conflictstyle
```

This should print `zdiff3`, read from `shared.gitconfig`. Leave out `--global` here: with it,
Git reads `~/.gitconfig` alone and doesn't follow the include, so the shared settings look as if
they were missing.

To check an installed copy against this repo later, again from the repository's root:

```bash
diff settings/git/gitconfig ~/.config/git/shared.gitconfig
diff settings/git/gitignore ~/.gitignore
```

## Per-machine setup

These stay in each machine's own `~/.gitconfig`, below the include.

- **Name and email:**

  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "you@example.com"
  ```

- **Commit signing.** I sign commits with an SSH key kept in 1Password. On a fresh computer,
  follow 1Password's
  [Sign Git commits with SSH](https://developer.1password.com/docs/ssh/git-commit-signing/)
  instructions. 1Password writes the settings into `~/.gitconfig` itself: the key, the path of its
  signing program, and `commit.gpgsign = true`. They aren't in the shared file because the key and
  the program's path differ between machines, and because turning signing on before a key is set
  up makes every commit fail.
- **Git LFS**, where it is used: `git lfs install` adds its own `[filter "lfs"]` section.

## Known issues

- **Some settings need a recent Git.** An older Git silently ignores settings it doesn't know:
  `push.autoSetupRemote` needs Git 2.37, `rebase.updateRefs` 2.38 and `fetch.all` 2.44. Two
  values are worse, because an older Git stops with an error on them:
  `merge.conflictstyle = zdiff3` before Git 2.35 breaks merges, rebases and `git pull`, and
  `help.autocorrect = prompt` before Git 2.34 breaks every mistyped command. Overriding them
  below the include doesn't help: Git reads the shared file's value first and stops there. On
  such a machine, leave those lines out of the installed copy (`diff3` works in place of
  `zdiff3`), or upgrade Git. `git --version` shows the version. I haven't tried this file on a
  Git older than 2.54.
- **`fetch.pruneTags` deletes local tags that the remote doesn't have.** A tag made locally and
  not yet pushed is removed by the next `git fetch`. Push a tag straight after making it, or run
  that fetch with `--no-prune-tags`. In a repository with more than one remote, such as a fork
  with `origin` and `upstream`, it also deletes every tag that only one remote has, on every
  `git fetch`: tags aren't kept per remote, and `fetch.all` fetches each remote with pruning.
  Turn it off in that repository with `git config fetch.pruneTags false`.
- **`git pull` rebases instead of merging** (`pull.rebase`), and stashes uncommitted changes
  first, putting them back afterwards (`rebase.autoStash`). If putting them back conflicts, the
  changes are still in the stash: `git stash list` shows them.
- **`core.fsmonitor` starts one background process for each repository** it is used in. Git's
  built-in monitor is only available on macOS and Windows.
- **`init.defaultBranch` only names the first branch of a new repository.** Existing repositories
  whose main branch is called `master` are not changed.

## Preferences

What to reproduce on another machine, with or without the file. The groups are the article's.

**Clearly better than the defaults:**

- Lists of branches and tags are shown in columns, like `ls` (`column.ui = auto`).
- Branches are listed with the most recently committed first (`branch.sort = -committerdate`).
- Tags are sorted as version numbers, so `v1.10` comes after `v1.9`
  (`tag.sort = version:refname`).
- A new repository's first branch is called `main` (`init.defaultBranch = main`).
- Diffs:
  - use the histogram algorithm, which gives clearer diffs than the default when code has moved
    or been reordered (`diff.algorithm = histogram`);
  - show moved lines in different colours from added and removed ones
    (`diff.colorMoved = plain`);
  - label the two sides by where they come from, `i/` for the index, `w/` for the working tree and
    `c/` for a commit, in place of `a/` and `b/` (`diff.mnemonicPrefix = true`);
  - detect renamed files (`diff.renames = true`).
- Pushing:
  - sends the current branch to the branch of the same name on the remote
    (`push.default = simple`, which is also Git's default);
  - sets the upstream branch on the first push, so `git push` works on a new branch without
    `--set-upstream` (`push.autoSetupRemote = true`);
  - also sends annotated tags that point into the commits being pushed (`push.followTags = true`).
- Fetching:
  - fetches from every remote, not only `origin` (`fetch.all = true`);
  - removes local copies of branches and tags that were deleted on the remote
    (`fetch.prune = true`, `fetch.pruneTags = true`).

**No reason not to:**

- When a command is mistyped, Git suggests the closest one and asks before running it
  (`help.autocorrect = prompt`).
- The commit message editor shows the diff being committed, below the message. It isn't saved
  into the message (`commit.verbose = true`).
- Git remembers how each merge conflict was resolved, and resolves the same conflict the same way
  when it comes up again, staging the result. This helps most when rebasing a branch more than
  once (`rerere.enabled = true`, `rerere.autoupdate = true`).
- The ignore file for every repository is `~/.gitignore` (`core.excludesfile = ~/.gitignore`).
  Mine ignores Claude Code's per-machine project settings (`.claude/settings.local.json`), the
  `.DS_Store` files macOS's Finder leaves in each folder it opens, and JetBrains IDEs' `.idea/`
  project directories.
- Rebasing:
  - an interactive rebase puts `fixup!` and `squash!` commits next to the commits they amend
    (`rebase.autoSquash = true`);
  - uncommitted changes are stashed before a rebase and put back after it
    (`rebase.autoStash = true`);
  - when a rebased branch has other branches stacked on its commits, those branches are moved
    along with it (`rebase.updateRefs = true`).

**A matter of taste** (the article leaves these off, and I turn them on):

- A background process watches each repository for file changes, and Git caches its list of
  untracked files, so `git status` is faster in a large repository (`core.fsmonitor = true`,
  `core.untrackedCache = true`).
- Merge conflicts show a third section, the original text that both sides changed, between the
  two versions (`merge.conflictstyle = zdiff3`).
- `git pull` rebases local commits onto the fetched ones and makes no merge commit
  (`pull.rebase = true`).

## Next steps

- Install this on each machine that still has the settings typed straight into `~/.gitconfig`,
  and delete them there.
- Add to `gitignore` any other files that never belong in any repository, as they turn up.
- Try the file on a machine with an older Git, and record what it does with the settings it
  doesn't know.
