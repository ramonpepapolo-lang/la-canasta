"""Tries searches before they go into the daily collection (run by hand from GitHub: Actions > Probar búsquedas).
Fetches each term at Jumbo, Carrefour, ChangoMas and Dia and writes probe.csv.gz with the same columns as data/,
so the rules for new products in canastas/canastas.json can be written against the real product names.
Saves nothing in the repository. Usage: python probe_searches.py "term one, term two" (empty = EXTRA_SEARCHES)."""
import ast, csv, gzip, json, sys, time
from urllib.parse import quote
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SHOPS = {"Jumbo": "https://www.jumbo.com.ar", "Carrefour": "https://www.carrefour.com.ar",
         "ChangoMas": "https://www.masonline.com.ar", "Dia": "https://diaonline.supermercadosdia.com.ar"}
COLUMNS = ["date", "shop", "search", "sku_id", "ean", "name", "brand", "category", "unit", "unit_multiplier",
           "price", "list_price", "available", "basket_type", "extra"]
arg = sys.argv[1].strip() if len(sys.argv) > 1 else ""
if arg:
    terms = [t.strip() for t in arg.split(",") if t.strip()]
else:
    tree = ast.parse(open("scrape_supermarkets.py", encoding="utf-8").read())
    terms = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "EXTRA_SEARCHES")
rows, seen = [], set()
for shop, base in SHOPS.items():
    for term in terms:
        try:
            data = requests.get(f"{base}/api/catalog_system/pub/products/search?ft={quote(term)}&_from=0&_to=49",
                                headers={"User-Agent": UA}, timeout=30).json()
        except Exception as e:
            print(shop, term, "problem:", e); data = []
        for p in data if isinstance(data, list) else []:
            for item in p.get("items") or []:
                try:
                    offer = item["sellers"][0]["commertialOffer"]
                except (KeyError, IndexError, TypeError):
                    continue
                if (shop, item.get("itemId")) in seen:
                    continue
                seen.add((shop, item.get("itemId")))
                rows.append({"date": "probe", "shop": shop, "search": term, "sku_id": item.get("itemId"), "ean": item.get("ean"),
                             "name": item.get("nameComplete") or p.get("productName"), "brand": p.get("brand"),
                             "category": (p.get("categories") or [""])[0], "unit": item.get("measurementUnit"),
                             "unit_multiplier": item.get("unitMultiplier"), "price": offer.get("Price"),
                             "list_price": "" if shop == "Jumbo" else offer.get("ListPrice"), "available": offer.get("IsAvailable"),
                             "basket_type": "", "extra": ""})
        time.sleep(1)
    print(shop, sum(1 for r in rows if r["shop"] == shop), "products")
with gzip.open("probe.csv.gz", "wt", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows)
print(len(terms), "terms,", len(rows), "products")
