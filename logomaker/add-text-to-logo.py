#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click",
# ]
# ///
"""
Add text to an NC outline SVG to create logo variants.

Takes the NC state outline SVG and composites text with it in various
layout modes (below, overlay, clipped) to produce logos for iterative
design exploration.
"""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import click

log = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

DEFAULT_INPUT = "data/nc-outline.svg"
DEFAULT_OUTPUT = "data/nc-logo.svg"
DEFAULT_TEXT = ["NORTH CAROLINA", "WIKIPEDIANS"]


def parse_input_svg(input_path):
    """Parse the input SVG and extract the NC shape path data and transform."""
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)

    tree = ET.parse(input_path)
    root = tree.getroot()

    viewbox = root.get("viewBox")
    vb_parts = [float(x) for x in viewbox.split()]
    vb_x, vb_y, vb_w, vb_h = vb_parts

    # Find the main <g> element and its path
    main_g = None
    for child in root:
        if child.tag == f"{{{SVG_NS}}}g":
            main_g = child
            break

    if main_g is None:
        raise ValueError("Could not find main <g> element in input SVG")

    transform = main_g.get("transform", "")
    path_el = list(main_g)[0]
    path_d = path_el.get("d")
    path_style = path_el.get("style", "")

    # Also look for clipPath in defs
    clip_path_d = None
    defs = root.find(f"{{{SVG_NS}}}defs")
    if defs is not None:
        clip_el = defs.find(f".//{{{SVG_NS}}}clipPath[@id='a']/{{{SVG_NS}}}path")
        if clip_el is not None:
            clip_path_d = clip_el.get("d")

    return {
        "viewbox": (vb_x, vb_y, vb_w, vb_h),
        "transform": transform,
        "path_d": path_d,
        "path_style": path_style,
        "clip_path_d": clip_path_d,
    }


def parse_style(style_str):
    """Parse a CSS style string into a dict."""
    result = {}
    for part in style_str.split(";"):
        part = part.strip()
        if ":" in part:
            k, v = part.split(":", 1)
            result[k.strip()] = v.strip()
    return result


def build_style(style_dict):
    """Build a CSS style string from a dict."""
    return ";".join(f"{k}:{v}" for k, v in style_dict.items())


def make_svg_element(tag, **attrs):
    """Create an SVG element with the given attributes."""
    el = ET.Element(f"{{{SVG_NS}}}{tag}")
    for k, v in attrs.items():
        if v is not None:
            el.set(k.replace("_", "-"), str(v))
    return el


def make_svg_subelement(parent, tag, **attrs):
    """Create an SVG sub-element with the given attributes."""
    el = ET.SubElement(parent, f"{{{SVG_NS}}}{tag}")
    for k, v in attrs.items():
        if v is not None:
            el.set(k.replace("_", "-"), str(v))
    return el


def add_text_elements(parent, text_lines, x, y, font_family, font_size,
                      font_weight, text_color, text_anchor, line_spacing,
                      letter_spacing):
    """Add <text> elements for each line, centered at (x, y)."""
    num_lines = len(text_lines)
    # Center the text block vertically: offset so middle line is at y
    total_height = font_size * line_spacing * (num_lines - 1)
    start_y = y - total_height / 2

    for i, line in enumerate(text_lines):
        line_y = start_y + i * font_size * line_spacing
        style_parts = {
            "font-family": font_family,
            "font-size": f"{font_size}px",
            "font-weight": font_weight,
            "fill": text_color,
        }
        if letter_spacing is not None:
            style_parts["letter-spacing"] = letter_spacing

        text_el = make_svg_subelement(
            parent, "text",
            x=x, y=line_y,
            text_anchor=text_anchor,
            dominant_baseline="central",
            style=build_style(style_parts),
        )
        text_el.text = line


