"""Daily price pages: one page per product kind (precios/leche.html, precios/yerba.html, ...).

Every number comes straight from the saved daily files in data/. Only the products the index follows
(basket.csv) at the 4 index shops, only when they were in stock that day. Nothing is estimated.

  - Today's table: each product's price paid today, its list price when the shop marks a promo,
    and the price per litre or kilo worked out from the size printed in the product name.
  - "Same product in each shop" chart: the one barcode sold in the most shops, its price every day.
  - Change: the same products in the same shop, today against 7 days earlier (same weekday, so weekend
    promotions do not distort it), and today against their average of the base week (24 to 30 Oct),
    the same base as the index. Both are geometric means of the price ratios, like the index.

Run after compute_index.py. Writes precios/*.html and precios/index.html, and adds them to sitemap.xml.
"""
import csv, gzip, glob, html, json, math, os, re, sys
from collections import defaultdict
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "precios")
SITE = "https://lacanastaindex.com"
SHOPS = ["Carrefour", "Jumbo", "ChangoMas", "Dia"]
SHOP_NAME = {"Carrefour": "Carrefour", "Jumbo": "Jumbo", "ChangoMas": "ChangoMás", "Dia": "Día"}
SHOP_COLOR = {"Carrefour": "#2B3B5C", "Jumbo": "#2D7A57", "ChangoMas": "#D98A2B", "Dia": "#B2462B"}
BASE_WEEK = ("2026-10-24", "2026-10-30")
NO_REGULAR = {"Jumbo"}  # Jumbo's website gives no real list price

# slug, type_id, h1 es, h1 en, name es (for sentences), gender es (f/m/mp), name en, unit (l/kg)
KINDS = [
    ("leche", "leche", "Precio de la leche hoy", "Price of milk today", "la leche", "f", "milk", "l"),
    ("yerba", "yerba", "Precio de la yerba hoy", "Price of yerba mate today", "la yerba", "f", "yerba mate", "kg"),
    ("aceite-de-girasol", "aceite_girasol", "Precio del aceite de girasol hoy", "Price of sunflower oil today", "el aceite de girasol", "m", "sunflower oil", "l"),
    ("arroz", "arroz", "Precio del arroz hoy", "Price of rice today", "el arroz", "m", "rice", "kg"),
    ("fideos", "fideos", "Precio de los fideos hoy", "Price of dry pasta today", "los fideos", "mp", "dry pasta", "kg"),
    ("azucar", "azucar", "Precio del azúcar hoy", "Price of sugar today", "el azúcar", "m", "sugar", "kg"),
    ("harina", "harina_000", "Precio de la harina hoy", "Price of flour today", "la harina", "f", "flour", "kg"),
    ("cafe", "cafe", "Precio del café hoy", "Price of coffee today", "el café", "m", "coffee", "kg"),
    ("coca-cola", "coca_cola", "Precio de la Coca-Cola hoy", "Price of Coca-Cola today", "la Coca-Cola", "f", "Coca-Cola", "l"),
    ("dulce-de-leche", "dulce_de_leche", "Precio del dulce de leche hoy", "Price of dulce de leche today", "el dulce de leche", "m", "dulce de leche", "kg"),
]
# Sizes the name does not make clear enough to trust a price per litre or kilo.
SIZE_UNSURE = {"7790742348203"}  # "2sachet 1lt ... x 2": one litre or two? left out

MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
DIA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
DAY = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

SIZE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|kilo|grs|gr|g|lts|lt|l|ml|cc)\b", re.I)


def size_of(name):
    """(amount, 'l' or 'kg') from the last size written in the name, or None."""
    m = SIZE_RE.findall(name)
    if not m:
        return None
    n, u = m[-1]
    n = float(n.replace(",", "."))
    u = u.lower()
    if u in ("kg", "kilo"):
        return (n, "kg")
    if u in ("g", "gr", "grs"):
        return (n / 1000, "kg")
    if u in ("l", "lt", "lts"):
        return (n, "l")
    return (n / 1000, "l")  # ml, cc


def d_es(d, weekday=False):
    s = f"{d.day} de {MES[d.month-1]} de {d.year}"
    return f"{DIA[d.weekday()]} {s}" if weekday else s


def d_en(d, weekday=False):
    s = f"{d.day} {MON[d.month-1]} {d.year}"
    return f"{DAY[d.weekday()]} {s}" if weekday else s


def money(x, lang):
    """Whole pesos: $2.019 in Spanish, $2,019 in English."""
    s = f"{round(x):,}"
    return "$" + (s.replace(",", ".") if lang == "es" else s)


def pct(x, lang, sign=True):
    s = f"{x:+.1f}" if sign else f"{abs(x):.1f}"
    return (s.replace(".", ",") if lang == "es" else s) + "%"


