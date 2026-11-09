#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "click",
#     "pandas",
#     "python-dotenv",
#     "pyyaml",
# ]
# ///
"""
What to listen to next, for the two ways the library actually gets used.

    uv run recommend.py new data/audiobooks.csv --genre fantasy --max-hours 12
    uv run recommend.py relisten data/audiobooks.csv
    uv run recommend.py relisten data/audiobooks.csv --long-ago     # dig past the usual favourites
    uv run recommend.py taste data/audiobooks.csv                   # which genres have gone down best

`new` ranks what has not been listened to: the next book of a series already under way first, then
by how well the author, narrator and genre have gone down before. `relisten` ranks finished
fiction — something already known, to have on in the background.
"""

import logging

import click
import pandas as pd

from audiobooks import author_names, load, squash

# What a relisten is worth as a rating when there is none: the median rating of the books that
# were both rated and listened to twice or more.
RELISTENED_RATING = 4.25
# How many imaginary average books every author, narrator and genre starts with, so that a single
# five-star book does not crown its author. Higher is more sceptical.
SHRINKAGE = 2
WEIGHTS = {"author": 3, "narrator": 1.5, "genre": 1}

logger = logging.getLogger(__name__)


def affinity(df: pd.DataFrame) -> pd.Series:
    """How much each book was liked, 0-5: its rating, or a relisten standing in for one. Else NaN."""
    relistened = df["count"].ge(2).map({True: RELISTENED_RATING, False: float("nan")})
    return pd.concat([df.rating_0_5, relistened], axis=1).max(axis=1)


def group_affinity(df: pd.DataFrame, liked: pd.Series, column: str) -> pd.Series:
    """
    Each book's expected liking judged by `column` alone: the mean liking of the other books
    sharing its value, shrunk towards the library-wide mean. Books with nothing to go on get
    exactly that mean, so they neither gain nor lose.

    An author or narrator cell can name several people ("Terry Pratchett, Neil Gaiman"); each is
    judged on their own and the book takes the average, so a co-written book borrows from both
    authors' solo work. Series and genre are one value per cell and pass through the same code.
    """
    prior = liked.mean()
    people = df[column].map(lambda cell: sorted(author_names(cell)) or [cell]) if column in ("author", "narrator") else df[column]
    long = people.explode().dropna().rename("name").reset_index()  # one row per (book, name)
    long["liked"] = liked.loc[long["index"]].to_numpy()
    groups = long.groupby("name").liked
    # Leave the book's own rating out, or every finished book recommends itself.
    total = long.name.map(groups.sum()) - long.liked.fillna(0)
    n = long.name.map(groups.count()) - long.liked.notna()
    long["score"] = (total + prior * SHRINKAGE) / (n + SHRINKAGE)
    return long.groupby("index").score.mean().reindex(df.index).fillna(prior)


def next_in_series(df: pd.DataFrame, heard: pd.Series) -> pd.Series:
    """True for the earliest unheard book of each series that has at least one heard book."""
    in_series = df[df.series.notna()]
    under_way = set(in_series[heard.reindex(in_series.index)].series)
    unheard = in_series[~heard.reindex(in_series.index) & in_series.series.isin(under_way)]
    # Unnumbered books sort last, so a numbered sequel wins where there is one.
    first = unheard.sort_values("series_position", na_position="last").groupby("series").head(1)
    return df.index.isin(first.index)


def score(df: pd.DataFrame) -> pd.DataFrame:
    """Add `liked`, the per-column affinities, `next_in_series` and an overall `expected` liking."""
    df = df.copy()
    df["liked"] = affinity(df)
    for column in WEIGHTS:
        df[f"{column}_affinity"] = group_affinity(df, df.liked, column)
    df["expected"] = sum(df[f"{c}_affinity"] * w for c, w in WEIGHTS.items()) / sum(WEIGHTS.values())
    # Judged already, in this edition or another: the library holds some books twice over, and a
    # second copy of a book that has been heard is a relisten, not something new.
    work = df.title.map(squash) + "|" + df.author.map(squash)
    df["heard"] = df.status.isin(["Finished", "Finished?"]) | df["count"].ge(1) | df.liked.notna()
    df["heard"] = work.isin(work[df.heard])
    df["next_in_series"] = next_in_series(df, df.heard)
    df["series_affinity"] = group_affinity(df, df.liked, "series")
    return df


def why(row, prior: float) -> str:
    """The reasons behind a row's rank, in the order they mattered."""
    reasons = []
    if row.get("next_in_series"):
        position = f"#{row.series_position:g} in " if pd.notna(row.series_position) else "in "
        reasons.append(f"next {position}{row.series} (series at {row.series_affinity:.1f})")
    if pd.notna(row.liked):
        listens = f", heard {row['count']:g}x" if pd.notna(row["count"]) else ""
        reasons.append(f"you gave it {row.liked:g}{listens}")
    for column in WEIGHTS:
        if abs(row[f"{column}_affinity"] - prior) >= 0.15:
            reasons.append(f"{column} {row[column]} at {row[f'{column}_affinity']:.1f}")
    if row.get("status") in ("Started", "Reading") and pd.notna(row.last_started):
        reasons.append(f"stalled since {row.last_started:%Y-%m}")
    if row.get("returnable") == "Yes" and pd.notna(row.get("days_remaining")):
        reasons.append(f"returnable for {row.days_remaining:g} more days")
    return "; ".join(reasons)


