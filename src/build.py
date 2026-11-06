#!/usr/bin/env python3
"""Writes the README's panels (assets/*.svg) from the data at the bottom of this file.

The look is luizgodoy.dev's: the rose-pine palette, Oxanium / Chakra Petch / Share Tech Mono, cut-corner frames
with the rose -> pine -> iris border, the rooftop and the ramen stall. GitHub shows a README image as an <img>,
which loads nothing from outside, so each panel is self-contained: every font is subset to the glyphs that panel
uses and inlined, every still is inlined, and text is laid out here (measured with the real font metrics) because
an SVG cannot wrap text by itself. Motion is CSS, and prefers-reduced-motion turns it off.

    pip install fonttools brotli
    python3 src/build.py
"""
import base64
import io
import random
import re
from collections import defaultdict
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / 'assets'

INK, ROSE, LILAC, PINE, GOLD, LOVE, IRIS, BLUE = '#130c0d', '#f6b6be', '#ffdffb', '#29ab87', '#f2ce6c', '#d68585', '#b9a2e8', '#7fb4ff'
TEXT, MUTE, LINE = '#f7e0e2', '#ccb1b5', 'rgba(246,182,190,.18)'
SITE = 'https://luizgodoy.dev'


# ---------- type ----------

class Face:
    """A font: its metrics for layout, and a subset of it for embedding."""

    def __init__(self, family, file, fallback):
        self.family, self.path, self.css = family, ROOT / 'fonts' / file, f'{family}, {fallback}'
        self.tt = TTFont(self.path)
        self.cmap, self.upm = self.tt.getBestCmap(), self.tt['head'].unitsPerEm
        self.variable = 'fvar' in self.tt
        self._hmtx = {}

    def hmtx(self, weight):
        if not self.variable:
            return self.tt['hmtx'].metrics
        if weight not in self._hmtx:
            self._hmtx[weight] = instancer.instantiateVariableFont(TTFont(self.path), {'wght': weight})['hmtx'].metrics
        return self._hmtx[weight]

    def width(self, text, size, weight=400, ls=0):
        m = self.hmtx(weight)
        adv = sum(m[self.cmap[ord(c)]][0] if ord(c) in self.cmap else self.upm * .62 for c in text)
        return adv / self.upm * size + ls * size * len(text)

    def embed(self, chars):
        font = TTFont(self.path)
        opts = subset.Options()
        opts.flavor, opts.name_IDs, opts.notdef_outline = 'woff2', [], True
        s = subset.Subsetter(opts)
        s.populate(text=''.join(sorted(chars)) + ' ')
        s.subset(font)
        buf = io.BytesIO()
        font.save(buf)
        weight = '200 800' if self.variable else '400'
        return (f'@font-face{{font-family:"{self.family}";font-weight:{weight};'
                f'src:url(data:font/woff2;base64,{base64.b64encode(buf.getvalue()).decode()}) format("woff2")}}')


DISPLAY = Face('Oxanium', 'oxanium.woff2', 'sans-serif')
BODY = Face('Chakra Petch', 'chakra-400.woff2', 'sans-serif')
MONO = Face('Share Tech Mono', 'share-tech-mono.woff2', 'monospace')


def rich(s, base=None, hi=ROSE):
    """'plain **highlighted** plain' -> runs [(text, colour)]."""
    return [(part, hi if i % 2 else base) for i, part in enumerate(s.split('**')) if part]


def runs_of(r):
    return [(r, None)] if isinstance(r, str) else r


def wrap(runs, face, size, maxw, weight=400, ls=0):
    """Greedy word wrap of coloured runs; returns lines, each a list of runs."""
    lines, w = [[]], 0
    for text, colour in runs_of(runs):
        for word in re.split(r'(\s+)', text):
            if not word:
                continue
            ww = face.width(' ' if word.isspace() else word, size, weight, ls)
            if word.isspace():
                if lines[-1]:
                    lines[-1].append((' ', colour))
                    w += ww
                continue
            if lines[-1] and w + ww > maxw:
                lines.append([])
                w = 0
            lines[-1].append((word, colour))
            w += ww
    out = []
    for line in lines:
        while line and line[-1][0] == ' ':
            line.pop()
        merged = []
        for text, colour in line:
            if merged and merged[-1][1] == colour:
                merged[-1] = (merged[-1][0] + text, colour)
            else:
                merged.append((text, colour))
        out.append(merged)
    return out


def plain(runs):
    return ''.join(t for t, _ in runs_of(runs))


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def frame(x, y, w, h, c=14):
    """The site's .frame: a 1px rose -> pine -> iris border around a dark panel."""
    return [f'<path d="{cut(x, y, w, h, c)}" fill="url(#grad)"/>', f'<path d="{cut(x + 1, y + 1, w - 2, h - 2, c - .4)}" fill="url(#panel)"/>']


def cut(x, y, w, h, c):
    """The site's frame: top-left and bottom-right corners cut."""
    return f'M{x + c:g} {y:g}H{x + w:g}V{y + h - c:g}L{x + w - c:g} {y + h:g}H{x:g}V{y + c:g}Z'


# ---------- a panel ----------

BASE_CSS = '''
@keyframes blink{50%{opacity:0}}
@keyframes fade{from{opacity:0}}
@keyframes grow{from{transform:scaleY(0)}}
@keyframes draw{from{stroke-dashoffset:400}}
@keyframes pulse{50%{opacity:.45}}
@keyframes cursor{0%,99%{opacity:.8}100%{opacity:0}}
@keyframes acquire{from{transform:scale(1.18);opacity:0}}
@keyframes sheen{0%{transform:translateX(-130%)}35%,100%{transform:translateX(130%)}}
@keyframes gla{0%,88%,100%{opacity:0;transform:none}89%{opacity:.9;transform:translate(-5px,0)}91%{opacity:.9;transform:translate(4px,-2px)}93%{opacity:.9;transform:translate(-2px,1px)}94%{opacity:0}}
@keyframes glb{0%,89%,100%{opacity:0;transform:none}90%{opacity:.9;transform:translate(5px,0)}92%{opacity:.9;transform:translate(-3px,2px)}94%{opacity:.9;transform:translate(2px,0)}95%{opacity:0}}
.blink{animation:blink 2.4s steps(1) infinite}
.gla{animation:gla 6s steps(1) infinite}.glb{animation:glb 6s steps(1) infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.wipe{display:none}}
'''


