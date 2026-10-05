#!/usr/bin/env python3
"""Build the Hyperinflation Archive (v2) into dist/: every page rendered as complete static HTML.

    python3 scripts/build-site.py [--out dist]

Inputs: data/periods.json · data/eras.json · data/exchange-rates/*.json · data/books/*.json ·
content/<id>/info.md (exported from the knowledge base by export-knowledge.py) · site/style.css ·
assets/bills/{web,thumbnails}. No JavaScript is needed to read any page: charts are SVG drawn here,
the only script is the optional savings calculator.
"""
import csv
import html
import io
import json
import math
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / (sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "dist")
SITE = "https://hyperinflation.rogzy.org"
YEAR = 2026
E = html.escape
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
MON3 = [m[:3] for m in MONTHS]

PERIODS = json.loads((ROOT / "data/periods.json").read_text())["periods"]
ERAS = json.loads((ROOT / "data/eras.json").read_text())["eras"]
BY_ID = {p["id"]: p for p in PERIODS}
CHRONO = sorted(PERIODS, key=lambda p: (int(p["periodStart"]), int(p["periodEnd"])))
HYPER = [p for p in PERIODS if p.get("kind") != "chronic"]
NOTE_COUNT = sum(len(p["bills"]) for p in PERIODS)
ERA_OF = {i: e for e in ERAS for i in e["ids"]}
LIBRARY = json.loads((ROOT / "data/library.json").read_text()) if (ROOT / "data/library.json").exists() else {"shelves": []}
LIB_BOOKS = [b for s in LIBRARY["shelves"] for b in s["books"]]
PLANB_CREDIT = ('Books, covers and descriptions from <a href="https://github.com/PlanB-Network/bitcoin-educational-content">Plan B '
                'Network’s open educational content</a>, <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>, '
                'with titles, names and punctuation corrected.')
PLANB_THANKS = """<aside class="thanks" aria-label="Thanks"><p><strong>Thank you to Plan B Academy</strong> for collecting this open-source library.
We took it from their <a href="https://github.com/PlanB-Network/bitcoin-educational-content">repository</a>. Go further on
<a href="https://planb.academy/en">their website</a>, in <a href="https://planb.academy/en/resources/books">their full library</a>,
and with the free course <a href="https://planb.academy/en/courses/hyperinflation-case-studies-caa75343-ac90-4249-bcca-0e2e57c3a0f1">Hyperinflation Case Studies</a>.</p></aside>"""


def rates(pid):
    f = ROOT / "data/exchange-rates" / f"{pid}.json"
    return json.loads(f.read_text()) if f.exists() else None


def books(pid):
    f = ROOT / "data/books" / f"{pid}.json"
    return json.loads(f.read_text())["books"] if f.exists() else []


# ------------------------------------------------------------------ markdown (the small subset info.md uses)
def inline(s):
    s = E(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"(https?://[^\s<)]+)", r'<a href="\1">\1</a>', s)
    return s


def sections(md):
    out, cur = {}, None
    for ln in md.splitlines():
        m = re.match(r"^## (.+)", ln)
        if m:
            cur = m.group(1).strip()
            out[cur] = []
        elif cur is not None and not ln.startswith("<!--") and not ln.startswith("*H&K ="):
            out[cur].append(ln)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def block(text):
    res, items, para = [], [], []

    def flush():
        if para:
            res.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if items:
            res.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for ln in text.splitlines():
        if not ln.strip():
            flush()
        elif re.match(r"^- ", ln):
            if para:
                flush()
            items.append(ln[2:].strip())
        elif ln.startswith("  ") and items:
            items[-1] += " " + ln.strip()
        elif ln.startswith("|"):
            continue
        else:
            para.append(ln.strip())
    flush()
    return "\n".join(res)


def table(text):
    rows = [r for r in text.splitlines() if r.startswith("|")]
    if len(rows) < 3:
        return ""
    cells = lambda r: [c.strip() for c in r.strip().strip("|").split("|")]
    head = cells(rows[0])
    body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells(r)) + "</tr>" for r in rows[2:])
    return ('<div class="tablewrap" data-align="left"><table class="kf"><thead><tr>' +
            "".join(f"<th>{E(h)}</th>" for h in head) + f"</tr></thead><tbody>{body}</tbody></table></div>")


def timeline_items(text):
    items = []
    for ln in text.splitlines():
        m = re.match(r"^- \*\*(.+?)\*\* — (.+)", ln)
        if m:
            t = m.group(2)
            items.append([m.group(1), t[0].upper() + t[1:]])
        elif ln.startswith("  ") and items:
            items[-1][1] += " " + ln.strip()
    return items


def first_sentence(text):
    """the opening sentence; two when the first is a short label ("The reference case.")."""
    t = re.sub(r"\s+", " ", re.sub(r"\*\*|\*", "", text)).strip()
    parts = re.findall(r".+?[.!?](?=\s|$)", t)
    if not parts:
        return t
    return parts[0] if len(parts[0]) >= 60 or len(parts) == 1 else parts[0] + " " + parts[1].strip()


# ------------------------------------------------------------------ dates
def date_key(label):
    """'12 November 1923' → '1923-11-12' · 'mid-1922' → '1922-06-00' · '1914–1918' → '1914-00-00'."""
    y = re.search(r"(\d{4})", label)
    y = int(y.group(1)) if y else 0
    mo = 6 if "mid" in label.lower() else 0
    for i, name in enumerate(MONTHS):
        if re.search(rf"\b({name}|{name[:3]})\b", label):
            mo = i + 1
    d = re.match(r"^(\d{1,2}) ", label)
    return f"{y:04d}-{mo:02d}-{int(d.group(1)) if d else 0:02d}"


def bill_date(label):
    """the date printed on a note, from its label: '(26 Oct 1923)' / '(Harare 2008)' / '(1923)'."""
    m = re.search(r"\((?:[^()]*?)(\d{1,2} )?(" + "|".join(MON3) + r")?[a-z]* ?(\d{4})\)", label)
    if not m:
        m2 = re.search(r"(\d{4})", label)
        return (f"{m2.group(1)}-00-00", m2.group(1)) if m2 else (None, None)
    day, mon, yr = m.group(1), m.group(2), m.group(3)
    mo = MON3.index(mon) + 1 if mon else 0
    shown = " ".join(x for x in [day.strip() if day else None, mon, yr] if x)
    return f"{yr}-{mo:02d}-{int(day) if day else 0:02d}", shown


