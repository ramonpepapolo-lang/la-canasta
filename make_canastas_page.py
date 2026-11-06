"""Writes the website's "Creá tu canasta" pages, with the same screens as the La Canasta app (app/src/app.html):
  - canastas/app.html: the app itself, full screen (it is what the phone's home-screen icon opens).
  - canastas/index.html: a normal page of the website (menu, "app coming soon" banner, footer) with the app inside:
    in an iPhone frame on a computer, full width on a phone.

The page reads today's data live from the website: app-datos/datos.json (index, ranking, moves), canastas/datos.json
and canastas/catalogo.json (made by make_canastas.py every day). Run after make_canastas.py (and after any change to
app/src/app.html). The AI assistant answers when an AI service is set (window.LC_AI_URL); without it, the built-in
assistant answers.
"""
import json, os, re
from make_price_pages import add_to_sitemap, make_chrome, SITE

ROOT = os.path.dirname(os.path.abspath(__file__))
# the AI assistant (app/ai-worker.js on Cloudflare): its address once it is set up; empty = the built-in assistant answers
AI_URL = ""

TITLE = "Creá tu canasta: dónde conviene comprar hoy en Carrefour, Jumbo, ChangoMás y Día · La Canasta"
DESC = ("Decí o escribí qué querés comprar (un asado para 6, la compra de la semana, lo que sea) y La Canasta te arma la canasta, "
        "te dice en qué supermercado sale menos hoy y te lleva al más cercano. Precios reales de hoy, gratis.")

# what the computer shows next to the phone: the website's links and the app coming soon
SIDE = """<aside class="side" aria-label="La Canasta">
    <a href="/" aria-label="La Canasta, inicio"><img class="side-logo lg-l" src="/la-canasta-logo/la-canasta-logo-horizontal.svg" alt="La Canasta"><img class="side-logo lg-d" src="/la-canasta-logo/la-canasta-logo-horizontal-white.svg" alt="La Canasta"></a>
    <h1>Creá tu canasta</h1>
    <p>Decile qué querés comprar, como a una persona. Te arma la canasta, te dice en qué súper sale menos con los precios de hoy y te lleva al más cercano.</p>
    <p class="soon-line"><b>La app de La Canasta</b> <span class="soon">PRÓXIMAMENTE</span><br>Para iPhone y Android. Es esta misma: usala acá gratis.</p>
    <nav class="side-links" aria-label="La web">
      <a href="/">El índice de hoy</a><a href="/precios/">Precios de hoy</a><a href="/informes.html">Informes</a><a href="/metodo.html">Cómo se calcula</a>
    </nav>
    <small id="sideDate"></small>
  </aside>"""

SIDE_CSS = """<style>
.side .soon-line { font-size: 14px; }
.side .soon-line b { color: var(--ink); }
.side .soon { display: inline-block; background: var(--sun); color: #1A1206; font-size: 11px; font-weight: 800; letter-spacing: .1em; border-radius: 999px; padding: 2px 8px; margin-left: 4px; vertical-align: 1px; }
.side-links { display: flex; flex-wrap: wrap; gap: 8px; }
.side-links a { font-size: 13px; font-weight: 700; color: var(--navy); background: var(--card); box-shadow: var(--shadow); padding: 8px 12px; border-radius: 999px; text-decoration: none; }
.side-links a:hover { background: var(--sky); }
</style>"""