class Doc:
    def __init__(self, w, label):
        self.w, self.label = w, label
        self.defs, self.body, self.css = [], [], [BASE_CSS]
        self.used = defaultdict(set)
        self.ids = 0
        self.defs.append(f'<linearGradient id="grad" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="{ROSE}"/>'
                         f'<stop offset=".5" stop-color="{PINE}"/><stop offset="1" stop-color="{IRIS}"/></linearGradient>')
        self.defs.append('<linearGradient id="panel" x1=".3" y1="0" x2=".7" y2="1"><stop offset="0" stop-color="#2c181e"/>'
                         '<stop offset="1" stop-color="#140c0f"/></linearGradient>')

    def uid(self, p='i'):
        self.ids += 1
        return f'{p}{self.ids}'

    def add(self, *parts):
        self.body.extend(parts)

    def text(self, x, y, runs, face, size, weight=400, ls=0, fill=TEXT, anchor='start', attrs='', upper=False):
        runs = [(t.upper() if upper else t, c) for t, c in runs_of(runs)]
        for t, _ in runs:
            self.used[face.family] |= set(t)
        inner = ''.join(f'<tspan fill="{c}">{esc(t)}</tspan>' if c else esc(t) for t, c in runs)
        ls_attr = f' letter-spacing="{ls * size:.2f}"' if ls else ''
        anchor_attr = f' text-anchor="{anchor}"' if anchor != 'start' else ''
        return (f'<text x="{x:g}" y="{y:g}" font-family="{face.css}" font-size="{size}" font-weight="{weight}" '
                f'fill="{fill}"{ls_attr}{anchor_attr} {attrs}>{inner}</text>')

    def put(self, *a, **k):
        self.add(self.text(*a, **k))

    def row(self, x, y, items, face, size, weight=400, ls=0, fill=TEXT, gap=16):
        """Runs set side by side with a fixed gap (SVG collapses the spaces that would do it)."""
        for runs in items:
            self.put(x, y, runs, face, size, weight, ls, fill)
            x += face.width(plain(runs), size, weight, ls) + gap
        return x

    def para(self, x, y, runs, face, size, maxw, lh, weight=400, ls=0, fill=TEXT, upper=False, attrs=''):
        """Wrapped text whose first line's top is y; returns the y under the last line."""
        lines = wrap(runs, face, size, maxw, weight, ls)
        for i, line in enumerate(lines):
            self.put(x, y + (lh - size) / 2 + size * .8 + i * lh, line, face, size, weight, ls, fill, upper=upper, attrs=attrs)
        return y + len(lines) * lh

    def frame(self, x, y, w, h, c=14):
        self.add(*frame(x, y, w, h, c))

    def image(self, file, w, h, focus=(.5, .5)):
        """A still laid out like object-fit: cover around a focus point; returns its box."""
        iw0, ih0 = 1280, 720
        s = max(w / iw0, h / ih0)
        iw, ih = iw0 * s, ih0 * s
        ix, iy = (w - iw) * focus[0], (h - ih) * focus[1]
        data = base64.b64encode((ROOT / 'img' / file).read_bytes()).decode()
        self.add(f'<image href="data:image/webp;base64,{data}" x="{ix:.1f}" y="{iy:.1f}" width="{iw:.1f}" height="{ih:.1f}" preserveAspectRatio="none"/>')
        return ix, iy, iw, ih

    def render(self, h):
        fonts = [face.embed(self.used[face.family]) for face in (DISPLAY, BODY, MONO) if self.used[face.family]]
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h:.0f}" viewBox="0 0 {self.w} {h:.0f}" '
                f'role="img" aria-label="{esc(self.label)}"><title>{esc(self.label)}</title>'
                f'<style>{"".join(fonts)}{"".join(self.css)}</style><defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')

    def save(self, name, h):
        (OUT / name).write_text(self.render(h))


def glitch(d, x, y, text, size, fill, delay=0):
    """The site's .glitch: rose and pine slices of the word that jump out for a few frames every few seconds."""
    top, h = y - size * .78, size * .98
    for cls, colour, band in (('gla', ROSE, (.1, .4)), ('glb', PINE, (.55, .88))):
        cid = d.uid('c')
        d.defs.append(f'<clipPath id="{cid}"><rect x="{x - 20:g}" y="{top + h * band[0]:.1f}" width="{DISPLAY.width(text, size, 800) + 40:.0f}" height="{h * (band[1] - band[0]):.1f}"/></clipPath>')
        d.add(f'<g clip-path="url(#{cid})"><g class="{cls}" style="animation-delay:{delay}s">',
              d.text(x, y, text, DISPLAY, size, 800, -.02, colour), '</g></g>')
    d.add(d.text(x, y, text, DISPLAY, size, 800, -.02, fill))


def section_head(d, x, y, w, pre, post, note):
    """The site's .sh: a huge outlined word, the tail of it filled, and a mono note boxed on the right."""
    size = 104
    word_w = DISPLAY.width((pre + post).upper(), size, 800, -.01)
    base = y + size * .74
    d.add(f'<text x="{x}" y="{base:.1f}" font-family="{DISPLAY.css}" font-size="{size}" font-weight="800" letter-spacing="{-.01 * size:.2f}" '
          f'fill="none" stroke="{ROSE}" stroke-width="1.5">{esc(pre.upper())}<tspan fill="{ROSE}" stroke="none">{esc(post.upper())}</tspan></text>')
    d.used[DISPLAY.family] |= set((pre + post).upper())
    nw = w - word_w - 28
    lines = wrap(rich(note, None, TEXT), MONO, 14, nw - 28)
    nh = len(lines) * 21 + 24
    ny = base - nh
    nx = x + w - nw
    d.add(f'<rect x="{nx:.1f}" y="{ny:.1f}" width="{nw:.1f}" height="{nh}" fill="{INK}" fill-opacity=".72"/>',
          f'<rect x="{nx:.1f}" y="{ny:.1f}" width="2" height="{nh}" fill="{PINE}"/>')
    d.para(nx + 14, ny + 12, rich(note, None, TEXT), MONO, 14, nw - 28, 21, fill=MUTE)
    return base + 34


# ---------- the panels ----------

