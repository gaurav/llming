"""Checks on the ranking — that the signals pull the way they are meant to."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import recommend  # noqa: E402

NOW = pd.Timestamp.now()


def book(title, author, status="Not started", rating=None, count=None, series=None, position=None, finished=None):
    return {
        "title": title, "author": author, "narrator": None, "genre": "Fantasy", "status": status,
        "rating_0_5": rating, "count": count, "series": series, "series_position": position,
        "last_finished": finished, "last_started": None, "duration_hours": 10.0,
    }  # fmt: skip


@pytest.fixture
def library():
    return recommend.score(
        pd.DataFrame(
            [
                book("Loved One", "Series Author", "Finished", rating=5, count=1, series="Saga", position=1),
                book("Loved Two", "Series Author", series="Saga", position=2),
                book("Loved Three", "Series Author", series="Saga", position=3),
                book("Standalone", "Liked Author"),
                book("Liked Before", "Liked Author", "Finished", rating=4.5, count=1, finished=NOW - pd.Timedelta(days=30)),
                book("Meh Before", "Meh Author", "Finished", rating=2, count=1),
                book("Meh Again", "Meh Author"),
                book("Unrated Favourite", "Quiet Author", "Finished", count=3, finished=NOW - pd.Timedelta(days=1500)),
                book("Recent Favourite", "Loud Author", "Finished", rating=4.5, count=1, finished=NOW - pd.Timedelta(days=10)),
                book("Loved One", "Series Author", series="Saga", position=1),  # a second edition, unheard
                book("Given Up On", "Meh Author", "Started", rating=1),
            ]
        )
    )


def test_the_next_book_in_a_liked_series_comes_first_and_only_the_next(library):
    ranked = recommend.rank_new(library).title.tolist()
    assert ranked[0] == "Loved Two"
    # Book three is not "next" until two is heard, so it ranks on its author alone, like any other.
    assert not library.set_index("title").next_in_series["Loved Three"]
    assert ranked.index("Standalone") < ranked.index("Meh Again")


def test_another_edition_of_a_heard_book_and_a_book_already_rated_are_not_new(library):
    ranked = recommend.rank_new(library).title.tolist()
    assert "Loved One" not in ranked and "Given Up On" not in ranked


def test_a_book_with_no_narrator_is_judged_at_the_mean_on_that_count(library):
    # Every book here lacks a narrator. Subtracting each one's own rating from a group it was never
    # in is what once produced "narrator nan at 2.4".
    assert library.narrator_affinity.tolist() == pytest.approx([library.liked.mean()] * len(library))


def test_a_book_does_not_vouch_for_itself(library):
    # Meh Author's rated books sink "Meh Again". But "Recent Favourite" is its author's only book,
    # so with its own rating left out there is nothing to go on, and it sits at the library mean.
    by_title = library.set_index("title")
    assert by_title.author_affinity["Recent Favourite"] == pytest.approx(library.liked.mean())
    assert by_title.author_affinity["Meh Again"] < library.liked.mean()


def test_an_unrated_relisten_counts_as_liked(library):
    assert library.set_index("title").liked["Unrated Favourite"] == recommend.RELISTENED_RATING


def test_long_ago_digs_past_the_recent_favourite(library):
    usual = recommend.rank_relisten(library, long_ago=False).title.tolist()
    deeper = recommend.rank_relisten(library, long_ago=True).title.tolist()
    assert usual.index("Recent Favourite") < usual.index("Unrated Favourite")
    assert deeper.index("Unrated Favourite") < deeper.index("Recent Favourite")
    assert "Loved Two" not in usual  # never heard, so never a relisten


def test_taste_ranks_groups_by_shrunk_mean_and_counts_what_is_waiting(library):
    table = recommend.taste(library, "author")
    # Meh Author is rated twice, both badly; one bad book would have been pulled back to the mean.
    assert table.index[-1] == "Meh Author"
    assert table.loc["Meh Author", "mean"] < table.loc["Meh Author", "score"] < library.liked.mean()
    # Two Saga sequels wait unheard; the second edition of the heard first book is not one of them.
    assert table.loc["Series Author", "unheard"] == 2
    assert table.rated.min() > 0  # an author with nothing rated has no taste to report