FACE_WORDS = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}


def face_value(label):
    m = re.match(r"^([\d,.]+)\s*(thousand|million|billion|trillion)?\b", label)
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return v * FACE_WORDS.get(m.group(2) or "", 1)


def peak_key(p):
    m = re.search(r"(" + "|".join(MONTHS) + r") (\d{4})", p.get("peakMonth", ""))
    return f"{m.group(2)}-{MONTHS.index(m.group(1)) + 1:02d}" if m else None


# ------------------------------------------------------------------ numbers
def fmt_rate(v):
    if v >= 1e15:
        e = int(math.floor(math.log10(v)))
        m = v / 10 ** e
        return f"{m:.1f}".rstrip("0").rstrip(".") + "×10" + str(e).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
    for n, w in ((1e12, "trillion"), (1e9, "billion"), (1e6, "million")):
        if v >= n:
            return f"{v / n:.3g} {w}"
    return f"{v:,.0f}" if v >= 100 else f"{v:,.3g}"


def axis_label(e):
    if e < 3:
        return f"{10 ** e:,}"
    if e < 6:
        return f"{10 ** e:,}"
    words = {6: "1 million", 7: "10 million", 8: "100 million", 9: "1 billion", 10: "10 billion", 11: "100 billion",
             12: "1 trillion", 13: "10 trillion", 14: "100 trillion"}
    return words.get(e, "10" + str(e).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")))


def usd(v):
    if v >= 10:
        return f"${v:,.0f}"
    if v >= 0.01:
        return f"${v:,.2f}"
    s = f"{v:.12f}".rstrip("0")
    return "$" + (s if s != "0." else "0")


def is_approx(er):
    return bool(er and "Approximate" in (er.get("notes") or ""))


# ------------------------------------------------------------------ SVG
INK, GRID, ACC, PAPER = "#121212", "#e2dfd6", "#d6411c", "#f7f6f2"
RAMP = ["#e8e4da", "#f3cfa8", "#ec9e66", "#df6b3b", "#c23b1f", "#6e1a10"]


def months_of(s):
    y, m = map(int, s.split("-")[:2])
    return y * 12 + m - 1


def rate_chart(p, er, note_marks, narrow=False):
    """wide = desktop; narrow = a phone-shaped copy with larger type (CSS shows one of the two)."""
    pts = er["dataPoints"]
    W, H, L, R, T, B = (380, 400, 74, 14, 26, 36) if narrow else (760, 360, 100, 22, 26, 40)
    fs = 13 if narrow else 12
    xs = [months_of(d["date"]) for d in pts]
    x0, x1 = min(xs), max(xs)
    if x1 == x0:
        x1 = x0 + 1
    lo = math.floor(math.log10(min(d["rate"] for d in pts)))
    hi = math.ceil(math.log10(max(d["rate"] for d in pts)))
    if hi == lo:
        hi += 1
    X = lambda mo: L + (mo - x0) / (x1 - x0) * (W - L - R)
    Y = lambda v: T + (1 - (math.log10(v) - lo) / (hi - lo)) * (H - T - B)
    step = max(1, math.ceil((hi - lo) / (5 if narrow else 7)))
    o = [f'<svg viewBox="0 0 {W} {H}" class="chart {"narrow" if narrow else "wide"}"{' aria-hidden="true"' if narrow else ''} role="img" aria-label="{E(er.get("unit", ""))}, logarithmic scale" font-family="Archivo, sans-serif">']
    for e in range(lo, hi + 1, step):
        y = Y(10 ** e)
        o.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>'
                 f'<text x="{L - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="{fs}" fill="{INK}" opacity=".75">{axis_label(e)}</text>')
    y0, y1 = x0 // 12, x1 // 12
    ystep = (1 if y1 - y0 <= 4 else 2 if y1 - y0 <= 10 else 5) if narrow else (1 if y1 - y0 <= 7 else 2 if y1 - y0 <= 14 else 5)
    for yr in range(y0 + (0 if x0 % 12 == 0 else 1), y1 + 1):
        if (yr - y0) % ystep:
            continue
        x = X(yr * 12)
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{T}" y2="{H - B}" stroke="{GRID}"/>'
                 f'<text x="{x + 4:.1f}" y="{H - B + 18}" font-size="{fs + 0.5}" fill="{INK}">{yr}</text>')
    line = " ".join(f"{X(months_of(d['date'])):.1f},{Y(d['rate']):.1f}" for d in pts)
    o.append(f'<polyline points="{line}" fill="none" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>')
    for d in pts:
        o.append(f'<circle cx="{X(months_of(d["date"])):.1f}" cy="{Y(d["rate"]):.1f}" r="2.2" fill="{INK}"><title>{d["date"]}: {fmt_rate(d["rate"])}</title></circle>')
    pk = peak_key(p)
    hit = next((d for d in pts if d["date"] == pk), None)
    if hit:
        x, y = X(months_of(pk)), Y(hit["rate"])
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{ACC}"/>'
                 f'<text x="{x - 9:.1f}" y="{y + 4:.1f}" text-anchor="end" font-size="12.5" font-weight="700" fill="{ACC}">Worst month</text>')
    rate_at = {d["date"]: d["rate"] for d in pts}
    for i, mo in note_marks:
        if mo in rate_at:
            x, y = X(months_of(mo)), Y(rate_at[mo])
            o.append(f'<a href="#note-{i}" aria-label="Banknote {i + 1}"><rect x="{x - 16:.1f}" y="{y - 16:.1f}" width="32" height="32" fill="transparent"/>'
                     f'<rect x="{x - 6:.1f}" y="{y - 5:.1f}" width="12" height="8" fill="{PAPER}" stroke="{INK}" stroke-width="1.3"/></a>')
    o.append("</svg>")
    return "\n".join(o)


def heat(pct):
    if pct is None:
        return RAMP[0]
    k = min(len(RAMP) - 1, max(1, int((math.log10(pct) - 1.6) / 3.4 * (len(RAMP) - 1)) + 1))
    return RAMP[k]


