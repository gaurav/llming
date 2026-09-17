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


def test_sheet_url_says_what_to_do_when_env_is_missing(monkeypatch):
    monkeypatch.setattr("audiobooks.load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("GOOGLE_SHEET_ID", raising=False)
    with pytest.raises(RuntimeError, match="env.default"):
        sheet_url()
