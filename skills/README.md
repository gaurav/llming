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
  session that produced them, and stops a description that is rewritten every round from silently
  accreting instead.
- **wrap** — gets what the agent has worked out into the repo before the session is wiped, and
  checks first whether a previous run already did.

## copilot-review

Reviewing Copilot's comments is the same dozen steps every time, and an agent working them out
from scratch on each PR gets them subtly wrong. This pins down the procedure *and* my preferences:
check the suppressed comments too, expect some comments to be stale (a Claude review usually lands
first and has already fixed things), and close out every thread so the PR is clear for human review
unless something genuinely needs a person to look again.

No repeat-run check here, and unlike `update-pr` that isn't a decision I had to make — a previous
run leaves its record on the PR itself. Threads it handled are resolved, and the ones it declined
carry the reply saying why. So a human can see whether another run is wanted before starting one,
and an agent that starts one anyway finds most threads already resolved and does almost nothing.
The state the other two skills have to derive from git is, for this skill, just visible.

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

Deliberately *no* equivalent of `wrap`'s step-0 gate here, which took a round of getting wrong to
see: the commonest way a description goes stale is a previous `/wrap` having committed and pushed,
which leaves exactly the clean tree such a gate would stop on. The staleness this skill fixes lives
in the diff against the base branch, not in uncommitted work.

Running it repeatedly turned out to have a failure mode of its own, and it took a very long PR to
see it. Each run reads the existing body, keeps what still looks true, and adds this round's news —
and no single one of those edits is unreasonable. After five rounds the description said the same
test count in four places, explained the project's premise back to the maintainer who maintains it,
and had started narrating its own revision history: *the figure above is now superseded*, *an
earlier version of this paragraph said something else*. The skill's churn rule was already there
and was no help, because none of that is churn about the PR — it is churn about the document. So
the skill now says rewrite rather than append, each fact exactly once, and treats a fact repeated
across two sections as the signal to go back and merge instead of patching.

The audience line was wrong in a way that reads as right. "Write for someone with no context"
produces paragraphs arguing for a premise the reviewer already holds — on a PR to an upstream
maintainer, their own project explained back to them. They have no context on *this change*; they
have plenty on everything around it. Cheap to state, and it recovers a surprising amount of room.

The other half of that room came from numbers. Anything a reader could recount from the diff —
files, commits, call sites — gets approximated, because the precision is noise that then has to be
maintained. Precision is for the numbers that *are* the claim and cost a re-run to check: test
results, benchmarks, versions. Those also have to say where they came from and at which commit,
which is what lets the *next* run notice that the measurement now predates three commits. That last
part matters more than it sounds: a skill designed to run repeatedly will otherwise re-assert a
stale figure forever, with each run's confidence borrowed from the one before. Cross-references
rot the same way, so the skill re-checks every `#N` the old body cites — a paragraph explaining how
two other PRs relate to this one survived several rounds after both had merged.

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

What they do have is a boundary, drawn deliberately narrow. `wrap` touches the PR in exactly two
ways and neither is a rewrite: it says the description looks stale, because pushing is the thing
that made it stale, and it offers to append its blocking items to the description as checkboxes.
Both are handoffs rather than couplings — `update-pr` re-decides every checkbox on its next run and
does not need to know where one came from. Everything else about the description stays `update-pr`'s
job, including deciding whether a body is *wrong*, which needs the diff read against it and is a
worse job done hurriedly at the end of a session than left to be done properly.

The blocking half of that is the one that matters. Before it, `wrap` would identify a blocker and
print it to a terminal that was about to be closed — noticed and then lost, which is worse than
never having looked. The PR body is the only place at hand that survives the session.

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

The step-0 gate came later, from running this across several PRs in a row and watching it re-do
work a previous run had already done — recording a lesson that was already recorded, hunting for
tests on a diff that was already committed and pushed. Those two sections are the expensive part,
so the skill now looks at the tree and the branches first and says what it found. It reports the
evidence rather than a verdict, because a clean tree genuinely doesn't prove nothing is owed: the
work may have been committed by hand, or by an earlier run that recorded no lesson. I'd rather be
told "clean tree, nothing unpushed" and make that call myself.

## Writing these

One failure mode has now shown up twice, in both skills, and is worth naming: a step whose prose
describes a check the commands underneath it don't perform, or perform and then walk past. `wrap`'s
step 0 promised a `[origin/x: gone]` marker a plain `git fetch` cannot produce; `update-pr`'s step 1
promised to catch a diverged head, first with commands that compared nothing and then, once they
did, with no instruction to stop. Prose reads as true because it describes an intention, and an
agent following it will narrate the check it was told about rather than the one it ran. When adding
a check to a skill, read the block as if the surrounding sentences weren't there — what would this
actually tell me, and what does the skill do differently on each answer?

## What earns a skill

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