def rank_new(df: pd.DataFrame) -> pd.DataFrame:
    """Unheard books, best bet first."""
    picks = df[df.status.isin(["Not started", "Started", "Reading"]) & ~df.heard].copy()
    picks["score"] = picks.expected
    # ponytail: one flat formula for the series pull — a liked series lifts its next book by up to
    # 2.5, a disliked one sinks it. Tune the 2.5 if sequels crowd out everything else.
    picks.loc[picks.next_in_series, "score"] += picks.series_affinity - 2.5
    picks.loc[picks.status != "Not started", "score"] -= 0.25  # a stall is a mild vote against
    return picks.sort_values("score", ascending=False)


def rank_relisten(df: pd.DataFrame, long_ago: bool) -> pd.DataFrame:
    """Books already heard, best background listen first."""
    picks = df[df.status.isin(["Finished", "Finished?"]) | df["count"].ge(1)].copy()
    picks = picks.sort_values("count", ascending=False).drop_duplicates(["title", "author"])  # one edition each
    # Its own rating where there is one; otherwise what its author, narrator and genre suggest.
    picks["score"] = picks.liked.fillna(picks.expected) + 0.1 * picks["count"].clip(upper=5).fillna(0)
    if long_ago:
        # Half a point per year since the last listen, up to three years. No finish date on
        # record means it was long enough ago that nobody wrote it down.
        years = (pd.Timestamp.now() - picks.last_finished).dt.days / 365
        picks["score"] += 0.5 * years.fillna(3).clip(upper=3)
    return picks.sort_values(["score", "duration_hours"], ascending=False)


def taste(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """
    How each genre (or author, narrator, series, form) has gone down so far, best first, beside
    how much of it is still waiting. `score` is the mean shrunk exactly as the rankings shrink it,
    so a genre with one five-star book does not top the table; `mean` is the plain one.
    """
    prior, groups = df.liked.mean(), df.groupby(by)
    table = pd.DataFrame({"rated": groups.liked.count(), "mean": groups.liked.mean(), "owned": groups.size()})
    table["score"] = (groups.liked.sum() + prior * SHRINKAGE) / (table.rated + SHRINKAGE)
    table["unheard"] = (~df.heard & df.status.eq("Not started")).groupby(df[by]).sum()
    return table[table.rated > 0].sort_values("score", ascending=False)


@click.command()
@click.argument("mode", type=click.Choice(["new", "relisten", "taste"]))
@click.argument("source", required=False)
@click.option("--genre", help="A genre (fantasy), or any part of an Audible category (detectives).")
@click.option("--form", help="A form from genre_map.yaml: 'radio drama', 'read by the author', 'short stories'.")
@click.option("--fiction/--non-fiction", default=None, help="[default: both for new; anything not known to be non-fiction for relisten]")
@click.option("--min-hours", type=float)
@click.option("--max-hours", type=float)
@click.option("--long-ago", is_flag=True, help="relisten: favour what was last heard longest ago.")
@click.option("--by", default="genre", show_default=True, type=click.Choice(["genre", "form", "author", "narrator", "series"]), help="taste: what to group on.")
@click.option("-n", "count", default=20, show_default=True, help="How many to list.")
@click.option("--csv", "as_csv", is_flag=True, help="Print CSV with every column, to hand to something else.")
def main(mode, source, genre, form, fiction, min_hours, max_hours, long_ago, by, count, as_csv) -> None:
    """Recommend books for MODE from SOURCE (a CSV from download_sheet.py; default: the live Sheet)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    df = score(load(source))
    prior = df.liked.mean()

    if mode == "taste":
        if fiction is not None:
            df = df[df.fiction == fiction]
        table = taste(df, by).head(count)
        click.echo(f"{'score':>5}  {'mean':>5}  {'rated':>5}  {'owned':>5}  {'unheard':>7}  {by}   (library mean {prior:.2f})")
        for name, row in table.iterrows():
            click.echo(f"{row.score:5.2f}  {row['mean']:5.2f}  {row.rated:5.0f}  {row.owned:5.0f}  {row.unheard:7.0f}  {name}")
        return

    picks = rank_new(df) if mode == "new" else rank_relisten(df, long_ago)
    if fiction is not None:
        picks = picks[picks.fiction == fiction]
    elif mode == "relisten":
        # Background listening wants a story. Only what is known to be non-fiction goes: the map
        # leaves Comedy and Poetry undecided, and those stay in unless --fiction insists.
        picks = picks[picks.fiction != False]  # noqa: E712
    # fillna before .str: with no Audible cache yet, or no forms typed, these columns are entirely
    # empty, which pandas reads as numbers and refuses to treat as text.
    if genre:
        in_categories = picks.categories.fillna("").astype(str).str.contains(genre, case=False, regex=False)
        picks = picks[picks.genre.fillna("").astype(str).str.lower().eq(genre.lower()) | in_categories]
    if form:
        picks = picks[picks.form.fillna("").astype(str).str.lower() == form.lower()]
    if min_hours:
        picks = picks[picks.duration_hours >= min_hours]
    if max_hours:
        picks = picks[picks.duration_hours <= max_hours]
    picks = picks.head(count).copy()
    picks["why"] = [why(row, prior) for _, row in picks.iterrows()]

    if as_csv:
        click.echo(picks.to_csv(index=False))
        return
    # Laid out by hand rather than with to_string(): pandas right-aligns text, which pushes the
    # why column — the one worth reading — off the edge of the screen.
    layout = "{:>5}  {:>5}  {:<40}  {:<25}  {:<18}  {}"
    click.echo(layout.format("score", "hours", "title", "author", "genre", "why"))
    for row in picks.fillna({"title": "", "author": "", "genre": ""}).itertuples():
        hours = f"{row.duration_hours:.1f}" if pd.notna(row.duration_hours) else ""
        click.echo(layout.format(f"{row.score:.1f}", hours, row.title[:40], row.author[:25], row.genre[:18], row.why))


if __name__ == "__main__":
    main()