def timeline_svg():
    W, L, R, lane_h = 1100, 20, 20, 30
    yr0, yr1 = 1918, 2036
    X = lambda y: L + (y - yr0) / (yr1 - yr0) * (W - L - R)
    lanes, placed = [], []
    for p in CHRONO:
        s, e = int(p["periodStart"]), int(p["periodEnd"]) + 1
        end = X(e) + 8 + 7.4 * len(p["country"])
        for i, last in enumerate(lanes):
            if X(s) > last + 6:
                lanes[i] = end
                placed.append((p, i))
                break
        else:
            lanes.append(end)
            placed.append((p, len(lanes) - 1))
    H = 44 + lane_h * len(lanes) + 24
    o = [f'<svg viewBox="0 0 {W} {H}" class="timeline" role="img" aria-label="The {len(HYPER)} hyperinflations from 1921 to 2023 on one time axis" font-family="Archivo, sans-serif">']
    for dec in range(1920, 2030, 10):
        x = X(dec)
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="24" y2="{H - 20}" stroke="{GRID}"/>'
                 f'<text x="{x:.1f}" y="16" text-anchor="middle" font-size="12.5" fill="{INK}" opacity=".65">{dec}</text>')
    for p, lane in placed:
        s, e = int(p["periodStart"]), int(p["periodEnd"]) + 1
        y = 34 + lane * lane_h
        dash = ' stroke-dasharray="3 2"' if p.get("kind") == "chronic" else ""
        o.append(f'<a href="{p["id"]}/"><title>{E(p["country"])} {p["periodStart"]}–{p["periodEnd"]}: {E(p["peakInflation"])}</title>'
                 f'<rect x="{X(s):.1f}" y="{y}" width="{max(5, X(e) - X(s)):.1f}" height="20" rx="2" fill="{heat(p.get("peakMonthlyPct"))}" stroke="{INK}" stroke-opacity=".35"{dash}/>'
                 f'<text x="{X(e) + 6:.1f}" y="{y + 15}" font-size="13" fill="{INK}">{E(p["country"])}</text></a>')
    o.append("</svg>")
    return "\n".join(o)


# ------------------------------------------------------------------ page shell
FONTS = "https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400;62..125,600;62..125,800&family=IBM+Plex+Mono:wght@400;500&display=swap"


def shell(rel, title, desc, path, body, og_image="assets/bills/web/100_Trillion_Zimbabwe.jpg", jsonld=None, script=""):
    canon = f"{SITE}/{path}"
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Hyperinflation Archive">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE}/{og_image.replace(' ', '%20')}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml">
<link rel="alternate" type="text/plain" href="{rel}llms.txt" title="For language models">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<link rel="stylesheet" href="{rel}style.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
<a class="brand" href="{rel or './'}">Hyperinflation<span>/</span>Archive</a>
<nav class="main" aria-label="Main"><a href="{rel or './'}#timeline">Timeline</a><a href="{rel or './'}#cases">Cases</a><a href="{rel}library/">Library</a><a href="{rel}about/#data">Method</a><a href="{rel}about/">About</a></nav>
</div></header>
<main id="main">
{body}
</main>
<footer class="foot"><div class="wrap">
<p>Made by <a href="https://rogzy.org/">Rogzy</a> &amp; Luna · banknotes from David St-Onge’s collection, used with permission ·
<a href="https://github.com/Rogzy-DB/hyperinflation-bank-note">GitHub</a> · learn more with <a href="https://planb.academy">Plan B Academy</a></p>
<p>© {YEAR} Rogzy · code &amp; texts under the <a href="https://opensource.org/license/mit">MIT</a> licence · banknote images © David St-Onge, not covered by it ·
<a href="{rel}about/">About, data &amp; copyright</a> · educational, not financial advice</p>
</div></footer>
{script}
</body>
</html>
"""


# ------------------------------------------------------------------ home
def home():
    eras = []
    for era in ERAS:
        cards = []
        for pid in era["ids"]:
            p = BY_ID[pid]
            ch = p.get("kind") == "chronic"
            img = (f'<img src="assets/bills/thumbnails/{E(p["bills"][0].replace(".png", ".jpg"))}" alt="{E(p["billLabels"][p["bills"][0]])}" loading="lazy" width="300" height="150">'
                   if p["bills"] else '<span class="nothumb">No banknote in the collection yet</span>')
            cards.append(f"""<a class="card{' chronic' if ch else ''}" href="{pid}/"><div class="img">{img}</div>
<div class="tx"><h3>{E(p['country'])}</h3><span class="mono">{p['periodStart']}–{p['periodEnd']} · {E(p['currency'])}</span>
<span class="pk">{E(p['peakInflation'])}</span><span class="mono">{('worst month · ' + E(p['peakMonth'])) if not ch else 'contrast case: never 50% in a month'}</span></div></a>""")
        n = len(era["ids"])
        eras.append(f'<section class="era" aria-labelledby="era-{len(eras)}"><header><h2 id="era-{len(eras)}">{E(era["name"])}</h2>'
                    f'<span class="mono">{era["years"]} · {n} case{"s" if n > 1 else ""}</span></header><div class="cards" data-align="left">{"".join(cards)}</div></section>')
    body = f"""<div class="wrap">
<section class="hero">
 <p class="mono">1921 → 2023 · {len(HYPER)} hyperinflations · {NOTE_COUNT} banknotes · every figure sourced</p>
 <h1>A century of money <em>dying</em></h1>
 <p class="dek">Every major hyperinflation since 1921 on one line. Each bar is a crisis, its colour how bad the worst month got.
 Open one for the full case: the context, what happened, life during it, how it ended, the banknotes and the data.</p>
</section>
<div class="tl" id="timeline">{timeline_svg()}</div>
<div class="legend mono"><span>Worst month:</span>{''.join(f'<i style="background:{c}"></i>' for c in RAMP[1:])}<span>50% → 10¹⁶ % in one month</span><span>· dashed: never 50% (contrast)</span></div>
<div id="cases">{''.join(eras)}</div>
<section class="method" aria-label="How to read this site">
 <div><h3>What counts</h3><p>A hyperinflation starts in the month prices rise 50% or more (Cagan 1956). The worst month comes from Hanke &amp; Krus (2012) unless a case says otherwise. Turkey is a contrast case.</p></div>
 <div><h3>Every figure sourced</h3><p>Each case is written from a knowledge base where every number carries its source. What could not be verified is left out, not softened.</p></div>
 <div><h3>For study, and for your AI</h3><p>Every case has its data as <a href="data/all.json">JSON</a> and CSV, a citation, and the site has an <a href="llms.txt">llms.txt</a>. Quote it, check it, teach with it.</p></div>