def hero():
    W = 1200
    d = Doc(W, 'luiz godoy. full-stack netrunner from dourados-ms, brazil. a flying car parked on a rainy rooftop under rose-pine neon.')
    x0, colw = 64, 520

    # lay the copy out first: the panel is as tall as the copy needs
    kicker_y, name1, name2 = 118, 268, 268 + 126
    tag_top = name2 + 50
    tag = [('full-stack netrunner. i ship ', None), ('weird useful stuff', ROSE),
           (' on cloudflare workers, mostly at 4pm, sometimes at 3am. games, agents, desktop pets, u know?', None)]
    tag_lines = wrap(tag, BODY, 21, colw)
    stakes_top = tag_top + len(tag_lines) * 32 + 22
    stakes = [('514', ' commits in one day. the agent crew built the app that runs agent crews.'),
              ('1,916', ' pokemon cards playable. ctrl-click does 999.'),
              ('0', ' audio files in a whole godot game. every sound is generated at boot.')]
    stake_lines = [wrap([('> ', PINE), (n, GOLD), (t, MUTE)], MONO, 14, colw + 90) for n, t in stakes]
    H = stakes_top + sum(len(s) for s in stake_lines) * 21 + 40

    clip = d.uid('c')
    d.defs.append(f'<clipPath id="{clip}"><path d="{cut(0, 0, W, H, 22)}"/></clipPath>')
    d.defs.append(f'<linearGradient id="shade" x1="0" x2="1"><stop offset="0" stop-color="{INK}" stop-opacity=".97"/>'
                  f'<stop offset=".34" stop-color="{INK}" stop-opacity=".88"/><stop offset=".58" stop-color="{INK}" stop-opacity=".12"/>'
                  f'<stop offset="1" stop-color="{INK}" stop-opacity="0"/></linearGradient>')
    d.defs.append(f'<linearGradient id="floor" x1="0" x2="0" y1="0" y2="1"><stop offset=".7" stop-color="{INK}" stop-opacity="0"/>'
                  f'<stop offset="1" stop-color="{INK}" stop-opacity=".7"/></linearGradient>')
    d.add(f'<g clip-path="url(#{clip})"><rect width="{W}" height="{H}" fill="{INK}"/>')
    ix, iy, iw, ih = d.image('rooftop.webp', W, H, (.7, .4))

    # rain: two tiles of streaks per layer, the layer falls one panel height and loops
    rng = random.Random(77)
    for layer, (n, dur, op, length) in enumerate(((70, 1.3, .14, (16, 30)), (34, .75, .24, (34, 64)))):
        streaks = ''.join(
            f'<path d="M{x:.0f} {y:.0f}l{-l * .1:.1f} {l:.0f}"/>'
            for x, y, l in ((rng.uniform(0, W + 40), rng.uniform(0, H), rng.uniform(*length)) for _ in range(n)))
        d.css.append(f'.rain{layer}{{animation:fall{layer} {dur}s linear infinite}}@keyframes fall{layer}{{to{{transform:translateY({H}px)}}}}')
        d.add(f'<g class="rain{layer}" stroke="{LILAC}" stroke-opacity="{op}" stroke-width="1"><g>{streaks}</g>'
              f'<g transform="translate(0 {-H})">{streaks}</g></g>')
    d.add(f'<rect width="{W}" height="{H}" fill="url(#shade)"/><rect width="{W}" height="{H}" fill="url(#floor)"/>')

    # target lock on the AV, where the site puts it on this frame
    lx, ly, lw, lh = ix + .485 * iw, iy + .33 * ih, .445 * iw, .33 * ih
    k = 22
    corners = (f'M{lx} {ly + k}V{ly}H{lx + k}M{lx + lw - k} {ly}H{lx + lw}V{ly + k}'
               f'M{lx} {ly + lh - k}V{ly + lh}H{lx + k}M{lx + lw - k} {ly + lh}H{lx + lw}V{ly + lh - k}')
    d.css.append('.lock{transform-box:fill-box;transform-origin:center;animation:acquire .9s cubic-bezier(.16,1,.3,1) .3s both,pulse 2.4s ease-in-out 1.2s infinite}')
    d.defs.append(f'<filter id="glow" x="-10%" y="-10%" width="120%" height="120%"><feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="{ROSE}" flood-opacity=".7"/></filter>')
    d.add(f'<g class="lock"><path d="{corners:}" fill="none" stroke="{ROSE}" stroke-width="2" filter="url(#glow)"/>')
    tag_w = MONO.width('AV-77 // UNREGISTERED', 12, ls=.14) + 16
    ice_w = MONO.width('ICE ×3', 12, ls=.14) + 16
    d.add(f'<rect x="{lx:.1f}" y="{ly + lh + 10:.1f}" width="{tag_w:.1f}" height="24" fill="{INK}" fill-opacity=".72"/>',
          d.text(lx + 8, ly + lh + 26, 'AV-77 // UNREGISTERED', MONO, 12, ls=.14, fill=ROSE),
          f'<rect x="{lx + lw - ice_w:.1f}" y="{ly + lh + 10:.1f}" width="{ice_w:.1f}" height="24" fill="{INK}" fill-opacity=".72"/>',
          d.text(lx + lw - ice_w + 8, ly + lh + 26, [('ICE ', MUTE), ('×3', GOLD)], MONO, 12, ls=.14), '</g>')

    # hud bar
    d.add(f'<rect width="{W}" height="52" fill="{INK}" fill-opacity=".72"/><rect y="51" width="{W}" height="1" fill="{ROSE}" fill-opacity=".18"/>',
          f'<rect y="51" width="{W}" height="2" fill="url(#grad)" opacity=".85"/>')
    d.put(32, 32, [('LG', None), ('//', PINE), ('NET', None)], DISPLAY, 15, 800, .12, ROSE)
    sx = 32 + DISPLAY.width('LG//NET', 15, 800, .12) + 34
    d.add(f'<rect class="blink" x="{sx:.0f}" y="22" width="7" height="7" fill="{PINE}"/>')
    d.row(sx + 13, 31, ['ONLINE', 'DOURADOS-MS', [('€$ ', None), ('3,604', GOLD)]], MONO, 13, ls=.06, fill=MUTE, gap=18)
    d.put(W - 32, 31, 'LUIZGODOY.DEV', MONO, 13, ls=.06, fill=ROSE, anchor='end')

    # the copy
    d.row(x0, kicker_y, [[('NETRUNNER PROFILE', PINE)], '· DOURADOS-MS, BRAZIL', '· JACKED IN SINCE 2018'], MONO, 13, ls=.14, fill=MUTE, gap=12)
    glitch(d, x0, name1, 'luiz', 150, TEXT)
    gw = DISPLAY.width('godoy', 150, 800, -.02)
    d.defs.append(f'<linearGradient id="namegrad" gradientUnits="userSpaceOnUse" x1="{x0}" y1="{name2}" x2="{x0 + gw:.0f}" y2="{name2 - 140}">'
                  f'<stop offset="0" stop-color="{ROSE}"/><stop offset=".5" stop-color="{PINE}"/><stop offset="1" stop-color="{IRIS}"/></linearGradient>')
    glitch(d, x0, name2, 'godoy', 150, 'url(#namegrad)', delay=.15)
    d.para(x0, tag_top, tag, BODY, 21, colw, 32)
    y = stakes_top
    for lines in stake_lines:
        for line in lines:
            d.put(x0, y + 15, line, MONO, 14)
            y += 21
    d.add('</g>', f'<path d="{cut(.75, .75, W - 1.5, H - 1.5, 22)}" fill="none" stroke="url(#grad)" stroke-width="1.5"/>')
    d.save('hero.svg', H)


