#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "pandas",
#     "python-dotenv",
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

import pandas as pd
from dotenv import load_dotenv

# Google's CSV export endpoint. Works without credentials as long as the Sheet is shared with
# "anyone with the link", which is what this whole approach relies on.
EXPORT_URL = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

# Columns whose *name* says they hold a date get parsed as dates. Deliberately name-driven rather
# than sniffing every column's contents: sniffing turns ratings, years and "3/5" into timestamps.
DATE_COLUMN_HINT = re.compile(r"date|started|finished|purchased|bought|added|released", re.I)

logger = logging.getLogger(__name__)


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


def load(source: str = None) -> pd.DataFrame:
    """Load the library. `source` is a path or URL; the Sheet from .env is the default."""
    source = source or sheet_url()
    logger.info("Reading audiobook library from %s", source)
    return tidy(pd.read_csv(source))


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