# the website page: the app inside, framed on a computer
PAGE = """
<div class="appsoon" role="note">
  <div class="container appsoon-in">
    <img src="/app-icons/icon-192.png" alt="" width="52" height="52">
    <div class="appsoon-t"><b><span class="es">La app de La Canasta</span><span class="en">The La Canasta app</span> <span class="soon"><span class="es">PRÓXIMAMENTE</span><span class="en">COMING SOON</span></span></b>
      <span><span class="es">Para iPhone y Android. Mientras tanto, usala acá gratis.</span><span class="en">For iPhone and Android. Meanwhile, use it here for free.</span></span></div>
    <div class="stores" aria-hidden="true"><span>App Store</span><span>Google Play</span></div>
  </div>
</div>
<main class="container cn">
  <nav class="crumbs" aria-label="Ruta"><a href="/">La Canasta</a> › <span class="es">Creá tu canasta</span><span class="en">Create your basket</span></nav>
  <div class="cn-grid">
    <section class="cn-text">
      <h1><span class="es">Creá tu canasta</span><span class="en">Create your basket</span></h1>
      <p class="lede"><span class="es">Decile qué querés comprar, como a una persona. Te arma la canasta, te dice en qué supermercado sale menos con los precios de hoy y te lleva al más cercano.</span><span class="en">Tell it what you want to buy, as you would tell a person. It builds the basket, tells you which supermarket is cheapest with today's prices and takes you to the nearest one.</span></p>
      <ul class="cn-points">
        <li><span class="es"><b>Hablá o escribí.</b> «Asado para 6», «la compra de la semana para dos», «¿cuánto sale la yerba?».</span><span class="en"><b>Speak or type.</b> "An asado for 6", "the weekly shop for two", "how much is yerba?". (The app is in Spanish.)</span></li>
        <li><span class="es"><b>Elegí vos.</b> {n_items} productos, cantidades, y lo más barato o primera marca.</span><span class="en"><b>You choose.</b> {n_items} products, quantities, and the cheapest or a leading brand.</span></li>
        <li><span class="es"><b>Andá al más barato.</b> Compara Carrefour, Jumbo, ChangoMás y Día y te abre el mapa.</span><span class="en"><b>Go to the cheapest.</b> It compares Carrefour, Jumbo, ChangoMás and Día and opens the map.</span></li>
        <li><span class="es"><b>Guardá tus canastas.</b> La semanal, la del mes, la del asado.</span><span class="en"><b>Save your baskets.</b> The weekly one, the monthly one, the asado.</span></li>
      </ul>
      <p class="cn-full"><a href="/canastas/app.html"><span class="es">Abrir en pantalla completa →</span><span class="en">Open full screen →</span></a></p>
    </section>
    <div class="cn-phone">
      <iframe src="/canastas/app.html" title="La Canasta: Creá tu canasta" allow="geolocation; microphone" loading="eager"></iframe>
    </div>
  </div>
  <section class="how">
    <h2><span class="es">Cómo se calcula</span><span class="en">How it is calculated</span></h2>
    <p class="es">Para cada producto de tu canasta, en cada súper, se toma el más barato que hay hoy en su página web (o el más barato de una primera marca, si lo elegís), por kilo, por litro o por unidad, y se multiplica por la cantidad. Son precios online del día, sin promos bancarias. Un precio muy lejos del de los otros súper se descarta como error de la web, igual que en el índice. El total compara solo lo que tienen los 4 súper, para que sea parejo. Son los precios online de cada cadena, sobre todo los del Gran Buenos Aires. Nada se estima.</p>
    <p class="en">For each product in your basket, at each supermarket, we take the cheapest one on its website today (or the cheapest of a leading brand, if you choose it), per kilo, per litre or per unit, and multiply by the quantity. These are the day's online prices, with no bank promotions. A price far from the other shops is discarded as a website error, as the index does. The total only compares what all 4 shops have, so it is fair. These are each chain's online prices, mostly those of Greater Buenos Aires. Nothing is estimated.</p>
    <p><a href="/precios/"><span class="es">Precio de cada producto hoy</span><span class="en">Today's price of each product</span></a> · <a href="/index.html#shops"><span class="es">Ranking de supermercados</span><span class="en">Supermarket ranking</span></a> · <a href="/metodo.html"><span class="es">Metodología</span><span class="en">Methodology</span></a></p>
  </section>
</main>
"""

PAGE_CSS = """<style>
.appsoon { background: linear-gradient(90deg, #2B3B5C, #34507a); color: #fff; }
.appsoon-in { display: flex; align-items: center; gap: 0.9rem; padding-block: 0.8rem; flex-wrap: wrap; }
.appsoon img { border-radius: 12px; flex: none; box-shadow: 0 6px 16px rgba(0,0,0,.25); }
.appsoon-t { display: grid; gap: 0.15rem; flex: 1 1 14rem; min-width: 0; font-size: 0.92rem; color: rgba(255,255,255,.85); }
.appsoon-t b { color: #fff; font-size: 1.02rem; }
.soon { display: inline-block; background: var(--sun); color: #1A1206; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.1em; border-radius: 999px; padding: 0.15rem 0.55rem; margin-left: 0.3rem; vertical-align: middle; }
.stores { display: flex; gap: 0.5rem; flex: none; }
.stores span { border: 1.5px solid rgba(255,255,255,.55); border-radius: 10px; padding: 0.35rem 0.7rem; font-weight: 700; font-size: 0.82rem; white-space: nowrap; }
.cn { display: grid; gap: 2.4rem; padding-block: 1.6rem 3rem; }
.crumbs { display: block; font-size: 0.9rem; color: var(--muted); }
.crumbs a { color: var(--muted); }
.cn-grid { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 3rem; align-items: center; }
.cn-text { display: grid; gap: 1rem; max-width: 34rem; }
.cn-text h1 { font-size: clamp(2.3rem, 5.5vw, 3.6rem); margin: 0; }
.cn-points { margin: 0; padding: 0; list-style: none; display: grid; gap: 0.75rem; }
.cn-points li { padding-left: 1.6rem; position: relative; }
.cn-points li::before { content: ""; position: absolute; left: 0; top: 0.5em; width: 0.6rem; height: 0.6rem; border-radius: 50%; background: var(--sun); }
.cn-full a { font-weight: 700; }
.cn-phone { width: 393px; height: 852px; max-height: calc(100vh - 40px); border-radius: 58px; border: 12px solid #11161F; box-shadow: 0 0 0 1.5px #3A4152, 0 40px 80px rgba(17,22,31,.25); overflow: hidden; background: #F3F7F9; }
.cn-phone iframe { display: block; width: 100%; height: 100%; border: 0; }
.how { display: grid; gap: 0.8rem; max-width: 62rem; }
html.lc-app .appsoon { display: none; }
@media (max-width: 860px) {
  .cn-grid { grid-template-columns: minmax(0, 1fr); gap: 1.2rem; }
  .cn-points, .cn-full { display: none; }
  .cn-phone { width: 100%; height: min(780px, calc(100svh - 120px)); min-height: 560px; max-height: none; border: 1px solid var(--rule); border-radius: 22px; box-shadow: 0 10px 30px rgba(30,43,69,.10); }
}
</style>"""


