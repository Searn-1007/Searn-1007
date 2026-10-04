"""
Build the animated SVG panels used by the profile README (assets/*.svg).

Fonts (Chakra Petch, JetBrains Mono; SIL OFL) and logos (Simple Icons, CC0) are
downloaded into scripts/.cache on first run, subset to the characters each panel
uses and embedded as base64 WOFF2, so the panels render the same everywhere.

    pip install fonttools brotli
    python scripts/build_assets.py
"""

import base64
import io
import math
import os
import re
import urllib.request

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "scripts", ".cache")
ASSETS = os.path.join(ROOT, "assets")

FONT_URLS = {
    "head": "https://github.com/google/fonts/raw/main/ofl/chakrapetch/ChakraPetch-Bold.ttf",
    "sub": "https://github.com/google/fonts/raw/main/ofl/chakrapetch/ChakraPetch-Medium.ttf",
    "mono": "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
}
ICON_URL = "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{}.svg"

# ---------------------------------------------------------------- palette
BG0, BG1 = "#060a13", "#0c1526"
PANEL = "#0d1729"
LINE = "#1c2b47"
CYAN, BLUE, VIOLET = "#22d3ee", "#3b82f6", "#a78bfa"
TEXT, MUTED = "#e6edf7", "#8a9bb8"
W = 1000


# ---------------------------------------------------------------- helpers
def fetch(url, name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        with urllib.request.urlopen(url) as r, open(path, "wb") as f:
            f.write(r.read())
    return path


def font_face(family, key, text, weight=None):
    """@font-face rule with the font subset to ``text`` and embedded as WOFF2."""
    path = fetch(FONT_URLS[key], key + ".ttf")
    font = TTFont(path)
    if "fvar" in font:
        font = instancer.instantiateVariableFont(font, {"wght": weight or 500})
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    sub = subset.Subsetter(opts)
    sub.populate(text=text + " ")
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'{family}';"
            f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")


def texts(svg_body):
    """All characters that appear as text content in the SVG body."""
    content = "".join(re.findall(r">([^<>]+)<", svg_body))
    return content.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def icon_path(slug):
    svg = open(fetch(ICON_URL.format(slug), slug + ".svg"), encoding="utf-8").read()
    return re.search(r' d="([^"]+)"', svg).group(1)


def svg(height, body, css="", fonts=("head", "sub", "mono")):
    chars = texts(body)
    faces = []
    if "head" in fonts:
        faces.append(font_face("Head", "head", chars))
    if "sub" in fonts:
        faces.append(font_face("Sub", "sub", chars))
    if "mono" in fonts:
        faces.append(font_face("Mono", "mono", chars, 500))
    style = "\n".join(faces) + """
.head{font-family:'Head',sans-serif;font-weight:700}
.sub{font-family:'Sub',sans-serif;font-weight:500}
.mono{font-family:'Mono',monospace}
""" + css
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
            f'viewBox="0 0 {W} {height}">\n<style>{style}</style>\n{body}\n</svg>\n')


def frame(height, inner, radius=18):
    """Dark rounded panel with a subtle border and grid, used by every section."""
    return f"""
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/>
  </linearGradient>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{CYAN}"/><stop offset=".55" stop-color="{BLUE}"/><stop offset="1" stop-color="{VIOLET}"/>
  </linearGradient>
  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
    <path d="M32 0H0V32" fill="none" stroke="{LINE}" stroke-width="1"/>
  </pattern>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="clip"><rect x="1" y="1" width="{W - 2}" height="{height - 2}" rx="{radius}"/></clipPath>
</defs>
<g clip-path="url(#clip)">
  <rect width="{W}" height="{height}" fill="url(#bg)"/>
  <rect width="{W}" height="{height}" fill="url(#grid)" opacity=".35"/>
  {inner}
</g>
<rect x="1" y="1" width="{W - 2}" height="{height - 2}" rx="{radius}" fill="none" stroke="{LINE}" stroke-width="2"/>
"""


def section_title(x, y, label, number):
    return f"""
<text x="{x}" y="{y}" class="mono" font-size="14" fill="{CYAN}" letter-spacing="2">{number}</text>
<text x="{x + 40}" y="{y}" class="head" font-size="22" fill="{TEXT}" letter-spacing="3">{label}</text>
<rect x="{x + 40}" y="{y + 12}" width="70" height="3" rx="1.5" fill="url(#accent)"/>
"""


