"""Share pictures (1200x630) that WhatsApp, X and others show when someone shares a La Canasta link.

og/home.png                       the index page: the week's number
og/precios-<product>.png          each price page: the cheapest price per litre or kilo today
og/precios-supermercado-mas-barato.png   which supermarket is cheapest this week
og/precios.png, og/canastas.png, og/la-canasta.png   general card
Pages point to them with ?v=DATE so apps show the new picture every day. Run after make_price_pages.py
and make_ranking_page.py.
"""
import json, os, re
from datetime import date
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OG = os.path.join(ROOT, "og")
W, H = 1200, 630
NAVY, MUTED, SUN, DOWN, BAND, RULE = "#2B3B5C", "#5D6A84", "#D98A2B", "#2D7A57", "#F3F7F9", "#DCE4EA"
MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def font(kind, size, weight=400):
    if kind == "serif":
        return ImageFont.truetype(os.path.join(OG, "fonts", "DMSerifDisplay-Regular.ttf"), size)
    f = ImageFont.truetype(os.path.join(OG, "fonts", "DMSans.ttf"), size)
    try:
        f.set_variation_by_axes([min(max(size, 9), 40), weight])
    except Exception:
        pass
    return f


def fit(draw, text, kind, size, maxw, weight=400, minsize=28):
    while size > minsize:
        f = font(kind, size, weight)
        if draw.textlength(text, font=f) <= maxw:
            return f
        size -= 4
    return font(kind, minsize, weight)


def d_es(d):
    return f"{d.day} de {MES[d.month - 1]} de {d.year}"


def card(name, eyebrow, big, sub, when, big_color=NAVY):
    img = Image.new("RGB", (W, H), "#FFFFFF")
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 0, W, 10], fill=SUN)
    logo = Image.open(os.path.join(ROOT, "la-canasta-logo", "la-canasta-logo-horizontal.png")).convert("RGBA")
    lh = 70
    logo = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)
    img.paste(logo, (72, 62), logo)
    x, maxw = 72, W - 144
    ef = font("sans", 30, 700)
    dr.text((x, 188), eyebrow.upper(), font=ef, fill=MUTED)
    bf = fit(dr, big, "serif", 150, maxw)
    dr.text((x, 232), big, font=bf, fill=big_color)
    sf = fit(dr, sub, "sans", 42, maxw, 500, 26)
    dr.text((x, 418), sub, font=sf, fill=NAVY)
    dr.rectangle([0, H - 96, W, H], fill=NAVY)
    ff = font("sans", 32, 700)
    dr.text((72, H - 66), "lacanastaindex.com", font=ff, fill="#FFFFFF")
    if when:
        wf = font("sans", 28, 500)
        dr.text((W - 72 - dr.textlength(when, font=wf), H - 62), when, font=wf, fill="#DCE6F0")
    img.save(os.path.join(OG, name + ".png"), optimize=True)


def pct_es(x):
    return ("+" if x > 0 else "−" if x < 0 else "") + f"{abs(x):.2f}".replace(".", ",") + "%"


def main():
    os.makedirs(OG, exist_ok=True)
    today = None
    # Which supermarket is cheapest this week
    weeks = json.load(open(os.path.join(ROOT, "index", "semanas", "ranking.json"), encoding="utf-8"))
    w = next((w for w in weeks if w.get("days_of_data", 0) >= 3 and w.get("shops")), None)
    names = {"Carrefour": "Carrefour", "Jumbo": "Jumbo", "ChangoMas": "ChangoMás", "Dia": "Día"}
    if w:
        shops = sorted(w["shops"], key=lambda s: s["pct"])
        today = date.fromisoformat(w["days"][-1])
        worst = shops[-1]
        card("precios-supermercado-mas-barato", "¿Qué súper es más barato esta semana?", names[shops[0]["shop"]],
             f"{names[worst['shop']]}, {worst['pct']:.1f}% más caro por la misma compra".replace(".", ","), d_es(today), DOWN)
    # The index: the week's number
    s = json.load(open(os.path.join(ROOT, "index", "semana.json"), encoding="utf-8"))
    if s.get("ready"):
        a, b = date.fromisoformat(s["now"][0]), date.fromisoformat(s["now"][1])
        today = b
        cheap = f" · {names[shops[0]['shop']]}, el más barato" if w else ""
        card("home", "Precios del súper en Argentina", pct_es(s["paid"]),
             f"Últimos 7 días contra los 7 anteriores{cheap}", d_es(b))
    # Each price page: the cheapest price per litre or kilo today
    import make_price_pages as m
    fp = os.path.join(ROOT, "precios", "fotos.json")
    basket, want, prices = m.load()
    dates = sorted(d for d in prices if prices[d])
    for k in m.KINDS:
        K = m.build_kind(k, basket, prices, dates)
        priced = [i for i in K["items"] if i["per"] is not None]
        if not priced:
            continue
        best = priced[0]
        unit = "por litro" if k[7] == "l" else "por kilo"
        money = m.money(best["per"], "es")
        day = date.fromisoformat(K["today"])
        card("precios-" + k[0], k[2], f"Desde {money}", f"{unit}, en {names[best['shop']]} · {best['name']}"[:90], d_es(day))
    # General cards
    card("la-canasta", "Índice diario de precios del súper", "La Canasta", "Argentina · datos abiertos, todos los días", "")
    card("precios", "Precios del súper hoy", "Leche, yerba, aceite…", "Dónde está más barato, súper por súper", d_es(today) if today else "")
    card("canastas", "La app de La Canasta", "Muy pronto, gratis", "App Store y Google Play", "")
    # The index page points to today's picture
    if today:
        f = os.path.join(ROOT, "index.html")
        t = open(f, encoding="utf-8").read()
        t2 = re.sub(r'<meta property="og:image" content="[^"]*">',
                    f'<meta property="og:image" content="https://lacanastaindex.com/og/home.png?v={today.isoformat()}">', t, count=1)
        if t2 != t:
            open(f, "w", encoding="utf-8").write(t2)
    print("share cards written", sorted(os.listdir(OG)))


if __name__ == "__main__":
    main()