</section>
</div>"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Hyperinflation Archive", "url": SITE + "/",
          "description": f"{len(HYPER)} hyperinflations since 1921 as sourced case studies, with {NOTE_COUNT} banknotes and data.",
          "author": {"@type": "Person", "name": "Rogzy", "url": "https://rogzy.org/"}, "license": "https://opensource.org/license/mit"}
    return shell("", "Hyperinflation Archive — a century of money dying",
                 f"Every major hyperinflation since 1921 as a sourced case study: context, history, banknotes and data. {len(HYPER)} cases, {NOTE_COUNT} banknotes.",
                 "", body, jsonld=ld)


# ------------------------------------------------------------------ case study
SECTION_TITLES = [("Causes", "context", "Context: why it happened"), ("Life during it", "life", "Life during it"),
                  ("The end", "end", "How it ended"), ("Where it stands", "now", "Where it stands"),
                  ("Lessons", "lessons", "Consequences &amp; lessons")]


def case(p, prev, nxt):
    pid = p["id"]
    S = sections((ROOT / "content" / pid / "info.md").read_text())
    er = None if p.get("hasExchangeRates") is False else rates(pid)
    approx = is_approx(er)
    rate_at = {d["date"]: d["rate"] for d in er["dataPoints"]} if er else {}
    chronic = p.get("kind") == "chronic"
    era = ERA_OF[pid]

    # banknotes: date, face value, what it bought that month (only from a series that is not approximate)
    notes = []
    for i, b in enumerate(p["bills"]):
        label = p["billLabels"][b]
        key, shown = bill_date(label)
        mo = key[:7] if key and key[5:7] != "00" else None
        face = face_value(label)
        worth = None
        if mo and mo in rate_at and face and not approx:
            worth = usd(face / rate_at[mo])
        notes.append(dict(i=i, file=b.replace(".png", ".jpg"), label=label, key=key, shown=shown, mo=mo, worth=worth))

    # key band
    k1 = (E(p["peakInflation"]), "prices in the worst month", E(p["peakMonth"])) if not chronic else ("&lt; 50%", "in every month", "chronic inflation, not a hyperinflation")
    k2 = (E(p["doubling"]), "for prices to double", "at the peak (Hanke &amp; Krus)") if p.get("doubling") else None
    k3 = (E(p["hkEpisode"]), "above 50% a month", "the hyperinflation itself") if p.get("hkEpisode") else None
    k4 = (str(len(p["bills"])) if p["bills"] else "None yet", "banknotes in the collection", E(p["currency"]))
    keys = [k for k in (k1, k2, k3, k4) if k]
    band = "".join(f'<div class="k"><b{" class=\"long\"" if len(re.sub("<[^>]+>|&[a-z]+;", "x", a)) > 12 else ""}>{a}</b><span>{b}</span><small>{c}</small></div>' for a, b, c in keys)

    summary = S.get("Summary", "")
    dek = first_sentence(summary)
    # the dek is the summary's first sentence: "In short" continues from the second, never repeats it
    flat = re.sub(r"\s+", " ", summary).strip()
    plain = re.sub(r"\*\*|\*", "", flat)
    rest_of_summary = flat
    if plain.startswith(dek):
        cut, n = 0, 0
        for i, ch in enumerate(flat):            # walk the marked-up text until len(dek) plain chars are consumed
            if flat.startswith("**", i) or (ch == "*"):
                continue
            n += 1
            if n == len(dek):
                cut = i + 1
                break
        rest_of_summary = flat[cut:].lstrip(" *").strip() or flat

    # what happened: events + notes on one line
    evs = [(date_key(d), "ev", d, t) for d, t in timeline_items(S.get("Timeline", ""))]
    evs += [(n["key"], "note", n["shown"], n) for n in notes if n["key"]]
    evs.sort(key=lambda e: e[0])
    story = []
    for _, typ, d, t in evs:
        if typ == "ev":
            story.append(f'<div class="ev"><div class="d">{E(d)}</div><div class="t">{inline(t)}</div></div>')
        else:
            n = t
            worth = f'<span class="worth">worth ≈ {n["worth"]} that month</span>' if n["worth"] else ""
            story.append(f"""<div class="ev note" id="note-{n['i']}"><div class="d">dated<br>{E(d)}</div><div class="t">
<img src="../assets/bills/web/{E(n['file'])}" alt="{E(n['label'])}" loading="lazy" width="1200" height="600"><div><b>{E(n['label'])}</b>{worth}</div></div></div>""")
    has_story = bool(evs)

    # chart + data
    chart_block = ""
    if er:
        marks = [(n["i"], n["mo"]) for n in notes if n["mo"]]
        chart_block = f"""<section class="s" aria-labelledby="h-curve"><h2 id="h-curve">The curve</h2>
<p>{E(er.get('unit', ''))}, logarithmic scale: each line up is many times the one below.{' The small squares are the banknotes, at the month dated on them.' if any(n['mo'] in rate_at for n in notes) else ''}</p>
{rate_chart(p, er, marks)}{rate_chart(p, er, marks, narrow=True)}
<p class="chart-note" data-align="left">{E(er.get('notes') or '')} Source: {E(', '.join(er.get('sources', [])))}.</p>
</section>"""
    elif p.get("hasExchangeRates") is False:
        chart_block = """<section class="s"><h2>The curve</h2><p>No exchange-rate chart for this case yet: no series we could source
month by month. The figures that matter are in the text and the key figures below, each with its source.</p></section>"""

    grid = "".join(f'<div class="c"><h2 id="{a}">{t}</h2>{block(S[src])}</div>' for src, a, t in SECTION_TITLES if S.get(src))

    calc = ""
    script = ""
    if er and not approx and len(er["dataPoints"]) >= 5:
        pts = er["dataPoints"]
        last = pts[-1]
        opts = "".join(f'<option value="{d["date"]}">{MONTHS[int(d["date"][5:7]) - 1]} {d["date"][:4]}</option>' for d in pts[:-1])
        first = pts[0]
        static = (f"Savings worth $1,000 in {MONTHS[int(first['date'][5:7]) - 1]} {first['date'][:4]}, kept in {E(p['currency'])}, "
                  f"were worth {usd(1000 * first['rate'] / last['rate'])} in {MONTHS[int(last['date'][5:7]) - 1]} {last['date'][:4]}.")
        calc = f"""<div class="calc"><label for="calc-from">Savings worth $1,000, kept in {E(p['currency'])} from</label>
<select id="calc-from">{opts}</select><p id="calc-out" aria-live="polite">{static}</p></div>"""
        script = """<script>
(function () {
  var R = %s, last = %s, cur = %s, sel = document.getElementById('calc-from'), out = document.getElementById('calc-out');
  if (!sel) return;
  function usd(v) { if (v >= 10) return '$' + Math.round(v).toLocaleString('en-US'); if (v >= 0.01) return '$' + v.toFixed(2);
    var s = v.toFixed(12).replace(/0+$/, ''); return '$' + (s === '0.' ? '0' : s); }
  sel.addEventListener('change', function () {
    out.textContent = 'Savings worth $1,000 in ' + sel.options[sel.selectedIndex].text + ', kept in ' + cur + ', were worth ' +
      usd(1000 * R[sel.value] / R[last.date]) + ' in ' + last.label + '.';
  });
})();
</script>""" % (json.dumps({d["date"]: d["rate"] for d in pts}),
                json.dumps({"date": last["date"], "label": f"{MONTHS[int(last['date'][5:7]) - 1]} {last['date'][:4]}"}),
                json.dumps(p["currency"]))

    data_rows = "".join(f"<tr><td>{d['date']}</td><td>{fmt_rate(d['rate'])}</td></tr>" for d in er["dataPoints"]) if er else ""
    data_table = f'<details><summary>The series, point by point</summary><div class="tablewrap" data-align="left"><table class="data"><tr><th>Month</th><th>{E(er.get("tooltipUnit") or "per $")}</th></tr>{data_rows}</table></div></details>' if er else ""
    downloads = [f'<a href="../data/{pid}.json">Case data (JSON)</a>']
    if er:
        downloads.append(f'<a href="../data/{pid}.csv">Series (CSV)</a>')
    if p["bills"]:
        downloads.append(f'<a href="../downloads/{pid}.zip">Banknotes (ZIP)</a>')
    title_plain = f"{p['country']} {p['periodStart']}–{p['periodEnd']}"
    cite = (f"“{E(title_plain)}”, <em>Hyperinflation Archive</em>, {SITE.replace('https://', '')}/{pid}/ ({YEAR}). "
            f"Figures: Hanke &amp; Krus (2012) and the sources listed below.")

    lib = [b for b in LIB_BOOKS if pid in b.get("cases", [])]
    reading = (f'<section class="s" aria-labelledby="h-read"><h2 id="h-read">Further reading</h2><div class="books" data-align="left">'
               + "".join(book_card(b, "../") for b in lib) + f'</div><p class="mono">More in the <a href="../library/">Library</a>. {PLANB_CREDIT}</p></section>'
               + "".join(book_modal(b, "../") for b in lib)) if lib else ""
    bk = books(pid)
    books_html = ""
    if bk:
        books_html = '<h3>Books</h3><ul>' + "".join(
            f'<li><em>{E(b["title"])}</em>, {E(b["author"])} ({b["year"]}). {E(b["description"])}</li>' for b in bk) + "</ul>"
    gallery = "".join(f"""<figure id="plate-{n['i']}"><img src="../assets/bills/web/{E(n['file'])}" alt="{E(n['label'])}" loading="lazy" width="1200" height="600">
<figcaption><b>{E(n['label'])}</b>{f'<span class="worth">worth ≈ {n["worth"]} that month</span>' if n['worth'] else ''}</figcaption></figure>""" for n in notes)
    gallery_block = (f'<section class="s" aria-labelledby="h-notes"><h2 id="h-notes">The banknotes</h2>'
                     f'<div class="gallery" data-align="left">{gallery}</div></section>') if notes else \
        '<section class="s"><h2>The banknotes</h2><p>No banknote from this case in the collection yet.</p></section>'

    kind = "Chronic inflation" if chronic else "Hyperinflation"
    body = f"""<div class="wrap chead">
 <p class="mono"><a href="../#cases">Cases</a> / {E(era['name'])} / {E(p['country'])}</p>
 <h1>{E(p['country'])}<br>{p['periodStart']}–{p['periodEnd']}</h1>
 <p class="dek">{inline(dek)}</p>
 {'<span class="badge">Contrast case: never 50% in a month, so not a hyperinflation</span>' if chronic else ''}
</div>
<div class="band" role="list" aria-label="Key figures"><div class="wrap">{band}</div></div>
<div class="wrap">
<p class="reform"><b>Currency reform:</b> {E(p['currencyReform'])} · <b>Cause:</b> {E(p['cause'])} · <b>Resolution:</b> {E(p['resolution'])}</p>
<section class="s prose" aria-labelledby="h-short"><h2 id="h-short">In short</h2>{block(rest_of_summary)}</section>
{chart_block}
{f'<section class="s" aria-labelledby="h-story"><h2 id="h-story">What happened</h2><p>The events in order{", with the banknotes at the date on them" if notes else ""}.</p><div class="story">{"".join(story)}</div></section>' if has_story else ''}
{f'<section class="s"><div class="grid2">{grid}</div></section>' if grid else ''}
{gallery_block}
<section class="s" aria-labelledby="h-data"><h2 id="h-data">The data</h2>
{calc}
{table(S.get('Key figures', ''))}
{data_table}
<div class="dl">{''.join(downloads)}</div>
<div class="cite"><span class="mono">Cite this case</span><br>{cite}</div>
</section>
<section class="s" aria-labelledby="h-src"><h2 id="h-src">Sources</h2>{block(S.get('Sources', '')).replace('<ul>', '<ol class="src">').replace('</ul>', '</ol>')}
<p class="mono">H&amp;K = Hanke, S. H. &amp; Krus, N. (2012), <em>World Hyperinflations</em>, Cato Institute Working Paper no. 8.</p>{books_html}</section>
{reading}
<nav class="prevnext" aria-label="Other cases">{f'<a href="../{prev["id"]}/">← {E(prev["country"])} {prev["periodStart"]}</a>' if prev else '<span></span>'}{f'<a href="../{nxt["id"]}/">{E(nxt["country"])} {nxt["periodStart"]} →</a>' if nxt else ''}</nav>
</div>"""
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": f"{title_plain}: {kind.lower()}",
          "description": dek, "url": f"{SITE}/{pid}/", "author": {"@type": "Person", "name": "Rogzy"},
          "license": "https://opensource.org/license/mit", "isPartOf": {"@type": "WebSite", "name": "Hyperinflation Archive", "url": SITE + "/"},
          "about": {"@type": "Event", "name": f"{kind} in {p['country']}", "startDate": p["periodStart"], "endDate": p["periodEnd"]}}
    og = f"assets/bills/web/{p['bills'][0].replace('.png', '.jpg')}" if p["bills"] else "assets/bills/web/100_Trillion_Zimbabwe.jpg"
    return shell("../", f"{title_plain} — {kind} — Hyperinflation Archive", dek, f"{pid}/", body, og_image=og, jsonld=ld,
                 script=script + (MODAL_JS if lib else ""))