# ---------------------------------------------------------------- 1. hero
def hero():
    h = 360
    # robot arm (shoulder at bx,by), drawn in its rest pose and animated with CSS
    bx, by = 800, 300
    l1, l2 = 120, 100
    a1, a2 = math.radians(-62), math.radians(48)
    ex, ey = bx + l1 * math.cos(a1), by + l1 * math.sin(a1)
    wx, wy = ex + l2 * math.cos(a1 + a2), ey + l2 * math.sin(a1 + a2)
    inner = f"""
<radialGradient id="halo" cx="0.8" cy="0.55" r="0.55">
  <stop offset="0" stop-color="{BLUE}" stop-opacity=".35"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#ffffff"/><stop offset=".45" stop-color="{CYAN}"/><stop offset="1" stop-color="{VIOLET}"/>
</linearGradient>
<rect width="{W}" height="{h}" fill="url(#halo)"/>
<rect class="scan" x="0" y="0" width="{W}" height="2" fill="{CYAN}" opacity=".25"/>

<text x="60" y="92" class="mono" font-size="16" fill="{CYAN}">&gt; hello, world<tspan class="cursor">_</tspan></text>
<text x="56" y="168" class="head" font-size="64" fill="url(#name)" filter="url(#glow)">Nguyễn Hà Sơn</text>
<text x="60" y="214" class="sub" font-size="20" fill="{TEXT}" letter-spacing="5">FULL-STACK ROBOTICS</text>
<text x="60" y="250" class="mono" font-size="15" fill="{MUTED}">Mechatronics · Talented Engineering Program · HUST</text>

<g class="mono" font-size="13">
  {''.join(f'<g transform="translate({60 + i * 128},286)"><rect width="118" height="30" rx="15" fill="{PANEL}" stroke="{LINE}"/><text x="59" y="20" text-anchor="middle" fill="{TEXT}">{t}</text></g>' for i, t in enumerate(["Design", "Simulate", "Build", "Control"]))}
</g>

<g stroke-linecap="round" fill="none">
  <ellipse cx="{bx}" cy="{by + 28}" rx="70" ry="10" fill="{CYAN}" opacity=".12" stroke="none"/>
  <rect x="{bx - 42}" y="{by + 8}" width="84" height="20" rx="6" fill="{PANEL}" stroke="{LINE}" stroke-width="2"/>
  <g class="j1">
    <line x1="{bx}" y1="{by}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="url(#accent)" stroke-width="14"/>
    <g class="j2">
      <line x1="{ex:.1f}" y1="{ey:.1f}" x2="{wx:.1f}" y2="{wy:.1f}" stroke="{BLUE}" stroke-width="11"/>
      <g class="j3">
        <path d="M{wx:.1f} {wy:.1f} l14 10 M{wx:.1f} {wy:.1f} l2 17" stroke="{VIOLET}" stroke-width="6"/>
        <circle class="spark" cx="{wx + 10:.1f}" cy="{wy + 20:.1f}" r="5" fill="{CYAN}" stroke="none" filter="url(#glow)"/>
      </g>
      <circle cx="{wx:.1f}" cy="{wy:.1f}" r="8" fill="{BG0}" stroke="{VIOLET}" stroke-width="3"/>
    </g>
    <circle cx="{ex:.1f}" cy="{ey:.1f}" r="10" fill="{BG0}" stroke="{CYAN}" stroke-width="3"/>
  </g>
  <circle cx="{bx}" cy="{by}" r="13" fill="{BG0}" stroke="{CYAN}" stroke-width="4" filter="url(#glow)"/>
</g>
"""
    css = f"""
.cursor{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.scan{{animation:scan 6s linear infinite}}
@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({h}px)}}}}
.j1{{transform-origin:{bx}px {by}px;animation:j1 7s ease-in-out infinite}}
.j2{{transform-origin:{ex:.1f}px {ey:.1f}px;animation:j2 7s ease-in-out infinite}}
.j3{{transform-origin:{wx:.1f}px {wy:.1f}px;animation:j3 7s ease-in-out infinite}}
@keyframes j1{{0%,100%{{transform:rotate(0)}}35%{{transform:rotate(-14deg)}}70%{{transform:rotate(10deg)}}}}
@keyframes j2{{0%,100%{{transform:rotate(0)}}35%{{transform:rotate(22deg)}}70%{{transform:rotate(-18deg)}}}}
@keyframes j3{{0%,100%{{transform:rotate(0)}}35%{{transform:rotate(-20deg)}}70%{{transform:rotate(16deg)}}}}
.spark{{animation:spark .9s ease-in-out infinite}}
@keyframes spark{{0%,100%{{opacity:.25}}50%{{opacity:1}}}}
"""
    return svg(h, frame(h, inner), css)


