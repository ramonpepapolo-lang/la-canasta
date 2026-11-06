# La Canasta: turns the report numbers into short PDFs (2 pages at most), in Spanish and English.
#   Weekly:  index/semanas/AAAA-MM-DD.json      -> informes/semanas/AAAA-MM-DD-es.pdf / -en.pdf
#   Monthly: index/informes/AAAA-MM.json        -> informes/mensuales/AAAA-MM-es.pdf / -en.pdf
#            (only months marked "publishable" in index/informes/lista.json)
# Every number comes from those JSON files, which verify_index.py checks independently. Nothing is
# calculated here except wording. A PDF is only made again when its numbers change (informes/hashes.json).
# Needs Playwright with Chromium. These PDFs are never emailed.
#   python render_reports.py            render what is new or changed
#   python render_reports.py --all      render everything again
#   python render_reports.py --test DIR render the weekly JSON files in DIR into DIR (for checking)

import glob
import hashlib
import html
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_VERSION = "1"
NAVY, CELESTE, SUN, UP, DOWN, MUTED = "#2B3B5C", "#7FB1C6", "#D98A2B", "#C0392B", "#2E7D5B", "#6B7488"
SHOP = {"Carrefour": "Carrefour", "Jumbo": "Jumbo", "ChangoMas": "ChangoMás", "Dia": "Día"}
MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
       "noviembre", "diciembre"]
MONTH_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
            "November", "December"]
TYPE_ES = {"pan_lactal": "Pan lactal", "harina_000": "Harina", "arroz": "Arroz", "fideos": "Fideos secos",
           "pollo_entero": "Pollo entero", "asado": "Asado", "vacio": "Vacío", "nalga": "Nalga", "carne_picada": "Carne picada", "milanesa_carne": "Milanesas de carne", "cuadril": "Cuadril", "cortes_magros": "Bola de lomo, cuadrada y peceto", "bifes": "Bifes", "roast_paleta": "Roast beef y paleta", "yogur": "Yogur", "galletitas": "Galletitas", "suprema": "Suprema de pollo", "leche": "Leche", "manteca": "Manteca", "queso_cremoso": "Queso",
           "dulce_de_leche": "Dulce de leche", "huevos": "Huevos", "aceite_girasol": "Aceite", "papa": "Papa",
           "cebolla": "Cebolla", "tomate": "Tomate", "banana": "Banana", "manzana": "Manzana", "azucar": "Azúcar",
           "yerba": "Yerba mate", "cafe": "Café", "te": "Té", "mayonesa": "Mayonesa", "pure_tomate": "Puré de tomate",
           "coca_cola": "Gaseosa", "agua": "Agua", "cerveza": "Cerveza", "vino": "Vino", "papel_higienico": "Papel higiénico",
           "detergente": "Detergente", "lavandina": "Lavandina", "jabon_ropa": "Jabón para ropa", "shampoo": "Shampoo",
           "pasta_dental": "Pasta dental", "jabon_tocador": "Jabón de tocador"}


def esc(x):
    return html.escape(str(x))


def num(v, lang, dec=2):
    s = f"{abs(v):,.{dec}f}"
    if lang == "es":
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def pct(v, lang, dec=2):
    if v is None:
        return "s/d" if lang == "es" else "n/a"
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sign}{num(v, lang, dec)}%"


def money(v, lang):
    return "$" + num(v, lang, 0)


def color(v):
    return UP if (v or 0) > 0 else (DOWN if (v or 0) < 0 else MUTED)


def day_label(d, lang, year=False):
    y, m, dd = int(d[:4]), int(d[5:7]), int(d[8:])
    if lang == "es":
        return f"{dd} de {MES[m - 1]}" + (f" de {y}" if year else "")
    return f"{dd} {MONTH_EN[m - 1]}" + (f" {y}" if year else "")


def short_day(d, lang):
    m, dd = int(d[5:7]), int(d[8:])
    return f"{dd}/{m}"