def case_data(p):
    S = sections((ROOT / "content" / p["id"] / "info.md").read_text())
    er = None if p.get("hasExchangeRates") is False else rates(p["id"])
    keep = ["id", "country", "currency", "kind", "periodStart", "periodEnd", "peakInflation", "peakMonthlyPct", "peakMonth",
            "doubling", "hkEpisode", "currencyReform", "cause", "resolution"]
    return {
        **{k: p.get(k) for k in keep if p.get(k) is not None},
        "url": f"{SITE}/{p['id']}/",
        "summary": re.sub(r"\*\*|\*", "", S.get("Summary", "")).strip(),
        "timeline": [{"date": d, "event": re.sub(r"\*\*|\*", "", t)} for d, t in timeline_items(S.get("Timeline", ""))],
        "banknotes": [{"label": p["billLabels"][b], "image": f"{SITE}/assets/bills/web/{b.replace('.png', '.jpg').replace(' ', '%20')}"} for b in p["bills"]],
        "exchangeRates": ({"unit": er.get("unit"), "approximate": is_approx(er), "notes": er.get("notes"), "sources": er.get("sources"),
                           "points": er["dataPoints"]} if er else None),
        "sources": [re.sub(r"\*\*|\*", "", l[2:]).strip() for l in S.get("Sources", "").splitlines() if l.startswith("- ")],
        "licence": "Text and data: MIT (c) 2026 Rogzy. Banknote images (c) David St-Onge, not covered by the MIT licence.",
    }


