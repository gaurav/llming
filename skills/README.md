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
- **update-pr** — keeps the PR honest about itself, since its title and description outlive the
  session that produced them.
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

## update-pr

A PR title becomes a line in my release notes, and a PR description is the only place the *why*
of a change survives once the session that produced it is gone. Both drift: the title is written
when the branch is one commit old and the description when I still remember everything, and neither
gets revisited as the work turns into something else.

So this skill exists to be run repeatedly, not once at the end — every time a round of work lands.
It rewrites both against the actual diff rather than against the agent's memory of the session,
which is the specific failure it's guarding against: an agent asked to summarise a PR will happily
describe the three approaches it tried, when only the last one shipped.

The checkbox pass is the part I'd have skipped by hand. TODO lists in a description rot in both
directions — items ticked off that got reverted later, items never added because they surfaced
after the description was written — and the skill forces a decision on each one: do it here, drop
it, or file it.

The hard-wrapping rule is the one an agent breaks by reflex, because every other file it has been
reading is wrapped at 80 columns and GitHub turns each of those newlines into a line break. It very
nearly cost this repo a bundled script: I wrote a 110-line unwrapper for bodies that arrive already
wrapped, and a review found it silently mangling nested lists, indented code blocks, underlined
headings, `<pre>` content and deliberate line breaks — because unwrapping Markdown correctly means
parsing it, and it wasn't. `npx prettier --prose-wrap never` does the whole job in a flag. The
lesson generalised into `CLAUDE.md`; the skill now says don't wrap in the first place, and reaches
for prettier only when text has to survive verbatim.

The fix-here-or-file-an-issue bar is stated in full here and in `copilot-review`, and paraphrased in
`wrap`. That duplication is deliberate, not debt waiting to be factored out. A skill is loaded on
its own, so a cross-reference to another skill's wording isn't reliable at read time — but the real
reason is that the three are asking different questions. `wrap` is *we're out of time, write down
whatever you need to pick this up later*, so it errs toward capturing everything and deciding
nothing. `update-pr` is *this has to be good enough to review, and if it isn't, say so* — a loose
end there becomes a TODO in the PR that gets worked rather than an issue that gets filed and
forgotten. Expect these to drift further apart, and let them.

What all three do share is the shape of the decision, and it took a second pass to get right. The
first version tested only size and scope — small and connected, fix it here; otherwise file an
issue — which quietly treats "too big for this PR" as though it settled whether the PR was finished.
It doesn't. A missing error case or a doc paragraph that misdescribes what shipped can be too large
to fix in the diff and still be a thing the PR shouldn't merge without. So there are two questions
now: does it fit here, and if not, does the PR ship a defect without it. Only the second one can
block.

The bar for blocking is deliberately concrete — wrong behaviour under some real circumstance, an
error path that loses work or data, documentation that misdescribes what shipped — because the
obvious phrasing ("is this essential?") is one an agent answers yes to almost every time, and a
blocker list everything lands on is just a slower version of the issue tracker nothing comes back
out of. The mechanism then differs by skill: `update-pr` and `copilot-review` park a blocker as a
`- [ ]` in the PR body, where `update-pr`'s checkbox pass has to re-decide it on every run, and
`wrap` has no PR to write to so it lists them first and says they block.

The same answer covers the wider overlap, which is worth writing down because it looks like an
obvious cleanup: `update-pr` and `wrap` both commit, both push, both think about follow-up issues,
and I'll often run them back to back. Having one call the other would collapse a shared git survey
and then wedge two different questions into one set of instructions. Not worth it. The duplicated
mechanics are cheap; the judgement is what differs, and that's the part any factoring-out would
damage.

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