def cta():
    label = 'BREACH IT'
    tw = DISPLAY.width(label, 16, 600, .16)
    W, H = int(26 + tw + 12 + 14 + 26), 50
    d = Doc(W, 'breach it: take the ride on luizgodoy.dev')
    clip = d.uid('c')
    d.defs.append(f'<clipPath id="{clip}"><path d="{cut(0, 0, W, H, 10)}"/></clipPath>')
    d.defs.append('<linearGradient id="sheen" x1="0" x2="1"><stop offset=".35" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".5" stop-color="#fff" stop-opacity=".6"/><stop offset=".65" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    d.css.append('.sheen{animation:sheen 4s cubic-bezier(.2,.8,.2,1) 1s infinite;transform:translateX(-130%)}')
    d.add(f'<g clip-path="url(#{clip})"><rect width="{W}" height="{H}" fill="{ROSE}"/>')
    d.put(26, 31, label, DISPLAY, 16, 600, .16, INK)
    ax = 26 + tw + 12
    d.add(f'<path d="M{ax} {H / 2 + 6}l11 -11M{ax + 3} {H / 2 - 5}h8v8" fill="none" stroke="{INK}" stroke-width="2.2"/>',
          f'<rect class="sheen" x="-2" y="-2" width="{W + 4}" height="{H + 4}" fill="url(#sheen)"/></g>')
    d.save('cta.svg', H)


def gigs_head():
    W = 1000
    d = Doc(W, 'gigs: the fixer board')
    h = section_head(d, 28, 28, W - 56, 'gi', 'gs', GIGS_NOTE)
    d.body.insert(0, f'<path d="{cut(0, 0, W, h, 14)}" fill="{INK}"/>')
    d.save('gigs.svg', h)


CHIP = {'live': PINE, 'private build': GOLD, 'private': GOLD, 'in dev': GOLD, 'team toy': GOLD, 'revived': IRIS,
        'classified': IRIS, 'open source': LILAC, 'npm': LILAC}
DOODLE = ('<path d="M18 52c-6-18 4-34 22-34s26 14 22 30-14 20-24 20-16-6-20-16z"/><circle cx="33" cy="40" r="2.5"/>'
          '<circle cx="47" cy="40" r="2.5"/><path d="M35 52c3 3 8 3 11 0"/><path d="M58 22l12-12M66 10l4 4M56 24l-2 6 6-2"/>'
          '<path d="M24 66l-4 8M54 66l4 8"/>')


def chips(d, x, y, maxw, words, face=MONO, size=12):
    """The site's .stack: tag chips that wrap; returns the y under them."""
    cx, cy = x, y
    for word in words:
        w = face.width(word, size, ls=.04) + 14
        if cx > x and cx + w > x + maxw:
            cx, cy = x, cy + 28
        d.add(f'<rect x="{cx:.1f}" y="{cy}" width="{w:.1f}" height="22" fill="{ROSE}" fill-opacity=".08"/>',
              d.text(cx + 7, cy + 15, word, face, size, ls=.04, fill=ROSE))
        cx += w + 6
    return cy + 22


def gig_card(g, n, H=None):
    W, P = 490, 22
    d = Doc(W, f'gig {g["no"]}: {g["name"]}. {g["status"]}. {g["what"]}')
    y = P
    d.put(P, y + 12, f'GIG-{g["no"]}', MONO, 12, ls=.1, fill=MUTE)
    colour = CHIP[g['status']]
    cw = MONO.width(g['status'].upper(), 12, ls=.08) + 16
    d.add(f'<rect x="{W - P - cw:.1f}" y="{y - 4.5:.1f}" width="{cw:.1f}" height="22" fill="none" stroke="{colour}"/>',
          d.text(W - P - cw + 8, y + 11, g['status'], MONO, 12, ls=.08, fill=colour, upper=True))
    y += 30
    if g.get('doodle'):
        d.add(f'<g transform="translate({W - P - 64} {y - 8}) scale(.8)" fill="none" stroke="{BLUE}" stroke-width="2.4" stroke-linecap="round" '
              f'stroke-linejoin="round" stroke-dasharray="400" style="animation:draw 1.6s cubic-bezier(.3,.7,.3,1.2) .4s both">{DOODLE}</g>')
    y = d.para(P, y, g['name'], DISPLAY, 30, W - 2 * P - (70 if g.get('doodle') else 0), 32, 800, -.01)
    d.put(P, y + 18, g['fixer'], MONO, 12, ls=.1, fill=PINE, upper=True)
    y += 34
    y = d.para(P, y, g['what'], BODY, 15, W - 2 * P, 23, attrs='opacity=".9"')
    if g.get('note'):
        top = y + 12
        y = d.para(P + 12, top, g['note'], MONO, 13, W - 2 * P - 12, 19, fill=MUTE)
        d.add(f'<rect x="{P}" y="{top + 1}" width="2" height="{y - top - 2}" fill="{LOVE}"/>')
    y = chips(d, P, y + 14, W - 2 * P, g['stack'])
    natural = y + 14 + 84 + P
    H = H or natural

    # pinned to the bottom, like the site's margin-top: auto
    my = H - P - 84
    d.add(f'<path d="M{P} {my}H{W - P}" stroke="{ROSE}" stroke-opacity=".18" stroke-dasharray="4 3"/>')
    d.put(P, my + 24, 'THREAT', MONO, 12, ls=.08, fill=MUTE)
    for i in range(5):
        bx = P + i * 19
        on = i < g['threat']
        d.add(f'<path d="M{bx + 3.3:g} {my + 32}h16l-3.3 9h-16z" fill="{LOVE if on else ROSE}" fill-opacity="{1 if on else .14}"/>')
    px = W / 2 + 5
    d.put(px, my + 24, 'PAYOUT', MONO, 12, ls=.08, fill=MUTE)
    d.put(px, my + 44, f'€$ {g["pay"]:,}', DISPLAY, 17, 600, .02, GOLD)
    link = g.get('label')
    d.put(P, H - P - 4, (link + ' ↗') if link else 'no public link · ask me', DISPLAY if link else MONO, 13,
          600 if link else 400, .14 if link else .06, ROSE if link else MUTE, upper=bool(link))

    # the scan line that sweeps each card, staggered down the board
    d.css.append(f'@keyframes scan{{0%{{transform:translateX(0);opacity:0}}4%,14%{{opacity:1}}18%,100%{{transform:translateX({W}px);opacity:0}}}}')
    d.add(f'<g style="animation:scan 9s linear {1 + n * .7:.1f}s infinite;opacity:0"><rect x="-6" width="12" height="{H}" fill="{PINE}" opacity=".18"/>'
          f'<rect x="-1" width="2" height="{H}" fill="{PINE}"/></g>')
    d.body[0:0] = frame(0, 0, W, H)  # under the content, now that the height is known
    return d, natural


def classified():
    W, H, P = 1000, 220, 22
    g = CLASSIFIED
    d = Doc(W, 'gig XX: classified. breach it on luizgodoy.dev to read this one.')
    d.frame(0, 0, W, H)
    d.put(P, P + 12, 'GIG-XX', MONO, 12, ls=.1, fill=MUTE)
    cw = MONO.width('CLASSIFIED', 12, ls=.08) + 16
    d.add(f'<rect x="{W - P - cw:.1f}" y="{P - 4.5}" width="{cw:.1f}" height="22" fill="none" stroke="{IRIS}"/>',
          d.text(W - P - cw + 8, P + 11, 'CLASSIFIED', MONO, 12, ls=.08, fill=IRIS))
    d.defs.append('<filter id="redact" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="7"/></filter>')
    d.add('<g filter="url(#redact)" opacity=".55">')
    d.put(P, P + 64, g['name'], DISPLAY, 30, 800, -.01)
    d.para(P, P + 80, g['what'], BODY, 15, W - 2 * P, 23)
    d.add('</g>')
    d.put(W / 2, 112, 'CLASSIFIED', DISPLAY, 28, 800, .12, GOLD, anchor='middle')
    d.put(W / 2, 142, 'ICE detected. solve the breach on luizgodoy.dev to read this one.', MONO, 13, fill=MUTE, anchor='middle')
    bw = MONO.width('RUN BREACH ↗', 13, ls=.06) + 22
    d.add(f'<rect x="{W / 2 - bw / 2:.1f}" y="160" width="{bw:.1f}" height="30" fill="none" stroke="{LINE}"/>',
          d.text(W / 2, 180, 'RUN BREACH ↗', MONO, 13, ls=.06, fill=ROSE, anchor='middle'))
    d.save('gig-xx.svg', H)


def side_gigs():
    W, P = 1000, 18
    d = Doc(W, 'side gigs: ' + '; '.join(f'{a}, {b}' for a, b in SIDE_GIGS))
    items = [[('SIDE GIGS', PINE)]] + [[(a, ROSE), (' ' + b, MUTE)] for a, b in SIDE_GIGS]
    x, y = P, P
    for item in items:
        w = MONO.width(plain(item), 14, ls=.1 if item[0][1] == PINE else 0)
        if x > P and x + w > W - P:
            x, y = P, y + 26
        d.put(x, y + 16, item, MONO, 14, ls=.1 if item[0][1] == PINE else 0)
        x += w + 26
    H = y + 26 + P
    d.body.insert(0, f'<rect width="{W}" height="{H}" fill="{INK}" fill-opacity=".92"/><rect width="{W}" height="1" fill="{LINE}"/>'
                     f'<rect y="{H - 1}" width="{W}" height="1" fill="{LINE}"/>')
    d.save('side-gigs.svg', H)


def hours_chart(d, x, y, W, H):
    L, B, T, top = 38, 26, 24, 360
    bw = (W - L - 6) / 24
    s = []
    for v in (0, 100, 200, 300):
        gy = y + H - B - v / top * (H - B - T)
        s.append(f'<path d="M{x + L} {gy:.1f}H{x + W}" stroke="{ROSE}" stroke-opacity=".1"/>')
        s.append(d.text(x + L - 8, gy + 4, str(v), MONO, 11, fill=MUTE, anchor='end'))
    for i, v in enumerate(HOURS):
        h = v / top * (H - B - T)
        bx, by = x + L + i * bw + 2, y + H - B - h
        fill = {16: ROSE, 2: GOLD, 3: GOLD, 6: PINE}.get(i, 'rgba(246,182,190,.38)')
        s.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw - 4:.1f}" height="{h:.1f}" fill="{fill}" '
                 f'style="transform-box:fill-box;transform-origin:50% 100%;animation:grow .8s cubic-bezier(.2,.8,.2,1) {.4 + i * .032:.3f}s both">'
                 f'<title>{i:02d}:00 · {v} commits</title></rect>')
        if i % 3 == 0:
            s.append(d.text(bx + (bw - 4) / 2, y + H - 8, f'{i:02d}', MONO, 11, fill=MUTE, anchor='middle'))
    for i, label, colour in ((16, '347 · peak', ROSE), (2, '222', GOLD), (6, '23', PINE)):
        s.append(d.text(x + L + i * bw + bw / 2, y + H - B - HOURS[i] / top * (H - B - T) - 7, label, MONO, 12, fill=colour,
                        anchor='middle', attrs='style="animation:fade .5s 1.4s both"'))
    d.add(*s)