# ------------------------------------------------------------------ library
def amazon(b):
    from urllib.parse import quote_plus
    return "https://www.amazon.com/s?k=" + quote_plus(f"{b['title']} {b.get('author') or ''}".strip()) + "&i=stripbooks"


def book_card(b, rel):
    """the card opens its pop-up (#book-<id>, pure CSS :target, so it works without JS); no per-book outbound
    link to Plan B until it has a full summary for each (Rogzy, 2026-10-05)."""
    meta = " · ".join(str(x) for x in (b.get("author"), b.get("year"), b.get("level")) if x)
    d = b.get("description") or ""
    head = d if len(d) <= 190 else d[:190].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    cover = (f'<img class="cover" src="{rel}{E(b["cover"])}" alt="" loading="lazy" width="110" height="165">'
             if b.get("cover") else '<span class="cover"></span>')
    tag = '<span class="tag-free">free ebook</span>' if b.get("free") else ""
    return (f'<a class="book{" has-free" if b.get("free") else ""}" href="#book-{b["id"]}" aria-haspopup="dialog">{cover}<div><h3>{E(b["title"])}</h3><p class="mono">{E(meta)}{tag}</p>'
            + (f"<p>{E(head)}</p>" if head else "") + '<span class="open">Read more</span></div></a>')


def book_modal(b, rel):
    meta = " · ".join(str(x) for x in (b.get("author"), b.get("year"), b.get("level")) if x)
    cover = f'<img class="cover" src="{rel}{E(b["cover"])}" alt="Cover of {E(b["title"])}" loading="lazy" width="200" height="300">' if b.get("cover") else ""
    desc = "".join(f"<p>{E(p)}</p>" for p in re.split(r"\n{2,}", b.get("description") or "") if p.strip())
    summary = f'<h4>Summary</h4><div class="summary">{b["summary"]}</div>' if b.get("summary") else ""
    cases = ""
    if b.get("cases"):
        cases = '<p class="mono">Cases on this site: ' + ", ".join(f'<a href="{rel}{c}/">{E(BY_ID[c]["country"])} {BY_ID[c]["periodStart"]}</a>' for c in b["cases"] if c in BY_ID) + "</p>"
    btns = [f'<a class="btn" href="{E(amazon(b))}" rel="nofollow noopener">Buy on Amazon</a>']
    if b.get("free"):
        btns.insert(0, f'<a class="btn free" href="{E(b["free"]["url"])}" rel="noopener">Free ebook ({E(b["free"].get("format", "online"))})</a>')
    return (f'<div class="modal" id="book-{b["id"]}" role="dialog" aria-modal="true" aria-labelledby="bt-{b["id"]}">'
            f'<a class="backdrop" href="#_" aria-label="Close" tabindex="-1"></a><div class="panel">'
            f'<a class="close" href="#_" aria-label="Close">×</a>{cover}<div class="body"><h3 id="bt-{b["id"]}">{E(b["title"])}</h3>'
            f'<p class="mono">{E(meta)}</p>{desc}{summary}{cases}<div class="dl">{"".join(btns)}</div>'
            + ('<p class="mono">Free edition: ' + E(b["free"].get("note", "")) + "</p>" if b.get("free") and b["free"].get("note") else "")
            + "</div></div></div>")


MODAL_JS = """<script>
// the pop-ups work with CSS alone (#book-…); this only adds Escape and keeps the address clean on close
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape' && location.hash.indexOf('#book-') === 0) location.hash = '_';
});
window.addEventListener('hashchange', function () {
  if (location.hash === '#_') history.replaceState(null, '', location.pathname + location.search);
});
</script>"""


