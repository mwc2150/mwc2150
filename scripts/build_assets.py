"""Build the SVG assets used by the profile README.

GitHub READMEs can't load CSS or web fonts, so section and project titles are
drawn as SVGs with a subset of EB Garamond embedded as a data URI. Body copy stays
as real text in README.md.

Usage:
    python scripts/build_assets.py

Needs fontTools + brotli (pip install fonttools brotli). The EB Garamond variable
font is downloaded once into scripts/.cache/.
"""

from __future__ import annotations

import base64
import io
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CACHE = Path(__file__).resolve().parent / ".cache"

FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/ebgaramond/EBGaramond%5Bwght%5D.ttf"
FONT_AXES = {"wght": 600}

# Palette sampled from the Flying Nimbus GIF.
SKY = "#1133BB"
GOLD = "#FFCC1B"
INK_LIGHT = "#1122A9"  # title text on GitHub light (#ffffff)
INK_DARK = "#F3F1EC"  # title text on GitHub dark (#0d1117)


# --------------------------------------------------------------------- fonts

_font: TTFont | None = None


def _instance() -> TTFont:
    global _font
    if _font is None:
        CACHE.mkdir(exist_ok=True)
        path = CACHE / "ebgaramond.ttf"
        if not path.exists():
            print("downloading EB Garamond ...")
            urllib.request.urlretrieve(FONT_URL, path)
        _font = instancer.instantiateVariableFont(TTFont(path), FONT_AXES)
    return _font


def text_width(text: str, size: float, tracking: float = 0) -> float:
    """Advance width of `text` in px (kerning ignored; close enough for layout)."""
    font = _instance()
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    units = sum(hmtx[cmap[ord(ch)]][0] for ch in text)
    return units * size / font["head"].unitsPerEm + tracking * (len(text) - 1)


def font_face(text: str) -> str:
    """@font-face rule with EB Garamond subset to exactly `text`, as base64 WOFF2."""
    buf = io.BytesIO()
    _instance().save(buf)
    buf.seek(0)
    font = TTFont(buf)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt"]
    opts.name_IDs = []
    subsetter = subset.Subsetter(opts)
    subsetter.populate(text="".join(sorted(set(text + " "))))
    subsetter.subset(font)
    out = io.BytesIO()
    font.save(out)
    data = base64.b64encode(out.getvalue()).decode()
    return f"@font-face{{font-family:'F';src:url(data:font/woff2;base64,{data}) format('woff2');}}"


def svg(width: float, height: float, body: str, style: str, label: str) -> str:
    label = escape(label, {'"': "&quot;"})
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="{label}">'
        f"<title>{label}</title><style>{style}</style>{body}</svg>\n"
    )


def title(text: str, size: float, ink: str, height: float, baseline: float, x: float = 1) -> tuple[str, float, str]:
    tracking = -size / 50
    width = x + text_width(text, size, tracking) + 4
    style = font_face(text) + (
        ".t{font-family:'F',Georgia,serif;font-size:%gpx;letter-spacing:%gpx;fill:%s}" % (size, tracking, ink)
    )
    return f'<text class="t" x="{x:g}" y="{baseline:g}">{escape(text)}</text>', width, style


# ------------------------------------------------------------------ headers

def header(text: str, ink: str) -> str:
    body, width, style = title(text, 32, ink, 46, 33)
    return svg(width, 46, body, style, text)


# ------------------------------------------------------------------ projects

PROJECTS = {
    "pharmagentics": "PharmAgentics",
    "qual2cast": "Qual2Cast",
    "ai-pulse": "AI Pulse",
    "rl-planning": "RL for LLM planning",
}

ICONS = {
    # A capsule, half filled.
    "pharmagentics": (
        '<g transform="rotate(-40 28 28)">'
        '<rect x="16.5" y="22" width="23" height="12" rx="6"/>'
        f'<path d="M28 22 H22.5 a6 6 0 0 0 0 12 H28 Z" fill="{GOLD}"/>'
        "</g>"
    ),
    # Two known comps and a dashed estimate.
    "qual2cast": (
        '<path d="M15 39 H41"/>'
        '<rect x="17.5" y="29" width="5.5" height="10" rx="1"/>'
        '<rect x="25.5" y="23" width="5.5" height="16" rx="1"/>'
        '<rect x="33.5" y="17" width="5.5" height="22" rx="1" stroke-dasharray="2.6 2.4"/>'
    ),
    # A pulse line.
    "ai-pulse": '<path d="M14 30 H20.5 L24 20 L29.5 37 L33 26 L35.5 30 H42"/>',
    # A route to a pin.
    "rl-planning": (
        '<path d="M18 39 C 25 39, 21 31, 28 31 S 33 33, 35 30" stroke-dasharray="2.4 2.6"/>'
        f'<circle cx="18" cy="39" r="2.2" fill="{GOLD}"/>'
        '<path d="M36 29 C 36 29 30.5 23 30.5 19.5 A5.5 5.5 0 0 1 41.5 19.5 C 41.5 23 36 29 36 29 Z"/>'
        f'<circle cx="36" cy="19.5" r="1.8" fill="{GOLD}"/>'
    ),
}


def project_title(name: str, icon: str, ink: str) -> str:
    """A project's emblem tile followed by its name."""
    tile = 40
    text, width, style = title(name, 25, ink, tile, 28, x=tile + 12)
    emblem = (
        f'<g transform="scale({tile / 56})">'
        f'<rect width="56" height="56" rx="15" fill="{SKY}"/>'
        f'<g fill="none" stroke="{GOLD}" stroke-width="2.6" stroke-linecap="round" '
        f'stroke-linejoin="round">{icon}</g></g>'
    )
    return svg(width, tile, emblem + text, style, name)


# --------------------------------------------------------------------- main

HEADERS = {"about": "Hello, I’m Michael", "work": "Selected work", "toolkit": "Toolkit"}


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    out = {}
    for slug, text in HEADERS.items():
        out[f"h-{slug}-light.svg"] = header(text, INK_LIGHT)
        out[f"h-{slug}-dark.svg"] = header(text, INK_DARK)
    for slug, name in PROJECTS.items():
        out[f"p-{slug}-light.svg"] = project_title(name, ICONS[slug], INK_LIGHT)
        out[f"p-{slug}-dark.svg"] = project_title(name, ICONS[slug], INK_DARK)
    for name, text in out.items():
        (ASSETS / name).write_text(text, encoding="utf-8", newline="\n")
        print(f"{name:28} {len(text.encode()) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
