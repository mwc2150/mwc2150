"""Build the SVGs used by the profile README.

- The greeting, set in EB Garamond SemiBold.
- The project picker: a "Pick an emoji, any emoji." prompt in EB Garamond
  Italic, then four bare floating emoji, one per project, each linked to its
  repo in README.md. No names or blurbs are shown, so the pick is a small
  mystery; the README gives each emoji a title, so hovering shows its name.

Every SVG comes in a light and a dark variant (switched by <picture> in the
README). Fonts are embedded as subset WOFF2 data URIs because SVGs shown as
images can't fetch web fonts. Emoji are Noto Emoji (Apache 2.0) so they look
the same on every OS. The emoji bob with CSS animation inside the SVG, which
GitHub plays in <img>; it stops under prefers-reduced-motion.

Usage:
    python scripts/build_assets.py

Needs fontTools + brotli (pip install fonttools brotli). Fonts and emoji are
downloaded once into scripts/.cache/.
"""

from __future__ import annotations

import base64
import io
import re
import urllib.request
import xml.dom.minidom
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CACHE = Path(__file__).resolve().parent / ".cache"

FONTS_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/ebgaramond/"
# name -> (cache file, URL, weight, italic)
FONTS = {
    "heading": ("ebgaramond.ttf", FONTS_URL + "EBGaramond%5Bwght%5D.ttf", 600, False),
    "prompt": ("ebgaramond-italic.ttf", FONTS_URL + "EBGaramond-Italic%5Bwght%5D.ttf", 500, True),
}
EMOJI_URL = "https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji@v2.047/svg/emoji_u{code}.svg"

# (slug, emoji codepoint, alt text, bob period s, phase delay s, resting lift px, tilt deg)
# Periods are mutually awkward so the four never sync up, and the resting lifts
# stagger the row so it reads as loose objects in the air, not a grid.
PROJECTS = [
    ("pharmagentics", "1f48a", "PharmAgentics", 3.7, -0.4, 2, 3),
    ("qual2cast", "1f4bc", "Qual2Cast", 4.3, -2.1, 7, -2),
    ("ai-pulse", "1f4e1", "AI Pulse", 3.9, -3.3, 0, 2.5),
    ("rl-planning", "1f9e0", "RL for LLM planning", 4.6, -1.2, 5, -3),
]

# GitHub's own text colors, so everything sits natively in either theme.
THEMES = {
    "light": {"ink": "#1f2328", "muted": "#59636e", "shadow": "#1f2328", "shadow_op": 0.24},
    "dark": {"ink": "#f0f6fc", "muted": "#9198a1", "shadow": "#000000", "shadow_op": 1},
}

# Floating emoji canvas. 4 x 80 = 320px with no gaps between links, so the row
# stays on one line down to ~320px of content.
W, H = 80, 108
E = 52  # emoji size
FLOOR = 97  # shadow center y
REST_TOP = 30  # emoji top at rest, before per-emoji lift
RISE = 7  # bob amplitude, px


def _cached(name: str, url: str) -> Path:
    CACHE.mkdir(exist_ok=True)
    path = CACHE / name
    if not path.exists():
        print(f"downloading {name} ...")
        urllib.request.urlretrieve(url, path)
    return path


_fonts: dict[str, TTFont] = {}


def _font(kind: str) -> TTFont:
    if kind not in _fonts:
        file, url, weight, _ = FONTS[kind]
        _fonts[kind] = instancer.instantiateVariableFont(TTFont(_cached(file, url)), {"wght": weight})
    return _fonts[kind]


def font_face(kind: str, text: str) -> str:
    """@font-face rule named 'G' with the `kind` font subset to `text`, as base64 WOFF2."""
    buf = io.BytesIO()
    _font(kind).save(buf)
    buf.seek(0)
    font = TTFont(buf, recalcTimestamp=False)
    font["head"].modified = font["head"].created  # keep rebuilds byte-identical
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    opts.name_IDs = []
    subsetter = subset.Subsetter(opts)
    subsetter.populate(text="".join(sorted(set(text + " "))))
    subsetter.subset(font)
    out = io.BytesIO()
    font.save(out)
    data = base64.b64encode(out.getvalue()).decode()
    style = "font-style:italic;" if FONTS[kind][3] else ""
    return f"@font-face{{font-family:'G';{style}src:url(data:font/woff2;base64,{data}) format('woff2');}}"


