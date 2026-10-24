# La Canasta: every day, collects prices from Jumbo, Carrefour, ChangoMas and Dia
# and saves them in the "data" folder, one file per day.

import csv
import datetime
import gzip
import os
import sys
import time
from urllib.parse import quote
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

SHOPS = {
    "Jumbo": "https://www.jumbo.com.ar",
    "Carrefour": "https://www.carrefour.com.ar",
    "ChangoMas": "https://www.masonline.com.ar",
    "Dia": "https://diaonline.supermercadosdia.com.ar",
}

SEARCHES = [
    "leche", "yogur", "manteca", "queso", "dulce de leche", "huevos",
    "pan lactal", "harina", "arroz", "fideos", "azucar", "aceite girasol",
    "yerba", "cafe", "te en saquitos", "galletitas", "pure de tomate", "mayonesa",
    "carne picada", "pollo", "papa", "cebolla", "tomate", "banana", "manzana",
    "gaseosa", "agua mineral", "cerveza", "vino tinto",
    "papel higienico", "detergente", "lavandina", "jabon en polvo",
    "shampoo", "pasta dental", "jabon de tocador",
]

today = datetime.date.today().isoformat()
prices = {}  # one entry per shop + product, so nothing is saved twice

for shop, base in SHOPS.items():
    before = len(prices)
    for term in SEARCHES:
        url = f"{base}/api/catalog_system/pub/products/search?ft={quote(term)}&_from=0&_to=49"
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
            products = r.json()
        except Exception as e:
            print(f"{shop} '{term}': failed ({e})")
            continue

        for p in products:
            for item in p.get("items", []):
                try:
                    offer = item["sellers"][0]["commertialOffer"]
                except (KeyError, IndexError):
                    continue
                prices[(shop, item.get("itemId"))] = {
                    "date": today,
                    "shop": shop,
                    "search": term,
                    "sku_id": item.get("itemId"),
                    "ean": item.get("ean"),
                    "name": item.get("nameComplete") or p.get("productName"),
                    "brand": p.get("brand"),
                    "category": (p.get("categories") or [""])[0],
                    "unit": item.get("measurementUnit"),
                    "unit_multiplier": item.get("unitMultiplier"),
                    "price": offer.get("Price"),
                    "list_price": offer.get("ListPrice"),
                    "available": offer.get("IsAvailable"),
                }
        time.sleep(2)  # be polite: wait 2 seconds between searches
    print(f"{shop}: {len(prices) - before} prices")

if not prices:
    sys.exit("Got no prices at all. Something is wrong.")

os.makedirs("data", exist_ok=True)
path = f"data/{today}.csv.gz"
rows = list(prices.values())
with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
print(f"Saved {len(rows)} prices to {path}")
