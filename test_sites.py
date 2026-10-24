# La Canasta: test whether each supermarket lets GitHub's servers see prices.

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SEARCH = "/api/catalog_system/pub/products/search?ft=leche%20la%20serenisima&_from=0&_to=4"

SITES = {
    "Jumbo": "https://www.jumbo.com.ar" + SEARCH,
    "Carrefour": "https://www.carrefour.com.ar" + SEARCH,
    "ChangoMas": "https://www.masonline.com.ar" + SEARCH,
    "Dia": "https://diaonline.supermercadosdia.com.ar" + SEARCH,
    "Coto": "https://www.cotodigital.com.ar/",
}

for name, url in SITES.items():
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
        print(f"\n=== {name}: status {r.status_code}")
        try:
            for p in r.json()[:3]:
                offer = p["items"][0]["sellers"][0]["commertialOffer"]
                print(f"  {p['productName']}: ${offer['Price']}")
        except Exception:
            print("  First bit of the page:", r.text[:200].replace("\n", " "))
    except requests.RequestException as e:
        print(f"\n=== {name}: could not connect ({e})")
