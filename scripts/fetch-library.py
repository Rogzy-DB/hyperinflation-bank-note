#!/usr/bin/env python3
"""Fetch the Library from Plan B Network's open educational content into data/library.json.

    python3 scripts/fetch-library.py

Source: https://github.com/PlanB-Network/bitcoin-educational-content (resources/books/<id>/book.yml + en.yml),
licensed CC BY-SA 4.0. The descriptions are reused under that licence, with attribution on the site; the covers come
from the same repo (assets/cover_en.webp) into assets/library/<id>.webp. The list of books is ours: SHELVES below. The snapshot is committed,
so building the site never needs the network.
"""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = "https://raw.githubusercontent.com/PlanB-Network/bitcoin-educational-content/dev/resources/books"
PAGE = "https://planb.academy/en/resources/books"

SHELVES = [
    ("Hyperinflation and monetary history", [
        "when-money-dies", "fiat-money-inflation-in-france", "monetary-regimes-and-inflation-history-economic-and-political-relationships-second-edition",
        "this-time-is-different-eight-centuries-of-financial-folly", "lord-of-finance", "big-debt-crisis", "debt-the-first-5000-years",
        "the-mandibles", "hard-boiled-egg-index", "argentarius"]),
    ("What money is, and what breaks it", [
        "the-theory-of-money-and-credit", "what-has-government-done-to-our-money", "the-mystery-of-banking", "the-ethics-of-money-production",
        "money-sound-and-unsound", "honest-money", "how-is-fiat-money-possible", "the-creature-from-jekyll-island", "economics-in-one-lesson",
        "shelling-out-origins-money", "on-the-origins-of-money", "traictie-premiere-invention-monnoies", "human-action",
        "du-credit-et-des-banques"]),
    ("Fiat, and the way out", [
        "broken-money", "the-fiat-standard", "the-bitcoin-standard", "layered-money", "the-price-of-tomorrow", "gradually-then-suddenly",
        "resistance-money", "check-your-financial-privilege", "end-the-fed"]),
]
# which cases a book speaks to directly (shown on the case page)
CASES = {
    "when-money-dies": ["germany-1921-1923", "austria-1921-1922"],
    "lord-of-finance": ["germany-1921-1923"],
    "hard-boiled-egg-index": ["zimbabwe-2007-2009"],
    "monetary-regimes-and-inflation-history-economic-and-political-relationships-second-edition": ["germany-1921-1923", "hungary-1945-1946", "greece-1941-1944"],
}


# corrections to the upstream data (typos, punctuation); CC BY-SA allows changes, the site says they were made
FIXES = {
    "the-theory-of-money-and-credit": {"author": "Ludwig von Mises"},
    "fiat-money-inflation-in-france": {"title": "Fiat Money Inflation in France"},
    "monetary-regimes-and-inflation-history-economic-and-political-relationships-second-edition":
        {"title": "Monetary Regimes and Inflation: History, Economic and Political Relationships"},
    "this-time-is-different-eight-centuries-of-financial-folly": {"title": "This Time Is Different: Eight Centuries of Financial Folly"},
    "the-mandibles": {"title": "The Mandibles: A Family, 2029–2047"},
    "debt-the-first-5000-years": {"title": "Debt: The First 5,000 Years"},
    "how-is-fiat-money-possible": {"title": "How Is Fiat Money Possible?", "year": 1994},
    "gradually-then-suddenly": {"year": 2023},
    # years: the upstream file gives the edition, not the first publication (checked 2026-10-05)
    "hard-boiled-egg-index": {"year": 2019, "title": "Hard-Boiled Egg Index: Surviving Zimbabwe's Hyperinflation",
                              "description": "A Zimbabwean's first-hand account of living through the 2007–2009 hyperinflation."},
    "argentarius": {"year": 1933, "title": "Argentarius: Letters of a Bank Director to His Son"},
    "big-debt-crisis": {"title": "Big Debt Crises"},
    "the-price-of-tomorrow": {"title": "The Price of Tomorrow: Why Deflation Is the Key to an Abundant Future"},
}