def esc(s):
    return html.escape(str(s), quote=True)


def load():
    basket = list(csv.DictReader(open(os.path.join(ROOT, "basket.csv"), encoding="utf-8")))
    want = {}  # (shop, sku) -> basket row
    for r in basket:
        if r["shop"] in SHOPS:
            want[(r["shop"], r["sku_id"])] = r
    prices = defaultdict(dict)  # date -> (shop, sku) -> {"paid", "list", "name"}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "????-??-??.csv.gz"))):
        d = os.path.basename(f)[:10]
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                k = (r["shop"], r["sku_id"])
                if k not in want or k in prices[d] or r.get("available") != "True":
                    continue
                if (r.get("unit") or "").lower() != "un" or str(r.get("unit_multiplier")) not in ("1", "1.0"):
                    continue
                try:
                    paid = float(r["price"])
                except (TypeError, ValueError):
                    continue
                if paid <= 0:
                    continue
                lst = None
                if r["shop"] not in NO_REGULAR:
                    try:
                        lst = float(r["list_price"])
                    except (TypeError, ValueError):
                        lst = None
                prices[d][k] = {"paid": paid, "list": lst}
    return basket, want, prices


def geo(ratios):
    return (math.exp(sum(math.log(x) for x in ratios) / len(ratios)) - 1) * 100 if ratios else None


def build_kind(kind, basket, prices, dates):
    slug, tid, h1_es, h1_en, name_es, gender, name_en, unit = kind
    rows = [r for r in basket if r["type_id"] == tid and r["shop"] in SHOPS]
    keys = [(r["shop"], r["sku_id"]) for r in rows]
    ean_of = {(r["shop"], r["sku_id"]): r["ean"] for r in rows}
    names = defaultdict(list)
    for r in rows:
        names[r["ean"]].append(r["name"].strip())
    # One display name per barcode: the shortest shop name that still carries the size.
    disp, size = {}, {}
    for e, ns in names.items():
        with_size = [n for n in ns if size_of(n)] or ns
        disp[e] = re.sub(r"\s+", " ", min(with_size, key=lambda x: (len(x), x))).rstrip(".")
        sizes = {size_of(n) for n in ns}
        if e not in SIZE_UNSURE and len(sizes) == 1 and None not in sizes:
            s = sizes.pop()
            if s[1] == unit and s[0] > 0:
                size[e] = s[0]
    today = dates[-1]
    tday = date.fromisoformat(today)
    p = prices[today]
    items = []
    for k in keys:
        if k not in p:
            continue
        e = ean_of[k]
        v = p[k]
        promo = v["list"] is not None and v["list"] > v["paid"] + 0.5
        per = v["paid"] / size[e] if e in size else None
        items.append({"shop": k[0], "ean": e, "name": disp[e], "paid": v["paid"], "list": v["list"] if promo else None,
                      "per": per, "off": (1 - v["paid"] / v["list"]) * 100 if promo else None})
    items.sort(key=lambda x: (x["per"] is None, x["per"] or 0, x["paid"], x["shop"], x["ean"]))
    # Change against 7 days earlier, same products, same shop
    week_ago = (tday - timedelta(days=7)).isoformat()
    r7 = [p[k]["paid"] / prices[week_ago][k]["paid"] for k in keys if k in p and week_ago in prices and k in prices[week_ago]]
    # Against the base week average, same products
    base_days = [d for d in dates if BASE_WEEK[0] <= d <= BASE_WEEK[1]]
    rb = []
    for k in keys:
        if k not in p:
            continue
        b = [prices[d][k]["paid"] for d in base_days if k in prices[d]]
        if len(b) >= 4:
            rb.append(p[k]["paid"] / (sum(b) / len(b)))
    ch7, chb = geo(r7), geo(rb)
    # Same barcode in the most shops (needed in at least 2), most days with a price
    shops_by_ean = defaultdict(set)
    for k in keys:
        shops_by_ean[ean_of[k]].add(k[0])
    def days_with(e):
        return sum(1 for d in dates for k in keys if ean_of[k] == e and k in prices[d])
    ref = None
    cands = [e for e, s in shops_by_ean.items() if len(s) >= 2]
    if cands:
        ref = max(cands, key=lambda e: (len(shops_by_ean[e]), days_with(e), -int(e)))
    series = {}
    if ref:
        for k in keys:
            if ean_of[k] == ref:
                series[k[0]] = [(d, prices[d][k]["paid"]) for d in dates if k in prices[d]]
    # Same barcode in 2+ shops today: where is it cheapest
    same = defaultdict(dict)
    for it in items:
        same[it["ean"]][it["shop"]] = it["paid"]
    compare = []
    for e, by in same.items():
        if len(by) >= 2:
            lo = min(by.values())
            hi = max(by.values())
            cheapest = sorted(s for s, v in by.items() if v == lo)
            compare.append({"ean": e, "name": disp[e], "by": by, "cheapest": cheapest, "gap": (hi / lo - 1) * 100})
    compare.sort(key=lambda c: (-len(c["by"]), -c["gap"], c["ean"]))
    return {"slug": slug, "kind": kind, "today": today, "items": items, "ch7": ch7, "n7": len(r7), "chb": chb, "nb": len(rb),
            "week_ago": week_ago, "ref": ref, "ref_name": disp.get(ref), "series": series, "compare": compare,
            "n_products": len(keys), "unit": unit}