def months_chart(d, x, y, W, H):
    B, T, top = 22, 18, 700
    step = (W - 20) / (len(MONTHS) - 1)
    pts = [(x + 10 + i * step, y + H - B - v / top * (H - B - T)) for i, (_, v) in enumerate(MONTHS)]
    line = ' '.join(f'{"L" if i else "M"}{px:.1f} {py:.1f}' for i, (px, py) in enumerate(pts))
    d.defs.append(f'<linearGradient id="mg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{ROSE}" stop-opacity=".35"/>'
                  f'<stop offset="1" stop-color="{ROSE}" stop-opacity="0"/></linearGradient>')
    d.css.append('@keyframes trace{from{stroke-dashoffset:1}}')
    d.add(f'<path d="{line} L{pts[-1][0]:.1f} {y + H - B} L{pts[0][0]:.1f} {y + H - B}Z" fill="url(#mg)" style="animation:fade 1.2s .9s both"/>',
          f'<path d="{line}" pathLength="1" stroke-dasharray="1" fill="none" stroke="{ROSE}" stroke-width="2" style="animation:trace 1.8s cubic-bezier(.2,.8,.2,1) .4s both"/>')
    for i, (m, _) in enumerate(MONTHS):
        if i % 2 == 0:
            d.put(pts[i][0], y + H - 4, m, MONO, 11, fill=MUTE, anchor='middle')
    px, py = pts[11]
    d.add(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{GOLD}" style="animation:fade .4s 2s both"/>',
          d.text(px - 9, py + 4, 'sep · 687', MONO, 12, fill=GOLD, anchor='end', attrs='style="animation:fade .4s 2s both"'))


