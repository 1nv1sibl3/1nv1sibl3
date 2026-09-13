"""cardlib — shared helpers for the GitHub profile terminal cards.

Every card is a static SVG (SMIL animation, presentation attributes only —
no <style>, no <script>, no external fonts) so it renders inside GitHub's
camo-proxied <img> tags.

Set CARDS_QA=1 to emit the FINAL static frame (no <animate>, no opacity="0",
solid cursors, rain frozen) into .tmp/qa/ for visual review.
"""

import os
from pathlib import Path

# ── palette (monochrome: black / grey / white) ──────────────────────────
BG = "#0D1117"
PANEL = "#161B22"
EDGE = "#30363D"
DEEP = "#010409"
ACCENT = "#E6EDF3"
TEXT = "#C9D1D9"
DIM = "#8B949E"
TRACK = "#21262D"
SOFT = "#B0B8C1"
DOT_MAX = "#E6EDF3"  # traffic dot 1 (light)
DOT_MID = "#8B949E"  # traffic dot 2 (mid)
DOT_MIN = "#30363D"  # traffic dot 3 (dark)

FONT = "ui-monospace, 'Cascadia Code', Consolas, 'Courier New', monospace"


def grey_ramp(i, n):
    """Evenly interpolate a grey from #E6EDF3 (i=0) to #484F58 (i=n-1).
    Used so each language bar/dot/pie slice gets a distinct grey shade."""
    if n <= 1:
        return "#E6EDF3"
    t = i / (n - 1)
    r = round(0xE6 + (0x48 - 0xE6) * t)
    g = round(0xED + (0x4F - 0xED) * t)
    b = round(0xF3 + (0x58 - 0xF3) * t)
    return f"#{r:02X}{g:02X}{b:02X}"

LANG_COLORS = {
    "TypeScript": "#3178C6",
    "Python": "#3572A5",
    "JavaScript": "#F1E05A",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Java": "#B07219",
    "SCSS": "#C6538C",
    "Shell": "#89E051",
    "PowerShell": "#012456",
    "Dockerfile": "#384D54",
    "Batchfile": "#C1F12E",
    "C": "#555555",
    "C++": "#F34B7D",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Dart": "#00B4AB",
    "Vue": "#41B883",
    "Svelte": "#FF3E00",
    "MDX": "#F8E1A5",
    "TeX": "#3D6117",
    "Makefile": "#427819",
    "Jupyter Notebook": "#DA5B0B",
}

QA = os.environ.get("CARDS_QA") == "1"
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / (".tmp/qa" if QA else "assets")

# ── geometry ─────────────────────────────────────────────────────────────
TITLE_H = 36          # title bar occupies y 1..36 (35 px inside the stroke)
DOT_CY = 18
DOT_R = 4.5
CHAR_W = 0.58         # approx monospace advance (em) — used for cursor placement


def _n(v):
    """Format a number without float noise (0.30000000000000004 → 0.3)."""
    v = round(float(v), 3)
    s = f"{v:g}"
    return s


def esc(text):
    """Escape a text run for XML content."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_w(s, size):
    """Rough rendered width of a monospace run (used for cursor placement)."""
    return len(s) * size * CHAR_W


def txt(x, y, s, size=13, fill=TEXT, anchor=None, appear=None, weight=None):
    """A <text> run. `appear` = seconds offset for the fade-in idiom
    (ignored in QA mode, where the final frame is emitted)."""
    attrs = (f'x="{_n(x)}" y="{_n(y)}" font-family="{FONT}" '
             f'font-size="{_n(size)}" fill="{fill}"')
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    if weight:
        attrs += f' font-weight="{weight}"'
    body = esc(s)
    if appear is not None and not QA:
        attrs += ' opacity="0"'
        return (f'<text {attrs}>{body}'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{_n(appear)}s" dur="0.35s" fill="freeze"/></text>')
    return f'<text {attrs}>{body}</text>'


def blink(x, y, w=9, h=14, dur="1.1s"):
    """Blinking block cursor. Solid in QA mode."""
    head = (f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" '
            f'height="{_n(h)}" fill="{ACCENT}"')
    if QA:
        return head + "/>"
    return (head + f'><animate attributeName="opacity" values="1;1;0;0" '
            f'keyTimes="0;0.5;0.5;1" dur="{dur}" repeatCount="indefinite"/></rect>')


def window(w, h, title, content, aria, bare=False, scan=False):
    """Full SVG document with terminal window chrome.

    bare=True  → no title bar / dots (just the rounded rect)
    scan=True  → slow green scanline sweep (omitted in QA)
    """
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{_n(w)}" '
             f'height="{_n(h)}" viewBox="0 0 {_n(w)} {_n(h)}" role="img" '
             f'aria-label="{esc(aria)}">')
    p.append(f'<rect x="0.5" y="0.5" width="{_n(w - 1)}" height="{_n(h - 1)}" '
             f'rx="10" fill="{BG}" stroke="{EDGE}" stroke-width="1"/>')
    if not bare:
        p.append(f'<path d="M 1 {TITLE_H} L 1 10 A 9 9 0 0 1 10 1 '
                 f'L {_n(w - 10)} 1 A 9 9 0 0 1 {_n(w - 1)} 10 '
                 f'L {_n(w - 1)} {TITLE_H} Z" fill="{PANEL}"/>')
        p.append(f'<circle cx="20" cy="{DOT_CY}" r="{DOT_R}" fill="{DOT_MAX}"/>'
                 f'<circle cx="36" cy="{DOT_CY}" r="{DOT_R}" fill="{DOT_MID}"/>'
                 f'<circle cx="52" cy="{DOT_CY}" r="{DOT_R}" fill="{DOT_MIN}"/>')
        p.append(txt(w / 2, 22, title, size=11, fill=DIM, anchor="middle"))
    p.append(content)
    if scan and not QA:
        p.append(f'<clipPath id="winclip"><rect x="0.5" y="0.5" '
                 f'width="{_n(w - 1)}" height="{_n(h - 1)}" rx="10"/></clipPath>')
        p.append(f'<linearGradient id="scang" x1="0" y1="0" x2="0" y2="1">'
                 f'<stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>'
                 f'<stop offset="0.5" stop-color="{ACCENT}" stop-opacity="0.04"/>'
                 f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>'
                 f'</linearGradient>')
        p.append(f'<g clip-path="url(#winclip)">'
                 f'<rect x="0" y="0" width="{_n(w)}" height="52" fill="url(#scang)">'
                 f'<animateTransform attributeName="transform" type="translate" '
                 f'from="0 -52" to="0 {_n(h)}" dur="7s" repeatCount="indefinite"/>'
                 f'</rect></g>')
    p.append("</svg>")
    return "".join(p)


def strip(cmd, note):
    """One-line command strip: 760x64, "$ {cmd}" + cursor + right-aligned note."""
    prompt = f"$ {cmd}"
    cur_x = round(24 + text_w(prompt, 13) + 5)
    content = (
        txt(24, 52, prompt, size=13, fill=ACCENT, appear=0.1)
        + blink(cur_x, 41)
        + txt(736, 52, note, size=11, fill=DIM, anchor="end", appear=0.45)
    )
    return window(760, 64, "inv1s1bl3@github:~", content,
                  aria=f"terminal: {prompt}")