def nice_ticks(lo, hi, n=4):
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw), default=10 * mag)
    a = math.floor(lo / step) * step
    b = math.ceil(hi / step) * step
    return [a + i * step for i in range(int(round((b - a) / step)) + 1)]


def chart_svg(series, lang, narrow=False):
    if not series:
        return ""
    W, H, L, R, T, B = (360, 240, 56, 10, 12, 30) if narrow else (640, 260, 62, 14, 14, 34)
    alld = sorted({d for s in series.values() for d, _ in s})
    vals = [v for s in series.values() for _, v in s]
    lo, hi = min(vals), max(vals)
    pad = max((hi - lo) * 0.08, hi * 0.02)
    ticks = nice_ticks(lo - pad, hi + pad)
    lo, hi = ticks[0], ticks[-1]
    x = lambda d: L + (W - L - R) * (alld.index(d) / max(1, len(alld) - 1))
    y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{"Precio por día" if lang == "es" else "Price per day"}">']
    for v in ticks:
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#DCE4EA"/>'
                   f'<text x="{L-8}" y="{y(v)+4:.1f}" text-anchor="end">{money(v, lang)}</text>')
    step = max(1, math.ceil(len(alld) / (4 if narrow else 6)))
    for i, d in enumerate(alld):
        last = len(alld) - 1
        if (i % step == 0 and (i == last or last - i >= step * 0.6)) or i == last:
            dd = date.fromisoformat(d)
            lab = f"{dd.day}/{dd.month}"
            out.append(f'<text x="{x(d):.1f}" y="{H-10}" text-anchor="middle">{lab}</text>')
    for s in SHOPS:
        if s not in series:
            continue
        pts = series[s]
        c = SHOP_COLOR[s]
        path = " ".join(f"{'M' if i == 0 else 'L'}{x(d):.1f},{y(v):.1f}" for i, (d, v) in enumerate(pts))
        out.append(f'<path d="{path}" fill="none" stroke="{c}" stroke-width="2.5" stroke-linejoin="round"/>')
        d, v = pts[-1]
        out.append(f'<circle cx="{x(d):.1f}" cy="{y(v):.1f}" r="4" fill="{c}"/>')
    out.append("</svg>")
    return "".join(out)


def word(chg, gender, lang):
    if lang == "en":
        return "more expensive" if chg > 0 else "cheaper"
    up = {"f": "más cara", "m": "más caro", "mp": "más caros"}
    down = {"f": "más barata", "m": "más barato", "mp": "más baratos"}
    return (up if chg > 0 else down)[gender]


def join_shops(priced, best, lang):
    tied = sorted({i["shop"] for i in priced if abs(i["per"] - best["per"]) < 0.5}, key=SHOPS.index)
    names = [SHOP_NAME[x] for x in tied]
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + (" y " if lang == "es" else " and ") + names[-1]


def label_es(k):
    n = k[4].split(" ", 1)[1]
    return n[0].upper() + n[1:]


def esta(gender):
    return "están" if gender == "mp" else "está"