def library():
    shelves = "".join(f'<section class="era" aria-labelledby="sh-{i}"><header><h2 id="sh-{i}">{E(s["name"])}</h2>'
                      f'<span class="mono">{len(s["books"])} books</span></header><div class="books" data-align="left">'
                      + "".join(book_card(b, "../") for b in s["books"]) + "</div></section>"
                      for i, s in enumerate(LIBRARY["shelves"]))
    body = f"""<div class="wrap chead"><p class="mono"><a href="../">Home</a> / Library</p><h1>The<br>Library</h1>
<p class="dek">The books to go further: hyperinflations told by those who studied them, what money is and what breaks it, and the way out.</p></div>
<div class="wrap lib">{PLANB_THANKS}
<p class="filter mono"><input type="checkbox" id="only-free"><label for="only-free">Free ebook only ({sum(1 for b in LIB_BOOKS if b.get("free"))})</label></p>
{shelves}<p class="mono">{PLANB_CREDIT}</p></div>
{"".join(book_modal(b, "../") for b in LIB_BOOKS)}"""
    return shell("../", "Library — Hyperinflation Archive",
                 "Books on hyperinflation, money and the way out, from Plan B Academy's library.", "library/", body, script=MODAL_JS)


# ------------------------------------------------------------------ about, 404, llms.txt, sitemap
def about():
    body = f"""<div class="wrap chead"><p class="mono"><a href="../">Home</a> / About</p><h1>About, data<br>&amp; copyright</h1>
<p class="dek">How the figures are measured, where they come from, who owns what, and what this site does not claim.</p></div>
<div class="wrap prose">
<h2 id="copyright">Copyright &amp; licence</h2>
<ul>
<li><strong>Site, code and texts:</strong> © {YEAR} Rogzy, under the <a href="https://github.com/Rogzy-DB/hyperinflation-bank-note/blob/main/LICENSE">MIT licence</a>. Reuse them, commercially too, as long as you keep the copyright and licence notice.</li>
<li><strong>Banknote images:</strong> scans from <strong>David St-Onge</strong>’s collection, shown with his permission. They are <strong>not</strong> covered by the MIT licence: the downloads are for personal and educational use; any other reuse needs his permission.</li>
<li><strong>The banknote designs</strong> belong to the central banks and governments that issued them. Almost all were withdrawn long ago; a few recent ones (Lebanon 2021, Venezuela 2020) may still be legal tender and are shown for history and education, not for reproduction.</li>
<li><strong>Library:</strong> books, covers and descriptions from <a href="https://github.com/PlanB-Network/bitcoin-educational-content">Plan B Network’s open educational content</a> (CC BY-SA 4.0); the book covers belong to their publishers.</li>
<li><strong>Third parties:</strong> fonts from Google Fonts (Archivo, IBM Plex Mono).</li>
</ul>
<h2 id="data">How the data works</h2>
<h3>What counts as a hyperinflation</h3>
<p>Phillip Cagan’s definition (1956), the one most economists use: a hyperinflation <strong>begins in the month prices rise 50% or more</strong> and ends when the monthly rate falls below 50% and stays there for at least a year. 50% a month is about 13,000% a year. The archive holds <strong>{len(HYPER)} hyperinflations</strong> and one <strong>contrast case</strong>, Turkey 1990–2005: decades of high inflation, never 50% in a month.</p>
<h3>Worst month</h3>
<p>The highest price rise in a <strong>single month</strong>, from the reference table of Hanke &amp; Krus (<em>World Hyperinflations</em>, 2012) unless a case says otherwise. Never an annual rate: mixing the two makes cases impossible to compare. The exceptions are named on their pages: Venezuela (National Assembly estimate) and Lebanon (an <em>implied</em> rate, inferred by Steve Hanke from the black-market exchange rate).</p>
<h3>Doubling time and dates</h3>
<p>“For prices to double” is the number of days (or hours) prices took to double at the worst month’s pace (Hanke &amp; Krus). The years in a case’s title cover the wider crisis; “above 50% a month” gives the months of the hyperinflation itself.</p>
<h3>The curves</h3>
<ul>
<li>How many units of the currency one US dollar bought, on a <strong>logarithmic scale</strong> and a true time axis.</li>
<li>When a currency was redenominated, later values are <strong>converted back into the original unit</strong>, so removing zeros never looks like a recovery. The note under each curve says so.</li>
<li>Many historical series exist only as scattered figures. Curves built from them are marked <strong>approximate</strong>: they show the shape, not exact values. The figures to quote are in the text, each with its source. Where no trustworthy series exists (Angola, the Philippines, Bolivia, Soviet Russia), there is no curve rather than a guess.</li>
<li>“Worth ≈ $X that month” under a banknote divides its face value by that month’s average rate, and is shown only where the series is not approximate. Within a month of hyperinflation the rate could move several times over.</li>
</ul>
<h3>Banknotes and histories</h3>
<p>Each banknote label is read off the note: denomination and the date printed on it. Each history is written from a knowledge base where every figure carries its source; anything that could not be verified is left out of the page.</p>
<h3>Data for reuse, and for language models</h3>
<p>Every case has a JSON file (figures, timeline, banknotes, series, sources) and a CSV of its series; <a href="../data/all.json">all.json</a> holds every case. <a href="../llms.txt">llms.txt</a> describes the site for AI assistants. Please cite the case page.</p>
<h3>Found an error?</h3>
<p>Historical figures differ between sources and we will have made mistakes. <a href="https://github.com/Rogzy-DB/hyperinflation-bank-note/issues">Open an issue on GitHub</a> with the page, the figure and your source.</p>
<h2 id="sources">Main sources</h2>
<ul>
<li>Hanke, S. H. &amp; Krus, N. (2012), <em>World Hyperinflations</em>, Cato Institute Working Paper no. 8: episodes, worst months, doubling times.</li>
<li>Cagan, P. (1956), “The Monetary Dynamics of Hyperinflation”, in M. Friedman (ed.), <em>Studies in the Quantity Theory of Money</em>.</li>
<li>Hanke, S. H. (2020), “Lebanon Hyperinflates”, Cato Institute.</li>
<li>Wikipedia articles on each currency and crisis, cited on each case with the date they were read.</li>
<li>Fergusson, A. (1975), <em>When Money Dies</em>; Bresciani-Turroni, C. (1931, English translation 1937), <em>The Economics of Inflation</em>.</li>
</ul>
<h2 id="disclaimer">Disclaimer</h2>
<ul>
<li>This site is <strong>educational</strong>. It is not financial, investment, legal or tax advice, and nothing on it predicts what any currency will do.</li>
<li>Figures are given as reported by the cited sources, which sometimes disagree; we pick one, name it, and note serious disagreements. Provided as is, without warranty (MIT licence).</li>
<li>The banknotes are historical items shown for study. They are not for sale here, and almost all of them stopped being money long ago.</li>
<li><strong>Privacy:</strong> no account, no cookies, no analytics. Fonts load from Google Fonts, which sees your IP address like any web request.</li>
</ul>
</div>"""
    return shell("../", "About, data & copyright — Hyperinflation Archive",
                 "How the Hyperinflation Archive measures and sources its figures, copyright, and disclaimer.", "about/", body)