def ptitle(d, x, y, w, left, right):
    d.put(x, y + 10, left, MONO, 12, ls=.14, fill=PINE, upper=True)
    d.put(x + w, y + 10, right, MONO, 12, ls=.14, fill=MUTE, upper=True, anchor='end')
    return y + 28


def profile():
    W, P, IP = 1000, 28, 24
    d = Doc(W, 'profile: telemetry and cyberdeck spec sheet, numbers from github and local git over the last 12 months')
    bg = len(d.body)
    y = section_head(d, P, P, W - 2 * P, 'pro', 'file', PROFILE_NOTE)
    fw, iw = W - 2 * P, W - 2 * P - 2 * IP

    # telemetry
    top, body = y, len(d.body)
    y = ptitle(d, P + IP, y + IP, iw, 'telemetry', '2025-10 → 2026-10')
    colw = (iw - 5 * 14) / 6
    bottom = y
    for i, (num, label, colour) in enumerate(STATS):
        cx = P + IP + i * (colw + 14)
        d.put(cx, y + 36, num, DISPLAY, 42, 800, fill=colour)
        bottom = max(bottom, d.para(cx, y + 48, label, MONO, 12, colw, 16, ls=.06, fill=MUTE, upper=True))
    y = bottom + 22
    hours_chart(d, P + IP, y, iw, 220)
    y += 220 + 10
    d.put(P + IP, y + 12, 'commits by hour, local time. the 16:00 peak is the day job, the 02:00 one is not.', MONO, 12, ls=.04, fill=MUTE)
    y += 18 + IP
    d.body[body:body] = frame(P, top, fw, y - top)
    y += 18

    # cyberdeck
    top, body = y, len(d.body)
    y = ptitle(d, P + IP, y + IP, iw, 'cyberdeck', 'installed chrome')
    lw = 520
    dtw = max(MONO.width(k.upper(), 14, ls=.06) for k, _ in SPEC) + 18
    ly = y
    for k, v in SPEC:
        d.put(P + IP, ly + 15, k, MONO, 14, ls=.06, fill=MUTE, upper=True)
        ly = d.para(P + IP + dtw, ly, rich(v), MONO, 14, lw - dtw, 20) + 9
    rx, rw = P + IP + lw + 28, iw - lw - 28
    lines = wrap(DAYJOB, BODY, 14, rw - 28)
    jh = 12 + 18 + len(lines) * 21 + 12
    d.add(f'<rect x="{rx}" y="{y}" width="{rw}" height="{jh}" fill="none" stroke="{LINE}" stroke-dasharray="4 3"/>')
    d.put(rx + 14, y + 24, 'DAY JOB', MONO, 12, ls=.1, fill=GOLD)
    d.para(rx + 14, y + 32, DAYJOB, BODY, 14, rw - 28, 21)
    months_chart(d, rx, y + jh + 18, rw, 150)
    y = max(ly - 9, y + jh + 18 + 150) + IP
    d.body[body:body] = frame(P, top, fw, y - top)
    H = y + P
    d.body.insert(bg, f'<path d="{cut(0, 0, W, H, 14)}" fill="{INK}"/>')
    d.save('profile.svg', H)


def comms():
    W, P = 1000, 28
    d = Doc(W, 'comms: intercepted transmissions, all real, all typed by luiz. ' + ' / '.join(t for _, _, t in COMMS))
    bg = len(d.body)
    y = section_head(d, P, P, W - 2 * P, 'com', 'ms', COMMS_NOTE)
    colw = (W - 2 * P - 18) / 2
    qw = colw - 38
    t, rows = .6, []
    for r in range(0, len(COMMS), 2):
        rows.append([wrap([('“', ROSE), (q, None), ('”', ROSE)], DISPLAY, 22, qw, 500) for _, _, q in COMMS[r:r + 2]])
    for r, row in enumerate(rows):
        rh = max(16 + 12 + 10 + len(lines) * 27.5 + 18 for lines in row)
        for c, lines in enumerate(row):
            i = r * 2 + c
            tx, ch, _ = COMMS[i]
            x, ty = P + c * (colw + 18), y + (40 if c else 0)
            h = 16 + 12 + 10 + len(lines) * 27.5 + 18
            clip = d.uid('c')
            d.defs.append(f'<clipPath id="{clip}"><rect x="{x}" y="{ty}" width="{colw}" height="{h}"/></clipPath>')
            d.add(f'<rect x="{x}" y="{ty}" width="{colw}" height="{h}" fill="#1a0e12"/>',
                  f'<rect x="{x}" y="{ty}" width="2" height="{h}" fill="{PINE if i % 4 in (1, 2) else ROSE}"/>')
            head = f'TX {tx} · SRC: LUIZ · CH: {ch.upper()}'
            d.put(x + 20, ty + 28, head, MONO, 12, ls=.14, fill=MUTE)
            # the decoder: each line types itself out, then the header says so
            d.add(f'<g clip-path="url(#{clip})">')
            for k, line in enumerate(lines):
                ly = ty + 38 + k * 27.5
                d.put(x + 20, ly + 21, line, DISPLAY, 22, 500)
                n = len(plain(line))
                lw = DISPLAY.width(plain(line), 22, 500) + 4
                dur = n / 48
                d.css.append(f'@keyframes w{i}_{k}{{to{{transform:translateX({lw:.0f}px)}}}}')
                d.add(f'<g class="wipe" style="animation:w{i}_{k} {dur:.2f}s steps({n}) {t:.2f}s both"><rect x="{x + 18}" y="{ly}" width="{colw}" height="27.5" fill="#1a0e12"/>'
                      f'<rect x="{x + 18}" y="{ly + 4}" width="10" height="21" fill="{GOLD}" opacity=".8" style="animation:cursor {dur:.2f}s {t:.2f}s both"/></g>')
                t += dur
            d.add('</g>')
            d.put(x + 20 + MONO.width(head, 12, ls=.14) + 8, ty + 28, '· DECODED', MONO, 12, ls=.14, fill=PINE,
                  attrs=f'style="animation:fade .3s {t:.2f}s both"')
            t += .15
        y += rh + 14
    y += 40 + 46

    # contact
    lines = wrap(CONTACT, MONO, 15, 560)
    ch = 30 + 64 + 18 + len(lines) * 22.5 + 30
    d.add(f'<rect x="{P}" y="{y}" width="{W - 2 * P}" height="{ch}" fill="#1d1014"/><rect x="{P}" y="{y}" width="2" height="{ch}" fill="{ROSE}"/>')
    d.put(P + 30, y + 30 + 52, [('got a gig? ', None), ('ping me.', ROSE)], DISPLAY, 68, 800, -.01)
    d.para(P + 30, y + 30 + 64 + 18, CONTACT, MONO, 15, 560, 22.5, fill=MUTE)
    y += ch
    H = y + P
    d.body.insert(bg, f'<path d="{cut(0, 0, W, H, 14)}" fill="{INK}"/>')
    d.save('comms.svg', H)


