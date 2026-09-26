# Skills

Coding agent skills, kept in this repo so they can be shared across machines and carried from
project to project. They span both work and home use.

Each skill's `SKILL.md` says what it does and when an agent should reach for it — that frontmatter
`description` is written *for the agent*, as trigger text. This file is the other half: why the
skill exists, what I was actually trying to solve, and what I'd do next. That's the part that
isn't recoverable from the skill itself.

- **copilot-review** — pins the repeated steps and my triage preferences so an agent doesn't
  re-derive them on every PR.
- **github-issues** — a rule rather than a task: correct your own stale issue instead of commenting
  under it, never rewrite anyone else's, and close anyone else's only through a PR.
- **github-milestones** — my milestone scheme, so an agent tells a bucket from a deadline, leaves
  untriaged issues alone, and doesn't treat a soft release date that has passed as an alarm.
- **sync-docs** — a broad use-your-judgement pass that rechecks every documentation claim against
  the code.
- **update-pr** — keeps the PR honest about what shipped: rewrites the title and description against
  the diff each round, and moves anything durable into the repo so the description stays short.
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

It is also the one skill here that files an issue without asking me first. `update-pr` and `wrap`
offer their follow-ups and wait, because an issue born at the end of a session needs enough context
written into it to make sense later, and I want to see that before it exists. An issue deferred from
a Copilot comment starts with that context: a specific comment on a specific line of a specific PR.
The skill requires the issue to carry all of it — the comment link, a permalink at the head commit,
and the code fragment pasted in, since a link to a line that has since moved explains nothing — so
it should be understandable cold. If one ever isn't, that is the reason to make this skill ask too.

## github-issues

The only rule in a directory of tasks. An issue I wrote that has gone out of date should be edited
until it is accurate, with whatever it still asks for that no longer belongs there split out into a
new issue — and an issue anyone else wrote should never be edited, whatever permissions I hold on
the repository. The first half is about how issues are read. Nobody reads the comments under a wrong
description before acting on it, so a correcting comment leaves the wrong thing in the place people
look. The second half needs no justification beyond stating it, but agents do not infer it: admin
rights on a repository read as permission to fix anything in it. "Edited" means the words: body and
title. Triage — labels, assignees, milestone, project — stays allowed on anyone's issue, because it
is easy to undo and shows in the timeline, where the author can object to it. Reopening an issue or
an unmerged PR is allowed for the same reason, and because a wrong reopen fails the right way: the
thing goes back on the list and gets looked at again.

Closing follows from the second half but is not quite the same rule. Someone else's issue can be
closed, but only by a `Closes #N` in the pull request that resolves it, never directly. A direct
close that turns out to be wrong is one nobody sees — the bug just stops being tracked until it is
rediscovered — whereas a closing keyword puts the claim in front of a reviewer, beside the change
it rests on, and leaves a link behind.

