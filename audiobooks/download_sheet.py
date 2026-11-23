#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "click",
#     "pandas",
#     "python-dotenv",
#     "pyyaml",
#     "requests",
# ]
# ///
"""
Download the master tab of the audiobook Google Sheet into data/ as CSV.

    uv run download_sheet.py 2>&1 | tee data/last-run.log

The Sheet ID and tab gid come from .env (copy env.default to .env first). The file is saved
byte-for-byte as Google exports it, so the loader sees exactly what the Sheet says.
"""

import logging
from pathlib import Path

import click
import requests

from audiobooks import load, sheet_url

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--output",
    default="data/audiobooks.csv",
    show_default=True,
    type=click.Path(dir_okay=False),
    help="Where to write the CSV.",
)
def main(output: str) -> None:
    """Fetch the audiobook sheet and save it to OUTPUT."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    try:
        url = sheet_url()
    except RuntimeError as e:  # no .env yet — a traceback helps nobody
        raise click.ClickException(str(e))
    logger.info("Downloading the Sheet's master tab")  # not its URL: that carries the Sheet ID
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    # An unshared Sheet answers 200 with a sign-in page rather than an error, so check the type.
    if "text/csv" not in response.headers.get("content-type", ""):
        raise click.ClickException(
            f"Google returned {response.headers.get('content-type')!r}, not CSV. The Sheet is "
            "probably not shared: set its access to 'Anyone with the link'. Check the ID and gid too."
        )

    # data/ is gitignored, so it is absent after a fresh clone — and it is where --output defaults.
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as f:
        f.write(response.content)
    logger.info("Wrote %s (%d bytes)", output, len(response.content))

    df = load(output)
    logger.info("Parsed %d audiobooks with %d columns: %s", len(df), len(df.columns), ", ".join(df.columns))


if __name__ == "__main__":
    main()