def touchdown():
    W, H = 1200, 440
    d = Doc(W, 'touchdown at the ramen stall. AV abandoned. NCPD notified.')
    clip = d.uid('c')
    d.defs.append(f'<clipPath id="{clip}"><path d="{cut(0, 0, W, H, 22)}"/></clipPath>')
    d.defs.append(f'<radialGradient id="td" cx=".5" cy=".46" r=".46"><stop offset="0" stop-color="{INK}" stop-opacity=".85"/>'
                  f'<stop offset="1" stop-color="{INK}" stop-opacity="0"/></radialGradient>')
    d.defs.append(f'<linearGradient id="tdf" x1="0" x2="0" y1="0" y2="1"><stop offset=".72" stop-color="{INK}" stop-opacity="0"/>'
                  f'<stop offset="1" stop-color="{INK}" stop-opacity=".92"/></linearGradient>')
    d.add(f'<g clip-path="url(#{clip})"><rect width="{W}" height="{H}" fill="{INK}"/>')
    d.image('street.webp', W, H, (.5, .3))
    d.add(f'<rect width="{W}" height="{H}" fill="url(#td)"/><rect width="{W}" height="{H}" fill="url(#tdf)"/>')
    d.put(W / 2, 150, 'alt 0m // ramen stall', MONO, 13, ls=.2, fill=PINE, upper=True, anchor='middle')
    tw = DISPLAY.width('touchdown.', 116, 800, -.02)
    glitch(d, W / 2 - tw / 2, 262, 'touchdown.', 116, TEXT, delay=1)
    d.put(W / 2, 312, 'AV abandoned. NCPD notified.', MONO, 15, ls=.12, fill=GOLD, upper=True, anchor='middle')
    d.put(W / 2, H - 26, '© 2026 luiz godoy · built on a rose-pine rice · no eddies were harmed', MONO, 12, ls=.06, fill=MUTE, anchor='middle')
    d.add('</g>', f'<path d="{cut(.75, .75, W - 1.5, H - 1.5, 22)}" fill="none" stroke="url(#grad)" stroke-width="1.5"/>')
    d.save('touchdown.svg', H)


# ---------- content (from luizgodoy.dev) ----------

GIGS_NOTE = 'fixer board. **10 open contracts**, all real, mostly shipped as one cloudflare worker + d1/do/kv/r2. threat = how hard it fought back. payout in eddies, made up, vibes accurate.'
PROFILE_NOTE = 'cyberdeck spec sheet. **numbers pulled from github + local git**, last 12 months. 3,584 of these are private so u gotta trust me bro.'
COMMS_NOTE = 'intercepted transmissions. **all real, all typed by me**, typos included. the decoder is still catching up.'
CONTACT = 'contact: github / ping me. email coming soon, the fixer is still setting up the dead drop. prs, ideas, and prank requests welcome.'
DAYJOB = 'full-stack engineer on a healthcare scheduling platform (react, node/deno, expo, aws).'

