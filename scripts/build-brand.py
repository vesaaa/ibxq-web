#!/usr/bin/env python3
"""Generate every logo file under brand/ (SVG sources, PNG exports, app icons, favicon.ico)
and refresh the site's own favicon files.

    pip install fonttools brotli pillow
    python3 scripts/build-brand.py

Text is converted to outlines from the fonts in fonts/, so the SVGs need no fonts installed.
PNGs are rendered by scripts/render-brand.js and the overview sheet (brand/preview.png) by
scripts/brand-preview.js, both with Node + Playwright/Chromium.
"""
import json, pathlib, shutil, subprocess
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "brand"

HEART = "M0 -10C-8 -30 -40 -22 -40 2C-40 24 -14 36 0 52C14 36 40 24 40 2C40 -22 8 -30 0 -10Z"
RING = 'transform="rotate(-18 60 62)"'
BACK = 'd="M6 62A54 19 0 0 1 114 62"'      # far half of the orbit (passes behind the heart)
FRONT = 'd="M6 62A54 19 0 0 0 114 62"'     # near half (passes in front)
PLANET = (111.4, 45.3)

# colours
ROSE, VIOLET, BLUE, TEAL = "#F07388", "#9C8EF2", "#6FA2F0", "#3FC4AF"
INK_ON_DARK, INK_ON_LIGHT, ROSE_ON_LIGHT = "#ECEEF6", "#151A2C", "#D94A6C"


