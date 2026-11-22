"""Build the project buttons used by the profile README.

Each button is an SVG (one per GitHub theme) wrapped in a link in README.md.
Project names are set in EB Garamond, embedded as a subset WOFF2 data URI
because SVGs shown as images can't fetch web fonts. The one-line blurb uses the
viewer's system UI font, matching GitHub's own text. Emoji are Noto Emoji
(Apache 2.0) so they look the same on every OS.

Usage:
    python scripts/build_assets.py

Needs fontTools + brotli (pip install fonttools brotli). Fonts and emoji are
downloaded once into scripts/.cache/.
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
EMOJI_URL = "https://cdn.jsdelivr.net/gh/googlefonts/noto-emoji@v2.047/svg/emoji_u{code}.svg"

# (slug, emoji codepoint, name, blurb)
PROJECTS = [
    ("pharmagentics", "1f48a", "PharmAgentics", "Multi-agent AI for pharma brand performance"),
    ("qual2cast", "1f4bc", "Qual2Cast", "Valuing private companies via public comps"),
    ("ai-pulse", "1f4e1", "AI Pulse", "Compute, data and model trends behind AI"),
    ("rl-planning", "1f9e0", "RL for LLM planning", "PPO-trained memory for LLM planning agents"),
]

# GitHub's own surface colors, so the buttons sit natively in either theme.
THEMES = {
    "light": {"bg": "#f6f8fa", "border": "#d1d9e0", "ink": "#1f2328", "muted": "#59636e"},
    "dark": {"bg": "#151b23", "border": "#3d444d", "ink": "#f0f6fc", "muted": "#9198a1"},
}

W, H = 400, 84


def _cached(name: str, url: str) -> Path:
    CACHE.mkdir(exist_ok=True)
    path = CACHE / name
    if not path.exists():
        print(f"downloading {name} ...")
        urllib.request.urlretrieve(url, path)
    return path


_font: TTFont | None = None


def font_face(text: str) -> str:
    """@font-face rule with EB Garamond SemiBold subset to `text`, as base64 WOFF2."""
    global _font
    if _font is None:
        _font = instancer.instantiateVariableFont(TTFont(_cached("ebgaramond.ttf", FONT_URL)), {"wght": 600})
    buf = io.BytesIO()
    _font.save(buf)
    buf.seek(0)
    font = TTFont(buf)
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
    return f"@font-face{{font-family:'G';src:url(data:font/woff2;base64,{data}) format('woff2');}}"


def text_width(text: str, size: float, tracking: float = 0) -> float:
    """Advance width of `text` in px (kerning ignored; close enough for layout)."""
    font_face(text)  # loads the font
    cmap, hmtx = _font.getBestCmap(), _font["hmtx"]
    units = sum(hmtx[cmap[ord(ch)]][0] for ch in text)
    return units * size / _font["head"].unitsPerEm + tracking * (len(text) - 1)


def heading(text: str, t: dict[str, str]) -> str:
    """The opening greeting, set in EB Garamond."""
    size, height = 32, 46
    tracking = -size / 50
    width = text_width(text, size, tracking) + 6
    label = escape(text, {'"': "&quot;"})
    style = font_face(text) + (
        ".h{font-family:'G',Georgia,serif;font-size:%gpx;letter-spacing:%gpx;fill:%s}" % (size, tracking, t["ink"])
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height}" '
        f'viewBox="0 0 {width:.0f} {height}" role="img" aria-label="{label}"><title>{label}</title>'
        f'<style>{style}</style><text class="h" x="1" y="33">{escape(text)}</text></svg>\n'
    )


def emoji(code: str) -> str:
    data = base64.b64encode(_cached(f"emoji_u{code}.svg", EMOJI_URL.format(code=code)).read_bytes()).decode()
    return f'<image x="20" y="22" width="40" height="40" href="data:image/svg+xml;base64,{data}"/>'


def button(code: str, name: str, blurb: str, t: dict[str, str]) -> str:
    label = escape(f"{name}: {blurb}", {'"': "&quot;"})
    style = (
        font_face(name)
        + ".n{font-family:'G',Georgia,serif;font-size:23px;fill:%s}" % t["ink"]
        + ".b{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif;"
        "font-size:13.5px;fill:%s}" % t["muted"]
    )
    # A small arrow in the top-right corner says "this goes somewhere".
    arrow = (
        f'<path d="M{W - 30} 30 L{W - 20} 20 M{W - 28} 20 H{W - 20} V28" fill="none" '
        f'stroke="{t["muted"]}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" aria-label="{label}"><title>{label}</title><style>{style}</style>'
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>'
        f"{emoji(code)}{arrow}"
        f'<text class="n" x="76" y="38">{escape(name)}</text>'
        f'<text class="b" x="76" y="61">{escape(blurb)}</text>'
        "</svg>\n"
    )


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for theme, colors in THEMES.items():
        path = ASSETS / f"h-hello-{theme}.svg"
        path.write_text(heading("Hello, I’m Michael", colors), encoding="utf-8", newline="\n")
        print(path.name)
    for slug, code, name, blurb in PROJECTS:
        for theme, colors in THEMES.items():
            path = ASSETS / f"btn-{slug}-{theme}.svg"
            text = button(code, name, blurb, colors)
            path.write_text(text, encoding="utf-8", newline="\n")
            print(f"{path.name:30} {len(text.encode()) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