GIGS = [
    dict(no='01', name='bits', status='private build', threat=5, pay=514000, fixer='fixer: margins', doodle=True,
         what='talk to one main bot, it runs a whole crew of claude code bots in ur repos on ur own login. the crew built the app that runs crews. 514 commits in one day, not even joking.',
         note='mascot is margins: pen-doodle creatures that draw themselves in. this one has a pencil behind its ear.',
         stack=['electron', 'typescript', 'vite', 'vitest', 'pnpm']),
    dict(no='02', name='aurora arena tcg', status='live', threat=4, pay=1916000, fixer='fixer: the queue bots', url='https://auroratcg.app', label='auroratcg.app',
         what='fan-made pokemon tcg in the browser. all 1,916 standard cards playable, ranked, friends-only spectating, and queue bots so it never feels dead. durable objects pinned to south america so ur moves land fast.',
         note='"if i\'m holding CTRL i do 999 damage to all his pokemons hahahaha that would be funny as hell". shipped it. owner only, never ranked. fan project, not affiliated w/ pokemon.',
         stack=['react', 'pixijs', 'durable objects', 'd1', 'r2']),
    dict(no='03', name='schemaflow', status='live', threat=4, pay=143000, fixer='fixer: a dba w/ trust issues', url='https://schemaflow.uk', label='schemaflow.uk',
         what='db diagrams that don\'t suck. live collab, ddl export for 5 dialects, and a hand-written mcp server so agents edit ur schema while u watch it move.',
         note='two security sweeps. 26 findings. 26 fixed.',
         stack=['react', 'yjs', 'workers', 'durable objects', 'mcp']),
    dict(no='04', name='plugpal', status='open source', threat=2, pay=5000, fixer='fixer: blob, mochi & pip', url='https://plugpal.luizgodoy.dev', label='plugpal.luizgodoy.dev',
         what='tiny pixel pet that lives on ur desktop and reacts to ur charger. drinks from the cable, sweats at 20%, faints at 5%, parties at 100%. no account, no server, no analytics.',
         note='there\'s one in the corner of luizgodoy.dev. check ur battery.',
         stack=['rust', 'tauri v2', 'typescript']),
    dict(no='05', name='dungeonborne offline', status='revived', threat=5, pay=999999, fixer='fixer: a dead server',
         what='a shut-down online extraction game, brought back so i can play it solo. game preservation + reverse engineering: fake lobby services, lua bot brains, a fake auction house for immersion.',
         note='"bro i have no idea how happy i\'m to be able to play this again, seriously." admin button: whale buys everything.',
         stack=['reverse engineering', 'lua', 'python']),
    dict(no='06', name='dungeonborned', status='in dev', threat=4, pay=68000, fixer='fixer: the throne room',
         what='first-person extraction crawler in godot 4.7. procedural moonlit castle ruin, built from a headless-blender kit. zero audio files: every sound is generated at boot.',
         note='patch notes: fixed permanent slow motion after blocking (hit-stop reset race).',
         stack=['godot 4.7', 'gdscript', 'blender py']),
    dict(no='07', name='throwdown', status='team toy', threat=1, pay=3, fixer='fixer: two engineers', url=SITE + '/#gig-07', label='play it on luizgodoy.dev',
         what='two engineers. one PR. loser reviews. rock paper scissors, 4-char pit codes, hidden simultaneous throws, best of 3.',
         note='type "throwdown" anywhere on luizgodoy.dev. loser reviews.',
         stack=['cloudflare worker', 'bun']),
    dict(no='08', name='local meeting copilot', status='private', threat=3, pay=7200, fixer='fixer: a 2-hour call',
         what='local-first meeting copilot that survives a 2-hour call. whisper on cpu, live suggestions, a glass hud, and notes written back to my obsidian vault. no electron. no local llm.',
         stack=['fastapi', 'faster-whisper', 'pipewire', 'sqlite']),
    dict(no='09', name='clizin', status='npm', threat=1, pay=1004, fixer='fixer: ur staged diff', url='https://github.com/LuizHGodoy/clizin', label='repo',
         what='ai commit messages from ur staged git diff, in portuguese. npx clizin and go. no more "teste" commits (i\'m guilty).',
         stack=['node', 'npm']),
    dict(no='10', name='claude-e2e', status='open source', threat=2, pay=2600, fixer='fixer: qa that never sleeps', url='https://github.com/LuizHGodoy/claude-e2e', label='repo',
         what='claude code plugin. /e2e drives a real browser over ur app: breakpoints, a11y, visual checks, screenshots and video as receipts.',
         stack=['claude code', 'agent-browser']),
]
CLASSIFIED = dict(name='zig moba engine',
                  what='u breached it, so here: a moba engine from scratch in zig. ecs on glfw + opengl 4.0, champions, towers, minions. layered platform / engine / framework / moba. 34 commits, zero shame.')
SIDE_GIGS = [('zig moba engine', 'ecs on glfw + opengl, from scratch'), ('grim', 'godot sword combo + goblin'),
             ('taskbar-dungeon', 'a crawler in ur taskbar'), ('cael', 'my hyprland sidebar ai, refuses rm -rf'),
             ('apenas-apps-porcaria', '"just crappy apps". tic-tac-toe, tanks')]

STATS = [('3,604', 'contributions / 12mo', ROSE), ('266', 'of 366 days active', PINE), ('116', 'best day (sep 5)', GOLD),
         ('16:00', 'busiest hour', ROSE), ('02–03', 'second spike. yeah.', GOLD), ('23', 'commits ever at 6am', PINE)]
HOURS = [126, 161, 222, 221, 38, 57, 23, 76, 52, 82, 134, 157, 204, 244, 271, 331, 347, 322, 292, 287, 260, 191, 104, 94]
MONTHS = [('oct', 37), ('nov', 195), ('dec', 273), ('jan', 120), ('feb', 179), ('mar', 309), ('apr', 265), ('may', 222),
          ('jun', 158), ('jul', 495), ('aug', 465), ('sep', 687), ('oct', 199)]
SPEC = [('os', 'cachyos + **hyprland** + caelestia shell'), ('palette', '**rose-pine**, pulled from my wallpaper (this readme too)'),
        ('langs', 'typescript, gdscript, python, rust, go, zig'), ('infra', 'one **cloudflare worker** + d1/do/kv/r2. always.'),
        ('agents', 'claude code crews, codex, local llms, headless blender'), ('online', 'github since 2018 · 69 followers'),
        ('side quests', 'pokemon tcg, cs2, anime, chess, dead games')]

COMMS = [('0x3f', 'games', 'this is fire, very nice game bro.'), ('0x51', 'design', 'yeah option D - cinematic is goated.'),
         ('0x6a', 'rig', 'what is cooking my cpu?'), ('0x7c', 'games', 'sweet can u do a feature to prank my friends real quick?'),
         ('0x8e', 'dead-game', 'oh fuck i was spawned dead in the match hahaha wtf happend?'),
         ('0x9b', 'dead-game', 'i have full legendary items equiped and got one shoted lmao.'),
         ('0xa4', 'dead-game', 'buy my itemmmmmmmmmsssssssss'), ('0xb2', 'bits', 'nah bro i loved Margin doodles holly that looks so good'),
         ('0xc7', 'hyprland', 'idk how to close windows with this config aaaaaaaaaaaa'),
         ('0xd0', 'this-site', 'how would u make it more impressive without making it flashy?')]


def main():
    OUT.mkdir(exist_ok=True)
    hero()
    cta()
    gigs_head()
    for i in range(0, len(GIGS), 2):
        pair = GIGS[i:i + 2]
        h = max(gig_card(g, i + j)[1] for j, g in enumerate(pair))
        for j, g in enumerate(pair):
            gig_card(g, i + j, h)[0].save(f'gig-{g["no"]}.svg', h)
    classified()
    side_gigs()
    profile()
    comms()
    touchdown()
    for f in sorted(OUT.glob('*.svg')):
        print(f'{f.name:16} {f.stat().st_size / 1024:6.1f} KB')


if __name__ == '__main__':
    main()
