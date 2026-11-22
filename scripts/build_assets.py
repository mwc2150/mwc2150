"""Build the SVG assets used by the profile README.

GitHub READMEs can't load CSS or web fonts, so every piece of display type is
drawn as an SVG with a subset of Fraunces embedded as a data URI. Body copy
stays as real text in README.md.

Usage:
    python scripts/build_assets.py

Needs fontTools + brotli (pip install fonttools brotli) and Pillow. The
Fraunces variable fonts are downloaded once into scripts/.cache/.
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

FONT_URLS = {
    "roman": "https://raw.githubusercontent.com/google/fonts/main/ofl/fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf",
    "italic": "https://raw.githubusercontent.com/google/fonts/main/ofl/fraunces/Fraunces-Italic%5BSOFT,WONK,opsz,wght%5D.ttf",
}

# Palette sampled from the Flying Nimbus GIF.
SKY_DEEP = "#1122A9"
SKY = "#1133BB"
CLOUD = "#FBF7EE"
CLOUD_SHADE = "#B9C0EE"
MIST = "#D9E1FF"  # secondary text on sky, 9:1 on SKY
GOLD = "#FFCC1B"
EMBER = "#EE8811"
INK_LIGHT = SKY_DEEP  # header text on GitHub light (#ffffff)
INK_DARK = "#F3F1EC"  # header text on GitHub dark (#0d1117)

# Named instances of the variable font: (file, axis location).
STYLES = {
    "display": ("roman", {"opsz": 144, "wght": 800, "SOFT": 100, "WONK": 1}),
    "head": ("roman", {"opsz": 48, "wght": 680, "SOFT": 100, "WONK": 0}),
    "italic": ("italic", {"opsz": 14, "wght": 420, "SOFT": 50, "WONK": 0}),
}


# --------------------------------------------------------------------- fonts

def _variable(name: str) -> Path:
    CACHE.mkdir(exist_ok=True)
    path = CACHE / f"fraunces-{name}.ttf"
    if not path.exists():
        print(f"downloading Fraunces {name} ...")
        urllib.request.urlretrieve(FONT_URLS[name], path)
    return path


_instances: dict[str, TTFont] = {}


def _instance(style: str) -> TTFont:
    if style not in _instances:
        file, loc = STYLES[style]
        font = TTFont(_variable(file))
        _instances[style] = instancer.instantiateVariableFont(font, loc)
    return _instances[style]


def text_width(style: str, text: str, size: float, tracking: float = 0) -> float:
    """Advance width of `text` in px (kerning ignored; close enough for layout)."""
    font = _instance(style)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = font["head"].unitsPerEm
    units = sum(hmtx[cmap[ord(ch)]][0] for ch in text)
    return units * size / upm + tracking * (len(text) - 1)


def font_face(style: str, text: str) -> str:
    """@font-face rule with the style subset to exactly `text`, as base64 WOFF2."""
    font = _instance(style)
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    sub = TTFont(buf)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt"]
    opts.name_IDs = []
    opts.notdef_outline = True
    sub_er = subset.Subsetter(opts)
    sub_er.populate(text="".join(sorted(set(text + " "))))
    sub_er.subset(sub)
    out = io.BytesIO()
    sub.flavor = "woff2"
    sub.save(out)
    data = base64.b64encode(out.getvalue()).decode()
    return (
        f"@font-face{{font-family:'F-{style}';"
        f"src:url(data:font/woff2;base64,{data}) format('woff2');}}"
    )


# ------------------------------------------------------------------- shapes

def puff(cx: float, cy: float, s: float, top: str, under: str) -> str:
    """A cel-shaded cloud puff: an offset underside, then the lit top."""
    circles = [(-1.0, 0.15, 0.55), (-0.35, -0.3, 0.75), (0.45, -0.15, 0.65), (1.05, 0.2, 0.45)]
    base = f'<rect x="{cx - 1.1 * s:.1f}" y="{cy:.1f}" width="{2.2 * s:.1f}" height="{0.55 * s:.1f}" rx="{0.27 * s:.1f}"/>'
    blobs = "".join(
        f'<circle cx="{cx + dx * s:.1f}" cy="{cy + dy * s:.1f}" r="{r * s:.1f}"/>' for dx, dy, r in circles
    )
    return (
        f'<g fill="{under}" transform="translate(0 {0.22 * s:.1f})">{base}{blobs}</g>'
        f'<g fill="{top}">{base}{blobs}</g>'
    )


def trail(d: str, width: float, cls: str = "") -> str:
    """The Nimbus vapour trail: an ember rim around a gold core."""
    c = f' class="{cls}"' if cls else ""
    return (
        f'<path{c} d="{d}" pathLength="1" fill="none" stroke="{EMBER}" '
        f'stroke-width="{width:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path{c} d="{d}" pathLength="1" fill="none" stroke="{GOLD}" '
        f'stroke-width="{width * 0.55:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def svg(width: float, height: float, body: str, style: str, label: str) -> str:
    label = escape(label, {'"': "&quot;"})
    a11y =f' role="img" aria-label="{label}"' if label else ' aria-hidden="true"'
    title = f"<title>{label}</title>" if label else ""
    css = f"<style>{style}</style>" if style else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}"{a11y}>{title}{css}{body}</svg>\n'
    )


# --------------------------------------------------------------------- hero

def hero_card() -> str:
    first, last = "Michael", "Chen"
    tag1, tag2 = "Applied AI & analytics for pharma", "commercial ops and private equity."
    W, H = 400, 300

    loop = (
        "M -24 286 C 90 292, 236 290, 312 234 "
        "C 376 188, 384 118, 344 104 "
        "C 306 92, 296 146, 330 150 "
        "C 362 154, 378 112, 360 74"
    )

    style = (
        font_face("display", first + last)
        + font_face("italic", tag1 + tag2)
        + ".name{font-family:'F-display',Georgia,serif;font-size:60px;letter-spacing:-1.3px;fill:%s}" % CLOUD
        + ".tag{font-family:'F-italic',Georgia,serif;font-style:italic;font-size:15.5px;fill:%s}" % MIST
        + ".draw{stroke-dasharray:1;stroke-dashoffset:0;"
        "animation:draw 2.1s cubic-bezier(.16,1,.3,1) .25s backwards}"
        "@keyframes draw{from{stroke-dashoffset:1}}"
        ".nimbus{transform-box:fill-box;transform-origin:50% 50%;"
        "animation:arrive .7s cubic-bezier(.16,1,.3,1) 1.5s backwards,bob 3.2s ease-in-out 2.2s infinite alternate}"
        "@keyframes arrive{from{opacity:0;transform:scale(.5)}}"
        "@keyframes bob{to{transform:translateY(-3px)}}"
        ".drift{animation:drift 11s ease-in-out infinite alternate}"
        ".drift.slow{animation-duration:16s}"
        "@keyframes drift{to{transform:translateX(-14px)}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )

    body = (
        "<defs><linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'>"
        f"<stop offset='0' stop-color='{SKY_DEEP}'/><stop offset='1' stop-color='{SKY}'/>"
        "</linearGradient></defs>"
        f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
        f'<g class="drift slow">{puff(212, 34, 15, CLOUD, CLOUD_SHADE)}</g>'
        f'<g class="drift">{puff(392, 284, 20, CLOUD, CLOUD_SHADE)}</g>'
        f"{trail(loop, 9, 'draw')}"
        f'<g class="nimbus">{puff(360, 70, 13, GOLD, EMBER)}</g>'
        f'<text class="name" x="26" y="118">{first}</text>'
        f'<text class="name" x="26" y="176">{last}</text>'
        f'<text class="tag" x="28" y="216">{tag1.replace("&", "&amp;")}</text>'
        f'<text class="tag" x="28" y="237">{tag2}</text>'
    )
    return svg(W, H, body, style, f"{first} {last}. {tag1} {tag2}")


# ------------------------------------------------------------------ headers

def header(text: str, ink: str) -> str:
    """Section title with the gold Nimbus puff as its mark."""
    size, H = 28, 46
    tw = text_width("head", text, size, -0.5)
    W = tw + 46
    style = (
        font_face("head", text)
        + ".h{font-family:'F-head',Georgia,serif;font-size:%dpx;letter-spacing:-0.5px;fill:%s}" % (size, ink)
    )
    body = f'<text class="h" x="1" y="32">{text}</text>{puff(tw + 26, 20, 9, GOLD, EMBER)}'
    return svg(W, H, body, style, text)


def project_title(name: str, icon: str, ink: str) -> str:
    """A project's emblem tile followed by its name."""
    size, H, tile = 22, 40, 40
    tw = text_width("head", name, size, -0.3)
    W = tile + 12 + tw + 4
    style = (
        font_face("head", name)
        + ".n{font-family:'F-head',Georgia,serif;font-size:%dpx;letter-spacing:-0.3px;fill:%s}" % (size, ink)
    )
    body = (
        f'<g transform="scale({tile / 56})">{_emblem_body(icon)}</g>'
        f'<text class="n" x="{tile + 12}" y="28">{escape(name)}</text>'
    )
    return svg(W, H, body, style, name)


# ------------------------------------------------------------------- emblems

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
        '<circle cx="18" cy="39" r="2.2" fill="' + GOLD + '"/>'
        '<path d="M36 29 C 36 29 30.5 23 30.5 19.5 A5.5 5.5 0 0 1 41.5 19.5 C 41.5 23 36 29 36 29 Z"/>'
        '<circle cx="36" cy="19.5" r="1.8" fill="' + GOLD + '"/>'
    ),
}


def _emblem_body(icon: str) -> str:
    return (
        f'<rect width="56" height="56" rx="15" fill="{SKY}"/>'
        f'<g fill="none" stroke="{GOLD}" stroke-width="2.6" stroke-linecap="round" '
        f'stroke-linejoin="round">{icon}</g>'
    )


# --------------------------------------------------------------------- main

HEADERS = {"about": "About", "work": "Selected work", "toolkit": "Toolkit"}


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    out = {"hero-card.svg": hero_card()}
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