# ---------- Charts (inline SVG) ----------
def line_chart(series, shade_from, lang, w=680, h=180):
    """Daily index, price paid and list price. Days from shade_from on are shaded (this week)."""
    if len(series) < 2:
        return ""
    vals = [p["paid"] for p in series] + [p["regular"] for p in series]
    lo, hi = min(vals), max(vals)
    pad = max(0.3, (hi - lo) * 0.15)
    lo, hi = lo - pad, hi + pad
    L, R, T, B = 46, 16, 14, 34
    X = lambda i: L + i * (w - L - R) / (len(series) - 1)
    Y = lambda v: T + (hi - v) * (h - T - B) / (hi - lo)
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="DM Sans" font-size="11">']
    first_now = next((i for i, p in enumerate(series) if p["date"] >= shade_from), None)
    if first_now is not None:
        x0 = X(first_now) - (X(1) - X(0)) / 2 if first_now > 0 else L
        out.append(f'<rect x="{x0:.1f}" y="{T}" width="{w - R - x0:.1f}" height="{h - T - B}" fill="{CELESTE}" opacity="0.16"/>')
        out.append(f'<text x="{w - R - 4}" y="{T + 13}" text-anchor="end" fill="{NAVY}" font-weight="700">'
                   f'{"Esta semana" if lang == "es" else "This week"}</text>')
    step = 0.5 if hi - lo < 4 else 1.0
    t = (int(lo / step) + 1) * step
    while t < hi:
        out.append(f'<line x1="{L}" x2="{w - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="#E3E7EE"/>')
        out.append(f'<text x="{L - 6}" y="{Y(t) + 4:.1f}" text-anchor="end" fill="{MUTED}">{num(t, lang, 1)}</text>')
        t += step
    for i, p in enumerate(series):
        out.append(f'<text x="{X(i):.1f}" y="{h - 12}" text-anchor="middle" fill="{MUTED}">{short_day(p["date"], lang)}</text>')
    for key, col, dash in (("regular", MUTED, "4 3"), ("paid", NAVY, "")):
        pts = " ".join(f"{X(i):.1f},{Y(p[key]):.1f}" for i, p in enumerate(series))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.4" stroke-dasharray="{dash}" stroke-linejoin="round"/>')
    for i, p in enumerate(series):
        out.append(f'<circle cx="{X(i):.1f}" cy="{Y(p["paid"]):.1f}" r="2.6" fill="{NAVY}"/>')
    out.append("</svg>")
    return "".join(out)


def bar_chart(rows, lang, w=680):
    """Horizontal bars around zero: rows = [(label, value)]."""
    if not rows:
        return ""
    m = max(1.0, max(abs(v) for _, v in rows))
    row_h, L, R = 18, 170, 16
    h = row_h * len(rows) + 8
    mid = L + (w - L - R) / 2
    half = (w - L - R) / 2 - 52  # room for the value label on each side
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="DM Sans" font-size="12">',
           f'<line x1="{mid}" x2="{mid}" y1="0" y2="{h}" stroke="#C9D1DE"/>']
    for i, (lab, v) in enumerate(rows):
        y = 4 + i * row_h
        bw = abs(v) / m * half
        x = mid if v >= 0 else mid - bw
        out.append(f'<text x="{L - 10}" y="{y + 15}" text-anchor="end" fill="{NAVY}">{esc(lab)}</text>')
        out.append(f'<rect x="{x:.1f}" y="{y + 4}" width="{max(bw, 1.5):.1f}" height="{row_h - 8}" rx="3" fill="{color(v)}" opacity="0.85"/>')
        tx = (mid + bw + 6) if v >= 0 else (mid - bw - 6)
        out.append(f'<text x="{tx:.1f}" y="{y + 15}" text-anchor="{"start" if v >= 0 else "end"}" fill="{color(v)}" font-weight="700">{pct(v, lang, 1)}</text>')
    out.append("</svg>")
    return "".join(out)


