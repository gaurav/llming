#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "click",
#     "pandas",
#     "python-dotenv",
#     "pyyaml",
#     "requests",
#     "tqdm",
# ]
# ///
"""
Look every book up in Audible's catalogue and cache what comes back in data/enrichment.csv:
series and position, narrators, runtime, category ladders and a short blurb.

    uv run enrich.py --limit 30 2>&1 | tee data/last-run.log    # a trial run
    uv run enrich.py 2>&1 | tee data/last-run.log               # everything not yet cached

Books whose Sheet row has an Audible ID, or an Audible URL, are fetched by the ASIN in it. The rest
are searched for by title and author, and accepted only on an exact match; the near misses land in
data/enrichment-review.csv with their candidates. Rows the Sheet no longer has are dropped from the
cache, so run this against a freshly downloaded Sheet. audiobooks.load() joins the cache back on.
"""

import html
import logging
import re
import time
from pathlib import Path

import click
import pandas as pd
import requests
from tqdm import tqdm

from audiobooks import AUTHOR_ROLE, author_names, book_key, load, read_enrichment, squash

API = "https://api.audible.com/1.0/catalog/products"
# product_desc carries title/subtitle; without it a search result's title comes back null.
RESPONSE_GROUPS = "product_desc,product_attrs,contributors,series,category_ladders"
COLUMNS = [
    "key", "status", "title", "author", "asin", "audible_title", "series", "series_position",
    "narrators", "runtime_min", "release_date", "categories", "summary", "delivery", "candidates",
]  # fmt: skip

BRACKETED = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]")
# Where a subtitle starts: "Babel: Or the Necessity…", "What Is a Girl Worth? My Story…"
SUBTITLE = re.compile(r"[:?!]")

logger = logging.getLogger(__name__)


def shortened(title) -> set:
    """A title without its subtitle, and without its brackets: '(Dramatised)', '[Audible Edition]'."""
    title = str(title)
    return {squash(SUBTITLE.split(title)[0]), squash(BRACKETED.sub("", title))} - {""}


def titles_match(sheet_title, product) -> bool:
    """
    Same title, allowing one side to carry a subtitle or a bracketed note the other lacks: the
    Sheet's 'Babel: Or the Necessity of Violence' is Audible's 'Babel'. A shortened title is only
    ever compared with the other side's whole one — shorten both and 'Star Wars: Thrawn' matches
    every Star Wars book, and 'The Early Years' matches 'The Later Years'.
    """
    title, subtitle = str(product.get("title") or ""), product.get("subtitle") or ""
    audible_whole = {squash(title), squash(f"{title} {subtitle}")} - {""}
    return squash(sheet_title) in audible_whole | shortened(title) or bool(shortened(sheet_title) & audible_whole)


def pick_match(title, author, narrator, products):
    """
    The product that is this book, or None. Exact title and a shared author, nothing looser: a
    search for the first book of a series returns the rest of the series too, often ahead of it.
    """
    matches = [
        p
        for p in products
        if titles_match(title, p)
        and author_names(author) & author_names(", ".join(a["name"] for a in p.get("authors") or []))
    ]
    # Several editions of one book match equally; the narrator, where the Sheet has one, says which.
    narrators = author_names(narrator)
    for p in matches:
        if narrators & author_names(", ".join(n["name"] for n in p.get("narrators") or [])):
            return p
    return matches[0] if matches else None


def flatten(product) -> dict:
    """The fields worth keeping from one catalogue product."""
    series = (product.get("series") or [{}])[0]
    ladders = [" > ".join(c["name"] for c in l["ladder"]) for l in product.get("category_ladders") or []]
    return {
        "asin": product.get("asin"),
        "audible_title": product.get("title"),
        "series": series.get("title"),
        "series_position": series.get("sequence"),
        "narrators": ", ".join(n["name"] for n in product.get("narrators") or []),
        "runtime_min": product.get("runtime_length_min"),
        "release_date": product.get("release_date"),
        "categories": "; ".join(ladders),
        "summary": html.unescape(re.sub(r"<[^>]+>", "", product.get("merchandising_summary") or "")).strip(),
        # SinglePartBook, MultiPartBook, PodcastParent… — what tells a podcast from a book.
        "delivery": product.get("content_delivery_type"),
    }


def describe(product) -> str:
    """One candidate, for a person reading the review file."""
    authors = ", ".join(a["name"] for a in product.get("authors") or [])
    return f"{product.get('title')} / {authors} / https://www.audible.com/pd/{product.get('asin')}"