def main():
    app = open(os.path.join(ROOT, "app", "src", "app.html"), encoding="utf-8").read()
    # the page's own title and the preview-only meta tag go; the website's head replaces them
    app = re.sub(r"^<title>.*?</title>\s*", "", app, count=1)
    app = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\s*', "", app, count=1)
    # the side panel next to the phone
    app, n = re.subn(r'<aside class="side".*?</aside>', SIDE, app, count=1, flags=re.S)
    if not n:
        raise SystemExit("app/src/app.html: side panel not found, update make_canastas_page.py")
    # the logo and the data, from the root of the website
    app = app.replace('src="la-canasta-logo/', 'src="/la-canasta-logo/')
    cat = json.load(open(os.path.join(ROOT, "canastas", "catalogo.json"), encoding="utf-8"))
    date = cat["date"]
    n_items = sum(1 for v in cat["items"].values() if v["shops"])
    ld = json.dumps({"@context": "https://schema.org", "@type": "WebApplication", "name": "La Canasta: Creá tu canasta",
                     "url": f"{SITE}/canastas/", "applicationCategory": "ShoppingApplication", "operatingSystem": "Web, iOS, Android",
                     "inLanguage": "es", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "ARS"},
                     "creator": {"@type": "Person", "name": "Ramon Pepa"}}, ensure_ascii=False)
    head = f"""<!doctype html>
<html lang="es" data-own-app>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:image" content="{SITE}/la-canasta-logo/la-canasta-icon-512.png">
<meta property="og:url" content="{SITE}/canastas/">
<meta name="twitter:card" content="summary">
<link rel="canonical" href="{SITE}/canastas/">\n<meta name="robots" content="noindex">
<link rel="icon" href="/la-canasta-logo/la-canasta-icon-32.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#F3F7F9">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="La Canasta">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" sizes="180x180" href="/app-icons/icon-180.png">
<script type="application/ld+json">{ld}</script>
<script>window.LC_WEB = true; window.LC_BASE = "/";{(" window.LC_AI_URL = " + json.dumps(AI_URL) + ";") if AI_URL else ""}</script>
<style>[hidden]{{display:none!important}} html{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}</style>
{SIDE_CSS}
"""
    noscript = (f'<noscript><p style="padding:16px;font-family:sans-serif">La Canasta compara hoy los precios de {n_items} productos '
                f'en Carrefour, Jumbo, ChangoMás y Día (precios del {date}). Para armar tu canasta hace falta JavaScript. '
                f'<a href="/precios/">Ver los precios de hoy</a> · <a href="/">El índice</a></p></noscript>')
    html = head + app + "\n" + noscript + '\n<script src="/counter.js?v=4"></script>\n</html>\n'
    os.makedirs(os.path.join(ROOT, "canastas"), exist_ok=True)
    with open(os.path.join(ROOT, "canastas", "app.html"), "w", encoding="utf-8") as f:
        f.write(html)
    page = make_chrome()(TITLE, DESC, "canastas/", PAGE.replace("{n_items}", str(n_items)), '<script type="application/ld+json">' + ld + "</script>\n" + PAGE_CSS)
    page = page.replace("</style>\n<header", 'html:not([lang=en]) .en{display:none!important} html[lang=en] .es{display:none!important}\n</style>\n<header', 1)
    with open(os.path.join(ROOT, "canastas", "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    add_to_sitemap(["canastas/"], date)
    print("canastas/index.html (website page) and canastas/app.html (the app) written, data of", date)


if __name__ == "__main__":
    main()
