"""Build the SVGs used by the profile README.

- The greeting, set in EB Garamond SemiBold.
- The project picker: a "Pick an emoji, any emoji ;)" prompt in EB Garamond
  Italic, then four bare floating emoji, one per project, each linked to its
  repo in README.md. No names or blurbs are shown, so the pick is a small
  mystery; the README gives each emoji a title, so hovering shows its name.
- Two bands of tool icons above and below the picker, scrolling in opposite
  directions. Each band is one SVG with the icons embedded (an SVG shown as an
  image can't load outside files), so add or remove a tool in TOOLS and rebuild.

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
import hashlib
import io
import math
import re
import struct
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

DEVICON = "https://cdn.jsdelivr.net/gh/devicons/devicon@v2.18.0/icons/"
LOBE = "https://cdn.jsdelivr.net/npm/@lobehub/icons-static-svg@1.104.0/icons/"
HOMARR = "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons@d4b500dc40a8e1043b1581cabb7208892cf35472/svg/"

# (name, icon URL[, dark-theme icon URL]) in band order. The first half goes in
# the top band, the rest in the bottom one.
TOOLS = [
    ("Python", DEVICON + "python/python-original.svg"),
    ("Jupyter", DEVICON + "jupyter/jupyter-original.svg"),
    ("pandas", DEVICON + "pandas/pandas-original.svg"),
    ("NumPy", DEVICON + "numpy/numpy-original.svg"),
    ("SciPy", "https://cdn.simpleicons.org/scipy/6C96E4"),
    ("Seaborn", DEVICON + "seaborn/seaborn-original.svg"),
    ("scikit-learn", DEVICON + "scikitlearn/scikitlearn-original.svg"),
    ("PyTorch", DEVICON + "pytorch/pytorch-original.svg"),
    ("TensorFlow", DEVICON + "tensorflow/tensorflow-original.svg"),
    ("XGBoost", "https://xgboost.ai/images/logo/xgboost-logo-trimmed.png"),
    ("LightGBM", "https://cdn.jsdelivr.net/gh/microsoft/LightGBM@b892602e2ca4cd79dfe5439c7c35fa1b4ab61567/R-package/man/figures/logo.svg"),
    ("Hugging Face", DEVICON + "huggingface/huggingface-original.svg"),
    ("LangChain", "https://cdn.simpleicons.org/langchain/399985"),
    ("Claude Code and Anthropic API", LOBE + "claudecode-color.svg"),
    ("Gemini", LOBE + "gemini-color.svg"),
    ("OpenAI Codex and API", LOBE + "codex-color.svg"),
    ("xAI", "https://cdn.jsdelivr.net/npm/@lobehub/icons-static-png@2.10.0/light/xai.png",
     "https://cdn.jsdelivr.net/npm/@lobehub/icons-static-png@2.10.0/dark/xai.png"),
    ("R", DEVICON + "r/r-original.svg"),
    ("ggplot2", "https://cdn.jsdelivr.net/gh/tidyverse/ggplot2@87a95d9103536296c8334e72f9f722855cd16bcb/man/figures/logo.png"),
    ("dplyr", "https://cdn.jsdelivr.net/gh/tidyverse/dplyr@819c99f7284b3a413b391c60bea49ae7bfb8bafc/man/figures/logo.png"),
    ("Quarto", "https://cdn.simpleicons.org/quarto/75AADB"),
    ("Matplotlib", DEVICON + "matplotlib/matplotlib-original.svg"),
    ("DuckDB", DEVICON + "duckdb/duckdb-original.svg"),
    ("MySQL", DEVICON + "mysql/mysql-original.svg"),
    ("PostgreSQL", DEVICON + "postgresql/postgresql-original.svg"),
    ("Apache Spark (PySpark)", DEVICON + "apachespark/apachespark-original.svg"),
    ("Apache Hadoop", DEVICON + "hadoop/hadoop-original.svg"),
    ("Google Cloud (BigQuery and Vertex AI)", DEVICON + "googlecloud/googlecloud-original.svg"),
    ("AWS (EC2, S3, and RDS)", DEVICON + "amazonwebservices/amazonwebservices-original.svg"),
    ("Microsoft Excel", HOMARR + "microsoft-excel.svg"),
    ("Power BI", "https://cdn.jsdelivr.net/gh/microsoft/PowerBI-Icons@24f1db8bdfab951c25db591772140d2f4ec5bc1e/SVG/Power-BI.svg"),
    ("Tableau", "https://devicons.io/devicons/icons/tableau-icon.svg"),
    ("Streamlit", DEVICON + "streamlit/streamlit-original.svg"),
    ("Microsoft PowerPoint", HOMARR + "microsoft-powerpoint.svg"),
    ("Microsoft Word", HOMARR + "microsoft-word.svg"),
    ("FastAPI", DEVICON + "fastapi/fastapi-original.svg"),
    ("Docker", DEVICON + "docker/docker-original.svg"),
    ("Selenium", DEVICON + "selenium/selenium-original.svg"),
    ("Git", DEVICON + "git/git-original.svg"),
    ("Microsoft Copilot", HOMARR + "microsoft-copilot.svg"),
    ("Figma", DEVICON + "figma/figma-original.svg"),
    ("Shopify Analytics", "https://cdn.simpleicons.org/shopify/80AD45"),
    ("React", DEVICON + "react/react-original.svg"),
    ("HTML", DEVICON + "html5/html5-original.svg"),
    ("CSS", DEVICON + "css3/css3-original.svg"),
    ("JavaScript", DEVICON + "javascript/javascript-original.svg"),
]

# Tool bands. No viewBox and no fixed size on purpose: the SVG then draws at
# 1:1 inside whatever box the README gives it (width="100%" height="52"), so
# icons keep their size on phones and the edge fade sits at the band's real
# edges. (A fixed width would make browsers synthesize a viewBox and squash it.)
BAND_H = 52
ICON = 32  # icon height; wide logos get up to twice that in width
ICON_GAP = 18
BAND_MAX_W = 1280  # widest box we cover without a gap in the loop
BAND_SPEED = 26  # px per second

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


def tool_icon(url: str) -> tuple[str, bytes]:
    """(media type, bytes) of a tool icon, downloaded once into the cache."""
    req = urllib.request.Request(url, headers={"User-Agent": "build_assets.py"})
    path = CACHE / "tools" / hashlib.sha1(url.encode()).hexdigest()[:16]
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {url} ...")
        with urllib.request.urlopen(req) as r:
            path.write_bytes(r.read())
    data = path.read_bytes()
    return ("image/png" if data.startswith(b"\x89PNG") else "image/svg+xml"), data


def aspect(ctype: str, data: bytes) -> float:
    """Width / height of an icon."""
    if ctype == "image/png":
        w, h = struct.unpack(">II", data[16:24])
        return w / h
    text = data.decode("utf-8", "ignore")
    vb = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', text)
    if vb:
        return float(vb.group(1)) / float(vb.group(2))
    w, h = re.search(r'\swidth="([\d.]+)', text), re.search(r'\sheight="([\d.]+)', text)
    return float(w.group(1)) / float(h.group(1)) if w and h else 1.0


def band(tools: list[tuple], theme: str, direction: int) -> str:
    """A strip of tool icons drifting left (direction -1) or right (+1) forever."""
    images, x = [], 0.0
    for tool in tools:
        url = tool[2] if theme == "dark" and len(tool) > 2 else tool[1]
        ctype, data = tool_icon(url)
        w = min(max(ICON * aspect(ctype, data), ICON), ICON * 2)
        uri = f"data:{ctype};base64,{base64.b64encode(data).decode()}"
        images.append(f'<image x="{x:.1f}" y="{(BAND_H - ICON) / 2:g}" width="{w:.1f}" height="{ICON}" href="{uri}"/>')
        x += w + ICON_GAP
    strip = x  # one full cycle; copies follow end to end
    frm, to = (0, -strip) if direction < 0 else (-strip, 0)
    style = (
        f"@keyframes m{{from{{transform:translateX({frm:.1f}px)}}to{{transform:translateX({to:.1f}px)}}}}"
        f".m{{animation:m {strip / BAND_SPEED:.1f}s linear infinite}}"
        "@media (prefers-reduced-motion:reduce){.m{animation:none}}"
    )
    copies = "".join(f'<use href="#s" x="{strip * k:.1f}"/>' for k in range(math.ceil(BAND_MAX_W / strip) + 1))
    # Icons drift in and out through a soft fade at both ends.
    fade = (
        '<linearGradient id="fg"><stop offset="0" stop-color="#000"/><stop offset=".06" stop-color="#fff"/>'
        '<stop offset=".94" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
        '<mask id="f"><rect width="100%" height="100%" fill="url(#fg)"/></mask>'
    )
    label = escape("Tools I work with: " + ", ".join(t[0] for t in tools), {'"': "&quot;"})
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" role="img" '
        f'aria-label="{label}"><title>{label}</title><style>{style}</style>'
        f'<defs>{fade}<g id="s">{"".join(images)}</g></defs>'
        f'<g mask="url(#f)"><g class="m">{copies}</g></g></svg>\n'
    )


def write(name: str, text: str) -> None:
    xml.dom.minidom.parseString(text)  # must be well-formed XML
    path = ASSETS / name
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"{name:30} {len(text.encode()) / 1024:6.1f} KB")


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for theme, t in THEMES.items():
        write(f"heading-{theme}.svg", heading("Hello, I’m Michael!", t))
        write(f"cta-{theme}.svg", prompt("Pick an emoji, any emoji ;)", t))
        for slug, code, name, period, delay, lift, tilt in PROJECTS:
            write(f"float-{slug}-{theme}.svg", floater(code, name, period, delay, lift, tilt, t))
        half = (len(TOOLS) + 1) // 2
        write(f"tools-top-{theme}.svg", band(TOOLS[:half], theme, -1))
        write(f"tools-bottom-{theme}.svg", band(TOOLS[half:], theme, 1))


if __name__ == "__main__":
    main()
