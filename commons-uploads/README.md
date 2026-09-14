# commons-uploads

Works out which photos in a local export are already on Wikimedia Commons, and sorts the ones
that aren't into a folder ready for the Upload Wizard. Built for the April 8, 2024 eclipse photos
from Angel Mounds, where a partly failed Commons upload left no record of what had made it.

It joins three sources on the EXIF capture time (`DateTimeOriginal`): the JPEGs in a folder, the
files in a Commons category, and optionally the photos in a Flickr album. Nothing is uploaded or
modified anywhere but the local `data/` folder. Uploading is left to Commons' own tools.

## How to run

Put the exported JPEGs somewhere under `data/`. For the Flickr columns, create an API key at
<https://www.flickr.com/services/apps/create/>, copy `env.default` to `.env` and fill it in
(`.env` is gitignored); the script reads it itself. Then:

```bash
uv run reconcile.py \
  --input "data/Total Solar Eclipse at Angel Mounds" \
  --category Total_Solar_Eclipse_at_Angel_Mounds_2024 \
  --flickr-album 72177720316118411 --flickr-user 83524507@N00 \
  2>&1 | tee data/last-run.log
```

That is a dry run: it writes `data/reconcile.csv` (one row per local file, with the matching
Commons title and Flickr photo, and a status of `on-commons`, `to-upload`, or `needs-review`)
and logs the counts. Add `--move` to sort the `to-upload` files into `data/to-upload/` and the
`needs-review` ones into `data/needs-review/`, leaving only the already-uploaded files in the
input folder. It never overwrites, and a second `--move` run is a no-op.

