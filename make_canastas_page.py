"""Writes canastas/index.html, the website's "Creá tu canasta" page: the same screens as the La Canasta app
(app/src/app.html), so the website and the app are identical. On a phone it fills the screen like the app; on a
computer it shows inside an iPhone frame, with the website's links next to it.

The page reads today's data live from the website: app-datos/datos.json (index, ranking, moves), canastas/datos.json
and canastas/catalogo.json (made by make_canastas.py every day). Run after make_canastas.py (and after any change to
app/src/app.html). The AI assistant answers when an AI service is set (window.LC_AI_URL); without it, the built-in
assistant answers.
"""
import json, os, re
from make_price_pages import add_to_sitemap, SITE

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
<link rel="canonical" href="{SITE}/canastas/">
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
    with open(os.path.join(ROOT, "canastas", "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    add_to_sitemap(["canastas/"], date)
    print("canastas/index.html written (the app's screens), data of", date)


if __name__ == "__main__":
    main()
