"""Checks on the tidying the loader does — the only part with logic worth breaking."""

import io
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audiobooks import normalise_column, sheet_url, tidy  # noqa: E402

# A Sheets export in miniature: messy headers, a blank padding row and column, padded values.
SAMPLE = """Title,Author(s),Genre ,Date Finished,My Rating,Duration,Money,,
The Left Hand of Darkness,Ursula K. Le Guin,Science Fiction ,2024-03-02,5,11:57:00,$3.75,,
Piranesi,Susanna Clarke, Fantasy,2025-11-14,4,28:28:00,???,,
,,,,,,,,
"""


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
