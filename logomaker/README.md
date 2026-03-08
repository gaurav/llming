# NC Wikipedians Logo Maker

Scripts for iteratively designing SVG logos for the **North Carolina Wikipedians** user group, based around the distinctive shape of North Carolina.

## Workflow

The pipeline is two steps:

1. **`generate-nc-outline.py`** — Takes the source NC flag-map SVG and strips the flag, producing a clean state outline.
2. **`add-text-to-logo.py`** — Takes the outline and composites text with it in various layout modes.

All scripts are run with `uv run` and write output to `data/`.

---

## `generate-nc-outline.py`

Removes the NC state flag from `Flag-map_of_North_Carolina.svg`, leaving just the state silhouette with a configurable fill and stroke.

```bash
uv run generate-nc-outline.py
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-i` / `--input` | `data/wikimedia-us-nc-logo/Flag-map_of_North_Carolina.svg` | Input flag-map SVG |
| `-o` / `--output` | `data/nc-outline.svg` | Output SVG |
| `--fill` | `#ffffff` | Fill color for the NC shape interior |
| `--stroke` | `#000000` | Stroke color for the outline border |
| `--stroke-width` | *(original)* | Override stroke width |
| `-v` / `--verbose` | — | Verbose logging |

**Examples:**

```bash
# Default: white fill, black stroke
uv run generate-nc-outline.py

# Blue fill, dark stroke
uv run generate-nc-outline.py --fill "#002868" --stroke "#001040" -o data/nc-outline-blue.svg
```

---

## `add-text-to-logo.py`

Composites text with the NC outline SVG in one of three layout modes. Designed for rapid iteration — run it repeatedly with different options to explore logo variations.

```bash
uv run add-text-to-logo.py
```

Produces `data/nc-logo.svg` by default: the NC shape with "NORTH CAROLINA" and "WIKIPEDIANS" in bold below it.

### Layout modes (`--layout`)

| Mode | Description |
|------|-------------|
| `below` *(default)* | NC shape on top, text centered below |
| `overlay` | Text centered over the shape |
| `clipped` | Text clipped to the NC silhouette — letters only visible inside the outline |

### All options

**Text:**

| Option | Default | Description |
|--------|---------|-------------|
| `-t` / `--text` | `NORTH CAROLINA`, `WIKIPEDIANS` | Text line (repeatable, one per invocation) |
| `--font-family` | `sans-serif` | Font family |
| `--font-size` | *(auto)* | Font size in viewBox units |
| `--font-weight` | `bold` | Font weight |
| `--text-color` | `#000000` | Text fill color |
| `--text-anchor` | `middle` | Alignment: `start`, `middle`, or `end` |
| `--line-spacing` | `1.2` | Line gap multiplier (relative to font-size) |
| `--letter-spacing` | *(none)* | SVG `letter-spacing` value |

**Shape overrides:**

| Option | Default | Description |
|--------|---------|-------------|
| `--shape-fill` | *(from input)* | Override NC shape fill |
| `--shape-stroke` | *(from input)* | Override NC shape stroke color |
| `--shape-stroke-width` | *(from input)* | Override NC shape stroke width |
| `--shape-opacity` | *(none)* | Shape group opacity (0.0–1.0) |

**Layout/output:**

| Option | Default | Description |
|--------|---------|-------------|
| `-i` / `--input` | `data/nc-outline.svg` | Input SVG |
| `-o` / `--output` | `data/nc-logo.svg` | Output SVG |
| `-l` / `--layout` | `below` | Layout mode |
| `--padding` | `2000` | Padding around content in viewBox units |
| `-v` / `--verbose` | — | Verbose logging |

### Examples

```bash
# Default: text below the shape
uv run add-text-to-logo.py

# Text clipped to the NC silhouette
uv run add-text-to-logo.py --layout clipped -o data/nc-logo-clipped.svg

# Overlay with faded shape
uv run add-text-to-logo.py --layout overlay --shape-opacity 0.3 -o data/nc-logo-overlay.svg

# Custom colors and font
uv run add-text-to-logo.py \
  --shape-fill "#002868" --text-color "#ffffff" \
  --font-family "Georgia" -o data/nc-logo-blue.svg

# Single large line, clipped
uv run add-text-to-logo.py --layout clipped \
  --text "WIKIPEDIANS" --font-size 25000 -o data/nc-logo-single.svg

# Log output for reproducibility
uv run add-text-to-logo.py [options] 2>&1 | tee data/last-run.log
```

### Font size reference

Font sizes are in SVG viewBox units. The NC shape occupies a viewBox roughly 107,000 × 40,000 units. Some useful reference points:

| Font size | Effect |
|-----------|--------|
| `5000–8000` | Small text below the shape (auto default for `below`) |
| `10000–20000` | Large headline text |
| `18000` | Auto default for `clipped` mode (fills ~45% of shape height) |
| `25000+` | Very large, good for single-word clipped logos |