Then upload `data/to-upload/` with the [Upload Wizard](https://commons.wikimedia.org/wiki/Special:UploadWizard),
50 files per session, and hand-check `data/needs-review/`. Re-running afterwards should report
everything as `on-commons`.

Drop `--flickr-album` and `--flickr-user` to skip Flickr entirely. `--uploader Gaurav` restricts
the Commons side to one user's files, which matters in a shared category. `--output` moves the
CSV somewhere other than `data/reconcile.csv`.

### Doing this again for a new batch

1. **Export the photos from Apple Photos as JPEG** into a new folder under `data/`. Either
   export mode works for matching, because only the EXIF capture time is used. "Export
   Unmodified Original" is still the better choice: it keeps the bytes identical, so Commons'
   own SHA-1 duplicate check will also work for anything already uploaded from the same file.
   HEIC originals must be exported as JPEG; the script only reads `.jpg`/`.jpeg`.
2. **Find the Commons category** the earlier uploads went into. It is the part after
   `Category:` in the URL, with underscores or spaces, and is the category the *files* sit in,
   not a parent. If uploads were scattered across categories, run once per category, or run
   against a parent and accept that `gcmtype=file` does not recurse into subcategories.
3. **Find the Flickr album ID and your NSID.** The album ID is the number at the end of the
   album URL (`.../albums/72177720316118411`). The NSID (`83524507@N00`) is the same for every
   album you own; it is in the album page source, or from
   `flickr.people.findByUsername` on the [API explorer](https://www.flickr.com/services/api/explore/flickr.people.findByUsername).
4. **Dry-run first, read the warnings, then `--move`.** The dry run costs nothing and the
   warnings are where the surprises show up: dimension mismatches, burst pairs, Commons files
   that match nothing local (which usually means the export is incomplete).
5. **Upload `data/to-upload/`**, 50 at a time, and resolve `data/needs-review/` by hand: the
   CSV row for each lists every Commons file at the same capture time, so open those and compare.
6. **Re-run without `--move`** once the uploads are done. Everything left in the input folder
   should be `on-commons`, and the Flickr line should show every photo you meant to upload.

There is no state file. If a move was wrong, drag the files back into the input folder and
re-run; the split is recomputed from scratch each time.

### What `reconcile.csv` contains

One row per JPEG in the input folder, in filename order.

| Column | Meaning |
| --- | --- |
| `file` | Filename in the input folder |
| `taken` | EXIF `DateTimeOriginal`, `YYYY:MM:DD HH:MM:SS`; empty if the file has none |
| `width`, `height` | Pixel size of the local file |
| `commons_title`, `commons_url` | Every Commons file with the same capture time, `; `-separated if more than one |
| `flickr_id`, `flickr_url` | Every Flickr photo with the same capture time, likewise |
| `status` | `on-commons` (one local file, one Commons file), `to-upload` (no Commons file), or `needs-review` |
| `note` | Why it needs review, and any dimension mismatch against the Commons copy |

`needs-review` is set when the capture time is shared by more than one local file, by more than
one Commons file, or is missing. Those files are never moved to `to-upload/`.

## Known issues and limitations

- **Capture time is the only join key.** Burst shots taken within the same second are flagged
  `needs-review` rather than matched. Files with no EXIF (screenshots, stripped exports) can't be
  matched at all and also land in `needs-review`.
- **A match means "same shot", not "same file".** A photo cropped before uploading still matches
  its uncropped original. The `note` column reports dimension mismatches so you can check.
- **Exact hashes were tried and don't work for this batch.** Apple Photos re-encodes on export,
  and Flickr serves its own copy, so none of the SHA-1s agree. See `CLAUDE.md` for the numbers.
- **Flickr needs an API key**, and as of 2025 Flickr only issues keys to Pro accounts. The
  keyless feed returns 20 photos at most.
- Every local file gets a row, but Commons files and Flickr photos that match nothing local are
  only logged as warnings, not written to the CSV.

## Next steps

- **Verify matches visually** with a perceptual hash: `imagehash` on the local file against the
  Commons thumbnail (or the original via `iiprop=url`), or against
  [imagehash.toolforge.org](https://github.com/Wikimedia-Suomi/ImageHash-Toolforge), which
  indexes Commons with the same library. Only worth it once a burst pair or a stripped-EXIF batch
  actually needs it.
- **Draft upload metadata for a batch**: titles, descriptions, categories, captions, and
  structured data. The natural output is a [Pattypan](https://commons.wikimedia.org/wiki/Commons:Pattypan)
  spreadsheet, since Pattypan already does a SHA-1 pre-check and handles the upload.
- **Match by Flickr ID** for files that were uploaded through Flickypedia or Flickr2Commons: they
  carry the Flickr photo ID in structured data (P12120) and the URL as source (P7482).
- **Match by SHA-1 as a fast path** when the local files are unmodified originals
  (`list=allimages&aisha1=` is public and instant), before falling back to capture time.

## Extending it

`reconcile.py` is one file with one command and no shared state. The pieces:

- `fetch_commons`, `fetch_flickr`, `scan_local` each produce the same shape: a dict from capture
  time to a list of entries (local is a flat list, keyed inside `reconcile`). A new source, say a
  second Commons category or an Apple Photos library read directly, is one more function
  returning that shape.
- `reconcile(local, commons, flickr)` is the pure join. All the status and note logic lives
  there, it takes no network or filesystem, and `tests/test_reconcile.py` covers it with
  hand-built dicts. Change matching rules here and extend that test; run it with
  `uv run pytest commons-uploads` from the repo root.
- `move_files` is the only thing that touches the filesystem beyond writing the CSV.
- `main` is the click wiring. Options map one-to-one onto the fetchers.

Likely extensions, in the order they are most likely to be needed:

- **A SHA-1 fast path**: hash each local file, query `list=allimages&aisha1=` (public, no key,
  batchable), and mark exact hits `on-commons` before the capture-time join. Only pays off for
  unmodified originals.
- **Perceptual verification**: `imagehash` on the local file against the Commons thumbnail
  (`iiprop=url` gives `thumburl`; ask for `iiurlwidth=1024`) to confirm a match or break a burst
  tie. That adds Pillow-based hashing and a download per match, so keep it behind a flag.
- **A metadata drafter** for the `to-upload/` folder: titles, descriptions, categories,
  captions, structured data, written as a Pattypan spreadsheet. That is a separate script; this
  one should stay a reconciler.

Dependencies are declared in the PEP 723 header at the top of the script (`click`, `pillow`,
`requests`, `tqdm`), so `uv run` installs them; the repo root `dev` group repeats them only so
the tests can import the script.

## Prior art

Nothing found does this exact job: local export plus Flickr album, against Commons, for files
that were uploaded by hand. The pieces exist, though, and the upload side is well covered.

| Tool | What it does | Checks "already on Commons"? |
| --- | --- | --- |
| [Upload Wizard](https://commons.wikimedia.org/wiki/Commons:Upload_Wizard) | Standard web uploader, 50 files per session | Exact SHA-1 only, and only after the upload ([T389222](https://phabricator.wikimedia.org/T389222)) |
| [Pattypan](https://commons.wikimedia.org/wiki/Commons:Pattypan) | Spreadsheet-driven bulk uploader | Exact SHA-1 before upload ([T223525](https://phabricator.wikimedia.org/T223525)) |
| [pywikibot](https://doc.wikimedia.org/pywikibot/) `upload.py` | Scripted uploads | Relies on server warnings; offers `site.allimages(sha1=...)` |
| [Flickypedia](https://github.com/Flickr-Foundation/flickypedia) | Flickr to Commons with structured data | By Flickr photo ID against a local copy of the SDC dumps, not queryable |
| [Flickr2Commons](https://commons.wikimedia.org/wiki/Commons:Flickr2Commons) | Flickr to Commons | Hides already-uploaded photos; method undocumented; currently broken ([T429006](https://phabricator.wikimedia.org/T429006)) |
| [OpenRefine Commons extension](https://commons.wikimedia.org/wiki/Commons:OpenRefine/Uploading_files_with_OpenRefine) | Bulk upload with SDC | Reconciles by filename only |
| [comload](https://taavi.wtf/posts/comload/) | Downloads a category's originals and metadata | n/a (download side) |
| [ImageHash-Toolforge](https://github.com/Wikimedia-Suomi/ImageHash-Toolforge) | pHash/dHash index of Commons | Near-duplicate search by hash; liveness unverified |
| `flickr-photos-api`, `flickr-url-parser` | Flickr Foundation's Python libraries | n/a |

Related Phabricator tasks, checked September 2026:

- [T389222](https://phabricator.wikimedia.org/T389222) UploadWizard should check for duplicates
  before uploading. Open.
- [T362352](https://phabricator.wikimedia.org/T362352) Warn about non-exact duplicates in
  UploadWizard. Open.
- [T121797](https://phabricator.wikimedia.org/T121797) Perceptual image hashing in MediaWiki.
  Open since 2015.
- [T167947](https://phabricator.wikimedia.org/T167947) Expose image hashes through the API.
  Open.
- [T364100](https://phabricator.wikimedia.org/T364100) Improve the Commons imagehash Toolforge
  project. Open.
- [T30320](https://phabricator.wikimedia.org/T30320) UploadWizard hash check broken. Closed;
  documents the `aisha1` lookup the wizard uses.
- [T268240](https://phabricator.wikimedia.org/T268240) Cross-wiki duplicate detection. Open.
- [T419263](https://phabricator.wikimedia.org/T419263) UploadWizard Flickr import broken by CSP.
  Resolved 2026.

The upshot: exact-duplicate detection is solved and public; near-duplicate detection is an open
wish with one volunteer service; and nobody has built the "reconcile my own export" step.