# ---------------------------------------------------------------- 2. about
def about():
    h = 300
    lines = [
        ("$", "whoami"),
        ("›", "Nguyễn Hà Sơn — Mechatronics student, Talented Engineering Program @ HUST (2023–)"),
        ("$", "cat focus.txt"),
        ("›", "Robotics, end to end: from the first sketch to a robot that actually moves"),
        ("$", "echo $STATUS"),
        ("›", "Building robots, one joint at a time"),
    ]
    rows = []
    for i, (p, t) in enumerate(lines):
        y = 112 + i * 28
        color = CYAN if p == "$" else TEXT
        pcolor = VIOLET if p == "$" else MUTED
        cursor = '<tspan class="cursor" fill="#22d3ee"> ▌</tspan>' if i == len(lines) - 1 else ""
        rows.append(f'<g>'
                    f'<text x="60" y="{y}" class="mono" font-size="16" fill="{pcolor}">{p}</text>'
                    f'<text x="86" y="{y}" class="mono" font-size="16" fill="{color}">{t}{cursor}</text></g>')
    inner = f"""
<rect x="0" y="0" width="{W}" height="46" fill="{PANEL}"/>
<line x1="0" y1="46" x2="{W}" y2="46" stroke="{LINE}" stroke-width="2"/>
<circle cx="30" cy="23" r="7" fill="#ff5f57"/><circle cx="54" cy="23" r="7" fill="#febc2e"/><circle cx="78" cy="23" r="7" fill="#28c840"/>
<text x="{W / 2}" y="29" text-anchor="middle" class="mono" font-size="14" fill="{MUTED}">son@hust: ~/about-me</text>
{''.join(rows)}
"""
    css = """
.cursor{animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
"""
    return svg(h, frame(h, inner), css, fonts=("mono",))


# ---------------------------------------------------------------- 3. pipeline
STAGE_ICONS = {
    # simple 32x32 line icons, centred on (0,0)
    "cad": "M-12 -6 L0 -13 L12 -6 L12 8 L0 15 L-12 8 Z M-12 -6 L0 1 L12 -6 M0 1 L0 15",
    "sim": "M-14 10 L14 10 M-14 10 L-14 -12 M-12 4 C-6 -14 0 14 6 -4 S 12 -8 14 -10",
    "build": "M-4 -14 L4 -14 L5 -9 L9 -7 L13 -10 L17 -4 L13 0 L13 3 L17 7 L13 13 L9 10 L5 12 L4 17 L-4 17 L-5 12 L-9 10 L-13 13 L-17 7 L-13 3 L-13 0 L-17 -4 L-13 -10 L-9 -7 L-5 -9 Z M0 -4 A 5.5 5.5 0 1 0 0.01 -4",
    "wire": "M-15 -6 L-6 -6 M-15 6 L-6 6 M-6 -11 L2 -11 Q 8 -11 8 0 Q 8 11 2 11 L-6 11 Z M8 0 L12 0 Q 16 0 16 6 L16 14",
    "hw": "M-10 -10 H10 V10 H-10 Z M-4 -4 H4 V4 H-4 Z M-6 -10 V-15 M0 -10 V-15 M6 -10 V-15 M-6 10 V15 M0 10 V15 M6 10 V15 M-10 -6 H-15 M-10 0 H-15 M-10 6 H-15 M10 -6 H15 M10 0 H15 M10 6 H15",
    "code": "M-6 -10 L-15 0 L-6 10 M6 -10 L15 0 L6 10 M3 -14 L-3 14",
}