def look_up(session, row) -> dict:
    """Enrichment for one Sheet row. Raises requests.RequestException if Audible cannot be reached."""
    asin = row.key if "|" not in row.key else ""
    if asin:
        response = session.get(f"{API}/{asin}", params={"response_groups": RESPONSE_GROUPS}, timeout=30)
        response.raise_for_status()
        product = response.json().get("product") or {}
        # An ASIN Audible no longer sells still answers 200, with a product that is only an asin.
        if not product.get("title"):
            return {"status": "not_found"}
        # A series page answers too, with no categories or runtime of its own — and its books may
        # be another language's edition. Refused rather than cached as an empty match.
        if product.get("content_delivery_type") == "BookSeries":
            logger.warning("%r: %s is a series page, not a listing; the Audible ID wants one of its books", row.title, asin)
            return {"status": "not_found"}
        return {"status": "matched", **flatten(product)}

    params = {
        "title": BRACKETED.sub("", SUBTITLE.split(str(row.title))[0]).strip(),
        "author": AUTHOR_ROLE.sub("", re.split(r",|&", str(row.author))[0]).strip(),
        "num_results": 10,
        "response_groups": RESPONSE_GROUPS,
    }
    response = session.get(API, params=params, timeout=30)
    response.raise_for_status()
    products = response.json().get("products") or []
    match = pick_match(row.title, row.author, row.narrator, products)
    if match:
        return {"status": "matched", **flatten(match)}
    if products:
        return {"status": "review", "candidates": "\n".join(describe(p) for p in products[:3])}
    return {"status": "not_found"}


@click.command()
@click.argument("source", required=False)
@click.option("--output", default="data/enrichment.csv", show_default=True, type=click.Path(dir_okay=False))
@click.option("--limit", type=int, help="Look up at most this many books, for a trial run.")
@click.option("--refresh", is_flag=True, help="Look everything up again, not only what is missing.")
@click.option("--delay", default=0.5, show_default=True, help="Seconds between requests.")
def main(source, output, limit, refresh, delay) -> None:
    """Enrich the library in SOURCE (a CSV from download_sheet.py; default: the live Sheet)."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    books = load(source, enrich=False)
    # An older Sheet lacks Audible ID, and tidy() drops any column left entirely blank.
    books = books.reindex(columns=list(dict.fromkeys([*books.columns, "url", "audible_id", "narrator"])))
    books["key"] = [book_key(*row) for row in zip(books.title, books.author, books.url, books.audible_id)]
    books = books.drop_duplicates("key")

    output = Path(output)
    # A machine with no cache of its own starts from the copy in the Sheet, not from nothing.
    cache = None if refresh else read_enrichment(output)
    cache = pd.DataFrame(columns=COLUMNS) if cache is None else cache.reindex(columns=COLUMNS)
    # Only a match is final. The few dozen misses are retried every run, which is how a URL pasted
    # into the Sheet, a new Audible listing or a better matcher gets to take effect.
    cache = cache[cache.status == "matched"]
    # Nor is a row the Sheet no longer has: a retitled or deleted book would otherwise ride along
    # into the Sheet's copy of this file for ever.
    cache = cache[cache.key.isin(books.key)]
    todo = books[~books.key.isin(cache.key)].iloc[:limit]
    logger.info("%d books, %d already cached, looking up %d", len(books), len(cache), len(todo))

    review_path = output.with_name("enrichment-review.csv")
    output.parent.mkdir(parents=True, exist_ok=True)

    def save(rows) -> pd.DataFrame:
        merged = pd.concat([cache, pd.DataFrame(rows, columns=COLUMNS)], ignore_index=True) if rows else cache
        merged.to_csv(output, index=False)
        merged[merged.status == "review"][["title", "author", "candidates"]].to_csv(review_path, index=False)
        return merged

    rows, disagree, session = [], [], requests.Session()
    try:
        for row in tqdm(todo.itertuples(), total=len(todo)):
            try:
                found = look_up(session, row)
            except requests.RequestException as e:  # left uncached, so the next run retries it
                logger.warning("Skipping %r: %s", row.title, e)
                continue
            rows.append({"key": row.key, "title": row.title, "author": row.author, **found})
            # A pasted ID is accepted whatever it points at, so note when the title disagrees.
            if found["status"] == "matched" and "|" not in row.key and not titles_match(row.title, {"title": found["audible_title"]}):
                disagree.append((row.key, row.title, found["audible_title"]))
            # A full run is twelve minutes of requests; a kill signal skips `finally`, so save as we go.
            if len(rows) % 50 == 0:
                save(rows)
            time.sleep(delay)
    finally:
        cache = save(rows)

    # Logged after the loop, not inside it: tqdm and logging share stderr, and a warning written
    # mid-bar lands on the bar's line, where anything filtering the bar out of a log eats it too.
    for key, title, audible_title in disagree:
        logger.warning("Check %s: the Sheet says %r, Audible says %r", key, title, audible_title)
    logger.info("Wrote %s: %s", output, cache.status.value_counts().to_dict())
    logger.info("%d to review in %s", (cache.status == "review").sum(), review_path)
    if any(row["status"] == "matched" for row in rows):
        logger.info("New matches: re-import %s over the Sheet's enrichment tab to keep that copy current", output)


if __name__ == "__main__":
    main()
