# La Canasta: prices of more supermarkets, saved every day but NOT used by the index or the website.
# Disco and Vea (Greater Buenos Aires, Cencosud like Jumbo), Toledo (Mar del Plata) and Cordiez (Cordoba).
# Same searches and same columns as scrape_supermarkets.py. Result: data-extra/YYYY-MM-DD.csv.gz,
# kept on the separate branch "datos-extra" (workflow "Más supermercados"), so they can be added later
# with their whole history.
import csv, datetime, gzip, os, time
from urllib.parse import quote
from zoneinfo import ZoneInfo
import requests
import importlib.util

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SHOPS = {"Disco": "https://www.disco.com.ar", "Vea": "https://www.vea.com.ar",
         "Toledo": "https://www.toledodigital.com.ar", "Cordiez": "https://www.cordiez.com.ar"}
# the same search list as the daily collection (read from scrape_supermarkets.py without running it)
src = open("scrape_supermarkets.py", encoding="utf-8").read()
ns = {}
exec(src[src.index("SEARCHES = ["):src.index("COLUMNS = [")], ns)
TERMS = ns["SEARCHES"] + ns["EXTRA_SEARCHES"]
COLUMNS = ["date", "shop", "search", "sku_id", "ean", "name", "brand", "category",
           "unit", "unit_multiplier", "price", "list_price", "available", "basket_type", "extra"]
today = datetime.datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date().isoformat()
rows = {}
for shop, base in SHOPS.items():
    before, fails = len(rows), 0
    for term in TERMS:
        try:
            d = requests.get(f"{base}/api/catalog_system/pub/products/search?ft={quote(term)}&_from=0&_to=49",
                             headers={"User-Agent": UA}, timeout=30).json()
        except Exception:
            d, fails = [], fails + 1
        for p in d if isinstance(d, list) else []:
            for it in p.get("items") or []:
                try:
                    o = it["sellers"][0]["commertialOffer"]
                except (KeyError, IndexError, TypeError):
                    continue
                k = (shop, it.get("itemId"))
                if k in rows:
                    continue
                rows[k] = {"date": today, "shop": shop, "search": term, "sku_id": it.get("itemId"), "ean": it.get("ean"),
                           "name": it.get("nameComplete") or p.get("productName"), "brand": p.get("brand"),
                           "category": (p.get("categories") or [""])[0], "unit": it.get("measurementUnit"),
                           "unit_multiplier": it.get("unitMultiplier"), "price": o.get("Price"),
                           "list_price": o.get("ListPrice"), "available": o.get("IsAvailable"), "basket_type": "", "extra": ""}
        time.sleep(1)
    print(f"{shop}: {len(rows) - before} prices ({fails} searches failed)")
os.makedirs("data-extra", exist_ok=True)
with gzip.open(f"data-extra/{today}.csv.gz", "wt", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLUMNS); w.writeheader(); w.writerows(rows.values())
print("saved", len(rows), "prices for", today)