That argument holds for my own issues too, so the keyword is the preferred route for those as well.
Adding it to an unmerged PR needs no permission, even when it is a different PR from the one being
worked on, and the skill had to say so explicitly: an agent once closed my issue directly because
its last item had landed on another PR's branch and the keyword "wouldn't fit". A closed issue
backed by unmerged work stays closed if the PR is abandoned. Closing directly is kept for catching
up with work that already merged unconnected, done with a comment on the issue, since the comment
records why and a report in the terminal is easy to miss. Closing for any other reason (obsolete,
superseded, won't-do) asks me first, except in very obvious cases.

All of it is what an agent does unasked, and I can overrule any of it for a single issue. That
clause exists because of duplicates: read strictly, the rules would have an agent close my detailed
issue in favour of someone else's thin one, mine being the only one it is allowed to close. The
better issue stays open whoever wrote it, the other gets a comment suggesting it be closed, and if
the case is obvious the agent asks me rather than waiting on a comment nobody may answer. One
escape hatch seemed better than a rule per case.

Editing my own issue asks first only when the edit is major — the issue is about something different
afterwards, or is being split. Minor edits just happen and get reported in a line. The line between
them is left to the agent's judgement on purpose: I expect it to be drawn wrongly sometimes, and an
agent asking me to confirm a typo fix is a real example to refine the wording with, which a rule
written in advance would not be. Either way I see something, which also tells me the skill fired.

Why a skill and not a line in a `CLAUDE.md`: in #20 I said an ambient writing convention is not
skill-shaped, on the grounds that nobody would ever type `/cite-provenance`. That still holds. What
makes this one different is that it applies at
a moment with a name — *about to change an issue* — rather than every time durable text gets
written, and a moment with a name is something a `description` can describe. Whether that is enough
to actually trigger it is the open question, and the skill is the experiment: if it turns out not to
fire, the answer is a hook rather than better prose, and #32 records what that costs.

Measuring that means comparing the sessions that changed an issue against the sessions that loaded
the skill: a session in the first list and not the second is a miss. The first list only sees the
`gh` CLI, so it is a floor, and only sessions started after the install on that machine count. The
greps, and the ways they have already gone wrong, are in `CLAUDE.md`.

The other skills that touch issues — `copilot-review`, `update-pr` and `wrap` — each point at this
one by name at the moment they would file one, which is also where the look-for-an-existing-issue
check lives, so it is written once. Those pointers are a second route to the rule, and a confound
for the experiment: a load that happens inside one of those skills says the pointer worked, not the
description.

## github-milestones

My milestones do two different jobs, and an agent that sees only the titles and due dates can't
tell which is which. Buckets (Critical, Needed soon, Needed later, Not urgent, Upstream) are
priorities, and they're undated. Release and date milestones are the contents of an upcoming
release, and their due dates range from hard to purely hopeful. Most are the hopeful kind, so most
of my milestones are past due most of the time. That's fine, but it reads as neglect to anything
that takes a due date at face value. The skill carries the scheme from machine to machine. It
also records the default that a milestone is a release: its issues get built, published as a
GitHub release, and then the milestone is closed. That holds unless a repository says it uses a
Project instead.

The canonical bucket list lives in `MILESTONES.md` in
[gaurav/milestones](https://github.com/gaurav/milestones), the tool I'm building to keep on top of
all this. The skill points there rather than keeping its own copy, so a change to the buckets is
made once.

Two restraints matter more than the scheme itself. First, an agent shouldn't milestone an issue
unless the milestone is obvious. My triage picks up anything without a milestone, and a guessed
bucket hides the issue from that triage. Second, due dates get suggested, never edited, and a date
in the past is not in itself worth mentioning. Without that second rule, every session that lists
milestones turns into a report on which ones are overdue. It names what to leave out rather than
the few cases worth raising, because a list of the only allowed cases silences whatever it forgot —
its first draft would have stayed quiet about a hard deadline slipping past with issues still open.

It is a separate skill rather than more of `github-issues`, even though the two meet whenever an
issue is filed. `github-issues` fires at one moment, *about to change an issue*, and is partly an
experiment in whether a description naming a single moment is enough to make a skill trigger.
Most of the milestone rules bite at moments that don't involve changing an issue: cutting a
release, closing a milestone, choosing what to work on next. A description stretched to cover all
of those would describe two skills, and it would change what that experiment measures partway
through. The cost of keeping them apart is that filing an issue has to load both. `github-issues`
points here at both of the places where milestones come up, the same way the other skills point
at `github-issues`.

Checking whether it fires works the same way as for `github-issues`, with the same caveat that the
first list is a floor; the greps are in `CLAUDE.md`.

Where it might go next: a triage skill that works through the unmilestoned issues with me, which is
the other half of the "leave it unmilestoned" rule.

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

A PR title becomes a line in my release notes. The description gets read during review and again
when I write that line, and then never — so it is the *worst* place for the *why* of a change to
survive, and the repo is the right one. Both drift: the title is written when the branch is one
commit old and the description when I still remember everything, and neither gets revisited as the
work turns into something else.

So this skill exists to be run repeatedly, not once at the end — every time a round of work lands.
It rewrites both against the actual diff rather than against the agent's memory of the session,
which is the specific failure it's guarding against: an agent asked to summarise a PR will happily
describe the three approaches it tried, when only the last one shipped.

Deliberately *no* equivalent of `wrap`'s step-0 gate here, which took a round of getting wrong to
see: the commonest way a description goes stale is a previous `/wrap` having committed and pushed,
which leaves exactly the clean tree such a gate would stop on. The staleness this skill fixes lives
in the diff against the base branch, not in uncommitted work.

Running it repeatedly has a failure mode of its own: accretion. Each run reads the existing body,
keeps what still looks true, and adds this round's news, and no single one of those edits is
unreasonable. After five rounds on one long PR the description said the same test count in four
places, explained the project's premise back to its own maintainer, and had started narrating its
own revision history: *the figure above is now superseded*. So the skill says rewrite rather than
append, each fact exactly once, and treats a fact repeated across two sections as the signal to
merge instead of patching.

Then the same failure arrived at a scale that rule could not touch: a 58,000-character description,
every part of it well written, most of it collapsed history, an account of the testing, and a
*third* copy of documentation already in that repo's README and code comments. The fix was a
different location, not better prose. Nobody reads a PR description except during review and when
writing a changelog line, so anything needed at any other time goes into the repo first — code
comment, `CLAUDE.md`, docs — and the description links to it. The body has a budget of about 5,000
characters, with an escape hatch rather than a hard cap: a cap gets gamed or broken silently, and a
bare principle gets agreed with and ignored. The budget counts collapsed text, because the previous
rule said churn *goes in a `<details>` block* and the model complied — 17,000 characters of
compliant collapsed text. The rule meant to bound the body had become the mechanism for growing it,
which is worth remembering the next time a rule gives an agent somewhere to put things.

The audience line was wrong in a way that reads as right. "Write for someone with no context"
produces paragraphs arguing for a premise the reviewer already holds — on a PR to an upstream
maintainer, their own project explained back to them. They have no context on *this change*; they
have plenty on everything around it.

The description opens with an abstract: a paragraph or three on what is in the PR and why it
matters, above every heading, ending in the `Closes #N` lines. The real reason is that I read PRs in
a tool that renders every section collapsed, so a description whose first line is a heading opens
as a wall of folded triangles and tells me nothing. That makes the abstract the one part guaranteed
to be read, and the rest of the rule follows from that: it cannot live inside a `<details>`, cannot
say "as described below", and cannot cite a figure whose provenance is three sections down. This is
a property of *my* reader and not of GitHub, in case the tool changes and the rule looks arbitrary.

Three things in the old body are treated as stale until checked, because a skill designed to run
repeatedly will otherwise re-assert them forever, each run's confidence borrowed from the one
before. **Numbers:** anything a reader could recount from the diff gets approximated, and the ones
that *are* the claim — test results, benchmarks, versions — say where and at which commit they were
measured, so the next run can notice they predate three commits. **Cross-references:** every `#N`
gets re-checked, after a paragraph on how two other PRs related to this one survived several rounds
past both merging. **Claims about the code:** a description saying a validator "now runs on every
`.base` file" was written from intent, and a review found it walking half of them. Nothing in the
diff flags a sentence like that, so each load-bearing claim is confirmed against the code as it
stands or cut down to what can be.

The checkbox pass is the part I'd have skipped by hand. TODO lists in a description rot in both
directions — items ticked off that got reverted later, items never added because they surfaced
after the description was written — and the skill forces a decision on each one: do it here, drop
it, or file it.

The hard-wrapping rule is the one an agent breaks by reflex, because everything else it reads is
wrapped at 80 columns and GitHub turns each of those newlines into a line break. The skill says
don't wrap in the first place, and reaches for `npx prettier --prose-wrap never` only when text has
to survive verbatim — the root `CLAUDE.md` has the story of the unwrapper script it replaced.

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

## Where update-pr, wrap and copilot-review overlap

All three decide what to fix now and what to file for later. The bar is stated in full in
`update-pr` and `copilot-review` and paraphrased in `wrap`, and that duplication is deliberate, not
debt waiting to be factored out. A skill is loaded on its own, so a cross-reference to another
skill's wording isn't reliable at read time — but the real reason is that they are asking different
questions. `wrap` is *we're out of time, write down whatever you need to pick this up later*, so it
errs toward capturing everything and deciding nothing. `update-pr` is *this has to be good enough to
review, and if it isn't, say so*. Expect these to drift further apart, and let them.

What they share is the shape of the decision, and it took a second pass to get right. Testing only
size and scope — small and connected, fix it here; otherwise file an issue — quietly treats "too big
for this PR" as though it settled whether the PR was finished. It doesn't: a missing error case can
be too large to fix in the diff and still be something the PR shouldn't merge without. So there are
two questions: does it fit here, and if not, does the PR ship a defect without it. Only the second
can block, and its bar is deliberately concrete — wrong behaviour under some real circumstance, an
error path that loses work or data, documentation that misdescribes what shipped — because "is this
essential?" is a question an agent answers yes to almost every time, and a blocker list everything
lands on is just a slower issue tracker. `update-pr` and `copilot-review` park a blocker as a
`- [ ]` in the PR body, where `update-pr`'s checkbox pass re-decides it on every run; `wrap` lists
blockers first and says they block.

`update-pr` and `wrap` also both commit, push and think about follow-up issues, and I often run them
back to back, so having one call the other looks like an obvious cleanup. It isn't: the duplicated
mechanics are cheap, the judgement is what differs, and that is the part any factoring-out would
damage. The boundary between them is drawn narrow. `wrap` touches the PR in only two ways, neither a
rewrite: it says the description looks stale, since its own push is what made it stale, and it
offers to append its blockers as checkboxes. The second is the one that matters — before it, `wrap`
would find a blocker and print it to a terminal that was about to be closed, and the PR body is the
only place at hand that survives the session. Deciding whether a body is *wrong* stays `update-pr`'s
job, because it needs the diff read against it and is a worse job done hurriedly at the end of a
session.

## What earns a skill

Context dependent, and deliberately broad. Three rough patterns so far:

- **Something I keep doing by hand** (`wrap`, `update-pr`, `copilot-review`). Centralising it makes
  it reproducible across machines, and gives me one place where improvements can be recorded and
  tracked over time instead of being reinvented each session.
- **An experiment** (`sync-docs`) — either about what tasks an LLM can usefully take on, or about
  LLM use itself. I expect more of these: ticket triage, planning skills.
- **A rule that only bites at identifiable moments** (`github-issues`, `github-milestones`). Ambient
  conventions belong in memory or a `CLAUDE.md`; a rule with a trigger can be a skill, and gets to
  stay out of context until it is needed. Unproven — see that skill's section.

Not every skill here will finish, and that's fine. Some turn out not to be useful. Some get built
just far enough to unblock one project and then set aside for review when there's time. And the
ones that prove genuinely useful tend to leave — the way `process-babel-logs` became a script
inside Babel itself, so the code generating the logs and the code reading them live in one place. I
expect skills to graduate the same way.