def page(K, others, chrome):
    slug, tid, h1_es, h1_en, name_es, gender, name_en, unit = K["kind"]
    tday = date.fromisoformat(K["today"])
    items = K["items"]
    per_u_es = "por litro" if unit == "l" else "por kilo"
    per_u_en = "per litre" if unit == "l" else "per kilo"
    priced = [i for i in items if i["per"] is not None]
    best = priced[0] if priced else (items[0] if items else None)
    if best and best["per"] is not None:
        tied = sorted({i["shop"] for i in priced if abs(i["per"] - best["per"]) < 0.5}, key=SHOPS.index)
    else:
        tied = [best["shop"]] if best else []
    shops_es = " y ".join([", ".join(SHOP_NAME[x] for x in tied[:-1]), SHOP_NAME[tied[-1]]] if len(tied) > 1 else [SHOP_NAME[x] for x in tied])
    shops_en = shops_es.replace(" y ", " and ")
    promos = sum(1 for i in items if i["list"])
    Name_es = name_es[0].upper() + name_es[1:]
    Name_en = name_en[0].upper() + name_en[1:]
    t_es = f"{h1_es}: dónde está más barata en Carrefour, Jumbo, ChangoMás y Día · La Canasta" if gender == "f" else \
           f"{h1_es}: dónde está más barato en Carrefour, Jumbo, ChangoMás y Día · La Canasta" if gender == "m" else \
           f"{h1_es}: dónde están más baratos en Carrefour, Jumbo, ChangoMás y Día · La Canasta"
    desc = (f"{h1_es} ({d_es(tday)}): precios de {len(items)} productos en Carrefour, Jumbo, ChangoMás y Día, "
            f"cuál conviene, promos y cuánto cambió en la semana. Datos diarios y abiertos de La Canasta.")
    # Summary sentences
    s_es, s_en = [], []
    if best:
        if best["per"] is not None:
            s_es.append(f"Hoy {name_es} más {'barata' if gender == 'f' else 'baratos' if gender == 'mp' else 'barato'} {per_u_es} {esta(gender)} en "
                        f"<strong>{shops_es}</strong>: {money(best['per'], 'es')} {per_u_es}" +
                        (f" ({esc(best['name'])} a {money(best['paid'], 'es')})." if len(tied) == 1 else ". Mirá la tabla para ver cada producto."))
            s_en.append(f"Today the cheapest {name_en} {per_u_en} is at <strong>{shops_en}</strong>: {money(best['per'], 'en')} {per_u_en}" +
                        (f" ({esc(best['name'])} at {money(best['paid'], 'en')})." if len(tied) == 1 else ". See the table for each product."))
    if K["ch7"] is not None:
        c = K["ch7"]
        wa = date.fromisoformat(K["week_ago"])
        if abs(c) < 0.05:
            s_es.append(f"Comparado con el {DIA[wa.weekday()]} {wa.day} de {MES[wa.month-1]}, los mismos productos en el mismo súper cuestan lo mismo.")
            s_en.append(f"Compared with {DAY[wa.weekday()]} {wa.day} {MON[wa.month-1]}, the same products in the same shop cost the same.")
        else:
            s_es.append(f"Comparado con el {DIA[wa.weekday()]} {wa.day} de {MES[wa.month-1]}, {name_es} {esta(gender)} "
                        f"<strong>{pct(c, 'es', False)} {word(c, gender, 'es')}</strong> en promedio (los mismos {K['n7']} productos en el mismo súper).")
            s_en.append(f"Compared with {DAY[wa.weekday()]} {wa.day} {MON[wa.month-1]}, {name_en} is "
                        f"<strong>{pct(c, 'en', False)} {word(c, gender, 'en')}</strong> on average (the same {K['n7']} products in the same shop).")
    if promos:
        s_es.append(f"{promos} de los {len(items)} productos de hoy {'tiene' if promos == 1 else 'tienen'} promo marcada.")
        s_en.append(f"{promos} of today's {len(items)} products {'has' if promos == 1 else 'have'} a marked promotion.")
    # Boxes
    def box(lab_es, lab_en, val_es, val_en, sub_es="", sub_en=""):
        return (f'<div class="pbox"><span class="plab"><span data-lang="es">{lab_es}</span><span data-lang="en">{lab_en}</span></span>'
                f'<strong><span data-lang="es">{val_es}</span><span data-lang="en">{val_en}</span></strong>'
                f'<span class="psub"><span data-lang="es">{sub_es}</span><span data-lang="en">{sub_en}</span></span></div>')
    boxes = []
    if best and best["per"] is not None:
        boxes.append(box(f"Lo más barato {per_u_es}", f"Cheapest {per_u_en}", money(best["per"], "es"), money(best["per"], "en"),
                         shops_es, shops_en))
    if K["ch7"] is not None:
        cls = "up" if K["ch7"] > 0.05 else "down" if K["ch7"] < -0.05 else "flat"
        boxes.append(box("En 7 días", "In 7 days", f'<span class="{cls}">{pct(K["ch7"], "es")}</span>', f'<span class="{cls}">{pct(K["ch7"], "en")}</span>',
                         f"{K['n7']} productos, mismo súper", f"{K['n7']} products, same shop"))
    if K["chb"] is not None:
        cls = "up" if K["chb"] > 0.05 else "down" if K["chb"] < -0.05 else "flat"
        boxes.append(box("Contra la semana base", "Against the base week", f'<span class="{cls}">{pct(K["chb"], "es")}</span>', f'<span class="{cls}">{pct(K["chb"], "en")}</span>',
                         "promedio del 24 al 30 de octubre", "average of 24 to 30 October"))
    boxes.append(box("Con promo hoy", "On promotion today", f"{promos} de {len(items)}", f"{promos} of {len(items)}",
                     "Jumbo no marca sus promos", "Jumbo does not mark its promotions"))
    # Today's table
    trs = []
    for it in items:
        promo_es = f'<span class="promo">-{pct(it["off"], "es", False).replace("%", "")}%</span> <s>{money(it["list"], "es")}</s>' if it["list"] else ""
        promo_en = f'<span class="promo">-{pct(it["off"], "en", False).replace("%", "")}%</span> <s>{money(it["list"], "en")}</s>' if it["list"] else ""
        per_es = money(it["per"], "es") + f"<i> {per_u_es}</i>" if it["per"] is not None else "—"
        per_en = money(it["per"], "en") + f"<i> {per_u_en}</i>" if it["per"] is not None else "—"
        trs.append(f'<tr><td>{esc(it["name"])}</td><td class="shopc">{SHOP_NAME[it["shop"]]}</td>'
                   f'<td class="r pricec"><strong><span data-lang="es">{money(it["paid"], "es")}</span><span data-lang="en">{money(it["paid"], "en")}</span></strong></td>'
                   f'<td class="r perc"><span data-lang="es">{per_es}</span><span data-lang="en">{per_en}</span></td>'
                   f'<td><span data-lang="es">{promo_es}</span><span data-lang="en">{promo_en}</span></td></tr>')
    # Same product, which shop
    cmp_rows = []
    for c in K["compare"][:8]:
        cells = "".join(
            (f'<td class="r{" best" if s in c["cheapest"] else ""}" data-shop="{SHOP_NAME[s]}"><span data-lang="es">{money(c["by"][s], "es")}</span><span data-lang="en">{money(c["by"][s], "en")}</span></td>'
             if s in c["by"] else f'<td class="r muted" data-shop="{SHOP_NAME[s]}">—</td>') for s in SHOPS)
        cmp_rows.append(f'<tr><td>{esc(c["name"])}</td>{cells}</tr>')
    # Chart legend
    legend = "".join(f'<span class="lkey" style="--c:{SHOP_COLOR[s]}">{SHOP_NAME[s]}</span>' for s in SHOPS if s in K["series"])
    first_day = date.fromisoformat(min(d for s in K["series"].values() for d, _ in s)) if K["series"] else None
    links = " · ".join(f'<a href="{o[0]}.html"><span data-lang="es">{label_es(o)}</span><span data-lang="en">{o[6][0].upper()+o[6][1:]}</span></a>' for o in others if o[0] != slug)
    q_es = f"¿Dónde {esta(gender)} más {'barata' if gender == 'f' else 'baratos' if gender == 'mp' else 'barato'} {name_es} hoy?"
    a_es = re.sub("<[^>]+>", "", s_es[0]) if s_es else ""
    q2_es = f"¿Cuánto aumentó {name_es} esta semana?" if gender != "mp" else f"¿Cuánto aumentaron {name_es} esta semana?"
    a2_es = re.sub("<[^>]+>", "", s_es[1]) if len(s_es) > 1 else ""
    ld = [
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "La Canasta", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Precios", "item": SITE + "/precios/"},
            {"@type": "ListItem", "position": 3, "name": h1_es, "item": f"{SITE}/precios/{slug}.html"}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q_es, "acceptedAnswer": {"@type": "Answer", "text": a_es}},
            {"@type": "Question", "name": q2_es, "acceptedAnswer": {"@type": "Answer", "text": a2_es}},
            {"@type": "Question", "name": "¿De dónde salen estos precios?", "acceptedAnswer": {"@type": "Answer", "text":
                "De las páginas web de Carrefour, Jumbo, ChangoMás y Día, recolectados todos los días por La Canasta, un índice independiente de precios de supermercado de la Argentina."}}]},
    ]
    body = f"""
<main class="container pp">
  <nav class="crumbs" aria-label="Ruta"><a href="../index.html">La Canasta</a> › <a href="index.html"><span data-lang="es">Precios</span><span data-lang="en">Prices</span></a> › <span data-lang="es">{esc(Name_es)}</span><span data-lang="en">{esc(Name_en)}</span></nav>
  <header class="pp-head">
    <h1><span data-lang="es">{h1_es}</span><span data-lang="en">{h1_en}</span></h1>
    <p class="lede"><span data-lang="es">En Carrefour, Jumbo, ChangoMás y Día. Precios del {d_es(tday, True)}.</span><span data-lang="en">At Carrefour, Jumbo, ChangoMás and Día. Prices of {d_en(tday, True)}.</span></p>
  </header>
  <div class="pboxes">{''.join(boxes)}</div>
  <p class="summary" data-lang="es">{' '.join(s_es)}</p>
  <p class="summary" data-lang="en">{' '.join(s_en)}</p>

  <section>
    <h2><span data-lang="es">Todos los precios de hoy</span><span data-lang="en">All of today's prices</span></h2>
    <p class="muted"><span data-lang="es">Ordenados del más barato al más caro {per_u_es}. El precio es el que se paga hoy en la web de cada súper; si hay promo marcada, al lado va el precio de lista.</span><span data-lang="en">Sorted from cheapest to dearest {per_u_en}. The price is what you pay today on each shop's website; when a promotion is marked, the list price is shown next to it.</span></p>
    <div class="tbl-wrap"><table class="ptable">
      <thead><tr><th><span data-lang="es">Producto</span><span data-lang="en">Product</span></th><th><span data-lang="es">Súper</span><span data-lang="en">Shop</span></th><th class="r"><span data-lang="es">Precio</span><span data-lang="en">Price</span></th><th class="r"><span data-lang="es">{per_u_es.capitalize()}</span><span data-lang="en">{per_u_en.capitalize()}</span></th><th>Promo</th></tr></thead>
      <tbody>{''.join(trs)}</tbody>
    </table></div>
  </section>

  <section>
    <h2><span data-lang="es">El mismo producto en cada súper</span><span data-lang="en">The same product in each shop</span></h2>
    <p class="muted"><span data-lang="es"><strong>{esc(K['ref_name'] or '')}</strong>, mismo código de barras, precio pagado cada día{f" desde el {first_day.day} de {MES[first_day.month-1]}" if first_day else ""}.</span><span data-lang="en"><strong>{esc(K['ref_name'] or '')}</strong>, same barcode, price paid each day{f" since {first_day.day} {MON[first_day.month-1]}" if first_day else ""}.</span></p>
    <div class="panel pchart"><div class="legend">{legend}</div><div class="wide">{chart_svg(K['series'], 'es')}</div><div class="narrow">{chart_svg(K['series'], 'es', narrow=True)}</div></div>
  </section>

  {"" if not cmp_rows else f'''<section>
    <h2><span data-lang="es">¿En qué súper conviene?</span><span data-lang="en">Which shop is cheaper?</span></h2>
    <p class="muted"><span data-lang="es">Productos idénticos (mismo código de barras) que hoy venden 2 súper o más. En verde, el más barato.</span><span data-lang="en">Identical products (same barcode) that 2 or more shops sell today. In green, the cheapest.</span></p>
    <div class="tbl-wrap"><table class="ptable cmp">
      <thead><tr><th><span data-lang="es">Producto</span><span data-lang="en">Product</span></th>{"".join(f'<th class="r">{SHOP_NAME[s]}</th>' for s in SHOPS)}</tr></thead>
      <tbody>{"".join(cmp_rows)}</tbody>
    </table></div>
  </section>'''}

  <section class="faq">
    <h2><span data-lang="es">Cómo se arma esta página</span><span data-lang="en">How this page is made</span></h2>
    <div data-lang="es"><p>Los precios salen de las páginas web de los cuatro súper, que La Canasta recolecta todos los días a la misma hora. Son los {K['n_products']} productos de este tipo que sigue el índice, solo los que tenían stock hoy. El precio {per_u_es} se calcula con el tamaño escrito en el nombre del producto. Los cambios comparan siempre los mismos productos en el mismo súper, como el índice. Jumbo no publica un precio de lista real, por eso sus promos no aparecen marcadas.</p>
    <p><a href="../metodo.html">Metodología completa</a> · <a href="../index.html">Índice de hoy</a> · <a href="../index.html#data">Descargar los datos</a></p></div>
    <div data-lang="en"><p>The prices come from the four shops' websites, which La Canasta collects every day at the same time. They are the {K['n_products']} products of this kind that the index follows, only those in stock today. The price {per_u_en} uses the size written in the product name. Changes always compare the same products in the same shop, like the index. Jumbo publishes no real list price, so its promotions are not marked.</p>
    <p><a href="../metodo.html">Full methodology</a> · <a href="../index.html">Today's index</a> · <a href="../index.html#data">Download the data</a></p></div>
  </section>

  <section>
    <h2><span data-lang="es">Otros precios de hoy</span><span data-lang="en">Other prices today</span></h2>
    <p class="others">{links}</p>
  </section>
</main>"""
    ld_html = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    return chrome(t_es, desc, f"precios/{slug}.html", body, ld_html)


