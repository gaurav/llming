"""Checks on the tidying the loader does — the only part with logic worth breaking."""

import io
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import audiobooks  # noqa: E402
from audiobooks import normalise_column, sheet_url, tidy  # noqa: E402

# A Sheets export in miniature: messy headers, a blank padding row and column, padded values.
SAMPLE = """Title,Author(s),Genre ,Date Finished,My Rating,Duration,Money,,
The Left Hand of Darkness,Ursula K. Le Guin,Science Fiction ,2024-03-02,5,11:57:00,$3.75,,
Piranesi,Susanna Clarke, Fantasy,2025-11-14,4,28:28:00,???,,
,,,,,,,,
"""


@pytest.fixture(autouse=True)
def no_real_sheet(monkeypatch):
    """
    With no local cache, the loader falls back to the enrichment tab named in .env. Keep every test
    here off the developer's real Sheet: no .env, and no gid left over in the environment.
    """
    monkeypatch.setattr(audiobooks, "load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("ENRICHMENT_GID", raising=False)


@pytest.fixture
def df():
    return tidy(pd.read_csv(io.StringIO(SAMPLE)))


def test_column_names_become_snake_case():
    assert normalise_column("Date Finished (est.)") == "date_finished_est"
    assert normalise_column("  My Rating  ") == "my_rating"


def test_blank_rows_and_columns_are_dropped(df):
    assert len(df) == 2
    assert list(df.columns)[:5] == ["title", "author_s", "genre", "date_finished", "my_rating"]


def test_duration_becomes_hours_past_the_24_hour_mark(df):
    # 28:28:00 is a real value in the sheet: to_timedelta has to not wrap it round a clock.
    assert df["duration_hours"].round(2).tolist() == [11.95, 28.47]


def test_money_becomes_a_number_and_unknowns_go_missing(df):
    # "???" is what the sheet holds where the price was never recorded.
    assert df["money"].tolist()[0] == 3.75
    assert pd.isna(df["money"].tolist()[1])


def test_date_columns_are_parsed_but_ratings_are_not(df):
    assert df["date_finished"].dt.year.tolist() == [2024, 2025]
    assert df["my_rating"].sum() == 9


def test_text_is_stripped_so_values_group(df):
    assert df["genre"].tolist() == ["Science Fiction", "Fantasy"]


@pytest.fixture
def env(monkeypatch):
    """Set the sheet variables directly, with the real .env stubbed out of the way."""

    def _env(**values):
        monkeypatch.setattr("audiobooks.load_dotenv", lambda *a, **k: False)
        for name in ("GOOGLE_SHEET_ID", "GOOGLE_SHEET_GID"):
            monkeypatch.delenv(name, raising=False)
        for name, value in values.items():
            monkeypatch.setenv(name, value)

    return _env


def test_sheet_url_says_what_to_do_when_env_is_missing(env):
    env()
    with pytest.raises(RuntimeError, match="env.default"):
        sheet_url()


def test_sheet_url_puts_the_id_and_gid_where_google_wants_them(env):
    env(GOOGLE_SHEET_ID="SHEET", GOOGLE_SHEET_GID="3")
    assert sheet_url() == "https://docs.google.com/spreadsheets/d/SHEET/export?format=csv&gid=3"


@pytest.mark.parametrize("gid", [None, "", "  "])
def test_gid_falls_back_to_the_first_tab(env, gid):
    # env.default ships GOOGLE_SHEET_GID=0, but a .env that drops or empties it still has to work.
    env(GOOGLE_SHEET_ID="SHEET", **({} if gid is None else {"GOOGLE_SHEET_GID": gid}))
    assert sheet_url().endswith("gid=0")


# --- genre normalisation and the Audible join -------------------------------------------------

GENRE_MAP = """
# specific genres sit above the catch-all, so a book with both ladders is Fantasy, not Literature
- genre: Fantasy
  fiction: true
  matches:
    - Science Fiction & Fantasy > Fantasy
- genre: Literature
  fiction: true
  matches:
    - Literature & Fiction > Genre Fiction > Literary Fiction
- genre: Fiction
  fiction: true
  matches:
    - Literature & Fiction
- genre: History
  fiction: false
- form: Radio drama
- genre: Comedy
  form: Radio drama
  matches:
    - Radio comedy
- genre: Comedy
"""


@pytest.fixture
def genre_map(tmp_path):
    path = tmp_path / "genre_map.yaml"
    path.write_text(GENRE_MAP)
    return audiobooks.read_genre_map(path)


def settle(genre_map, typed=None, grouping=None, categories=None):
    unmapped = set()
    return audiobooks.settle_genre(typed, grouping, categories, genre_map, unmapped), unmapped


def test_a_typed_genre_is_matched_whatever_its_case(genre_map):
    (genre, form, fiction, source), unmapped = settle(genre_map, typed="FICTION")
    assert (genre, fiction, source) == ("Fiction", True, "sheet") and not unmapped


def test_a_typed_genre_beats_audible(genre_map):
    result, _ = settle(genre_map, typed="History", categories="Science Fiction & Fantasy > Fantasy > Epic")
    assert result == ("History", None, False, "sheet")


def test_the_ladder_highest_in_the_map_wins_not_the_first_one_listed(genre_map):
    # Audible lists ladders alphabetically, which puts Literature ahead of nearly everything.
    categories = "Literature & Fiction > Genre Fiction > Literary Fiction; Science Fiction & Fantasy > Fantasy > Epic"
    assert settle(genre_map, categories=categories)[0] == ("Fantasy", None, True, "audible")


def test_a_ladder_matches_on_the_longest_prefix_the_map_lists(genre_map):
    # Three levels deep is what tells the literary shelf from fiction in general.
    assert settle(genre_map, categories="Literature & Fiction > Genre Fiction > Literary Fiction")[0][0] == "Literature"
    assert settle(genre_map, categories="Literature & Fiction > Genre Fiction > Westerns")[0][0] == "Fiction"


def test_a_ladder_falls_back_to_its_top_level(genre_map):
    assert settle(genre_map, categories="History > Europe > Great Britain")[0][0] == "History"


def test_a_form_in_the_genre_column_leaves_the_genre_to_audible(genre_map):
    result, _ = settle(genre_map, typed="Radio Drama", categories="History > Europe")
    assert result == ("History", "Radio drama", False, "audible")


def test_a_ladder_that_names_a_form_still_gets_its_genre_from_further_up(tmp_path):
    path = tmp_path / "genre_map.yaml"
    path.write_text(
        "- genre: Autobiography\n  matches: [Biographies & Memoirs]\n"
        "- genre: True crime\n  matches: [Biographies & Memoirs > True Crime]\n"
        "- genre: Fiction\n  matches: [Literature & Fiction]\n"
        "- form: Short stories\n  matches: [Literature & Fiction > Anthologies & Short Stories]\n"
    )
    genre_map = audiobooks.read_genre_map(path)
    stories = "Literature & Fiction > Anthologies & Short Stories > Short Stories"
    assert settle(genre_map, categories=stories)[0][:2] == ("Fiction", "Short stories")
    # But a ladder that already has a genre is not joined by its vaguer parent, however that ranks.
    assert settle(genre_map, categories="Biographies & Memoirs > True Crime > Murder")[0][0] == "True crime"


def test_a_genre_the_map_has_not_met_passes_through_and_is_reported(genre_map):
    (genre, *_), unmapped = settle(genre_map, typed="Solarpunk")
    assert genre == "Solarpunk" and unmapped == {"Solarpunk"}


def test_an_entry_with_a_genre_and_a_form_does_not_claim_the_bare_genre(genre_map):
    # "Radio comedy" is filed above plain Comedy here; typing "Comedy" must not gain a form from it.
    assert settle(genre_map, typed="Comedy")[0][:2] == ("Comedy", None)
    assert settle(genre_map, typed="Radio comedy")[0][:2] == ("Comedy", "Radio drama")


def test_a_value_listed_twice_is_refused(tmp_path):
    # A repeat would silently shadow the earlier entry, so the map refuses to load at all.
    path = tmp_path / "genre_map.yaml"
    path.write_text("- genre: Fantasy\n  matches: [Epic]\n- genre: Literature\n  matches: [epic]\n")
    with pytest.raises(ValueError, match="appears twice"):
        audiobooks.read_genre_map(path)


def test_a_genre_may_have_two_entries_at_different_heights(tmp_path):
    # Literary Fiction has to outrank Comedy while Classics stays below it, so Literature is listed
    # twice. Infinite Jest carries the first pair of ladders; My Man Jeeves the second.
    path = tmp_path / "genre_map.yaml"
    path.write_text(
        "- genre: Literature\n  matches: [Literature & Fiction > Genre Fiction > Literary Fiction]\n"
        "- genre: Comedy\n  matches: [Comedy & Humor]\n"
        "- genre: Literature\n  matches: [Literature & Fiction > Classics]\n"
    )
    genre_map = audiobooks.read_genre_map(path)
    literary = "Comedy & Humor > Literature & Fiction; Literature & Fiction > Genre Fiction > Literary Fiction"
    classic = "Comedy & Humor > Literature & Fiction; Literature & Fiction > Classics"
    assert settle(genre_map, categories=literary)[0][0] == "Literature"
    assert settle(genre_map, categories=classic)[0][0] == "Comedy"
    assert settle(genre_map, typed="literature")[0][0] == "Literature"


def test_the_committed_genre_map_loads():
    assert audiobooks.read_genre_map()["fantasy"][1] == "Fantasy"


def test_audible_fills_blanks_without_overriding_the_sheet(tmp_path, monkeypatch):
    cache = tmp_path / "enrichment.csv"
    cache.write_text(
        "key,status,asin,series,series_position,narrators,runtime_min,categories,summary\n"
        "B00WH5VZR8,matched,B00WH5VZR8,Some Series,2,Audible Narrator,600,History > Europe,A blurb\n"
        "piranesi|susannaclarke,matched,B0PIRANESI,,,Chiwetel Ejiofor,420,History,Another\n"
    )
    monkeypatch.setattr(audiobooks, "ENRICHMENT_CSV", cache)
    sheet = pd.DataFrame(
        {
            "title": ["Do No Harm", "Piranesi"],
            "author": ["Henry Marsh", "Susanna Clarke"],
            "url": ["https://www.audible.com/pd/Do-No-Harm-Audiobook/B00WH5VZR8", None],
            "narrator": ["Sheet Narrator", None],
            "duration_hours": [None, None],
            "finished": pd.to_datetime(["2024-01-01", None]),
            "finished_3_1": pd.to_datetime(["2025-06-01", None]),
        }
    )

    df = audiobooks.enriched(sheet)

    assert df.narrator.tolist() == ["Sheet Narrator", "Chiwetel Ejiofor"]
    assert df.duration_hours.tolist() == [10.0, 7.0]
    assert df.series_position.tolist()[0] == 2
    # The duplicated-header listen columns count too: the latest finish is the 2025 one.
    assert df.last_finished[0] == pd.Timestamp("2025-06-01")


def test_a_book_narrated_by_its_author_is_read_by_the_author_unless_a_form_was_typed(tmp_path, monkeypatch):
    monkeypatch.setattr(audiobooks, "ENRICHMENT_CSV", tmp_path / "absent.csv")
    sheet = pd.DataFrame(
        {
            "title": ["Born a Crime", "Piranesi", "Cabin Pressure"],
            "author": ["Trevor Noah", "Susanna Clarke", "John Finnemore"],
            "narrator": ["Trevor Noah", "Chiwetel Ejiofor", "John Finnemore, Roger Allam"],
            "grouping": [None, None, "Radio drama"],
        }
    )
    assert audiobooks.enriched(sheet).form.tolist() == ["Read by the author", None, "Radio drama"]


CACHE = (
    "key,status,asin,series,series_position,narrators,runtime_min,categories,summary\n"
    "593502388,matched,593502388,,,Someone,600,History,Sheets read this ASIN as a number\n"
    "B00WH5VZR8,matched,B00WH5VZR8,,,Someone,573,History,and left this one alone\n"
    "piranesi|susannaclarke,matched,1526622424,,,Someone,420,History,a title key is never padded\n"
)


def test_an_asin_that_sheets_turned_into_a_number_gets_its_leading_zero_back(tmp_path):
    path = tmp_path / "enrichment.csv"
    path.write_text(CACHE)
    cache = audiobooks.read_enrichment(path)
    assert cache.key.tolist() == ["0593502388", "B00WH5VZR8", "piranesi|susannaclarke"]
    assert cache.asin.tolist() == ["0593502388", "B00WH5VZR8", "1526622424"]


def test_with_no_local_cache_the_sheets_enrichment_tab_is_read_and_without_a_gid_nothing_is(tmp_path, monkeypatch):
    tab = tmp_path / "tab.csv"
    tab.write_text(CACHE)
    absent = tmp_path / "data" / "enrichment.csv"
    assert audiobooks.read_enrichment(absent) is None

    monkeypatch.setenv("ENRICHMENT_GID", "12345")
    monkeypatch.setattr(audiobooks, "sheet_url", lambda gid=None: str(tab) if gid == "12345" else "wrong tab")
    assert len(audiobooks.read_enrichment(absent)) == 3


def test_the_local_cache_is_preferred_to_the_tab(tmp_path, monkeypatch):
    # The tab is only as new as its last upload; the local file is what enrich.py just wrote.
    local = tmp_path / "enrichment.csv"
    local.write_text(CACHE)
    monkeypatch.setenv("ENRICHMENT_GID", "12345")
    monkeypatch.setattr(audiobooks, "sheet_url", lambda gid=None: pytest.fail("went to the Sheet"))
    assert len(audiobooks.read_enrichment(local)) == 3


def test_the_sheet_id_never_reaches_the_log(monkeypatch, caplog):
    # The Sheet is link-shared, so its ID is the access to it, and logs get pasted into transcripts.
    monkeypatch.setenv("GOOGLE_SHEET_ID", "SECRET-SHEET-ID")
    monkeypatch.setenv("ENRICHMENT_GID", "12345")
    monkeypatch.setattr(audiobooks, "ENRICHMENT_CSV", Path("/nonexistent/enrichment.csv"))
    fetched = []
    monkeypatch.setattr(pd, "read_csv", lambda source, **k: fetched.append(source) or pd.DataFrame(
        {"Title": ["Piranesi"], "Author": ["Susanna Clarke"], "key": ["x"], "status": ["matched"], **{c: [None] for c in audiobooks.AUDIBLE_COLUMNS}}
    ))
    with caplog.at_level("INFO"):
        audiobooks.load()
    assert len(fetched) == 2 and all("SECRET-SHEET-ID" in url for url in fetched)  # both tabs were read
    assert "SECRET-SHEET-ID" not in caplog.text