# ---------- Page frame ----------
def page(title_kind, title, subtitle, body, lang):
    fonts = "".join(
        f'@font-face{{font-family:"{fam}";src:url("file://{HERE}/videos/assets/{f}") format("woff2");font-weight:{wt}}}'
        for fam, f, wt in (("DM Serif Display", "dm-serif-display-latin-400-normal.woff2", 400),
                           ("DM Sans", "dm-sans-latin-400-normal.woff2", 400),
                           ("DM Sans", "dm-sans-latin-600-normal.woff2", 600),
                           ("DM Sans", "dm-sans-latin-700-normal.woff2", 700)))
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>
{fonts}
@page {{ size: A4; margin: 14mm 15mm 13mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: "DM Sans", Arial, sans-serif; color: {NAVY}; font-size: 10.2pt; line-height: 1.38; }}
h1 {{ font-family: "DM Serif Display", Georgia, serif; font-weight: 400; font-size: 21pt; line-height: 1.08; margin: 2mm 0 1mm; }}
h2 {{ font-family: "DM Serif Display", Georgia, serif; font-weight: 400; font-size: 14pt; margin: 4mm 0 1.5mm; }}
p {{ margin: 0 0 2mm; }}
.top {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid {NAVY}; padding-bottom: 2.5mm; }}
.top img {{ height: 9mm; }}
.kind {{ font-size: 8.5pt; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: {SUN}; }}
.sub {{ color: {MUTED}; font-size: 10pt; }}
.big {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; margin: 3mm 0 2.5mm; }}
.box {{ border: 1px solid #D9DFE8; border-radius: 3mm; padding: 3mm 4mm; }}
.box .l {{ font-size: 8.8pt; color: {MUTED}; font-weight: 600; }}
.box .v {{ font-family: "DM Serif Display", Georgia, serif; font-size: 24pt; line-height: 1.05; }}
.box .n {{ font-size: 8.6pt; color: {MUTED}; }}
.lead {{ font-size: 10.6pt; }}
.key {{ font-size: 8.6pt; color: {MUTED}; margin-top: -1mm; }}
.key b {{ display: inline-block; width: 7mm; height: 0; border-top: 2.4px solid {NAVY}; vertical-align: middle; margin: 0 1.5mm 0 0; }}
.key i {{ display: inline-block; width: 7mm; height: 0; border-top: 2.4px dashed {MUTED}; vertical-align: middle; margin: 0 1.5mm 0 4mm; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9.2pt; }}
th {{ text-align: left; font-size: 8pt; color: {MUTED}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; border-bottom: 1px solid #C9D1DE; padding: 1mm 1.5mm; }}
td {{ border-bottom: 1px solid #EEF1F5; padding: 1.2mm 1.5mm; vertical-align: top; }}
td.r, th.r {{ text-align: right; white-space: nowrap; }}
.two table {{ table-layout: fixed; font-size: 8.8pt; }}
.two th:nth-child(1) {{ width: 56%; }} .two th:nth-child(2) {{ width: 27%; }} .two th:nth-child(3) {{ width: 17%; }}
td.pn {{ line-height: 1.25; }}
.tag {{ font-size: 7.6pt; color: {MUTED}; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; }}
.note {{ background: #F3F6FA; border-left: 3px solid {CELESTE}; padding: 2.5mm 3.5mm; font-size: 9pt; margin-top: 4mm; }}
.foot {{ margin-top: 3mm; font-size: 8pt; color: {MUTED}; }}
.pb {{ break-before: page; }}
</style></head><body>
<div class="top"><img src="file://{HERE}/la-canasta-logo/la-canasta-logo-horizontal.svg" alt="La Canasta"><span class="kind">{esc(title_kind)}</span></div>
<h1>{esc(title)}</h1><p class="sub">{subtitle}</p>
{body}
</body></html>"""


# ---------- Weekly report ----------
def product_tag(p, lang):
    rp = p.get("regular_pct")
    if rp is None:
        return ""
    if abs(rp) < 1 and abs(p["pct"]) >= 3:
        return ("terminó una promoción" if p["pct"] > 0 else "empezó una promoción") if lang == "es" else \
               ("a promotion ended" if p["pct"] > 0 else "a promotion started")
    if abs(rp) >= 1:
        return (f"precio de lista {pct(rp, lang, 1)}") if lang == "es" else (f"list price {pct(rp, lang, 1)}")
    return ""


def product_rows(items, lang):
    rows = []
    for p in items:
        name = p["name"]
        if len(name) > 40:
            name = name[:38].rstrip() + "…"
        tag = product_tag(p, lang)
        rows.append(f'<tr><td class="pn">{esc(name)}<br><span class="tag">{esc(SHOP.get(p["shop"], p["shop"]))}'
                    f'{" · " + esc(tag) if tag else ""}</span></td>'
                    f'<td class="r">{money(p["before"], lang)}<br>→ {money(p["now"], lang)}</td>'
                    f'<td class="r" style="color:{color(p["pct"])};font-weight:700">{pct(p["pct"], lang, 1)}</td></tr>')
    return "".join(rows)


def weekly(w, lang):
    es = lang == "es"
    title = w["label_es"] if es else w["label_en"]
    prev = (f"{day_label(w['before_start'], lang)} al {day_label(w['before_end'], lang, True)}" if es
            else f"{day_label(w['before_start'], lang)} to {day_label(w['before_end'], lang, True)}")
    subtitle = (f"Informe semanal. Comparado con la semana anterior: {esc(prev)}. Precios online de Carrefour, Jumbo, ChangoMás y Día."
                if es else f"Weekly report. Compared with the week before: {esc(prev)}. Online prices from Carrefour, Jumbo, ChangoMás and Día.")
    paid, reg = w["paid"], w["regular"]
    diff = (paid or 0) - (reg or 0)
    pn, pb = w["promos_now"], w["promos_before"]
    promo_now = sum(v for v in pn.values() if v is not None)
    promo_before = sum(v for v in pb.values() if v is not None)

    # The summary, in plain words
    move = abs(paid or 0)
    if es:
        s1 = ("Los precios que se pagan en el súper " +
              ("casi no se movieron" if move < 0.3 else ("subieron" if paid > 0 else "bajaron")) +
              f": {pct(paid, lang)} contra la semana anterior. Sin contar promociones, el precio de lista cambió {pct(reg, lang)}.")
        if diff > 0.3:
            s2 = (f"La diferencia viene de las promociones: terminaron más ofertas de las que empezaron "
                  f"(en Carrefour, ChangoMás y Día hubo en promedio {num(promo_now, lang, 0)} productos de la canasta en oferta por día, "
                  f"contra {num(promo_before, lang, 0)} la semana anterior). Por eso lo que se paga subió más que los precios de lista.")
        elif diff < -0.3:
            s2 = (f"La diferencia viene de las promociones: hubo más ofertas "
                  f"(en Carrefour, ChangoMás y Día, {num(promo_now, lang, 0)} productos de la canasta en oferta por día en promedio, "
                  f"contra {num(promo_before, lang, 0)} la semana anterior). Por eso lo que se paga subió menos que los precios de lista.")
        else:
            s2 = (f"Las promociones casi no cambiaron el panorama: los dos números son parecidos "
                  f"({num(promo_now, lang, 0)} productos de la canasta en oferta por día en Carrefour, ChangoMás y Día, "
                  f"contra {num(promo_before, lang, 0)} la semana anterior).")
    else:
        s1 = ("The prices people pay at the supermarket " +
              ("barely moved" if move < 0.3 else ("rose" if paid > 0 else "fell")) +
              f": {pct(paid, lang)} against the week before. Leaving promotions out, the list price changed {pct(reg, lang)}.")
        if diff > 0.3:
            s2 = (f"The gap comes from promotions: more offers ended than started (at Carrefour, ChangoMás and Día an average of "
                  f"{num(promo_now, lang, 0)} basket products were on offer each day, against {num(promo_before, lang, 0)} the week before). "
                  f"That is why what people pay rose more than list prices.")
        elif diff < -0.3:
            s2 = (f"The gap comes from promotions: there were more offers (at Carrefour, ChangoMás and Día, {num(promo_now, lang, 0)} "
                  f"basket products on offer each day on average, against {num(promo_before, lang, 0)} the week before). "
                  f"That is why what people pay rose less than list prices.")
        else:
            s2 = (f"Promotions barely changed the picture: both numbers are close ({num(promo_now, lang, 0)} basket products on offer "
                  f"each day at Carrefour, ChangoMás and Día, against {num(promo_before, lang, 0)} the week before).")
    gs = [g for g in w["groups"] if g["in_headline"]]
    ups = [g for g in gs if g["pct"] > 0][:2]
    downs = sorted([g for g in gs if g["pct"] < 0], key=lambda g: g["pct"])[:2]
    gname = lambda g: g["name_es"] if es else g["name_en"]
    parts = []
    if ups:
        parts.append(("Lo que más subió: " if es else "Rose the most: ") +
                     (" y " if es else " and ").join(f"{gname(g).lower() if es else gname(g)} ({pct(g['pct'], lang, 1)})" for g in ups))
    if downs:
        parts.append(("lo que más bajó: " if es else "fell the most: ") +
                     (" y " if es else " and ").join(f"{gname(g).lower() if es else gname(g)} ({pct(g['pct'], lang, 1)})" for g in downs))
    s3 = ("; ".join(parts) + ".") if parts else ""
    if s3:
        s3 = s3[0].upper() + s3[1:]
    s4 = (f"De los {w['products_compared']} productos comparados, {w['products_up']} subieron, {w['products_down']} bajaron y "
          f"{w['products_same']} quedaron igual." if es else
          f"Of the {w['products_compared']} products compared, {w['products_up']} went up, {w['products_down']} went down and "
          f"{w['products_same']} stayed the same.")

    lbl_paid = "Precio que se paga" if es else "Price paid"
    lbl_reg = "Precio de lista (sin promociones)" if es else "List price (no promotions)"
    n_paid = "Con las promociones abiertas a todos" if es else "With the promotions open to everyone"
    n_reg = "Carrefour, ChangoMás y Día" if es else "Carrefour, ChangoMás and Día"
    big = (f'<div class="big"><div class="box"><div class="l">{lbl_paid}</div><div class="v" style="color:{color(paid)}">{pct(paid, lang)}</div>'
           f'<div class="n">{n_paid}</div></div><div class="box"><div class="l">{lbl_reg}</div>'
           f'<div class="v" style="color:{color(reg)}">{pct(reg, lang)}</div><div class="n">{n_reg}</div></div></div>')
    chart_t = "El índice, día por día" if es else "The index, day by day"
    key = (f'<p class="key"><b></b>{"Precio que se paga" if es else "Price paid"}<i></i>{"Precio de lista" if es else "List price"}'
           f' · {"100 = promedio del 24 al 30 de octubre de 2026" if es else "100 = average of 24 to 30 October 2026"}</p>')
    group_rows = [((gname(g)), g["pct"]) for g in gs]
    groups_t = "Por grupo de productos (precio que se paga)" if es else "By product group (price paid)"

    # Page 2
    up_t, down_t = ("Los que más subieron", "Los que más bajaron") if es else ("Biggest rises", "Biggest falls")
    th = (f'<tr><th>{"Producto" if es else "Product"}</th><th class="r">{"Antes → ahora" if es else "Before → now"}</th><th class="r">%</th></tr>')
    prods = (f'<div class="two"><div><h2>{up_t}</h2><table>{th}{product_rows(w["top_up"], lang)}</table></div>'
             f'<div><h2>{down_t}</h2><table>{th}{product_rows(w["top_down"], lang)}</table></div></div>')
    shop_rows = "".join(
        f'<tr><td>{esc(SHOP[s["shop"]])}</td><td class="r" style="color:{color(s["pct"])};font-weight:700">{pct(s["pct"], lang)}</td>'
        f'<td class="r">{(num(pb.get(s["shop"]), lang, 0) + " → " + num(pn.get(s["shop"]), lang, 0)) if pn.get(s["shop"]) is not None and pb.get(s["shop"]) is not None else ("no aplica" if es else "n/a")}</td></tr>'
        for s in w["shops"])
    shops_t = "Súper por súper" if es else "Shop by shop"
    shops_tbl = (f'<h2>{shops_t}</h2><table><tr><th>{"Súper" if es else "Shop"}</th><th class="r">{"Precio que se paga" if es else "Price paid"}</th>'
                 f'<th class="r">{"Productos en oferta por día" if es else "Products on offer per day"}</th></tr>{shop_rows}</table>'
                 f'<p class="tag">{"Promedio de productos de la canasta en oferta por día, semana anterior → esta. Jumbo no muestra un precio de lista real, por eso no se cuentan sus ofertas." if es else "Average basket products on offer per day, week before → this week. Jumbo shows no real list price, so its offers are not counted."}</p>')
    rk = w.get("ranking")
    rank_html = ""
    if rk:
        cheapest, dearest = rk["shops"][0], rk["shops"][-1]
        rank_rows = "".join(
            f'<tr><td>{i + 1}. {esc(SHOP[x["shop"]])}</td><td class="r">{money(x["total"], lang)}</td>'
            f'<td class="r">{("el más barato" if es else "cheapest") if i == 0 else pct(x["pct"], lang, 1)}</td></tr>'
            for i, x in enumerate(rk["shops"]))
        ex = rk["examples"][0] if rk["examples"] else None
        ex_txt = ""
        if ex:
            ex_txt = (f' El caso más extremo: {esc(ex["name"])} costó {money(ex["low"], lang)} en {SHOP[ex["low_shop"]]} y '
                      f'{money(ex["high"], lang)} en {SHOP[ex["high_shop"]]}, un {num(ex["pct"], lang, 0)}% más.' if es else
                      f' The most extreme case: {esc(ex["name"])} cost {money(ex["low"], lang)} at {SHOP[ex["low_shop"]]} and '
                      f'{money(ex["high"], lang)} at {SHOP[ex["high_shop"]]}, {num(ex["pct"], lang, 0)}% more.')
        rank_html = (f'<h2>{"¿Qué súper fue más barato?" if es else "Which shop was cheapest?"}</h2>'
                     f'<p>{"Los mismos" if es else "The same"} {rk["n_products"]} {"productos (mismo código de barras) en los 4 súper, con su precio promedio de la semana. " if es else "products (same barcode) at the 4 shops, at their average price for the week. "}'
                     f'{SHOP[cheapest["shop"]]} {"fue el más barato y" if es else "was the cheapest and"} {SHOP[dearest["shop"]]} '
                     f'{"el más caro, un" if es else "the most expensive,"} {num(dearest["pct"], lang, 1)}% {"más." if es else "more."}{ex_txt}</p>'
                     f'<table><tr><th>{"Súper" if es else "Shop"}</th><th class="r">{"Total de los mismos productos" if es else "Total for the same products"}</th>'
                     f'<th class="r">{"Diferencia" if es else "Difference"}</th></tr>{rank_rows}</table>')
    note = ("<b>Cómo leer este informe.</b> Esto no es la inflación del mes: compara el precio promedio de cada producto en esta semana "
            "con su precio promedio en los mismos días de la semana anterior, así las promociones de fin de semana quedan de los dos lados. "
            "Los productos se combinan como en el índice: por tipo, por grupo y con las ponderaciones oficiales del INDEC (ENGHo 2004/05). "
            "Un producto sin stock no se compara, y nunca se inventa un precio. La inflación del mes sale en el informe mensual. "
            "Método completo y datos abiertos: lacanastaindex.com"
            if es else
            "<b>How to read this report.</b> This is not the month's inflation: it compares each product's average price this week with "
            "its average price on the same days of the week before, so weekend promotions are on both sides. Products are combined as in "
            "the index: by kind, by group and with INDEC's official weights (ENGHo 2004/05). A product out of stock is not compared, and "
            "no price is ever made up. The month's inflation comes in the monthly report. Full method and open data: lacanastaindex.com")
    foot = (f'La Canasta · lacanastaindex.com · Ramon Pepa · {"Datos" if es else "Data"} CC BY 4.0')
    body = (big + f'<p class="lead">{s1} {s2}</p><p>{s3} {s4}</p>' +
            f'<h2>{chart_t}</h2>{line_chart(w["series"], w["start"], lang)}{key}' +
            f'<h2>{groups_t}</h2>{bar_chart(group_rows, lang)}' +
            f'<div class="pb"></div>{prods}{shops_tbl}{rank_html}<div class="note">{note}</div><p class="foot">{foot}</p>')
    return page("Informe semanal" if es else "Weekly report", title, subtitle, body, lang)


# ---------- Monthly report ----------
def monthly(r, lang, comment=""):
    es = lang == "es"
    y, m = int(r["month"][:4]), int(r["month"][5:])
    title = (f"Informe de {MES[m - 1]} de {y}" if es else f"{MONTH_EN[m - 1]} {y} report")
    method = {"average": ("el promedio del mes contra el promedio del mes anterior, como el INDEC",
                          "the month's average against the previous month's average, like INDEC"),
              "week": ("el precio promedio de cada producto en la última semana del mes contra los mismos días del mes anterior",
                       "each product's average price in the month's last week against the same days of the month before"),
              "end_to_end": ("el último día del mes contra el último día del mes anterior",
                             "the month's last day against the previous month's last day")}[r["method"]][0 if es else 1]
    subtitle = (f"Inflación del supermercado. Se mide {esc(method)}." if es else f"Supermarket inflation. Measured as {esc(method)}.")
    h = r["headline"]
    reg = h.get("avg_regular") if r["method"] == "average" else (h.get("week_regular") if r["method"] == "week" else h.get("end_to_end_regular"))
    big = (f'<div class="big"><div class="box"><div class="l">{"Inflación del súper (precio que se paga)" if es else "Supermarket inflation (price paid)"}</div>'
           f'<div class="v" style="color:{color(r["inflation"])}">{pct(r["inflation"], lang)}</div><div class="n">{"Con las promociones abiertas a todos" if es else "With the promotions open to everyone"}</div></div>'
           f'<div class="box"><div class="l">{"Precio de lista (sin promociones)" if es else "List price (no promotions)"}</div>'
           f'<div class="v" style="color:{color(reg)}">{pct(reg, lang)}</div><div class="n">Carrefour, ChangoMás {"y" if es else "and"} Día</div></div></div>')
    gs = [g for g in r["groups"] if g["in_headline"]]
    gname = {g: n for g, n in ((x, None) for x in [])}
    names_es = {"pan_cereales": "Pan y cereales", "carne_vacuna": "Carne vacuna", "carne_ave": "Pollo", "lacteos": "Lácteos y huevos", "aceites": "Aceites",
                "frutas": "Frutas", "verduras": "Verduras", "azucar": "Azúcar y dulces", "otros_alimentos": "Otros alimentos",
                "cafe_te_yerba": "Café, té y yerba", "aguas_gaseosas": "Aguas y gaseosas", "alcohol": "Bebidas alcohólicas",
                "limpieza": "Limpieza"}
    names_en = {"pan_cereales": "Bread and cereals", "carne_vacuna": "Beef", "carne_ave": "Chicken", "lacteos": "Dairy and eggs", "aceites": "Oils",
                "frutas": "Fruit", "verduras": "Vegetables", "azucar": "Sugar and sweets", "otros_alimentos": "Other food",
                "cafe_te_yerba": "Coffee, tea and yerba", "aguas_gaseosas": "Water and soft drinks", "alcohol": "Alcoholic drinks",
                "limpieza": "Cleaning products"}
    nm = names_es if es else names_en
    up = gs[0] if gs else None
    down = gs[-1] if gs else None
    s1 = (f"En {MES[m - 1]}, lo que se paga en el súper cambió {pct(r['inflation'], lang)}; sin promociones, {pct(reg, lang)}. "
          if es else f"In {MONTH_EN[m - 1]}, what people pay at the supermarket changed {pct(r['inflation'], lang)}; without promotions, {pct(reg, lang)}. ")
    if up and down:
        s1 += (f"Lo que más subió fue {nm.get(up['group'], up['group']).lower()} ({pct(up['pct'], lang, 1)}) y lo que más bajó, "
               f"{nm.get(down['group'], down['group']).lower()} ({pct(down['pct'], lang, 1)}). " if es else
               f"{nm.get(up['group'], up['group'])} rose the most ({pct(up['pct'], lang, 1)}) and {nm.get(down['group'], down['group'])} "
               f"fell the most ({pct(down['pct'], lang, 1)}). ")
    s1 += (f"De {r['products_compared']} productos comparados, {r['products_up']} subieron, {r['products_down']} bajaron y {r['products_same']} quedaron igual."
           if es else f"Of {r['products_compared']} products compared, {r['products_up']} went up, {r['products_down']} went down and {r['products_same']} stayed the same.")
    com = f'<div class="note" style="margin-top:2mm">{esc(comment)}<br><b>Ramon Pepa</b></div>' if comment else ""
    key = (f'<p class="key"><b></b>{"Precio que se paga" if es else "Price paid"}<i></i>{"Precio de lista" if es else "List price"}'
           f' · {"100 = promedio del 24 al 30 de octubre de 2026" if es else "100 = average of 24 to 30 October 2026"}</p>')
    th = (f'<tr><th>{"Producto" if es else "Product"}</th><th class="r">{"Antes → ahora" if es else "Before → now"}</th><th class="r">%</th></tr>')
    prods = (f'<div class="two"><div><h2>{"Los que más subieron" if es else "Biggest rises"}</h2><table>{th}{product_rows(r["top_up"], lang)}</table></div>'
             f'<div><h2>{"Los que más bajaron" if es else "Biggest falls"}</h2><table>{th}{product_rows(r["top_down"], lang)}</table></div></div>')
    shop_rows = "".join(f'<tr><td>{esc(SHOP.get(s["shop"], s["shop"]))}</td><td class="r" style="color:{color(s["pct"])};font-weight:700">{pct(s["pct"], lang)}</td></tr>'
                        for s in r["shops"])
    shops_tbl = (f'<h2>{"Súper por súper" if es else "Shop by shop"}</h2><table><tr><th>{"Súper" if es else "Shop"}</th>'
                 f'<th class="r">{"Precio que se paga" if es else "Price paid"}</th></tr>{shop_rows}</table>')
    indec = ""
    if os.path.exists("notas/indec.csv"):
        import csv as _csv
        for row in _csv.DictReader(open("notas/indec.csv", encoding="utf-8")):
            if row["month"] == r["month"]:
                indec = (f'<h2>{"Comparación con el INDEC" if es else "Compared with INDEC"}</h2><p>'
                         f'{"INDEC, alimentos y bebidas (GBA):" if es else "INDEC, food and drinks (Greater Buenos Aires):"} {pct(float(row["alimentos_pct"]), lang, 1)} · '
                         f'{"nivel general:" if es else "all items:"} {pct(float(row["general_pct"]), lang, 1)}. '
                         f'{"La Canasta mide solo productos de supermercado, por eso la comparación justa es con alimentos y bebidas." if es else "La Canasta only measures supermarket goods, so the fair comparison is with food and drinks."}</p>')
    note = ("<b>Cómo se mide.</b> Precios online de Carrefour, Jumbo, ChangoMás y Día, todos los días. Cada súper se compara solo consigo mismo. "
            "Los productos se combinan por tipo, por grupo y con las ponderaciones oficiales del INDEC (ENGHo 2004/05, Gran Buenos Aires). "
            "Un producto sin stock no se compara y nunca se inventa un precio. Método completo y datos abiertos: lacanastaindex.com"
            if es else
            "<b>How it is measured.</b> Online prices from Carrefour, Jumbo, ChangoMás and Día, every day. Each shop is only compared with itself. "
            "Products are combined by kind, by group and with INDEC's official weights (ENGHo 2004/05, Greater Buenos Aires). A product out of "
            "stock is not compared, and no price is ever made up. Full method and open data: lacanastaindex.com")
    body = (big + f'<p class="lead">{s1}</p>{com}' +
            f'<h2>{"El índice, día por día" if es else "The index, day by day"}</h2>{line_chart(r["series"], "9999", lang)}{key}' +
            f'<h2>{"Por grupo de productos" if es else "By product group"}</h2>{bar_chart([(nm.get(g["group"], g["group"]), g["pct"]) for g in gs], lang)}' +
            f'<div class="pb"></div>{prods}{shops_tbl}{indec}<div class="note">{note}</div>'
            f'<p class="foot">La Canasta · lacanastaindex.com · Ramon Pepa · {"Datos" if es else "Data"} CC BY 4.0</p>')
    return page("Informe mensual" if es else "Monthly report", title, subtitle, body, lang)


# ---------- Render ----------
def render(jobs):
    """jobs: list of (html, pdf_path). Checks every PDF has at most 2 pages."""
    if not jobs:
        return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        for doc, out in jobs:
            with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
                f.write(doc)
            pg.goto("file://" + f.name)
            pg.wait_for_timeout(300)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            pg.pdf(path=out, format="A4", print_background=True, prefer_css_page_size=True)
            os.unlink(f.name)
            pages = open(out, "rb").read().count(b"/Type /Page") - open(out, "rb").read().count(b"/Type /Pages")
            print(f"{out}: {pages} page(s)")
            if pages > 2:
                print(f"WARNING: {out} has more than 2 pages")
        b.close()


def main():
    args = sys.argv[1:]
    if args[:1] == ["--test"]:
        d = args[1]
        jobs = []
        for p in sorted(glob.glob(f"{d}/????-??-??.json")):
            w = json.load(open(p, encoding="utf-8"))
            for lang in ("es", "en"):
                jobs.append((weekly(w, lang), f"{d}/{w['id']}-{lang}.pdf"))
        for p in sorted(glob.glob(f"{d}/????-??.json")):
            r = json.load(open(p, encoding="utf-8"))
            for lang in ("es", "en"):
                jobs.append((monthly(r, lang), f"{d}/{r['month']}-{lang}.pdf"))
        render(jobs)
        return
    force = "--all" in args
    hashes_path = "informes/hashes.json"
    hashes = json.load(open(hashes_path, encoding="utf-8")) if os.path.exists(hashes_path) and not force else {}
    jobs = []

    def want(src, out_base, maker, *extra):
        raw = open(src, "rb").read() + "".join(extra).encode() + TEMPLATE_VERSION.encode()
        h = hashlib.sha256(raw).hexdigest()[:16]
        for lang in ("es", "en"):
            out = f"{out_base}-{lang}.pdf"
            if hashes.get(out) != h or not os.path.exists(out):
                jobs.append((maker(lang), out))
                hashes[out] = h

    for p in sorted(glob.glob("index/semanas/????-??-??.json")):
        w = json.load(open(p, encoding="utf-8"))
        want(p, f"informes/semanas/{w['id']}", lambda lang, w=w: weekly(w, lang))
    listing = json.load(open("index/informes/lista.json", encoding="utf-8")) if os.path.exists("index/informes/lista.json") else []
    for x in listing:
        if not x.get("publishable"):
            continue
        p = f"index/informes/{x['month']}.json"
        r = json.load(open(p, encoding="utf-8"))
        com = {lang: (open(f"notas/{x['month']}-{lang}.txt", encoding="utf-8").read().strip()
                      if os.path.exists(f"notas/{x['month']}-{lang}.txt") else "") for lang in ("es", "en")}
        want(p, f"informes/mensuales/{x['month']}", lambda lang, r=r, com=com: monthly(r, lang, com[lang]), com["es"], com["en"])
    render(jobs)
    os.makedirs("informes", exist_ok=True)
    json.dump(hashes, open(hashes_path, "w", encoding="utf-8"), indent=1, sort_keys=True)
    # Every report PDF goes into sitemap.xml, so Google (and the AI search tools that use it) can find it
    if os.path.exists("sitemap.xml"):
        sm = open("sitemap.xml", encoding="utf-8").read()
        new = [f"https://lacanastaindex.com/{p}" for p in sorted(hashes) if os.path.exists(p)]
        add = "".join(f"  <url><loc>{u}</loc><priority>0.6</priority></url>\n" for u in new if f"<loc>{u}</loc>" not in sm)
        if add:
            open("sitemap.xml", "w", encoding="utf-8").write(sm.replace("</urlset>", add + "</urlset>"))
    print(f"{len(jobs)} PDF(s) made.")


if __name__ == "__main__":
    main()
