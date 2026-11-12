"""Writes 404.html: the friendly page GitHub Pages shows when an address does not exist.
Uses the same top bar and footer as the rest of the site (from metodo.html), with links from the site root."""
import os, re
from make_price_pages import make_chrome

ROOT = os.path.dirname(os.path.abspath(__file__))

BODY = """
<main class="container pp nf">
  <header class="pp-head">
    <p class="eyebrow">404</p>
    <h1><span data-lang="es">Esta página no existe</span><span data-lang="en">This page doesn't exist</span></h1>
    <p class="lede"><span data-lang="es">Puede que el enlace esté mal escrito o que la página se haya movido. Probá con alguno de estos:</span><span data-lang="en">The link may be mistyped, or the page may have moved. Try one of these:</span></p>
  </header>
  <div class="cards">
    <a class="card-link" href="../index.html#index"><h3><span data-lang="es">El índice de hoy</span><span data-lang="en">Today's index</span></h3><p><span data-lang="es">Cuánto se movieron los precios del súper.</span><span data-lang="en">How supermarket prices moved.</span></p></a>
    <a class="card-link" href="../precios/index.html"><h3><span data-lang="es">Precios de hoy</span><span data-lang="en">Today's prices</span></h3><p><span data-lang="es">Leche, yerba, aceite y más, súper por súper.</span><span data-lang="en">Milk, yerba, oil and more, shop by shop.</span></p></a>
    <a class="card-link" href="../precios/supermercado-mas-barato.html"><h3><span data-lang="es">¿Qué súper es más barato?</span><span data-lang="en">Which shop is cheapest?</span></h3><p><span data-lang="es">El ranking de esta semana.</span><span data-lang="en">This week's ranking.</span></p></a>
    <a class="card-link" href="../informes.html"><h3><span data-lang="es">Informes</span><span data-lang="en">Reports</span></h3><p><span data-lang="es">El informe de cada semana y de cada mes.</span><span data-lang="en">Every weekly and monthly report.</span></p></a>
  </div>
</main>"""


def main():
    page = make_chrome()("Página no encontrada · La Canasta", "Esta página no existe. Volvé al índice de La Canasta.", "404.html", BODY,
                         '<meta name="robots" content="noindex">')
    page = re.sub(r'(href|src)="\.\./', r'\1="/', page)
    page = re.sub(r'og/404\.png\?v=[0-9-]+', 'og/la-canasta.png', page)
    page = page.replace('href="/index.html"', 'href="/"').replace('href="/precios/index.html"', 'href="/precios/"')
    open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(page)
    print("404.html written")


if __name__ == "__main__":
    main()
