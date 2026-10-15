#!/usr/bin/env python3
"""Render assets/hero.svg, the profile header: name and tagline over Matrix
digital rain, above a terminal that types lines from the film. Pure SVG + CSS animation, so it plays inside a README
<img> with no JavaScript and no third-party host.

Static asset: rerun by hand after editing NAME, TAGLINE or LINES. Seeded, so output is stable.
"""
import random
from pathlib import Path
from xml.sax.saxutils import escape

W, H = 900, 250
# Same Tokyo Night palette as the stat cards and banner, Red Bull red cursor.
BG, PANEL = "#1a1b27", "#16161e"
RAIN_DIM, RAIN, RAIN_TIP = "#4d6bc4", "#70a5fd", "#c0caf5"
PROMPT_C, TYPED, CURSOR = "#a9b1d6", "#38bdae", "#DB0A40"
MONO = "Consolas, 'Courier New', monospace"
SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"

NAME = "Luc de Marillac St Julien"
TAGLINE = "Computer Engineering student at The IIE  ·  .NET  ·  Android  ·  Cloud"

LINES = ["Wake up, Luc...", "The Matrix has you...", "Follow the white rabbit.", "Knock, knock, Luc."]
PROMPT = "luc@zion:~$ "
CYCLE = 20  # seconds for the whole script of lines
CW = 13     # forced width per typed character (textLength), keeps cursor in sync

# Half-width katakana + digits, like the film. Needs a CJK-capable system font;
# every mainstream desktop OS ships one.
GLYPHS = [chr(c) for c in range(0xFF66, 0xFF9E)] + list("0123456789Z:.=*+-<>")

rng = random.Random(1999)


def rain():
    cols, chars, step = 60, 18, 16
    out = []
    for i in range(cols):
        x = 8 + i * 15
        dur = rng.uniform(3.5, 8)
        delay = -rng.uniform(0, dur)
        spans = "".join(
            f'<tspan x="{x}" dy="{step}">{escape(rng.choice(GLYPHS))}</tspan>' for _ in range(chars)
        )
        out.append(
            f'<text class="col" fill="url(#fade)" style="animation-duration:{dur:.2f}s;'
            f'animation-delay:{delay:.2f}s">{spans}</text>'
        )
    return "\n".join(out)


def pct(v):
    return f"{v:.2f}%"


def typing():
    slot = 100 / len(LINES)
    px, py, pw, ph = 48, 154, 804, 70
    tx = px + 22
    x0 = tx + len(PROMPT) * CW
    base = py + 44
    css, body = [], []

    for i, line in enumerate(LINES):
        n = len(line)
        width = n * CW
        s, typed, end = i * slot, i * slot + slot * 0.35, i * slot + slot * 0.92

        # Whole line visible only during its slot.
        show = [f"0% {{opacity:{1 if s == 0 else 0}}}"]
        if s > 0:
            show.append(f"{pct(s - 0.01)} {{opacity:0}}")
        show += [f"{pct(s)} {{opacity:1}}", f"{pct(end)} {{opacity:1}}", f"{pct(end + 0.01)}, 100% {{opacity:0}}"]
        css.append(f"@keyframes show{i} {{ {' '.join(show)} }}")

        # A panel-coloured cover slides right one character at a time,
        # revealing the text; the cursor rides on its left edge.
        css.append(
            f"@keyframes type{i} {{ 0%, {pct(s)} {{transform:translateX(0);"
            f"animation-timing-function:steps({n},end)}} "
            f"{pct(typed)}, 100% {{transform:translateX({width}px)}} }}"
        )
        body.append(
            f'<g style="animation:show{i} {CYCLE}s linear infinite">'
            f'<text x="{x0}" y="{base}" class="typed" textLength="{width}" '
            f'lengthAdjust="spacingAndGlyphs">{escape(line)}</text>'
            f'<g style="animation:type{i} {CYCLE}s linear infinite">'
            f'<rect x="{x0}" y="{py + 2}" width="{pw}" height="{ph - 4}" fill="{PANEL}"/>'
            f'<rect class="cursor" x="{x0 + 1}" y="{base - 19}" width="{CW - 2}" height="24" fill="{CURSOR}"/>'
            f"</g></g>"
        )

    panel = (
        f'<clipPath id="panel"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="6"/></clipPath>'
        f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="6" fill="{PANEL}" '
        f'stroke="{RAIN}" stroke-opacity=".45"/>'
        f'<text x="{tx}" y="{base}" class="prompt" textLength="{len(PROMPT) * CW - CW}" '
        f'lengthAdjust="spacingAndGlyphs">{escape(PROMPT.strip())}</text>'
        f'<g clip-path="url(#panel)" filter="url(#glow)">{"".join(body)}</g>'
    )
    return "\n".join(css), panel


def main():
    css, panel = typing()
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="mt">
<title id="mt">{escape(NAME)}: {escape(TAGLINE.replace(chr(183), "-"))}. A terminal over Matrix rain types: {escape(' / '.join(LINES))}</title>
<defs>
  <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{RAIN_DIM}" stop-opacity="0"/>
    <stop offset="60%" stop-color="{RAIN_DIM}"/>
    <stop offset="92%" stop-color="{RAIN}"/>
    <stop offset="100%" stop-color="{RAIN_TIP}"/>
  </linearGradient>
  <filter id="glow" x="-10%" y="-50%" width="120%" height="200%" color-interpolation-filters="sRGB">
    <feGaussianBlur stdDeviation="2.2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <linearGradient id="shade" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{BG}" stop-opacity=".9"/>
    <stop offset="45%" stop-color="{BG}" stop-opacity=".55"/>
    <stop offset="100%" stop-color="{BG}" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="10"/></clipPath>
</defs>
<style>
.col {{ font: 14px {MONO}; animation: fall linear infinite; }}
@keyframes fall {{ from {{ transform: translateY(-300px); }} to {{ transform: translateY({H + 20}px); }} }}
.name {{ font: 700 42px {SANS}; fill: #ffffff; }}
.tag {{ font: 400 17px {SANS}; fill: {PROMPT_C}; }}
.prompt {{ font: 22px {MONO}; fill: {PROMPT_C}; }}
.typed {{ font: 700 22px {MONO}; fill: {TYPED}; }}
.cursor {{ animation: blink 1s steps(1) infinite; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
{css}
@media (prefers-reduced-motion: reduce) {{ .col, .cursor {{ animation: none !important; }} }}
</style>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="{BG}"/>
{rain()}
<rect width="{W}" height="{H}" fill="url(#shade)"/>
<rect width="5" height="{H}" fill="{CURSOR}"/>
<text x="48" y="76" class="name">{escape(NAME)}</text>
<text x="50" y="112" class="tag">{escape(TAGLINE)}</text>
{panel}
</g>
</svg>
"""
    out = Path(__file__).resolve().parent.parent / "assets" / "hero.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