def build_below_layout(info, text_lines, font_family, font_size, font_weight,
                       text_color, text_anchor, line_spacing, letter_spacing,
                       shape_fill, shape_stroke, shape_stroke_width,
                       shape_opacity, padding):
    """Build SVG with NC shape on top and text centered below."""
    vb_x, vb_y, vb_w, vb_h = info["viewbox"]

    # Auto font size: ~8% of shape width
    if font_size is None:
        font_size = vb_w * 0.08

    text_block_height = font_size * line_spacing * len(text_lines)
    gap = font_size * 0.8  # gap between shape and text

    # New viewBox: expand downward for text
    total_h = vb_h + gap + text_block_height + padding * 2
    total_w = vb_w + padding * 2
    new_vb_x = vb_x - padding
    new_vb_y = vb_y - padding
    new_vb_w = total_w
    new_vb_h = total_h

    # Compute display dimensions (scale to reasonable pixel size)
    display_w = 800
    display_h = display_w * (new_vb_h / new_vb_w)

    root = make_svg_element(
        "svg",
        width=f"{display_w:.2f}",
        height=f"{display_h:.2f}",
        viewBox=f"{new_vb_x} {new_vb_y} {new_vb_w} {new_vb_h}",
        version="1.0",
    )

    # NC shape group
    shape_g = make_svg_subelement(root, "g", transform=info["transform"])
    if shape_opacity is not None:
        shape_g.set("opacity", str(shape_opacity))

    style = apply_shape_overrides(
        info["path_style"], shape_fill, shape_stroke, shape_stroke_width
    )
    make_svg_subelement(shape_g, "path", d=info["path_d"], style=style)

    # Text centered below the shape
    text_x = vb_x + vb_w / 2
    text_y = vb_y + vb_h + gap + text_block_height / 2
    add_text_elements(
        root, text_lines, text_x, text_y,
        font_family, font_size, font_weight, text_color,
        text_anchor, line_spacing, letter_spacing,
    )

    return root


def build_overlay_layout(info, text_lines, font_family, font_size, font_weight,
                         text_color, text_anchor, line_spacing, letter_spacing,
                         shape_fill, shape_stroke, shape_stroke_width,
                         shape_opacity, padding):
    """Build SVG with text overlaid on the NC shape."""
    vb_x, vb_y, vb_w, vb_h = info["viewbox"]

    if font_size is None:
        font_size = vb_h * 0.25

    new_vb_x = vb_x - padding
    new_vb_y = vb_y - padding
    new_vb_w = vb_w + padding * 2
    new_vb_h = vb_h + padding * 2

    display_w = 800
    display_h = display_w * (new_vb_h / new_vb_w)

    root = make_svg_element(
        "svg",
        width=f"{display_w:.2f}",
        height=f"{display_h:.2f}",
        viewBox=f"{new_vb_x} {new_vb_y} {new_vb_w} {new_vb_h}",
        version="1.0",
    )

    # NC shape group
    shape_g = make_svg_subelement(root, "g", transform=info["transform"])
    if shape_opacity is not None:
        shape_g.set("opacity", str(shape_opacity))

    style = apply_shape_overrides(
        info["path_style"], shape_fill, shape_stroke, shape_stroke_width
    )
    make_svg_subelement(shape_g, "path", d=info["path_d"], style=style)

    # Text centered on the shape
    text_x = vb_x + vb_w / 2
    text_y = vb_y + vb_h / 2
    add_text_elements(
        root, text_lines, text_x, text_y,
        font_family, font_size, font_weight, text_color,
        text_anchor, line_spacing, letter_spacing,
    )

    return root


def build_clipped_layout(info, text_lines, font_family, font_size, font_weight,
                         text_color, text_anchor, line_spacing, letter_spacing,
                         shape_fill, shape_stroke, shape_stroke_width,
                         shape_opacity, padding):
    """Build SVG with text clipped to the NC shape silhouette."""
    vb_x, vb_y, vb_w, vb_h = info["viewbox"]

    if font_size is None:
        font_size = vb_h * 0.45

    new_vb_x = vb_x - padding
    new_vb_y = vb_y - padding
    new_vb_w = vb_w + padding * 2
    new_vb_h = vb_h + padding * 2

    display_w = 800
    display_h = display_w * (new_vb_h / new_vb_w)

    root = make_svg_element(
        "svg",
        width=f"{display_w:.2f}",
        height=f"{display_h:.2f}",
        viewBox=f"{new_vb_x} {new_vb_y} {new_vb_w} {new_vb_h}",
        version="1.0",
    )

    # Define clipPath using the NC shape
    defs = make_svg_subelement(root, "defs")
    clip = make_svg_subelement(defs, "clipPath", id="nc-clip")
    clip_g = make_svg_subelement(clip, "g", transform=info["transform"])
    make_svg_subelement(clip_g, "path", d=info["path_d"])

    # Text group clipped to NC shape
    text_g = make_svg_subelement(root, "g")
    text_g.set("clip-path", "url(#nc-clip)")

    # Optional background fill inside the clipped area
    bg_fill = shape_fill if shape_fill else "#ffffff"
    bg_g = make_svg_subelement(text_g, "g", transform=info["transform"])
    bg_style = parse_style(info["path_style"])
    bg_style["fill"] = bg_fill
    bg_style.pop("stroke", None)
    bg_style.pop("stroke-width", None)
    bg_style.pop("stroke-linejoin", None)
    make_svg_subelement(bg_g, "path", d=info["path_d"], style=build_style(bg_style))

    # Add text lines centered on the shape
    text_x = vb_x + vb_w / 2
    text_y = vb_y + vb_h / 2
    add_text_elements(
        text_g, text_lines, text_x, text_y,
        font_family, font_size, font_weight, text_color,
        text_anchor, line_spacing, letter_spacing,
    )

    # Draw the NC outline stroke on top (not clipped)
    stroke_g = make_svg_subelement(root, "g", transform=info["transform"])
    stroke_style = parse_style(info["path_style"])
    stroke_style["fill"] = "none"
    if shape_stroke:
        stroke_style["stroke"] = shape_stroke
    if shape_stroke_width:
        stroke_style["stroke-width"] = shape_stroke_width
    make_svg_subelement(stroke_g, "path", d=info["path_d"], style=build_style(stroke_style))

    return root


