#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "pandas",
#     "python-dotenv",
#     "pyyaml",
# ]
# ///
"""
Loader for the audiobook library sheet.

Reads the Google Sheet straight off the internet (the default) or a CSV previously saved by
download_sheet.py, and hands back a pandas DataFrame with tidied column names and types.

    from audiobooks import load
    df = load()                          # live, from the Sheet ID in .env
    df = load("data/audiobooks.csv")     # the downloaded copy

Run it directly to print what the sheet actually contains:  uv run audiobooks.py
"""

import logging
import os
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

# Google's CSV export endpoint. Works without credentials as long as the Sheet is shared with
# "anyone with the link", which is what this whole approach relies on.
EXPORT_URL = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

# Columns whose *name* says they hold a date get parsed as dates. Deliberately name-driven rather
# than sniffing every column's contents: sniffing turns ratings, years and "3/5" into timestamps.
DATE_COLUMN_HINT = re.compile(r"date|started|finished|purchased|bought|added|released", re.I)

# The ASIN is the last path segment of an Audible product URL: .../pd/Do-No-Harm-Audiobook/B00WH5VZR8
# Ten characters, either B0-style or an ISBN-10 (which can end in X).
ASIN_IN_URL = re.compile(r"audible\.[a-z.]+/pd/(?:[^/?#]+/)?([0-9A-Z]{10})(?:[/?#]|$)")

# Both sit beside this file rather than under the working directory, so load() finds them from
# anywhere. The cache is written by enrich.py; the genre map is committed and edited by hand.
ENRICHMENT_CSV = Path(__file__).parent / "data" / "enrichment.csv"
GENRE_MAP_YAML = Path(__file__).parent / "genre_map.yaml"
SHEET_COLUMNS = ["title", "author", "url", "genre", "grouping", "narrator", "duration_hours", "started", "finished"]
AUDIBLE_COLUMNS = ["asin", "series", "series_position", "narrators", "runtime_min", "categories", "summary"]

logger = logging.getLogger(__name__)


def asin_from_url(url) -> str:
    """The Audible ASIN inside a product URL, or '' for anything else (Libro.fm, blank, NaN)."""
    match = ASIN_IN_URL.search(url) if isinstance(url, str) else None
    return match.group(1) if match else ""


def squash(text) -> str:
    """'J. M. Barrie' and 'J.M. Barrié' both -> 'jmbarrie'. For comparing names, never for display."""
    if not isinstance(text, str):
        return ""
    ascii_only = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^0-9a-z]+", "", ascii_only.lower())


def book_key(title, author, url) -> str:
    """What enrichment is keyed on: the ASIN where the Sheet has one, else squashed title|author."""
    return asin_from_url(url) or f"{squash(title)}|{squash(author)}"


def sheet_url() -> str:
    """Build the CSV export URL from the Sheet ID in .env. Raises if .env is not set up."""
    load_dotenv()
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", "").strip()
    if not sheet_id:
        raise RuntimeError(
            "GOOGLE_SHEET_ID is not set. Copy env.default to .env and put your Sheet ID in it."
        )
    return EXPORT_URL.format(sheet_id=sheet_id, gid=os.environ.get("GOOGLE_SHEET_GID", "0").strip() or "0")


def normalise_column(name: str) -> str:
    """'Date Finished (est.)' -> 'date_finished_est'. Stable enough to write code against."""
    return re.sub(r"_+", "_", re.sub(r"[^0-9a-z]+", "_", str(name).strip().lower())).strip("_")


def tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names, drop empty rows/columns, and parse the date-looking columns."""
    df = df.copy()
    df.columns = [normalise_column(c) for c in df.columns]
    # Sheets pads exports with trailing blank rows and unnamed blank columns; both are noise.
    df = df.drop(columns=[c for c in df.columns if not c or c.startswith("unnamed")], errors="ignore")
    df = df.dropna(axis="index", how="all").dropna(axis="columns", how="all")

    for column in df.columns:
        if DATE_COLUMN_HINT.search(column) and not pd.api.types.is_numeric_dtype(df[column]):
            df[column] = pd.to_datetime(df[column], errors="coerce", format="mixed")

    # Strip whitespace off every text value, so "Fantasy " and "Fantasy" group together.
    # map over every column rather than selecting text ones: the dtype names for strings keep
    # moving between pandas versions, and non-strings fall through the isinstance untouched.
    for column in df.columns:
        df[column] = df[column].map(lambda v: v.strip() if isinstance(v, str) else v)

    # Two columns the Sheet keeps as text that only answer questions as numbers. Both are added
    # alongside, not over, the originals where the original still reads better ("11:57:00").
    if "duration" in df.columns:
        df["duration_hours"] = pd.to_timedelta(df["duration"], errors="coerce").dt.total_seconds() / 3600
    if "money" in df.columns:
        df["money"] = pd.to_numeric(
            df["money"].str.replace(r"[^0-9.]", "", regex=True), errors="coerce"
        )

    return df.reset_index(drop=True)


def read_genre_map(path=None) -> dict:
    """
    genre_map.yaml flattened to {lowercased raw value: (rank, genre, form, fiction)}. The rank is
    the entry's position in the file, and it matters: a book with several Audible ladders takes
    the genre of whichever ranks first, so specific genres sit above catch-alls like Literature.
    """
    with open(path or GENRE_MAP_YAML) as f:
        entries = yaml.safe_load(f)
    lookup = {}
    for rank, entry in enumerate(entries):
        genre, form = entry.get("genre", ""), entry.get("form", "")
        value = (rank, genre, form, entry.get("fiction"))
        # An entry matches its own name as well as what is listed under it. One with both a genre
        # and a form is a special case ("Radio comedy" is Comedy *and* Radio drama) and owns neither.
        own_name = [] if (genre and form) or not (genre or form) else [genre or form]
        for raw in [*own_name, *entry.get("matches", [])]:
            key = str(raw).strip().lower()
            if key in lookup:  # a repeat would silently shadow the earlier entry
                raise ValueError(f"{raw!r} appears twice in {path or GENRE_MAP_YAML}")
            lookup[key] = value
    return lookup


def ladder_entries(categories, genre_map) -> list:
    """Map entries for a book's Audible ladders: each ladder at two levels, else at its top level."""
    entries = []
    for ladder in str(categories).split(";") if isinstance(categories, str) else []:
        levels = [level.strip().lower() for level in ladder.split(">")]
        entry = genre_map.get(" > ".join(levels[:2])) or genre_map.get(levels[0])
        if entry:
            entries.append(entry)
    return sorted(entries)


