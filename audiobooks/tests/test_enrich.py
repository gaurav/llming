"""Checks on the Audible matcher — the one place a loose match would quietly mislabel a book."""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import enrich  # noqa: E402
from audiobooks import asin_from_id, asin_from_url, book_key  # noqa: E402


def product(asin, title, author, sequence="", narrator="Someone", subtitle=None):
    return {
        "asin": asin,
        "title": title,
        "subtitle": subtitle,
        "authors": [{"name": author}],
        "narrators": [{"name": narrator}],
        "series": [{"title": "Truly Devious", "sequence": sequence}],
        "category_ladders": [{"ladder": [{"name": "Teen & Young Adult"}, {"name": "Mystery"}]}],
        "merchandising_summary": "<p>A school &amp; a murder.</p>",
    }


class FakeSession:
    """Answers every GET with the same canned JSON."""

    def __init__(self, payload):
        self.payload = payload

    def get(self, *args, **kwargs):
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: self.payload)


def row(title, author, url=None, narrator=None):
    return SimpleNamespace(key=book_key(title, author, url), title=title, author=author, narrator=narrator)


def test_asin_comes_out_of_audible_urls_only():
    assert asin_from_url("https://www.audible.com/pd/Do-No-Harm-Audiobook/B00WH5VZR8") == "B00WH5VZR8"
    assert asin_from_url("https://www.audible.com/pd/Unwinding-Anxiety-Audiobook/0593409469?ref=x") == "0593409469"
    assert asin_from_url("https://libro.fm/audiobooks/9781478971238-the-terror") == ""
    assert asin_from_url(float("nan")) == ""


def test_the_audible_id_cell_takes_a_link_or_a_bare_asin_and_nothing_else():
    assert asin_from_id("https://www.audible.com/pd/Infinite-Jest-Audiobook/B0CZ4XD7HH") == "B0CZ4XD7HH"
    assert asin_from_id(" b0cz4xd7hh ") == "B0CZ4XD7HH"
    assert asin_from_id("593409469") == "0593409469"  # Sheets read it as a number and ate the zero
    assert asin_from_id("not on Audible") == "" and asin_from_id("BIOGRAPHY") == ""
    assert asin_from_id(float("nan")) == ""


def test_a_book_bought_elsewhere_is_keyed_on_its_audible_id_not_its_libro_fm_url():
    libro = "https://libro.fm/audiobooks/9781668642726"
    assert book_key("Infinite Jest (30th Anniv Ed)", "David Foster Wallace", libro, "B0CZ4XD7HH") == "B0CZ4XD7HH"
    assert book_key("Infinite Jest (30th Anniv Ed)", "David Foster Wallace", libro).endswith("|davidfosterwallace")
    # It also overrules the ASIN in an Audible URL, which is how a wrong edition gets corrected.
    audible = "https://www.audible.com/pd/Do-No-Harm-Audiobook/B00WH5VZR8"
    assert book_key("Do No Harm", "Henry Marsh", audible, "B0OTHERED1") == "B0OTHERED1"


def test_the_right_book_is_picked_when_the_series_sequel_comes_first():
    # What Audible really returns for "Truly Devious": a later book in the series ahead of book one.
    products = [
        product("B0SEQUEL00", "Nine Liars", "Maureen Johnson", "5"),
        product("B0774Y5HRR", "Truly Devious", "Maureen Johnson", "1"),
    ]
    assert enrich.pick_match("Truly Devious", "Maureen Johnson", None, products)["asin"] == "B0774Y5HRR"


def test_a_subtitle_in_the_sheet_and_a_role_on_the_author_still_match():
    products = [product("B0BABEL000", "Babel", "R. F. Kuang", subtitle="Or the Necessity of Violence")]
    match = enrich.pick_match("Babel: Or the Necessity of Violence", "R.F. Kuang, Someone Else (translator)", None, products)
    assert match["asin"] == "B0BABEL000"


def test_credentials_on_either_side_do_not_stop_an_author_matching():
    products = [product("B0PAIN0000", "Tell Me Where It Hurts", "Rachel Zoffness Ph.D")]
    assert enrich.pick_match("Tell Me Where It Hurts", "Rachel Zoffness, PhD", None, products)["asin"] == "B0PAIN0000"


def test_a_shared_series_prefix_is_not_a_match():
    products = [product("B0HEIR0000", "Star Wars: Heir to the Empire", "Timothy Zahn")]
    assert enrich.pick_match("Star Wars: Thrawn", "Timothy Zahn", None, products) is None


def test_a_bracketed_note_on_one_side_is_ignored_but_not_on_both():
    jeeves = [product("B0JEEVES00", "Right Ho, Jeeves", "P. G. Wodehouse")]
    assert enrich.pick_match("Right Ho, Jeeves (Dramatised)", "P. G. Wodehouse", None, jeeves)["asin"] == "B0JEEVES00"
    season_two = [product("B0SEASON20", "Upstanders (Season 2)", "Howard Schultz")]
    assert enrich.pick_match("Upstanders (Season 1)", "Howard Schultz", None, season_two) is None


def test_the_narrator_breaks_a_tie_between_editions():
    products = [
        product("B0FIRST000", "Great Expectations", "Charles Dickens", narrator="Simon Prebble"),
        product("B0SECOND00", "Great Expectations", "Charles Dickens", narrator="Martin Jarvis"),
    ]
    assert enrich.pick_match("Great Expectations", "Charles Dickens", "Martin Jarvis", products)["asin"] == "B0SECOND00"


def test_a_near_miss_goes_to_review_rather_than_being_accepted():
    session = FakeSession({"products": [product("B0OTHER000", "Truly Devious: The Graphic Novel Companion", "Someone Else")]})
    found = enrich.look_up(session, row("Truly Devious", "Maureen Johnson"))
    assert found["status"] == "review"
    assert "B0OTHER000" in found["candidates"]


def test_an_asin_audible_no_longer_sells_is_not_found():
    # Audible answers 200 with a product that holds nothing but the asin.
    session = FakeSession({"product": {"asin": "B00WH5VZR8"}})
    url = "https://www.audible.com/pd/Do-No-Harm-Audiobook/B00WH5VZR8"
    assert enrich.look_up(session, row("Do No Harm", "Henry Marsh", url)) == {"status": "not_found"}


def test_a_match_is_flattened_to_plain_columns():
    session = FakeSession({"products": [product("B0774Y5HRR", "Truly Devious", "Maureen Johnson", "1")]})
    found = enrich.look_up(session, row("Truly Devious", "Maureen Johnson"))
    assert found["series"] == "Truly Devious" and found["series_position"] == "1"
    assert found["categories"] == "Teen & Young Adult > Mystery"
    assert found["summary"] == "A school & a murder."
