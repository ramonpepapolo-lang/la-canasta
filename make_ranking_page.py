"""Writes precios/supermercado-mas-barato.html: which supermarket is cheapest in Argentina this week, from the
same weekly ranking the home page shows (index/semanas/ranking.json: the same products, with the same barcode,
in the 4 shops of the index, each price the average of the week). Run after compute_index.py and
make_price_pages.py, every day.
"""
import json, os
from datetime import date
from make_price_pages import SHOP_NAME, SITE, add_to_sitemap, d_en, d_es, esc, make_chrome, money, share_wa

ROOT = os.path.dirname(os.path.abspath(__file__))
PATH = "precios/supermercado-mas-barato.html"


def pct_es(x):
    return ("+" if x > 0 else "") + f"{x:.1f}".replace(".", ",") + "%"


def pct_en(x):
    return ("+" if x > 0 else "") + f"{x:.1f}%"


def n_es(n):
    return f"{n:,}".replace(",", ".")


CALC_JS = r'''<script>
(function () {
  var amt = document.getElementById("calcAmt"), shop = document.getElementById("calcShop"), out = document.getElementById("calcOut"), BEST = __BEST__;
  function fmt(x) { return "$" + Math.round(x).toLocaleString("es-AR"); }
  function show() {
    var en = document.documentElement.lang === "en", a = parseFloat((amt.value || "").replace(/[^0-9]/g, "")), p = parseFloat(shop.value);
    var name = shop.options[shop.selectedIndex].text;
    if (!a) { out.textContent = en ? "Type how much you spend and see the difference." : "Escribí cuánto gastás y mirá la diferencia."; return; }
    if (p <= 0) { out.innerHTML = en ? "You already shop at the cheapest one this week." : "Ya comprás en el más barato de esta semana. 👏"; return; }
    var save = a - a / (1 + p / 100);
    out.innerHTML = en ? "Buying the same at " + BEST + " instead of " + name + ", you would save about <strong>" + fmt(save) + " a month</strong> (" + fmt(save * 12) + " a year)."
                       : "Comprando lo mismo en " + BEST + " en vez de " + name + ", ahorrarías unos <strong>" + fmt(save) + " por mes</strong> (" + fmt(save * 12) + " por año).";
  }
  amt.addEventListener("input", function () { var d = amt.value.replace(/[^0-9]/g, ""); amt.value = d ? "$ " + Number(d).toLocaleString("es-AR") : ""; show(); });
  shop.addEventListener("change", show);
  document.querySelectorAll(".lang button").forEach(function (b) { b.addEventListener("click", function () { setTimeout(show, 0); }); });
  show();
})();
</script>'''


def pick(weeks):
    """The newest week with at least 3 days of data, else the newest complete one."""
    for w in weeks:
        if w.get("days_of_data", 0) >= 3 and w.get("shops"):
            return w
    return next((w for w in weeks if w.get("complete") and w.get("shops")), None)