def settle_genre(typed, grouping, categories, genre_map, unmapped) -> tuple:
    """
    (genre, form, fiction, source) for one book. What was typed into the Sheet always wins; Audible
    only fills a blank. Values the map has not met are added to `unmapped`.
    """
    genre = form = fiction = source = None
    # The genre column first, then grouping: grouping is mostly form, but holds a few genres too.
    for value, is_genre_column in ((typed, True), (grouping, False)):
        if not isinstance(value, str):
            continue
        entry = genre_map.get(value.lower())
        if entry is None:  # a new genre typed into the Sheet passes through as itself
            unmapped.add(value)
            entry = (0, value if is_genre_column else "", "", None)
        if entry[1] and not genre:
            _, genre, _, fiction = entry
            source = "sheet"
        form = form or entry[2] or None
    for _, ladder_genre, ladder_form, ladder_fiction in ladder_entries(categories, genre_map):
        if ladder_genre and not genre:
            genre, fiction, source = ladder_genre, ladder_fiction, "audible"
        form = form or ladder_form or None
    return genre, form, fiction, source


def enriched(df: pd.DataFrame) -> pd.DataFrame:
    """
    Join the Audible metadata cached by enrich.py, then settle each book's genre through
    genre_map.yaml — which is what lets the Sheet stay free-text and still group cleanly.
    """
    # Every column used below exists afterwards, empty if the Sheet lacks it.
    df = df.reindex(columns=list(dict.fromkeys([*df.columns, *SHEET_COLUMNS])))
    df["key"] = [book_key(t, a, u) for t, a, u in zip(df.title, df.author, df.url)]
    if ENRICHMENT_CSV.exists():
        extra = pd.read_csv(ENRICHMENT_CSV)
        extra = extra[extra.status == "matched"].drop_duplicates("key")
        df = df.merge(extra[["key", *AUDIBLE_COLUMNS]], on="key", how="left")
    else:
        logger.info("No %s yet; run enrich.py to fill genres and series from Audible", ENRICHMENT_CSV)
        df = df.reindex(columns=[*df.columns, *AUDIBLE_COLUMNS])

    genre_map, unmapped = read_genre_map(), set()
    settled = [settle_genre(*row, genre_map, unmapped) for row in zip(df.genre, df.grouping, df.categories)]
    df["genre_raw"] = df.genre
    for position, column in enumerate(["genre", "form", "fiction", "genre_source"]):
        df[column] = pd.Series([row[position] for row in settled], index=df.index, dtype=object)
    if unmapped:
        logger.info("Not in genre_map.yaml, passed through as typed: %s", ", ".join(sorted(unmapped)))

    # Audible fills what the Sheet leaves blank, and never overrides it.
    df["narrator"] = df.narrator.fillna(df.narrators)
    df["duration_hours"] = pd.to_numeric(df.duration_hours).fillna(pd.to_numeric(df.runtime_min) / 60)
    df["series_position"] = pd.to_numeric(df.series_position, errors="coerce")
    # The Sheet repeats started/finished once per listen; the latest of each is what ranking needs.
    for stem in ("started", "finished"):
        columns = [c for c in df.columns if re.fullmatch(rf"{stem}(_[0-9_]+)?", c)]
        df[f"last_{stem}"] = df[columns].apply(pd.to_datetime, errors="coerce").max(axis=1)
    return df.drop(columns=["narrators", "runtime_min"])


def load(source: str = None, enrich: bool = True) -> pd.DataFrame:
    """
    Load the library. `source` is a path or URL; the Sheet from .env is the default. `enrich=False`
    hands back the Sheet alone, without the Audible metadata or the genre normalisation.
    """
    source = source or sheet_url()
    logger.info("Reading audiobook library from %s", source)
    df = tidy(pd.read_csv(source))
    return enriched(df) if enrich else df


def main() -> None:
    """Print what the sheet holds — the fastest way to see whether the loader got it right."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    df = load(sys.argv[1] if len(sys.argv) > 1 else None)

    print(f"\n{len(df):,} audiobooks, {len(df.columns)} columns\n")
    summary = pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "filled": df.notna().sum(),
            "distinct": df.nunique(),
            "example": [df[c].dropna().iloc[0] if df[c].notna().any() else "" for c in df.columns],
        }
    )
    with pd.option_context("display.max_colwidth", 40, "display.width", 120):
        print(summary.to_string())


if __name__ == "__main__":
    main()