def hub(Ks, chrome):
    tday = date.fromisoformat(Ks[0]["today"])
    cards = []
    for K in Ks:
        slug, tid, h1_es, h1_en, name_es, gender, name_en, unit = K["kind"]
        priced = [i for i in K["items"] if i["per"] is not None]
        best = priced[0] if priced else None
        per_es = "por litro" if unit == "l" else "por kilo"
        per_en = "per litre" if unit == "l" else "per kilo"
        c = K["ch7"]
        cls = "flat" if c is None or abs(c) < 0.05 else "up" if c > 0 else "down"
        cards.append(f'''<a class="card-link" href="{slug}.html"><h3><span data-lang="es">{label_es(K["kind"])}</span><span data-lang="en">{name_en[0].upper()+name_en[1:]}</span></h3>
<p>{f'<span data-lang="es">Desde {money(best["per"], "es")} {per_es} en {join_shops(priced, best, "es")}</span><span data-lang="en">From {money(best["per"], "en")} {per_en} at {join_shops(priced, best, "en")}</span>' if best else ''}</p>
<p>{'' if c is None else f'<span data-lang="es">En 7 días: <strong class="{cls}">{pct(c, "es")}</strong></span><span data-lang="en">In 7 days: <strong class="{cls}">{pct(c, "en")}</strong></span>'}</p></a>''')
    body = f"""
<main class="container pp">
  <nav class="crumbs" aria-label="Ruta"><a href="../index.html">La Canasta</a> › <span data-lang="es">Precios</span><span data-lang="en">Prices</span></nav>
  <header class="pp-head">
    <h1><span data-lang="es">Precios del súper hoy</span><span data-lang="en">Supermarket prices today</span></h1>
    <p class="lede"><span data-lang="es">Leche, yerba, aceite, arroz y más, en Carrefour, Jumbo, ChangoMás y Día. Precios del {d_es(tday, True)}, actualizados todos los días.</span><span data-lang="en">Milk, yerba, oil, rice and more, at Carrefour, Jumbo, ChangoMás and Día. Prices of {d_en(tday, True)}, updated every day.</span></p>
  </header>
  <div class="cards">{''.join(cards)}</div>
</main>"""
    return chrome("Precios del súper hoy en Argentina: leche, yerba, aceite y más · La Canasta",
                  f"Precios de hoy ({d_es(tday)}) de leche, yerba, aceite, arroz, fideos, azúcar, harina, café, Coca-Cola y dulce de leche en Carrefour, Jumbo, ChangoMás y Día. Actualizados todos los días.",
                  "precios/", body, "")