def apply_shape_overrides(original_style, fill, stroke, stroke_width):
    """Apply optional overrides to the shape's style string."""
    style = parse_style(original_style)
    if fill is not None:
        style["fill"] = fill
    if stroke is not None:
        style["stroke"] = stroke
    if stroke_width is not None:
        style["stroke-width"] = stroke_width
    return build_style(style)


LAYOUT_BUILDERS = {
    "below": build_below_layout,
    "overlay": build_overlay_layout,
    "clipped": build_clipped_layout,
}


@click.command()
@click.option(
    "--input", "-i", "input_file",
    default=DEFAULT_INPUT, show_default=True,
    help="Input SVG file (NC outline)",
)
@click.option(
    "--output", "-o", "output_file",
    default=DEFAULT_OUTPUT, show_default=True,
    help="Output SVG file",
)
@click.option(
    "--layout", "-l",
    type=click.Choice(["below", "overlay", "clipped"]),
    default="below", show_default=True,
    help="Text layout mode",
)
@click.option(
    "--text", "-t", "text_lines",
    multiple=True,
    help="Text line (repeatable). Default: 'NORTH CAROLINA' 'WIKIPEDIANS'",
)
@click.option("--font-family", default="sans-serif", show_default=True)
@click.option(
    "--font-size", type=float, default=None,
    help="Font size in viewBox units (auto-calculated if not set)",
)
@click.option("--font-weight", default="bold", show_default=True)
@click.option("--text-color", default="#000000", show_default=True)
@click.option(
    "--text-anchor",
    type=click.Choice(["start", "middle", "end"]),
    default="middle", show_default=True,
)
@click.option("--line-spacing", type=float, default=1.2, show_default=True)
@click.option("--letter-spacing", default=None, help="SVG letter-spacing value")
@click.option("--shape-fill", default=None, help="Override shape fill color")
@click.option("--shape-stroke", default=None, help="Override shape stroke color")
@click.option("--shape-stroke-width", default=None, help="Override shape stroke width")
@click.option(
    "--shape-opacity", type=float, default=None,
    help="Shape group opacity (0.0-1.0)",
)
@click.option("--padding", type=float, default=2000, show_default=True,
              help="Padding around content in viewBox units")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def main(input_file, output_file, layout, text_lines, font_family, font_size,
         font_weight, text_color, text_anchor, line_spacing, letter_spacing,
         shape_fill, shape_stroke, shape_stroke_width, shape_opacity, padding,
         verbose):
    """Add text to an NC outline SVG to create logo variants."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        log.error("Input file not found: %s", input_path)
        raise SystemExit(1)

    if not text_lines:
        text_lines = DEFAULT_TEXT

    log.info("Reading %s", input_path)
    info = parse_input_svg(input_path)
    log.info("ViewBox: %s", info["viewbox"])
    log.info("Layout: %s", layout)
    log.info("Text lines: %s", list(text_lines))

    builder = LAYOUT_BUILDERS[layout]
    root = builder(
        info, list(text_lines),
        font_family, font_size, font_weight, text_color,
        text_anchor, line_spacing, letter_spacing,
        shape_fill, shape_stroke, shape_stroke_width,
        shape_opacity, padding,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    tree.write(str(output_path), xml_declaration=True, encoding="UTF-8")
    log.info("Wrote %s", output_path)


if __name__ == "__main__":
    main()
