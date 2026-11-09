Gotchas for `reconcile.py`. What the tool is for and how to run it is in `README.md`.

## Why capture time, not hashes

Checked against the real batch (133 exported JPEGs, 30 on Commons, 118 on Flickr):

- 0 of 30 Commons SHA-1s match a local file. Apple Photos' "Export N photos" re-encodes; only
  "Export Unmodified Original" keeps the bytes. Local files are ~10% smaller than the Commons
  copies of the same shot.
- A Flickr original (`url_o`) hashes differently from the Commons copy of the same shot too
  (7.8 MB vs 4.0 MB), so Flickr-to-Commons can't use SHA-1 either.
- `DateTimeOriginal` matched all 30 Commons files and all 118 Flickr photos to exactly one local
  file each. It is camera wall-clock time in every source, so there is no timezone arithmetic.

Formats differ: EXIF and Commons write `2024:04:08 12:59:46`, Flickr writes
`2024-04-08 12:59:46`. Everything is normalised to the colon form.

## Commons API

- `generator=categorymembers&gcmtype=file&prop=imageinfo&iiprop=metadata` is where
  `DateTimeOriginal` lives, as a `metadata` list of `{name, value}`. `gcmlimit=500` covers any
  category this tool will see, but the `continue` loop is there anyway.
- `list=allimages&aisha1=` works anonymously (verified), if SHA-1 ever becomes useful.
- Wikimedia requires a descriptive `User-Agent` with contact details; `python-requests/x` can be
  refused. Two requests per run is nowhere near the anonymous rate limit.

## Flickr API

- `flickr.photosets.getPhotos` needs `user_id` as well as the photoset ID, hence `--flickr-user`.
  Find the NSID (`83524507@N00`) in the album page source or via `flickr.people.findByUsername`.
- `extras=date_taken,url_o,o_dims` returns `datetaken`, the original URL, and original size.
  `url_o` only appears when the account may serve originals; it did here.
- The keyless `photoset.gne` feed is capped at 20 items and stamps `date_taken` with a bogus
  `-08:00` offset. Don't use it.
- Flickr only issues API keys to Pro accounts as of 2025. Keys are in `.env` (gitignored), names
  in `env.default`. The script loads `.env` itself; in an agent session, never read `.env`
  directly, or the key ends up in the transcript.
- `FLICKR_API_SECRET` is loaded but unused. Public album reads only need the key; the secret is
  for signing OAuth calls, which would only matter for private photos or writes.
- `load_env` is a deliberate five-line stand-in for python-dotenv: `KEY=VALUE`, `#` comments,
  no quoting, never overrides a variable already in the environment.

## Local scan

- Capture time comes from Pillow: `img.getexif().get_ifd(0x8769)[0x9003]`. The plain
  `getexif()` dict holds only IFD0 tags (`DateTime`, which is the *modification* time); the EXIF
  sub-IFD is where `DateTimeOriginal` lives.
- Only `.jpg`/`.jpeg` are scanned. HEIC would need `pillow-heif`; PNG and screenshots have no
  `DateTimeOriginal` and land in `needs-review`.
- `sips -g creation` on macOS reads the same tag and was used to cross-check during development.

## Facts about this batch

- `IMG_8413` and `IMG_8414` share `13:56:51`; both go to `needs-review`.
- `IMG_8393` was cropped before upload (Commons 3604x2372 vs local 4032x3024) and is reported as
  `on-commons` with a note.
- Two Commons files (the visitor-centre model and the palisade) are not in the Flickr album.