# legal free editions, each opened and checked 2026-10-05 (research agent): linked, never re-hosted.
# Most Mises Institute files are free downloads but remain their copyright; licence noted where it is open.
FREE = {
    "fiat-money-inflation-in-france": {"url": "https://cdn.mises.org/Fiat%20Money%20Inflation%20in%20France_2.pdf", "format": "PDF", "note": "public domain; Mises Institute scan of the 1933 printing"},
    "the-theory-of-money-and-credit": {"url": "https://cdn.mises.org/files/2026-04/The-Theory-of-Money-and-Credit_5.pdf", "format": "PDF", "note": "Mises Institute; English translation by H. E. Batson"},
    "what-has-government-done-to-our-money": {"url": "https://cdn.mises.org/files/2024-08/What%20Has%20Government%20Done%20to%20Our%20Money%202024.pdf", "format": "PDF", "note": "Mises Institute, 2024 edition"},
    "the-mystery-of-banking": {"url": "https://cdn.mises.org/Mystery%20of%20Banking_2.pdf", "format": "PDF", "note": "Mises Institute, 2nd edition 2008"},
    "the-ethics-of-money-production": {"url": "https://cdn.mises.org/The%20Ethics%20of%20Money%20Production_2.pdf", "format": "PDF", "note": "Mises Institute, 2008"},
    "money-sound-and-unsound": {"url": "https://cdn.mises.org/Money%2C%20Sound%20and%20Unsound_2.pdf", "format": "PDF", "note": "Mises Institute, CC BY 3.0"},
    "honest-money": {"url": "https://cdn.mises.org/Honest%20Money%20second%20edition%202015.pdf", "format": "PDF", "note": "2nd edition 2015, CC BY-NC-ND 4.0"},
    "how-is-fiat-money-possible": {"url": "https://cdn.mises.org/rae7_2_3_3.pdf", "format": "PDF", "note": "Review of Austrian Economics 7(2), 1994, open access"},
    "economics-in-one-lesson": {"url": "https://fee.org/resources/economics-in-one-lesson/", "format": "web", "note": "FEE, the 1946/1948 text"},
    "shelling-out-origins-money": {"url": "https://nakamotoinstitute.org/library/shelling-out/", "format": "web", "note": "Satoshi Nakamoto Institute, redistribution granted by the author"},
    "on-the-origins-of-money": {"url": "https://cdn.mises.org/On%20the%20Origins%20of%20Money_5.pdf", "format": "PDF", "note": "public domain text (tr. C. A. Foley, 1892); Mises edition CC BY 3.0"},
    "traictie-premiere-invention-monnoies": {"url": "https://archive.org/details/bub_gb_KLkZAAAAYAAJ", "format": "PDF", "note": "public domain; Wolowski edition, Paris 1864 (also on Gallica)"},
    "human-action": {"url": "https://cdn.mises.org/files/2024-09/Human%20Action.pdf", "format": "PDF", "note": "Mises Institute re-issue of the 1949 first edition"},
    "du-credit-et-des-banques": {"url": "https://archive.org/details/ducrditetdesba00coquuoft", "format": "PDF", "note": "public domain; 1848 first edition"},
    "gradually-then-suddenly": {"url": "https://nakamotoinstitute.org/library/gradually-then-suddenly/table-of-contents/", "format": "web", "note": "free online at the Satoshi Nakamoto Institute"},
}


def tidy(desc):
    """upstream descriptions sometimes open with a stray quote ('Lord of Finance" by…'): drop unbalanced quotes."""
    if not desc:
        return desc
    if desc.count('"') % 2:
        desc = desc.replace('"', "")
    return desc.replace("Amous", "Ammous")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (hyperinflation-archive library fetch)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def get_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (hyperinflation-archive library fetch)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def page_ok(url):
    """planb.academy answers 200 with an empty shell for ANY unknown path: judge the page by its <title>."""
    m = re.search(r"<title>([^<]*)", get(url))
    return bool(m) and m.group(1).strip() != "Plan ₿ Academy"


def yml_field(text, key):
    """tiny reader for the flat YAML these files use: scalar, or a '|' block."""
    m = re.search(rf"^{key}:\s*(.*)$", text, re.M)
    if not m:
        return None
    v = m.group(1).strip()
    if v in ("|", ">", "|-", ">-"):
        lines, start = [], m.end()
        for ln in text[start:].splitlines()[1:]:
            if ln.startswith("  ") or not ln.strip():
                lines.append(ln.strip())
            else:
                break
        return re.sub(r"\s+", " ", " ".join(lines)).strip()
    return v.strip('"').strip("'")


def tags(text):
    m = re.search(r"^tags:\s*\n((?:\s+- .+\n)+)", text, re.M)
    return [t.strip()[2:].strip() for t in m.group(1).splitlines()] if m else []


def main():
    shelves = []
    for name, ids in SHELVES:
        books = []
        for bid in ids:
            try:
                meta, en = get(f"{RAW}/{bid}/book.yml"), get(f"{RAW}/{bid}/en.yml")
            except Exception as e:
                print(f"✗ {bid}: {e}")
                continue
            year = yml_field(en, "publication_year")
            books.append({
                "id": bid,
                "title": yml_field(en, "title"),
                "author": yml_field(meta, "author"),
                "year": int(year) if year and year.isdigit() else year,
                "level": yml_field(meta, "level"),
                "tags": tags(meta),
                "description": yml_field(en, "description"),
                # the page lives at <folder>-<uuid>; the folder alone serves an empty shell (with HTTP 200)
                "url": f"{PAGE}/{bid}-{yml_field(meta, 'id')}",
                "cases": CASES.get(bid, []),
            })
            books[-1].update(FIXES.get(bid, {}))
            cover = yml_field(en, "cover")
            if cover:
                dest = ROOT / "assets/library" / f"{bid}.webp"
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    dest.write_bytes(get_bytes(f"{RAW}/{bid}/assets/{cover}"))
                    from PIL import Image  # shrink: cards show them ~110 px wide, 2× for sharp screens
                    im = Image.open(dest)
                    im.thumbnail((300, 460))
                    im.save(dest, "WEBP", quality=82)
                books[-1]["cover"] = f"assets/library/{bid}.webp"
            if not page_ok(books[-1]["url"]):
                raise SystemExit(f"✗ {bid}: {books[-1]['url']} is not a book page (empty shell) — nothing written")
            books[-1]["description"] = tidy(books[-1]["description"])
            if bid in FREE:
                books[-1]["free"] = FREE[bid]
            print(f"✓ {bid}")
        shelves.append({"name": name, "books": books})
    out = {"source": "Plan B Network, bitcoin-educational-content (https://github.com/PlanB-Network/bitcoin-educational-content)",
           "licence": "Descriptions: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), Plan B Network contributors; "
                      "titles, names and stray punctuation corrected by the Hyperinflation Archive",
           "shelves": shelves}
    (ROOT / "data/library.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"{sum(len(s['books']) for s in shelves)} books → data/library.json")


if __name__ == "__main__":
    main()