def pipeline():
    h = 300
    stages = [("cad", "CAD Design", "SolidWorks"), ("sim", "Simulation", "Model &amp; test"),
              ("build", "Assembly", "Mechanical"), ("wire", "Wiring", "Electrical"),
              ("hw", "Hardware", "Bring-up"), ("code", "Software", "Control &amp; ROS 2")]
    x0, dx, cy = 105, 158, 165
    nodes = []
    for i, (ic, title, sub) in enumerate(stages):
        x = x0 + i * dx
        nodes.append(f"""
<g class="node" style="animation-delay:{i * 0.5:.1f}s">
  <circle cx="{x}" cy="{cy}" r="44" fill="{PANEL}" stroke="{LINE}" stroke-width="2"/>
  <circle class="ring" cx="{x}" cy="{cy}" r="44" fill="none" stroke="url(#accent)" stroke-width="3" style="animation-delay:{i * 0.5:.1f}s"/>
  <path d="{STAGE_ICONS[ic]}" transform="translate({x},{cy})" fill="none" stroke="{CYAN}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="{x}" y="{cy + 76}" text-anchor="middle" class="head" font-size="17" fill="{TEXT}">{title}</text>
  <text x="{x}" y="{cy + 98}" text-anchor="middle" class="mono" font-size="12" fill="{MUTED}">{sub}</text>
  <text x="{x}" y="{cy - 58}" text-anchor="middle" class="mono" font-size="12" fill="{VIOLET}">0{i + 1}</text>
</g>""")
    x_end = x0 + (len(stages) - 1) * dx
    inner = f"""
{section_title(50, 62, "FROM IDEA TO WORKING ROBOT", "//")}
<line x1="{x0}" y1="{cy}" x2="{x_end}" y2="{cy}" stroke="{LINE}" stroke-width="3"/>
<line class="flow" x1="{x0}" y1="{cy}" x2="{x_end}" y2="{cy}" stroke="url(#accent)" stroke-width="3" stroke-dasharray="6 14"/>
{''.join(nodes)}
<circle r="6" fill="{CYAN}" filter="url(#glow)">
  <animateMotion dur="4s" repeatCount="indefinite" path="M{x0} {cy} L{x_end} {cy}"/>
</circle>
"""
    css = f"""
.flow{{animation:flow 1.2s linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:-40}}}}
.ring{{opacity:0;animation:ring 3s ease-in-out infinite}}
@keyframes ring{{0%,100%{{opacity:0}}15%,35%{{opacity:1}}}}
"""
    return svg(h, frame(h, inner), css)


# ---------------------------------------------------------------- 4. toolbox
def toolbox():
    tools = [("dassaultsystemes", "SolidWorks", "#E2231A"), ("ros", "ROS 2", "#22D3EE"),
             (None, "Gazebo", "#F58113"), ("mathworks", "MATLAB", "#E16737"),
             ("python", "Python", "#FFD43B"), ("cplusplus", "C++", "#659AD2"),
             ("ubuntu", "Ubuntu", "#E95420"), ("git", "Git", "#F05032"), ("docker", "Docker", "#2496ED")]
    h = 250
    tw, gap = 92, 12
    x0 = (W - (len(tools) * tw + (len(tools) - 1) * gap)) / 2
    tiles = []
    for i, (slug, name, color) in enumerate(tools):
        x = x0 + i * (tw + gap)
        if slug:
            logo = f'<path d="{icon_path(slug)}" transform="translate({x + tw / 2 - 18},{108}) scale(1.5)" fill="{TEXT}"/>'
        else:  # Gazebo: no Simple Icons logo, draw a stylised one
            cx, cy = x + tw / 2, 126
            logo = (f'<g transform="translate({cx},{cy})" fill="none" stroke="{TEXT}" stroke-width="2.6" stroke-linejoin="round">'
                    f'<path d="M0 -17 L15 -8 L15 9 L0 18 L-15 9 L-15 -8 Z"/><path d="M-15 -8 L0 1 L15 -8 M0 1 V18"/></g>')
        tiles.append(f"""
<g>
  <rect x="{x}" y="88" width="{tw}" height="120" rx="14" fill="{PANEL}" stroke="{LINE}" stroke-width="2"/>
  <rect x="{x + 20}" y="200" width="{tw - 40}" height="4" rx="2" fill="{color}" opacity=".55"/>
  <rect class="bar" x="{x + 20}" y="200" width="{tw - 40}" height="4" rx="2" fill="{color}" filter="url(#glow)" style="animation-delay:{i * 0.35:.2f}s"/>
  {logo}
  <text x="{x + tw / 2}" y="184" text-anchor="middle" class="mono" font-size="12.5" fill="{TEXT}">{name}</text>
</g>""")
    inner = f"""
{section_title(50, 62, "TOOLBOX", "//")}
{''.join(tiles)}
"""
    css = """
.bar{opacity:0;animation:bar 3.15s ease-in-out infinite}
@keyframes bar{0%,100%{opacity:0}12%,30%{opacity:1}}
"""
    return svg(h, frame(h, inner), css)


