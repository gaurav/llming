---
name: github-milestones
description: How the user's GitHub milestones work — bucket milestones (Critical, Needed soon, Needed later, Not urgent, Upstream) versus release and deadline milestones, when to put an issue on one, how a milestone becomes a release, and when to suggest moving a due date. Use before setting or changing an issue's milestone, creating, editing or closing a milestone, planning or cutting a release, or choosing what to work on next from a repository's milestones.
---

# github-milestones

Milestones come in two kinds, and nearly every mistake with them is treating one kind as the
other: a bucket read as a deadline, or a soft release date read as an alarm.

These are the user's conventions, for repositories where they run the milestones. A repository that
documents its own scheme — or says to track releases in a GitHub Project — in its `CLAUDE.md`,
`CONTRIBUTING.md` or README follows that instead.

## See what a repository has

```bash
gh api "repos/<owner>/<repo>/milestones?state=open" --paginate \
  --jq '.[] | "\(.number)\t\(.title)\t\(.due_on // "undated")\t\(.open_issues) open"'
```

## Buckets

The buckets, what each one means, and the rules for them live in `MILESTONES.md` in the
`gaurav/milestones` repository. Read it before putting an issue in a bucket or touching a bucket
milestone:

```bash
gh api repos/gaurav/milestones/contents/MILESTONES.md --jq .content | base64 -d
```

If it can't be fetched, say so and leave buckets alone rather than working from the names.

## Release and deadline milestones

Named for a release (`tool-name v1.2`) or a date (`2026aug22`). These are usually dated, and the
date means one of two things:

- **Hard or semi-hard** — a delivery expected for testing on that date, or the last day a build can
  start and still finish before another deadline.
- **Soft** — in a repository whose last release was v1.1, `v1.2` can simply mean *the next release,
  whenever that is*: ranked above Needed soon, with a date that is a hope.

Most are soft, so most drift into the past. A soft milestone being past due is normal and not
something to report.

## Milestones are releases

Unless the repository says otherwise, a release milestone's issues are what the release contains.
The release is built from them and published as a GitHub release, after which the milestone is
closed. Closing it is part of that outward-facing step: ask first, as for the release itself.

## Putting an issue on a milestone

Every issue should end up on a milestone — a bucket, or a release it is needed for — but that is
the user's triage to do, not yours. Leave a new or untouched issue unmilestoned unless it is
*clearly* Critical or clearly needed for a particular release — the user's triage workflow picks up
anything without a milestone. A guessed bucket hides an issue from that workflow, which is worse
than no bucket.

```bash
gh issue edit <N> --repo <owner>/<repo> --milestone "<title>"
gh issue create --repo <owner>/<repo> --milestone "<title>" ...
```

Whose issue it is doesn't matter here: setting a milestone is triage, which the `github-issues`
skill allows on anyone's issue.

## Nudging about a due date

Suggest a due-date change and let the user make it; don't edit the milestone yourself. A date being
in the past is not by itself worth mentioning — most are soft. What is worth mentioning:

- **A milestone really is urgent** and its date doesn't show it: a hard deadline mentioned in an
  issue or in conversation, Critical issues accumulating ahead of a release, an upstream contact
  that has to happen soon. Say which milestone, what date, and what the evidence was.
- **A hard deadline is at risk** — close or already passed, with issues still open.
- **An urgency date has outlived the urgency** — a bucket still carrying a deadline that has passed
  and no longer matters. Suggest removing it.

This is about due dates only. Anything else that looks wrong with a milestone, raise as you would
anywhere else.

## Writing a due date

When the user asks for a milestone with a due date, or for a new date on one, send `due_on` as
**noon UTC** on that day and read it back. GitHub keeps only the date, and a midnight-UTC timestamp
can land on the day before: `2027-01-06T00:00:00Z` was stored as `2027-01-05T00:00:00Z`, while
`2027-01-06T12:00:00Z` was stored as `2027-01-06T00:00:00Z`, the intended date.

```bash
gh api repos/<owner>/<repo>/milestones -f title="<title>" -f due_on="<YYYY-MM-DD>T12:00:00Z" \
  --jq '"\(.number) \(.title) \(.due_on)"'
gh api -X PATCH repos/<owner>/<repo>/milestones/<N> -f due_on="<YYYY-MM-DD>T12:00:00Z" --jq .due_on
```

The returned `due_on` reads as midnight UTC on the stored date. If that isn't the date asked for,
fix it before reporting the milestone as made.