def text_width(kind: str, text: str, size: float, tracking: float = 0) -> float:
    """Advance width of `text` in px (kerning ignored; close enough for layout)."""
    font = _font(kind)
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    units = sum(hmtx[cmap[ord(ch)]][0] for ch in text)
    return units * size / font["head"].unitsPerEm + tracking * (len(text) - 1)


def line(kind: str, text: str, size: float, height: int, baseline: float, tracking: float, color: str) -> str:
    """One line of text as an SVG, in the given embedded font."""
    italic = FONTS[kind][3]
    width = text_width(kind, text, size, tracking) + (8 if italic else 6)  # room for overhang
    label = escape(text, {'"': "&quot;"})
    style = font_face(kind, text) + (
        ".t{font-family:'G',Georgia,serif;%sfont-size:%gpx;letter-spacing:%gpx;fill:%s}"
        % ("font-style:italic;" if italic else "", size, tracking, color)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height}" '
        f'viewBox="0 0 {width:.0f} {height}" role="img" aria-label="{label}"><title>{label}</title>'
        f'<style>{style}</style><text class="t" x="{1 if not italic else 2}" y="{baseline}">{escape(text)}</text></svg>\n'
    )


def heading(text: str, t: dict) -> str:
    """The opening greeting."""
    return line("heading", text, 32, 46, 33, -32 / 50, t["ink"])


def prompt(text: str, t: dict) -> str:
    """The picker's one line of copy: italic and muted, quieter than the greeting."""
    return line("prompt", text, 24, 34, 24, -24 / 100, t["muted"])


def emoji_data(code: str) -> str:
    svg = _cached(f"emoji_u{code}.svg", EMOJI_URL.format(code=code)).read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml.*?\?>|<!--.*?-->", "", svg, flags=re.S)
    svg = re.sub(r">\s+<", "><", re.sub(r"\s+", " ", svg)).strip()
    return base64.b64encode(svg.encode()).decode()


def floater(code: str, name: str, period: float, delay: float, lift: int, tilt: float, t: dict) -> str:
    """One emoji hovering over a soft shadow that shrinks and fades as it rises."""
    label = escape(name, {'"': "&quot;"})
    x, y = (W - E) / 2, REST_TOP - lift
    rest_scale = 1 - lift * 0.022  # emoji resting higher start with a smaller shadow
    anim = (
        f"@keyframes b{{0%,100%{{transform:translateY(0) rotate({-tilt / 2:g}deg)}}"
        f"50%{{transform:translateY(-{RISE}px) rotate({tilt / 2:g}deg)}}}}"
        f"@keyframes s{{0%,100%{{transform:scale({rest_scale:.3f});opacity:1}}"
        f"50%{{transform:scale({rest_scale * 0.74:.3f});opacity:.55}}}}"
        f".f,.s{{transform-box:fill-box;transform-origin:50% 50%;"
        f"animation:{period}s cubic-bezier(.45,0,.55,1) {delay}s infinite both}}"
        ".f{animation-name:b}.s{animation-name:s}"
        # Still frame: emoji at rest with a slight lean, shadow at its resting size.
        f"@media (prefers-reduced-motion:reduce){{.f,.s{{animation:none}}"
        f".f{{transform:rotate({-tilt / 2:g}deg)}}.s{{transform:scale({rest_scale:.3f})}}}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{label}"><title>{label}</title><style>{anim}</style>'
        f'<defs><radialGradient id="g"><stop offset="0" stop-color="{t["shadow"]}" stop-opacity="{t["shadow_op"]}"/>'
        f'<stop offset="1" stop-color="{t["shadow"]}" stop-opacity="0"/></radialGradient></defs>'
        f'<ellipse class="s" cx="{W / 2:g}" cy="{FLOOR}" rx="23" ry="5" fill="url(#g)"/>'
        f'<g class="f"><image x="{x:g}" y="{y}" width="{E}" height="{E}" '
        f'href="data:image/svg+xml;base64,{emoji_data(code)}"/></g>'
        "</svg>\n"
    )


def write(name: str, text: str) -> None:
    xml.dom.minidom.parseString(text)  # must be well-formed XML
    path = ASSETS / name
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"{name:30} {len(text.encode()) / 1024:6.1f} KB")


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for theme, t in THEMES.items():
        write(f"greeting-{theme}.svg", heading("Hello, I’m Michael ;)", t))
        write(f"prompt-{theme}.svg", prompt("Pick an emoji, any emoji.", t))
        for slug, code, name, period, delay, lift, tilt in PROJECTS:
            write(f"float-{slug}-{theme}.svg", floater(code, name, period, delay, lift, tilt, t))


if __name__ == "__main__":
    main()
