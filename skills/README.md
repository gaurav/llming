# Skills

Coding agent skills, kept in this repo so they can be shared across machines and carried from
project to project. They span both work and home use.

Each skill's `SKILL.md` says what it does and when an agent should reach for it — that frontmatter
`description` is written *for the agent*, as trigger text. This file is the other half: why the
skill exists, what I was actually trying to solve, and what I'd do next. That's the part that
isn't recoverable from the skill itself.

- **copilot-review** — pins the repeated steps and my triage preferences so an agent doesn't
  re-derive them on every PR.
- **sync-docs** — a broad use-your-judgement pass that rechecks every documentation claim against
  the code.
- **wrap** — gets what the agent has worked out into the repo before the session is wiped.

## copilot-review

Reviewing Copilot's comments is the same dozen steps every time, and an agent working them out
from scratch on each PR gets them subtly wrong. This pins down the procedure *and* my preferences:
check the suppressed comments too, expect some comments to be stale (a Claude review usually lands
first and has already fixed things), and close out every thread so the PR is clear for human review
unless something genuinely needs a person to look again.

## sync-docs

My first attempt at a broad *use-your-judgement* skill rather than a fixed procedure. The bet: in
most of my repos the documentation is small next to the code it describes, so a single pass can
plausibly recheck **every** claim in the docs against the source — by reading the code, or by
actually running the relevant script or test.

It was also an experiment in LLM use itself: a deliberately big, ambitious goal, to see whether an
agent could take it on without getting lost in the weeds or burning the whole token quota.

Status: seems to work well, but lightly used. I've held off partly on a hunch that it costs a lot
of tokens for the return — a hunch I haven't actually tested. It also hasn't been tried on a repo
like Babel, where LLM-written documentation has grown large enough that "check everything in one
pass" may simply not hold.

Where it goes if it earns it:

1. A regular check-in during development — before cutting a release, recheck the documentation more
   thoroughly than a human review would, accepting that a non-exhaustive pass still catches the
   small discrepancies that accumulate.
2. A brake on LLM overdocumentation. The same read-everything pass is well placed to notice where
   documentation has become unclear or duplicative, and to suggest compressing, reorganising or
   trimming it.

## wrap

Three jobs at once.

The mechanical one: there are things I always want done before stopping — no stray commits or
uncommitted changes left behind, and a moment's thought about how the code just written could be
tested.

The substantive one: over a long session the agent builds up a picture of how some corner of a tool
works, how I think about it, and how I'd like it to work. All of that evaporates when the session
ends, so `wrap` gets it written into the repo first — before I start the next task fresh, or stop
for the night.

And the third: it's an explicit signal that the session is about to be wiped. If the agent has a
warning to raise or something it wants me to do, this is its last chance to say so.

# What earns a skill

Context dependent, and deliberately broad. Two rough patterns so far:

- **Something I keep doing by hand** (`wrap`, `copilot-review`). Centralising it makes it
  reproducible across machines, and gives me one place where improvements can be recorded and
  tracked over time instead of being reinvented each session.
- **An experiment** (`sync-docs`) — either about what tasks an LLM can usefully take on, or about
  LLM use itself. I expect more of these: ticket triage, planning skills.

Not every skill here will finish, and that's fine. Some turn out not to be useful. Some get built
just far enough to unblock one project and then set aside for review when there's time. And the
ones that prove genuinely useful tend to leave — the way `process-babel-logs` became a script
inside Babel itself, so the code generating the logs and the code reading them live in one place. I
expect skills to graduate the same way.