def notfound():
    body = """<div class="wrap chead"><h1>Page not<br>found</h1><p class="dek">This page does not exist, or it moved when the archive was rebuilt.
<a href="/">Start from the timeline</a>.</p></div>"""
    return shell("/", "Not found — Hyperinflation Archive", "Page not found.", "404.html", body)


def llms():
    lines = [f"# Hyperinflation Archive", "",
             f"> {len(HYPER)} hyperinflations since 1921 (and one contrast case), each as a sourced case study: context, chronology, life during it, "
             "how it ended, consequences, banknotes and data. Worst month = highest single-month price rise, from Hanke & Krus (2012) "
             "unless stated. Every figure on the site carries its source; unverified claims are left out.", "",
             "Licence: texts and data MIT (c) 2026 Rogzy; banknote images (c) David St-Onge, not covered. Please cite the case URL.", "",
             "## Data", f"- [All cases, one JSON]({SITE}/data/all.json)", f"- [Library: books on money and hyperinflation]({SITE}/library/)", f"- [Method and definitions]({SITE}/about/#data)", "", "## Cases"]
    for p in sorted(PERIODS, key=lambda p: -(p.get("peakMonthlyPct") or 0)):
        lines.append(f"- [{p['country']} {p['periodStart']}–{p['periodEnd']}]({SITE}/{p['id']}/): worst month {p['peakInflation'].replace(chr(160), ' ')}"
                     f" ({p['peakMonth']}); data: {SITE}/data/{p['id']}.json")
    return "\n".join(lines) + "\n"


def sitemap():
    urls = [f"{SITE}/", f"{SITE}/about/", f"{SITE}/library/"] + [f"{SITE}/{p['id']}/" for p in CHRONO]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
            "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")


def redirect(to):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Moved</title>
<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="canonical" href="{SITE}{to}">
<meta http-equiv="refresh" content="0; url={to}"><meta name="robots" content="noindex"></head>
<body><p>This page moved to <a href="{to}">{SITE}{to}</a>.</p>
<footer><p>© {YEAR} Rogzy · <a href="https://opensource.org/license/mit">MIT</a> licence</p></footer></body></html>
"""


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#121212"/>
<path d="M10 52 L26 46 L38 34 L46 20 L54 8" fill="none" stroke="#d6411c" stroke-width="7" stroke-linecap="square"/></svg>"""


# ------------------------------------------------------------------ build
def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data").mkdir(parents=True)
    (OUT / "downloads").mkdir()
    (OUT / "about").mkdir()
    (OUT / "library").mkdir()
    (OUT / "pages").mkdir()
    for sub in ("web", "thumbnails"):
        shutil.copytree(ROOT / "assets/bills" / sub, OUT / "assets/bills" / sub)
    if (ROOT / "assets/library").exists():
        shutil.copytree(ROOT / "assets/library", OUT / "assets/library")
    shutil.copy(ROOT / "site/style.css", OUT / "style.css")
    (OUT / "favicon.svg").write_text(FAVICON)
    (OUT / "index.html").write_text(home())
    (OUT / "about/index.html").write_text(about())
    (OUT / "library/index.html").write_text(library())
    (OUT / "404.html").write_text(notfound())
    allcases = []
    for i, p in enumerate(CHRONO):
        prev = CHRONO[i - 1] if i else None
        nxt = CHRONO[i + 1] if i + 1 < len(CHRONO) else None
        d = OUT / p["id"]
        d.mkdir()
        (d / "index.html").write_text(case(p, prev, nxt))
        cd = case_data(p)
        allcases.append(cd)
        (OUT / "data" / f"{p['id']}.json").write_text(json.dumps(cd, ensure_ascii=False, indent=1))
        er = None if p.get("hasExchangeRates") is False else rates(p["id"])
        if er:
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["month", er.get("tooltipUnit") or er.get("unit")])
            for pt in er["dataPoints"]:
                w.writerow([pt["date"], pt["rate"]])
            (OUT / "data" / f"{p['id']}.csv").write_text(buf.getvalue())
        if p["bills"]:
            with zipfile.ZipFile(OUT / "downloads" / f"{p['id']}.zip", "w", zipfile.ZIP_STORED) as z:
                for b in p["bills"]:
                    j = b.replace(".png", ".jpg")
                    z.write(ROOT / "assets/bills/web" / j, j)
                z.writestr("LICENCE.txt", "Banknote images (c) David St-Onge, used by the Hyperinflation Archive with his permission.\n"
                                          "Personal and educational use only; not covered by the site's MIT licence.\n")
        (OUT / "pages" / f"{p['id']}.html").write_text(redirect(f"/{p['id']}/"))
    (OUT / "pages" / "lebanon-2019-present.html").write_text(redirect("/lebanon-2019-2023/"))
    (OUT / "pages" / "about.html").write_text(redirect("/about/"))
    (OUT / "data" / "all.json").write_text(json.dumps({"site": SITE, "cases": allcases}, ensure_ascii=False))
    (OUT / "llms.txt").write_text(llms())
    (OUT / "sitemap.xml").write_text(sitemap())
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    n = sum(1 for _ in OUT.rglob("*.html"))
    print(f"built {OUT.relative_to(ROOT)}: {n} html, {len(CHRONO)} cases")


if __name__ == "__main__":
    main()
