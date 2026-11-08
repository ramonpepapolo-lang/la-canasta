"""Writes the website's app page, lacanastaindex.com/canastas/: the La Canasta app is coming soon to the App Store
and Google Play, free. The app itself is not on the website: it only lives inside the iPhone and Android app
(app/src/app.html, built by app/build-www.js).

Run after make_canastas.py (it reads canastas/catalogo.json only for the date of the sitemap).
"""
import json, os
from make_price_pages import add_to_sitemap, make_chrome

ROOT = os.path.dirname(os.path.abspath(__file__))

TITLE = "La app de La Canasta: muy pronto en App Store y Google Play, gratis · La Canasta"
DESC = "La app de La Canasta llega muy pronto, gratis, para iPhone y Android. Mientras tanto: el índice de hoy y los precios de hoy en Carrefour, Jumbo, ChangoMás y Día."

PAGE = """
<main class="container soonpage">
  <nav class="crumbs" aria-label="Ruta"><a href="/">La Canasta</a> › <span class="es">La app</span><span class="en">The app</span></nav>
  <section class="soon-card">
    <img class="soon-icon" src="/app-icons/icon-512.png" alt="La Canasta" width="132" height="132">
    <span class="soon-pill"><span class="es">MUY PRONTO</span><span class="en">VERY SOON</span></span>
    <h1><span class="es">La app de La Canasta</span><span class="en">The La Canasta app</span></h1>
    <p class="soon-lede"><span class="es">Perdón, todavía no está. Llega muy, muy pronto a App Store y Google Play, <b>gratis</b>.</span><span class="en">Sorry, it is not out yet. It is coming very, very soon to the App Store and Google Play, <b>for free</b>.</span></p>
    <div class="soon-stores" aria-label="App Store y Google Play: próximamente">
      <span class="store"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="3" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 18.5h4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><span><small><span class="es">Próximamente en</span><span class="en">Coming soon to</span></small>App Store</span></span>
      <span class="store"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3l14 9-14 9z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg><span><small><span class="es">Próximamente en</span><span class="en">Coming soon to</span></small>Google Play</span></span>
    </div>
    <a class="soon-btn" href="/#suscribirse"><span class="es">Avisame cuando salga</span><span class="en">Tell me when it is out</span></a>
    <p class="soon-note"><span class="es">Te avisamos por email el día que salga, junto con el informe mensual.</span><span class="en">We will email you the day it comes out, with the monthly report.</span></p>
  </section>
  <section class="soon-more">
    <h2><span class="es">Mientras tanto</span><span class="en">Meanwhile</span></h2>
    <div class="soon-links">
      <a href="/#index"><b><span class="es">El índice de hoy</span><span class="en">Today's index</span></b><span class="es">Cuánto subieron hoy los precios del súper.</span><span class="en">How much supermarket prices moved today.</span></a>
      <a href="/precios/"><b><span class="es">Precios de hoy</span><span class="en">Today's prices</span></b><span class="es">Leche, yerba, aceite y más, súper por súper.</span><span class="en">Milk, yerba, oil and more, shop by shop.</span></a>
      <a href="/informes.html"><b><span class="es">Informes</span><span class="en">Reports</span></b><span class="es">El informe completo de cada mes.</span><span class="en">The full report, every month.</span></a>
    </div>
  </section>
</main>
"""

PAGE_CSS = """<style>
.soonpage { display: grid; gap: 2.6rem; padding-block: 1.6rem 4rem; }
.crumbs { display: block; font-size: 0.9rem; color: var(--muted); }
.crumbs a { color: var(--muted); }
.soon-card { display: grid; justify-items: center; text-align: center; gap: 1.1rem; padding: clamp(2rem, 6vw, 3.6rem) 1.2rem; border-radius: 28px;
  background: radial-gradient(120% 90% at 50% 0%, var(--celeste-fill), transparent 70%), var(--band); border: 1px solid var(--rule); }
.soon-icon { width: 132px; height: 132px; border-radius: 30px; box-shadow: 0 18px 40px rgba(43,59,92,.22), 0 0 0 1px rgba(43,59,92,.06); }
.soon-pill { background: var(--sun); color: #1A1206; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.14em; border-radius: 999px; padding: 0.3rem 0.85rem; }
.soon-card h1 { font-size: clamp(2.2rem, 6vw, 3.6rem); }
.soon-lede { max-width: 30rem; margin: 0; font-size: 1.15rem; color: var(--navy); }
.soon-stores { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.7rem; }
.store { display: inline-flex; align-items: center; gap: 0.6rem; background: var(--navy); color: #fff; border-radius: 12px; padding: 0.55rem 1rem 0.55rem 0.8rem; text-align: left; line-height: 1.15; font-weight: 700; font-size: 1.02rem; }
.store svg { width: 22px; height: 22px; flex: none; }
.store small { display: block; font-weight: 500; font-size: 0.7rem; opacity: 0.8; }
.soon-btn { display: inline-block; margin-top: 0.4rem; background: #fff; color: var(--navy); border: 1.5px solid var(--navy); border-radius: 999px; padding: 0.7rem 1.4rem; font-weight: 700; text-decoration: none; }
.soon-btn:hover { background: var(--navy); color: #fff; }
.soon-note { margin: 0; font-size: 0.9rem; color: var(--muted); }
.soon-more { display: grid; gap: 1rem; }
.soon-more h2 { font-size: 1.8rem; }
.soon-links { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 0.9rem; }
.soon-links a { display: grid; gap: 0.3rem; padding: 1.1rem 1.2rem; border: 1px solid var(--rule); border-radius: var(--radius); text-decoration: none; color: var(--muted); font-size: 0.95rem; }
.soon-links a b { color: var(--navy); font-size: 1.05rem; }
.soon-links a:hover { border-color: var(--celeste); }
</style>"""


def main():
    date = json.load(open(os.path.join(ROOT, "canastas", "catalogo.json"), encoding="utf-8"))["date"]
    page = make_chrome()(TITLE, DESC, "canastas/", PAGE, PAGE_CSS)
    page = page.replace("</style>\n<header", 'html:not([lang=en]) .en{display:none!important} html[lang=en] .es{display:none!important}\n</style>\n<header', 1)
    with open(os.path.join(ROOT, "canastas", "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    # the app is no longer on the website
    old = os.path.join(ROOT, "canastas", "app.html")
    if os.path.exists(old):
        os.remove(old)
    add_to_sitemap(["canastas/"], date)
    print("canastas/index.html (app coming soon) written")


if __name__ == "__main__":
    main()