def main():
    weeks = json.load(open(os.path.join(ROOT, "index", "semanas", "ranking.json"), encoding="utf-8"))
    w = pick(weeks)
    if not w:
        print("No ranking yet"); return
    shops = sorted(w["shops"], key=lambda s: s["pct"])
    best, worst = shops[0], shops[-1]
    B, Wn = SHOP_NAME[best["shop"]], SHOP_NAME[worst["shop"]]
    last = date.fromisoformat(w["days"][-1])
    first = date.fromisoformat(w["days"][0])
    n = w["n_products"]
    upto_es = "" if w.get("complete") else f" (datos hasta el {d_es(last)})"
    upto_en = "" if w.get("complete") else f" (data up to {d_en(last)})"
    others_es = ", ".join(f"{SHOP_NAME[s['shop']]} {pct_es(s['pct'])}" for s in shops[1:])
    others_en = ", ".join(f"{SHOP_NAME[s['shop']]} {pct_en(s['pct'])}" for s in shops[1:])
    answer_es = (f"Esta semana el supermercado más barato es {B}. En la {w['label_es'][0].lower() + w['label_es'][1:]}{upto_es}, "
                 f"la misma compra de {n_es(n)} productos, con el mismo código de barras, costó más en los demás: {others_es}.")
    answer_en = (f"This week the cheapest supermarket is {B}. In the {w['label_en'][0].lower() + w['label_en'][1:]}{upto_en}, "
                 f"the same basket of {n:,} products, with the same barcodes, cost more elsewhere: {others_en}.")

    cc = sorted(w.get("cheapest_count", {}).items(), key=lambda kv: -kv[1])
    cc_es = ", ".join(f"{SHOP_NAME[s]} en {c}" for s, c in cc)
    cc_en = ", ".join(f"{SHOP_NAME[s]} in {c}" for s, c in cc)
    top = SHOP_NAME[cc[0][0]] if cc else B
    if top == B:
        tip_es = f"{B} gana tanto en la compra completa como producto por producto."
        tip_en = f"{B} wins both on the full basket and product by product."
    else:
        tip_es = (f"Para hacer toda la compra en un solo lugar, conviene {B}. Para productos sueltos conviene comparar: "
                  f"{top} tuvo el precio más bajo en más productos.")
        tip_en = (f"For the whole shop in one place, {B} is cheapest. For single products it pays to compare: "
                  f"{top} had the lowest price on more products.")

    boxes = []
    for i, s in enumerate(shops):
        nm = SHOP_NAME[s["shop"]]
        sub_es = "el más barato" if i == 0 else f"{pct_es(s['pct']).lstrip('+')} más caro que {B}"
        sub_en = "the cheapest" if i == 0 else f"{pct_en(s['pct']).lstrip('+')} dearer than {B}"
        boxes.append(f'<div class="pbox"><span class="plab">{i + 1}°</span><strong>{esc(nm)}</strong>'
                     f'<span class="psub"><span data-lang="es">{sub_es} · {money(s["total"], "es")}</span>'
                     f'<span data-lang="en">{sub_en} · {money(s["total"], "en")}</span></span></div>')

    ex_rows = []
    for e in w.get("examples", [])[:6]:
        ex_rows.append(f'<tr><td>{esc(e["name"])}</td><td class="r">{SHOP_NAME[e["low_shop"]]} {money(e["low"], "es")}</td>'
                       f'<td class="r">{SHOP_NAME[e["high_shop"]]} {money(e["high"], "es")}</td><td class="r">{pct_es(e["pct"])}</td></tr>')

    order = ["Dia", "Carrefour", "ChangoMas", "Jumbo"]
    hist = []
    for wk in weeks:
        if not wk.get("shops"):
            continue
        p = {s["shop"]: s["pct"] for s in wk["shops"]}
        cheapest = min(wk["shops"], key=lambda s: s["pct"])["shop"]
        cells = "".join(f'<td class="r">{"" if p.get(sh) is None else pct_es(p[sh])}</td>' for sh in order)
        hist.append(f'<tr><td><span data-lang="es">{esc(wk["label_es"])}</span><span data-lang="en">{esc(wk["label_en"])}</span>'
                    f'{"" if wk.get("complete") else " *"}</td><td>{SHOP_NAME[cheapest]}</td>{cells}</tr>')

    faq = [
        ("¿Qué supermercado es más barato en Argentina?", answer_es,
         "Which supermarket is cheapest in Argentina?", answer_en),
        ("¿Conviene comprar todo en el mismo súper?", f"{tip_es} De los {n_es(n)} productos comparados, tuvieron el precio más bajo (o empatado): {cc_es}.",
         "Is it worth buying everything at the same shop?", f"{tip_en} Of the {n:,} products compared, these had the lowest (or joint lowest) price: {cc_en}."),
        ("¿Cómo se compara?", "Se comparan solo los productos que venden los 4 súper, identificados por el mismo código de barras, así que es exactamente la misma compra. "
         "Cada precio es el promedio de la semana del precio que se paga online, con las promociones que se ven en la web. Los precios se recolectan todos los días.",
         "How is it compared?", "Only products sold by all 4 shops are compared, matched by the same barcode, so it is exactly the same basket. "
         "Each price is the week's average of the price paid online, including the promotions shown on the website. Prices are collected every day."),
        ("¿Cada cuánto se actualiza?", "Todos los días, después de la recolección de precios de la tarde (hora de Argentina).",
         "How often is it updated?", "Every day, after the afternoon price collection (Argentina time)."),
        ("¿Qué supermercados incluye?", "Carrefour, Jumbo, ChangoMás y Día, con sus precios online. Son precios de la web, sobre todo de Gran Buenos Aires.",
         "Which supermarkets are included?", "Carrefour, Jumbo, ChangoMás and Día, with their online prices, mostly for Greater Buenos Aires."),
    ]
    faq_html = "".join(
        f'<h3><span data-lang="es">{esc(qe)}</span><span data-lang="en">{esc(qn)}</span></h3>'
        f'<p><span data-lang="es">{esc(ae)}</span><span data-lang="en">{esc(an)}</span></p>' for qe, ae, qn, an in faq)

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": f"{SITE}/{PATH}", "url": f"{SITE}/{PATH}", "inLanguage": ["es", "en"],
         "name": "¿Qué supermercado es más barato en Argentina?", "dateModified": w["days"][-1],
         "author": {"@type": "Person", "@id": f"{SITE}/ramon-pepa.html#ramon", "name": "Ramon Pepa"},
         "publisher": {"@type": "Organization", "name": "La Canasta", "url": f"{SITE}/"},
         "isBasedOn": {"@type": "Dataset", "name": "La Canasta: índice diario de precios de supermercados en Argentina", "url": f"{SITE}/"}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": qe, "acceptedAnswer": {"@type": "Answer", "text": ae}} for qe, ae, _, _ in faq]},
    ]}
    ld_html = '<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False, indent=1) + "\n</script>"

    body = f"""
<main class="container pp">
  <nav class="crumbs" aria-label="Ruta"><a href="../index.html">La Canasta</a> › <a href="index.html"><span data-lang="es">Precios</span><span data-lang="en">Prices</span></a> › <span data-lang="es">Súper más barato</span><span data-lang="en">Cheapest supermarket</span></nav>
  <header class="pp-head">
    <h1><span data-lang="es">¿Qué supermercado es más barato en Argentina?</span><span data-lang="en">Which supermarket is cheapest in Argentina?</span></h1>
    <p class="summary"><span data-lang="es"><strong>{esc(B)}.</strong> {esc(answer_es[len("Esta semana el supermercado más barato es " + B + ". "):])}</span><span data-lang="en"><strong>{esc(B)}.</strong> {esc(answer_en[len("This week the cheapest supermarket is " + B + ". "):])}</span></p>
    <p class="psub"><span data-lang="es">Actualizado todos los días. Último dato: {d_es(last, True)}.</span><span data-lang="en">Updated every day. Latest data: {d_en(last, True)}.</span></p>
    {share_wa(f"¿Qué súper es más barato esta semana? {B}. Mirá el ranking 👉 {SITE}/{PATH}", f"Which supermarket is cheapest this week? {B}. See the ranking 👉 {SITE}/{PATH}")}
  </header>

  <section>
    <h2><span data-lang="es">El ranking de esta semana</span><span data-lang="en">This week's ranking</span></h2>
    <div class="pboxes">{''.join(boxes)}</div>
    <p class="psub"><span data-lang="es">Total de la misma compra de {n_es(n)} productos, promedio de la semana. {Wn} fue {pct_es(worst['pct']).lstrip('+')} más caro que {B}.</span><span data-lang="en">Total of the same basket of {n:,} products, week average. {Wn} was {pct_en(worst['pct']).lstrip('+')} more expensive than {B}.</span></p>
  </section>

  <section class="calc" id="ahorro">
    <h2><span data-lang="es">¿Cuánto ahorrás?</span><span data-lang="en">How much could you save?</span></h2>
    <div class="calc-row">
      <label><span><span data-lang="es">¿Cuánto gastás por mes en el súper?</span><span data-lang="en">How much do you spend a month at the supermarket?</span></span><input id="calcAmt" type="text" inputmode="numeric" autocomplete="off" placeholder="$ 400.000"></label>
      <label><span><span data-lang="es">¿Dónde comprás?</span><span data-lang="en">Where do you shop?</span></span><select id="calcShop">{''.join(f'<option value="{s["pct"]}"{" selected" if s is worst else ""}>{SHOP_NAME[s["shop"]]}</option>' for s in shops)}</select></label>
    </div>
    <p class="calc-out" id="calcOut" aria-live="polite"></p>
    <p class="psub"><span data-lang="es">Estimado con la misma compra de esta semana ({n_es(n)} productos, mismo código de barras). Es una cuenta aproximada: depende de qué comprás.</span><span data-lang="en">Estimated with this week's same basket ({n:,} products, same barcodes). A rough figure: it depends on what you buy.</span></p>
  </section>
  {CALC_JS.replace("__BEST__", json.dumps(B))}

  <section>
    <h2><span data-lang="es">¿Conviene comprar todo en el mismo súper?</span><span data-lang="en">Is it worth buying everything at the same shop?</span></h2>
    <p class="summary"><span data-lang="es">{esc(tip_es)} De los {n_es(n)} productos, tuvieron el precio más bajo (o empatado): {esc(cc_es)}.</span><span data-lang="en">{esc(tip_en)} Of the {n:,} products, these had the lowest (or joint lowest) price: {esc(cc_en)}.</span></p>
    <p><a href="index.html"><span data-lang="es">Dónde está más barato cada producto hoy: leche, yerba, aceite y más →</span><span data-lang="en">Where each product is cheapest today: milk, yerba, oil and more →</span></a></p>
  </section>

  <section>
    <h2><span data-lang="es">Las mayores diferencias de la semana</span><span data-lang="en">The biggest gaps this week</span></h2>
    <div class="tbl-wrap"><table class="ptable">
      <thead><tr><th><span data-lang="es">Producto</span><span data-lang="en">Product</span></th><th class="r"><span data-lang="es">Más barato</span><span data-lang="en">Cheapest</span></th><th class="r"><span data-lang="es">Más caro</span><span data-lang="en">Most expensive</span></th><th class="r"><span data-lang="es">Diferencia</span><span data-lang="en">Gap</span></th></tr></thead>
      <tbody>{''.join(ex_rows)}</tbody>
    </table></div>
  </section>

  <section>
    <h2><span data-lang="es">Semana por semana</span><span data-lang="en">Week by week</span></h2>
    <div class="tbl-wrap"><table class="ptable">
      <thead><tr><th><span data-lang="es">Semana</span><span data-lang="en">Week</span></th><th><span data-lang="es">Más barato</span><span data-lang="en">Cheapest</span></th>{''.join(f'<th class="r">{SHOP_NAME[s]}</th>' for s in order)}</tr></thead>
      <tbody>{''.join(hist)}</tbody>
    </table></div>
    <p class="psub"><span data-lang="es">Cuánto más cara fue la misma compra que en el súper más barato de cada semana. * Semana en curso.</span><span data-lang="en">How much more the same basket cost than at that week's cheapest shop. * Week in progress.</span></p>
  </section>

  <section class="faq">
    <h2><span data-lang="es">Preguntas frecuentes</span><span data-lang="en">Questions</span></h2>
    {faq_html}
    <p><a href="../metodo.html"><span data-lang="es">Metodología completa</span><span data-lang="en">Full methodology</span></a> · <a href="../index.html#shops"><span data-lang="es">Ranking en el índice</span><span data-lang="en">Ranking on the index page</span></a> · <a href="../index.html#data"><span data-lang="es">Descargar los datos</span><span data-lang="en">Download the data</span></a></p>
  </section>
</main>"""
    title = "¿Qué supermercado es más barato en Argentina? Ranking de Carrefour, Jumbo, ChangoMás y Día · La Canasta"
    desc = (f"Esta semana el súper más barato es {B}. La misma compra de {n_es(n)} productos (mismo código de barras) costó "
            f"{others_es}. Actualizado todos los días.")
    page = make_chrome()(title, desc, PATH, body, ld_html)
    open(os.path.join(ROOT, PATH), "w", encoding="utf-8").write(page)
    add_to_sitemap([PATH], w["days"][-1])
    print(PATH, "cheapest", B, "products", n, "week", w["id"])


if __name__ == "__main__":
    main()