def mark(style, small=False, uid="m"):
    """SVG body of the mark in a 120x120 box. style: original | flat | white | black.
    small=True is the simplified mark (one solid heart) meant for 32 px and below."""
    outer_t = 'transform="translate(60 49) scale(%s)"' % (".84" if small else ".82")
    inner_t = 'transform="translate(60 54) scale(.42)"'
    rw, pr = (6, 8) if small else (4, 6.5)          # ring stroke, planet radius
    ow = 7                                          # outer heart stroke (path units)
    if small:
        heart = lambda fill: '<path d="%s" %s fill="%s"/>' % (HEART, outer_t, fill)
        heart_mask = heart("#fff")
    else:
        heart = lambda fill: ('<path d="%s" %s fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (HEART, outer_t, fill, ow))
        heart_mask = heart("#fff")
    inner = lambda fill: "" if small else '<path d="%s" %s fill="%s"/>' % (HEART, inner_t, fill)
    planet = lambda fill: '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (PLANET[0], PLANET[1], pr, fill)

    if style == "original":
        defs = ('<linearGradient id="{u}h" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FF9CAB"/><stop offset=".45" stop-color="#F07388"/><stop offset="1" stop-color="#9C8EF2"/></linearGradient>'
                '<linearGradient id="{u}s" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFB3BE"/><stop offset="1" stop-color="#E0577A"/></linearGradient>'
                '<linearGradient id="{u}r" x1="0" x2="1"><stop offset="0" stop-color="#9C8EF2"/><stop offset="1" stop-color="#6FA2F0"/></linearGradient>'
                '<mask id="{u}m" maskUnits="userSpaceOnUse" x="0" y="0" width="120" height="120">{hm}</mask>').format(u=uid, hm=heart_mask)
        ring = 'stroke="url(#%sr)" stroke-width="%s" fill="none" stroke-linecap="round"' % (uid, rw)
        body = ('<path {b} {t} {ring}/>{heart}{inner}'
                '<g mask="url(#{u}m)"><path {f} {t} stroke="#7A3572" stroke-width="{sw}" fill="none"/></g>'
                '<path {f} {t} {ring}/>{planet}').format(
            b=BACK, f=FRONT, t=RING, ring=ring, u=uid, sw=rw + 6,
            heart=heart("url(#%sh)" % uid), inner=inner("url(#%ss)" % uid), planet=planet(TEAL))
        return "<defs>" + defs + "</defs>" + body

    # flat and one-colour styles: no gradients; where the orbit and the heart cross, the one behind is cut with a gap
    if style == "flat":
        c_heart, c_inner, c_ring, c_planet = ROSE, ROSE, VIOLET, TEAL
    else:
        c_heart = c_inner = c_ring = c_planet = "#fff" if style == "white" else "#000"
    gap = 4 if small else 3
    s_outer = 0.84 if small else 0.82
    if small:
        behind_heart = '<path d="%s" %s fill="#000" stroke="#000" stroke-width="%.1f" stroke-linejoin="round"/>' % (HEART, outer_t, 2 * gap / s_outer)
    else:
        behind_heart = ('<path d="%s" %s fill="none" stroke="#000" stroke-width="%.1f" stroke-linejoin="round"/>' % (HEART, outer_t, ow + 2 * gap / s_outer)
                        + '<path d="%s" %s fill="#000" stroke="#000" stroke-width="%.1f" stroke-linejoin="round"/>' % (HEART, inner_t, 2 * gap / 0.42))
    box = 'maskUnits="userSpaceOnUse" x="0" y="0" width="120" height="120"'
    defs = ('<mask id="{u}b" {box}><rect width="120" height="120" fill="#fff"/>{bh}</mask>'
            '<mask id="{u}f" {box}><rect width="120" height="120" fill="#fff"/><path {f} {t} stroke="#000" stroke-width="{sw}" fill="none" stroke-linecap="round"/></mask>').format(
        u=uid, box=box, bh=behind_heart, f=FRONT, t=RING, sw=rw + 2 * gap)
    ring = 'stroke="%s" stroke-width="%s" fill="none" stroke-linecap="round"' % (c_ring, rw)
    body = ('<g mask="url(#{u}b)"><path {b} {t} {ring}/></g><g mask="url(#{u}f)">{heart}</g>{inner}<path {f} {t} {ring}/>{planet}').format(
        u=uid, b=BACK, f=FRONT, t=RING, ring=ring, heart=heart(c_heart), inner=inner(c_inner), planet=planet(c_planet))
    return "<defs>" + defs + "</defs>" + body


def outline(font_file, text, size, tracking, x0):
    """Outline `text`, left edge at x0, vertically centred on y=60. Returns ([path d per glyph], right edge)."""
    font = TTFont(font_file)
    gs, cmap, s = font.getGlyphSet(), font.getBestCmap(), size / font["head"].unitsPerEm
    fmt = lambda v: ("%.2f" % v).rstrip("0").rstrip(".")
    def run(baseline):
        x, paths, bp = x0, [], BoundsPen(gs)
        for ch in text:
            g = gs[cmap[ord(ch)]]
            sp = SVGPathPen(gs, ntos=fmt)
            g.draw(TransformPen(sp, (s, 0, 0, -s, x, baseline)))
            g.draw(TransformPen(bp, (s, 0, 0, -s, x, baseline)))
            paths.append(sp.getCommands())
            x += g.width * s + tracking * size
        return paths, bp.bounds
    _, b = run(0)
    paths, b = run(60 - (b[1] + b[3]) / 2)
    return paths, b[2]


def svg(viewbox, body, title):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s" role="img" aria-label="%s">%s</svg>\n' % (viewbox, title, body))


def lockup(style, ground, word):
    """Mark + wordmark. word: 'zh' (爱伴星球) or 'en' (IBXQ). ground: 'dark' | 'light' | None (one-colour styles)."""
    if word == "zh":
        paths, right = outline(ROOT / "fonts/noto-serif-sc-900.woff2", "爱伴星球", 50, 0.06, 130)
    else:
        paths, right = outline(ROOT / "fonts/noto-serif-sc-900.woff2", "IBXQ", 52, 0.08, 131)
    if style in ("white", "black"):
        ink = accent = "#fff" if style == "white" else "#000"
    else:
        ink = INK_ON_DARK if ground == "dark" else INK_ON_LIGHT
        accent = ROSE if ground == "dark" else ROSE_ON_LIGHT
    text = "".join('<path d="%s" fill="%s"/>' % (d, accent if (word == "zh" and i == 0) else ink) for i, d in enumerate(paths))
    return svg("0 20 %.1f 80" % (right + 6), mark(style) + text, "爱伴星球 IBXQ")


def app_icon(rounded):
    bg = ('<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1A2145"/><stop offset="1" stop-color="#060914"/></linearGradient>'
          '<radialGradient id="gl" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#F07388" stop-opacity=".38"/><stop offset="1" stop-color="#F07388" stop-opacity="0"/></radialGradient></defs>'
          '<rect width="120" height="120" %sfill="url(#bg)"/><circle cx="60" cy="60" r="52" fill="url(#gl)"/>' % ('rx="27" ' if rounded else ""))
    # the mark at 72% keeps clear of the corners that iOS / Android masks cut away
    return svg("0 0 120 120", bg + '<g transform="translate(60 60) scale(.72) translate(-61 -60)">' + mark("original", uid="a") + "</g>", "爱伴星球 IBXQ")


def main():
    if OUT.exists():
        for d in ("svg", "png", "app-icon"):
            shutil.rmtree(OUT / d, ignore_errors=True)
    (OUT / "svg").mkdir(parents=True); (OUT / "app-icon").mkdir()
    jobs = []   # [svg path, png path, width or None, height or None]
    def emit(rel, content, pngs):
        p = OUT / rel; p.write_text(content, encoding="utf-8")
        for out, w, h in pngs:
            (OUT / out).parent.mkdir(parents=True, exist_ok=True)
            jobs.append([str(p), str(OUT / out), w, h])

    for style in ("original", "white", "black", "flat"):
        emit("svg/ibxq-mark-%s.svg" % style, svg("0 0 120 120", mark(style), "爱伴星球 IBXQ"),
             [("png/mark/%s/ibxq-mark-%s-%d.png" % (style, style, n), n, n) for n in (48, 64, 96, 128, 256, 512, 1024)])
        emit("svg/ibxq-mark-small-%s.svg" % style, svg("0 0 120 120", mark(style, small=True), "爱伴星球 IBXQ"),
             [("png/mark/%s/ibxq-mark-%s-%d.png" % (style, style, n), n, n) for n in (16, 24, 32)])
        for word in ("zh", "en"):
            grounds = [None] if style in ("white", "black") else ["dark", "light"]
            for g in grounds:
                name = "ibxq-logo-%s-%s" % (word, style) + ("-on-%s" % g if g else "")
                emit("svg/%s.svg" % name, lockup(style, g, word),
                     [("png/logo-%s/%s/%s-h%d.png" % (word, name.split("-", 3)[3], name, h), None, h) for h in (32, 64, 128, 256, 512)])

    emit("app-icon/ibxq-app-icon.svg", app_icon(False), [("app-icon/ibxq-app-icon-%d.png" % n, n, n) for n in (180, 192, 512, 1024)])
    emit("app-icon/ibxq-app-icon-rounded.svg", app_icon(True), [("app-icon/ibxq-app-icon-rounded-%d.png" % n, n, n) for n in (256, 512, 1024)])

    (OUT / "render-jobs.json").write_text(json.dumps(jobs))
    subprocess.run(["node", str(ROOT / "scripts/render-brand.js"), str(OUT / "render-jobs.json")], check=True)
    (OUT / "render-jobs.json").unlink()
    subprocess.run(["node", str(ROOT / "scripts/brand-preview.js")], check=True)

    # favicon.ico (16/32/48) + the files the site itself uses
    small = OUT / "png/mark/original"
    imgs = [Image.open(small / ("ibxq-mark-original-%d.png" % n)).convert("RGBA") for n in (16, 32, 48)]
    imgs[2].save(OUT / "app-icon/favicon.ico", format="ICO", append_images=imgs[:2], sizes=[(48, 48), (32, 32), (16, 16)])
    shutil.copy(OUT / "app-icon/favicon.ico", ROOT / "favicon.ico")
    shutil.copy(OUT / "svg/ibxq-mark-small-original.svg", ROOT / "favicon.svg")
    shutil.copy(small / "ibxq-mark-original-32.png", ROOT / "favicon-32.png")
    shutil.copy(OUT / "app-icon/ibxq-app-icon-180.png", ROOT / "apple-touch-icon.png")
    print("%d SVG, %d PNG" % (len(list(OUT.rglob("*.svg"))), len(list(OUT.rglob("*.png")))))


if __name__ == "__main__":
    main()