def make_chrome():
    """Head styles, top bar and footer taken from metodo.html, so the pages always match the site."""
    src = open(os.path.join(ROOT, "metodo.html"), encoding="utf-8").read()
    head_assets = src[src.index('<style>body{margin:0}'):src.index("</style>\n<header")] + "</style>"
    header = src[src.index('<header class="topbar">'):src.index("</header>") + len("</header>")]
    footer = src[src.index("<footer>"):src.index("</footer>") + len("</footer>")]
    def fix(s):  # links from a page one folder down
        return re.sub(r'(href|src)="(?!https?:|mailto:|#|\.\./|data:)([^"]+)"', r'\1="../\2"', s)
    head_assets, header, footer = fix(head_assets), fix(header), fix(footer)
    extra = """<style>
.pp { display: grid; gap: 2.6rem; padding-block: 2rem 0; max-width: 60rem; }
.pp section { display: grid; gap: 0.9rem; }
.pp h1 { font-size: clamp(2.3rem, 5.5vw, 3.6rem); }
.pp h2 { font-size: clamp(1.6rem, 3.5vw, 2.1rem); }
.pp-head { display: grid; gap: 0.7rem; }
.crumbs { display: block; font-size: 0.9rem; color: var(--muted); }
.crumbs a { color: var(--muted); }
.pboxes { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.8rem; }
.pbox { border: 1px solid var(--rule); border-radius: var(--radius); padding: 1rem 1.1rem; display: grid; gap: 0.2rem; align-content: start; min-width: 0; }
.pbox:first-child { background: var(--navy); color: #FFFFFF; border-color: var(--navy); }
.pbox:first-child .plab, .pbox:first-child .psub { color: rgba(255, 255, 255, 0.8); }
.plab { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
.pbox strong { font-size: clamp(1.6rem, 4vw, 2.1rem); font-weight: 700; line-height: 1.1; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.psub { font-size: 0.85rem; color: var(--muted); }
.summary { font-size: 1.12rem; max-width: 62ch; }
.ptable td:first-child { min-width: 12rem; }
.ptable td { white-space: normal; }
.ptable td.r { white-space: nowrap; }
.promo { display: inline-block; background: var(--sun); color: #FFFFFF; font-weight: 700; font-size: 0.78rem; border-radius: 6px; padding: 0.05rem 0.4rem; }
.ptable s { color: var(--muted); font-size: 0.85rem; white-space: nowrap; }
.cmp td.best { color: var(--down); font-weight: 700; }
.pchart { padding: 1rem 1rem 0.6rem; display: grid; gap: 0.6rem; }
.pchart svg { display: block; width: 100%; height: auto; }
.pchart .narrow { display: none; }
.perc i { display: none; font-style: normal; }
@media (max-width: 560px) {
  .pchart .wide { display: none; } .pchart .narrow { display: block; }
  .ptable thead { display: none; }
  .ptable, .ptable tbody, .ptable tr, .ptable td { display: block; }
  .ptable tr { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0.1rem 0.8rem; padding: 0.7rem 0.9rem; border-bottom: 1px solid var(--rule); }
  .ptable tr:last-child { border-bottom: 0; }
  .ptable td, .ptable td.r { border: 0; padding: 0; min-width: 0 !important; text-align: left; white-space: normal; }
  .ptable td:first-child { grid-column: 1 / -1; font-weight: 600; }
  .ptable .pricec, .ptable .perc + td { text-align: right; }
  .ptable .shopc, .ptable .perc { color: var(--muted); font-size: 0.9rem; }
  .perc i { display: inline; }
  .cmp td[data-shop] { display: flex; justify-content: space-between; gap: 0.5rem; }
  .cmp td[data-shop]::before { content: attr(data-shop); color: var(--muted); font-weight: 500; }
}
.legend { display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.88rem; color: var(--muted); }
.lkey { display: inline-flex; align-items: center; gap: 0.4rem; }
.lkey::before { content: ""; width: 1.1rem; height: 4px; border-radius: 2px; background: var(--c); }
.others { line-height: 2; max-width: none; }
.faq p + p { margin-top: 0.8rem; }
.pp .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.pp .card-link h3 { font-size: 1.5rem; }
@media (max-width: 820px) { .pboxes { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px) { .pp .cards { grid-template-columns: 1fr; } }
</style>"""
    script = """<script>
let lang = "es";
try { if (localStorage.getItem("lc-lang") === "en") lang = "en"; } catch (e) {}
function setLang(l) {
  lang = l; document.documentElement.lang = l;
  document.getElementById("btn-es").setAttribute("aria-pressed", String(l === "es"));
  document.getElementById("btn-en").setAttribute("aria-pressed", String(l === "en"));
  try { localStorage.setItem("lc-lang", l); } catch (e) {}
}
document.querySelectorAll(".lang button").forEach(b => b.addEventListener("click", () => setLang(b.dataset.set)));
setLang(lang);
</script>
<script src="../counter.js?v=5"></script>"""
    def chrome(title, desc, path, body, ld):
        url = f"{SITE}/{path}"
        return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, shrink-to-fit=no">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/la-canasta-logo/la-canasta-icon-512.png">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="canonical" href="{url}">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#2B3B5C">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="La Canasta">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" sizes="180x180" href="/app-icons/icon-180.png">
{ld}
{head_assets}
{extra}
{header}
{body}
{footer}
{script}
</body>
</html>
"""
    return chrome


def add_to_sitemap(paths, today):
    f = os.path.join(ROOT, "sitemap.xml")
    s = open(f, encoding="utf-8").read()
    changed = False
    for p in paths:
        url = f"{SITE}/{p}"
        block = re.search(r"<url>\s*<loc>" + re.escape(url) + r"</loc>.*?</url>", s, re.S)
        new = f"<url>\n    <loc>{url}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>daily</changefreq>\n  </url>"
        if block:
            if f"<lastmod>{today}</lastmod>" not in block.group(0):
                s = s[:block.start()] + new + s[block.end():]
                changed = True
        else:
            s = s.replace("</urlset>", "  " + new + "\n</urlset>")
            changed = True
    if changed:
        open(f, "w", encoding="utf-8").write(s)


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else OUT
    basket, want, prices = load()
    dates = sorted(d for d in prices if prices[d])
    if not dates:
        print("No data"); return
    chrome = make_chrome()
    os.makedirs(out, exist_ok=True)
    Ks = [build_kind(k, basket, prices, dates) for k in KINDS]
    for K in Ks:
        if not K["items"]:
            print("No prices today for", K["slug"]); continue
        open(os.path.join(out, K["slug"] + ".html"), "w", encoding="utf-8").write(page(K, KINDS, chrome))
        print(K["slug"], len(K["items"]), "prices", "7d", K["ch7"], "base", K["chb"], "ref", K["ref_name"])
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(hub(Ks, chrome))
    if out == OUT:
        add_to_sitemap(["precios/"] + [f"precios/{K['slug']}.html" for K in Ks if K["items"]], dates[-1])


if __name__ == "__main__":
    main()
