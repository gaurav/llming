#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click",
# ]
# ///
"""
Generate an NC outline SVG by removing the flag from the NC flag-map SVG.

The input SVG (Flag-map_of_North_Carolina.svg) contains the NC state outline
with the NC flag embedded inside it. This script strips the flag elements,
leaving just the NC shape outline with a solid fill.
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import click

log = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

DEFAULT_INPUT = "data/wikimedia-us-nc-logo/Flag-map_of_North_Carolina.svg"
DEFAULT_OUTPUT = "data/nc-outline.svg"


@click.command()
@click.option(
    "--input", "-i", "input_file",
    default=DEFAULT_INPUT,
    show_default=True,
    help="Input SVG file (NC flag-map)",
)
@click.option(
    "--output", "-o", "output_file",
    default=DEFAULT_OUTPUT,
    show_default=True,
    help="Output SVG file",
)
@click.option(
    "--fill",
    default="#ffffff",
    show_default=True,
    help="Fill color for the NC shape interior",
)
@click.option(
    "--stroke",
    default="#000000",
    show_default=True,
    help="Stroke color for the NC outline",
)
@click.option(
    "--stroke-width",
    default=None,
    help="Stroke width override (uses original if not set)",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def main(input_file, output_file, fill, stroke, stroke_width, verbose):
    """Remove the NC flag from the flag-map SVG, keeping just the state outline."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        log.error("Input file not found: %s", input_path)
        raise SystemExit(1)

    log.info("Reading %s", input_path)

    # Register namespaces to preserve them in output
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)

    tree = ET.parse(input_path)
    root = tree.getroot()

    log.debug("SVG viewBox: %s, width: %s, height: %s",
              root.get("viewBox"), root.get("width"), root.get("height"))

    # The SVG structure is:
    #   <defs><clipPath id="a"><path .../></clipPath></defs>   ← NC outline clip mask
    #   <clipPath>...</clipPath>                                ← anonymous, unreferenced
    #   <g transform="...">                                    ← main content group
    #     <path style="fill:none;stroke:#000000 ..."/>         ← NC outline stroke [0]
    #     <path clip-path="url(#a)" .../>                      ← flag elements [1..N]
    #     ...
    #   </g>

    # Find the main content group (last <g> child of root)
    main_g = None
    for child in root:
        if child.tag == f"{{{SVG_NS}}}g":
            main_g = child
            break

    if main_g is None:
        log.error("Could not find main <g> element in SVG")
        raise SystemExit(1)

    log.debug("Main group transform: %s", main_g.get("transform"))

    children = list(main_g)
    log.info("Main group has %d children (1 outline + %d flag elements)",
             len(children), len(children) - 1)

    # Find the NC outline stroke path: the one with fill:none and no clip-path
    outline_path = None
    flag_elements = []
    for child in children:
        style = child.get("style", "")
        has_clip = child.get("clip-path") is not None
        if not has_clip and "fill:none" in style and "stroke:#000000" in style:
            outline_path = child
            log.debug("Found NC outline stroke path")
        else:
            flag_elements.append(child)

    if outline_path is None:
        log.error("Could not find NC outline path in main group")
        raise SystemExit(1)

    log.info("Removing %d flag elements", len(flag_elements))
    for el in flag_elements:
        main_g.remove(el)

    # Update the outline path style to add a fill color
    original_style = outline_path.get("style", "")
    log.debug("Original outline style: %s", original_style)

    # Build new style: replace fill:none with the chosen fill color
    new_style = original_style.replace("fill:none", f"fill:{fill}")
    if stroke != "#000000":
        new_style = new_style.replace("stroke:#000000", f"stroke:{stroke}")
    if stroke_width is not None:
        # Replace stroke-width value in the style string
        import re
        new_style = re.sub(r"stroke-width:[^;]+", f"stroke-width:{stroke_width}", new_style)

    outline_path.set("style", new_style)
    log.debug("New outline style: %s", new_style)

    # Remove the anonymous unreferenced <clipPath> child from root
    # (it has no id, so nothing references it)
    for child in list(root):
        tag = child.tag.replace(f"{{{SVG_NS}}}", "")
        if tag == "clipPath" and child.get("id") is None:
            root.remove(child)
            log.info("Removed unreferenced anonymous <clipPath> from root")
            break

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(output_path), xml_declaration=True, encoding="UTF-8")
    log.info("Wrote output to %s", output_path)
    log.info("Done! SVG dimensions: %s x %s (viewBox: %s)",
             root.get("width"), root.get("height"), root.get("viewBox"))


if __name__ == "__main__":
    main()
