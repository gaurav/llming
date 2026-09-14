#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "click",
#     "pillow",
#     "requests",
#     "tqdm",
# ]
# ///
"""
Work out which photos in a local export are already on Wikimedia Commons (and on Flickr).

Joins three sources on EXIF capture time (DateTimeOriginal): the JPEGs in --input, the files in a
Commons category, and optionally the photos in a Flickr album. Exact hashes don't work for this,
because Apple Photos re-encodes on export and Flickr serves its own copy, but the camera's capture
time survives all of that and is exposed by both APIs without downloading anything.

Writes data/reconcile.csv, one row per local file, and with --move sorts the files not yet on
Commons into data/to-upload/ (ready for the Upload Wizard) and anything ambiguous into
data/needs-review/.
"""

import csv
import logging
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import click
import requests
from PIL import Image
from tqdm import tqdm

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
USER_AGENT = "commons-uploads/0.1 (https://github.com/gaurav/llming; gaurav@ggvaidya.com)"
EXIF_DATETIME_ORIGINAL = 0x9003

log = logging.getLogger("reconcile")


def load_env(path=HERE / ".env"):
    """Set KEY=VALUE lines from .env into os.environ, without overriding what's already set.

    Deliberately tiny: no python-dotenv, no quoting rules. Values are never logged.
    """
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def fetch_commons(category, uploader=None):
    """Return {capture_time: [file dicts]} for every file in a Commons category."""
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    params = {
        "action": "query",
        "generator": "categorymembers",
        "gcmtitle": f"Category:{category}",
        "gcmtype": "file",
        "gcmlimit": "500",
        "prop": "imageinfo",
        "iiprop": "sha1|size|metadata|url|user",
        "format": "json",
        "formatversion": "2",
    }
    by_time = defaultdict(list)
    total = 0
    while True:
        resp = session.get("https://commons.wikimedia.org/w/api.php", params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        for page in data.get("query", {}).get("pages", []):
            info = page["imageinfo"][0]
            if uploader and info.get("user") != uploader:
                continue
            total += 1
            meta = {m["name"]: m["value"] for m in info.get("metadata") or []}
            by_time[meta.get("DateTimeOriginal")].append(
                {
                    "title": page["title"],
                    "url": info["descriptionurl"],
                    "width": info["width"],
                    "height": info["height"],
                    "sha1": info["sha1"],
                    "user": info.get("user"),
                }
            )
        if "continue" not in data:
            break
        params.update(data["continue"])
    log.info("Commons: %d files in Category:%s", total, category)
    return by_time


def fetch_flickr(album, user_id, api_key):
    """Return {capture_time: [photo dicts]} for every photo in a Flickr album."""
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    by_time = defaultdict(list)
    page, total = 1, 0
    while True:
        resp = session.get(
            "https://api.flickr.com/services/rest/",
            params={
                "method": "flickr.photosets.getPhotos",
                "api_key": api_key,
                "photoset_id": album,
                "user_id": user_id,
                "extras": "date_taken,url_o,o_dims",
                "per_page": "500",
                "page": str(page),
                "format": "json",
                "nojsoncallback": "1",
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("stat") != "ok":
            raise click.ClickException(f"Flickr API error: {data.get('message')}")
        photoset = data["photoset"]
        for photo in photoset["photo"]:
            total += 1
            # Flickr writes 2024-04-08 12:59:46; EXIF writes 2024:04:08 12:59:46.
            taken = photo["datetaken"].replace("-", ":")
            by_time[taken].append(
                {
                    "id": photo["id"],
                    "url": f"https://www.flickr.com/photos/{user_id}/{photo['id']}/",
                    "width": photo.get("width_o"),
                    "height": photo.get("height_o"),
                }
            )
        if page >= int(photoset["pages"]):
            break
        page += 1
    log.info("Flickr: %d photos in album %s", total, album)
    return by_time


def scan_local(folder):
    """Return a list of {file, taken, width, height} for every JPEG in the folder."""
    paths = sorted(p for p in folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg"))
    rows = []
    for path in tqdm(paths, desc="Reading EXIF", unit="file"):
        with Image.open(path) as img:
            taken = img.getexif().get_ifd(0x8769).get(EXIF_DATETIME_ORIGINAL)
            rows.append({"file": path.name, "taken": taken, "width": img.width, "height": img.height})
    log.info("Local: %d JPEGs in %s", len(rows), folder)
    return rows


def reconcile(local, commons, flickr):
    """Join local files to Commons files and Flickr photos on capture time.

    Returns (rows, unmatched_commons, unmatched_flickr). Rows are one per local file with a
    status of on-commons, to-upload, or needs-review; the unmatched lists hold Commons/Flickr
    entries whose capture time matched no local file.
    """
    local_by_time = defaultdict(list)
    for entry in local:
        local_by_time[entry["taken"]].append(entry)

    rows = []
    for entry in local:
        taken = entry["taken"]
        row = {
            "file": entry["file"],
            "taken": taken or "",
            "width": entry["width"],
            "height": entry["height"],
            "commons_title": "",
            "commons_url": "",
            "flickr_id": "",
            "flickr_url": "",
            "status": "",
            "note": "",
        }
        notes = []
        commons_hits = commons.get(taken, []) if taken else []
        flickr_hits = flickr.get(taken, []) if taken else []
        if commons_hits:
            row["commons_title"] = "; ".join(h["title"] for h in commons_hits)
            row["commons_url"] = "; ".join(h["url"] for h in commons_hits)
        if flickr_hits:
            row["flickr_id"] = "; ".join(h["id"] for h in flickr_hits)
            row["flickr_url"] = "; ".join(h["url"] for h in flickr_hits)

        if not taken:
            row["status"] = "needs-review"
            notes.append("no EXIF capture time")
        elif len(local_by_time[taken]) > 1:
            row["status"] = "needs-review"
            others = [e["file"] for e in local_by_time[taken] if e["file"] != entry["file"]]
            notes.append(f"capture time shared with {', '.join(others)}")
        elif len(commons_hits) > 1:
            row["status"] = "needs-review"
            notes.append(f"{len(commons_hits)} Commons files share this capture time")
        elif commons_hits:
            row["status"] = "on-commons"
        else:
            row["status"] = "to-upload"

        for hit in commons_hits:
            if (hit["width"], hit["height"]) != (entry["width"], entry["height"]):
                notes.append(
                    f"commons {hit['width']}x{hit['height']} != local {entry['width']}x{entry['height']}"
                )
        row["note"] = "; ".join(notes)
        rows.append(row)

    unmatched_commons = [h for t, hits in commons.items() if t not in local_by_time for h in hits]
    unmatched_flickr = [h for t, hits in flickr.items() if t not in local_by_time for h in hits]
    return rows, unmatched_commons, unmatched_flickr


def move_files(rows, source, to_upload, needs_review):
    """Move to-upload and needs-review files out of the source folder, never overwriting."""
    dest_for = {"to-upload": to_upload, "needs-review": needs_review}
    planned = [(source / r["file"], dest_for[r["status"]] / r["file"]) for r in rows if r["status"] in dest_for]
    clashes = [dst for _, dst in planned if dst.exists()]
    if clashes:
        raise click.ClickException(
            f"Refusing to overwrite {len(clashes)} existing file(s), e.g. {clashes[0]}; move them aside first."
        )
    for src, dst in planned:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    log.info("Moved %d files", len(planned))


@click.command()
@click.option("--input", "input_dir", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path),
              help="Folder of exported JPEGs.")
@click.option("--category", required=True, help="Commons category name, without the Category: prefix.")
@click.option("--uploader", default=None, help="Only consider Commons files uploaded by this user.")
@click.option("--flickr-album", default=None, help="Flickr photoset ID. Needs FLICKR_API_KEY (see env.default).")
@click.option("--flickr-user", default=None, help="Flickr NSID of the album owner, e.g. 83524507@N00.")
@click.option("--output", default=DATA / "reconcile.csv", type=click.Path(dir_okay=False, path_type=Path),
              show_default=True, help="Where to write the reconciliation CSV.")
@click.option("--move", is_flag=True,
              help="Move files not on Commons into data/to-upload/ and ambiguous ones into data/needs-review/.")
def main(input_dir, category, uploader, flickr_album, flickr_user, output, move):
    """Report which local photos are already on Commons, and sort out the ones that aren't."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_env()

    flickr = {}
    if flickr_album:
        api_key = os.environ.get("FLICKR_API_KEY")
        if not api_key or not flickr_user:
            raise click.ClickException("--flickr-album needs --flickr-user and FLICKR_API_KEY (see env.default).")
        flickr = fetch_flickr(flickr_album, flickr_user, api_key)
    commons = fetch_commons(category, uploader)
    local = scan_local(input_dir)

    rows, unmatched_commons, unmatched_flickr = reconcile(local, commons, flickr)

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["file"])
        writer.writeheader()
        writer.writerows(rows)
    log.info("Wrote %s", output)

    counts = defaultdict(int)
    for row in rows:
        counts[row["status"]] += 1
        if row["note"]:
            log.warning("%s [%s]: %s", row["file"], row["status"], row["note"])
    for label, hits, key in (("Commons files", unmatched_commons, "title"), ("Flickr photos", unmatched_flickr, "url")):
        if hits:
            log.warning("%d %s match no local file, e.g. %s", len(hits), label,
                        ", ".join(h[key] for h in hits[:3]))
    log.info("Local: %d on Commons, %d to upload, %d need review",
             counts["on-commons"], counts["to-upload"], counts["needs-review"])
    if flickr:
        total = sum(len(hits) for hits in flickr.values())
        on_commons = sum(len(hits) for t, hits in flickr.items() if t in commons)
        log.info("Flickr: %d photos, %d already on Commons, %d not", total, on_commons, total - on_commons)

    if move:
        move_files(rows, input_dir, DATA / "to-upload", DATA / "needs-review")
    else:
        log.info("Dry run: re-run with --move to sort %d files out of %s",
                 counts["to-upload"] + counts["needs-review"], input_dir)


if __name__ == "__main__":
    sys.exit(main())