# ---------------------------------------------------------------- 5. project card
def project():
    h = 230
    tags = ["SolidWorks", "Python", "MATLAB/Simulink", "ROS 2", "Gazebo"]
    chips, x = [], 60
    for t in tags:
        wdt = 22 + 8.2 * len(t)
        chips.append(f'<g transform="translate({x:.0f},160)"><rect width="{wdt:.0f}" height="30" rx="15" fill="{PANEL}" stroke="{LINE}"/>'
                     f'<text x="{wdt / 2:.0f}" y="20" text-anchor="middle" class="mono" font-size="12.5" fill="{CYAN}">{t}</text></g>')
        x += wdt + 10
    inner = f"""
<rect x="0" y="0" width="6" height="{h}" fill="url(#accent)"/>
<text x="60" y="58" class="mono" font-size="13" fill="{VIOLET}" letter-spacing="2">FEATURED PROJECT</text>
<text x="60" y="100" class="head" font-size="34" fill="{TEXT}">robotic-arm-ros2</text>
<text x="60" y="134" class="sub" font-size="17" fill="{MUTED}">4-DOF welding robot arm — designed, simulated and controlled end to end</text>
{''.join(chips)}
<g transform="translate(860,115)" fill="none" stroke-linecap="round">
  <line x1="0" y1="-55" x2="0" y2="55" stroke="{LINE}" stroke-width="10"/>
  <line class="seam" x1="0" y1="-55" x2="0" y2="55" stroke="url(#accent)" stroke-width="10"/>
  <circle class="torch" cx="0" cy="-55" r="9" fill="{CYAN}" stroke="none" filter="url(#glow)"/>
</g>
<text x="925" y="205" text-anchor="end" class="mono" font-size="13" fill="{MUTED}">view repo →</text>
"""
    css = """
.seam{stroke-dasharray:110;stroke-dashoffset:110;animation:seam 4s ease-in-out infinite}
@keyframes seam{0%{stroke-dashoffset:110}70%,100%{stroke-dashoffset:0}}
.torch{animation:torch 4s ease-in-out infinite}
@keyframes torch{0%{transform:translateY(0)}70%,100%{transform:translateY(110px)}}
"""
    return svg(h, frame(h, inner), css)


# ---------------------------------------------------------------- 6. contact
def contact():
    h = 170
    inner = f"""
<text x="{W / 2}" y="70" text-anchor="middle" class="head" font-size="28" fill="{TEXT}" letter-spacing="3">LET'S BUILD SOMETHING THAT MOVES</text>
<g transform="translate({W / 2 - 170},96)">
  <rect width="340" height="46" rx="23" fill="{PANEL}" stroke="url(#accent)" stroke-width="2"/>
  <path d="M24 15 H50 V33 H24 Z M24 15 L37 25 L50 15" fill="none" stroke="{CYAN}" stroke-width="2.2" stroke-linejoin="round"/>
  <text x="194" y="29" text-anchor="middle" class="mono" font-size="16" fill="{TEXT}">hasonhd123@gmail.com</text>
</g>
"""
    return svg(h, frame(h, inner))


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for name, fn in [("hero", hero), ("about", about), ("pipeline", pipeline),
                     ("toolbox", toolbox), ("project", project), ("contact", contact)]:
        path = os.path.join(ASSETS, name + ".svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(fn())
        print(f"{path}  {os.path.getsize(path) // 1024} KB")


if __name__ == "__main__":
    main()
