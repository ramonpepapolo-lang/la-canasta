# La Canasta: every day, collects prices from Jumbo, Carrefour, ChangoMas, Dia and Coto
# and saves them in the "data" folder, one file per day.

import csv
import datetime
import gzip
import json
import os
import statistics
import sys
import time
import uuid
from urllib.parse import quote
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

# These 4 use the same shop software (VTEX), so one method works for all of them
SHOPS = {
    "Jumbo": "https://www.jumbo.com.ar",
    "Carrefour": "https://www.carrefour.com.ar",
    "ChangoMas": "https://www.masonline.com.ar",
    "Dia": "https://diaonline.supermercadosdia.com.ar",
}

# Coto uses a search company called Constructor.io. These are Coto's public search keys.
COTO_KEYS = ["key_41VWjhgxyQGjBiyf", "key_r6xzz4IAoTWcipni"]

SEARCHES = [
    "leche", "yogur", "manteca", "queso", "dulce de leche", "huevos",
    "pan lactal", "harina", "arroz", "fideos", "azucar", "aceite girasol",
    "yerba", "cafe", "te en saquitos", "galletitas", "pure de tomate", "mayonesa",
    "carne picada", "pollo", "papa", "cebolla", "tomate", "banana", "manzana",
    "gaseosa", "agua mineral", "cerveza", "vino tinto",
    "papel higienico", "detergente", "lavandina", "jabon en polvo",
    "shampoo", "pasta dental", "jabon de tocador",
]

COLUMNS = ["date", "shop", "search", "sku_id", "ean", "name", "brand", "category",
           "unit", "unit_multiplier", "price", "list_price", "available", "extra"]

today = datetime.date.today().isoformat()
prices = {}  # one entry per shop + product, so nothing is saved twice


def get_json(url):
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    return r.json()


# ---------- Part 1: Jumbo, Carrefour, ChangoMas, Dia ----------
for shop, base in SHOPS.items():
    before = len(prices)
    for term in SEARCHES:
        url = f"{base}/api/catalog_system/pub/products/search?ft={quote(term)}&_from=0&_to=49"
        try:
            products = get_json(url)
        except Exception as e:
            print(f"{shop} '{term}': failed ({e})")
            continue

        for p in products:
            for item in p.get("items", []):
                try:
                    offer = item["sellers"][0]["commertialOffer"]
                except (KeyError, IndexError):
                    continue
                if (shop, item.get("itemId")) in prices:
                    continue  # already saved from an earlier search
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
                    "extra": "",
                }
        time.sleep(2)  # be polite: wait 2 seconds between searches
    print(f"{shop}: {len(prices) - before} prices")


# ---------- Part 2: Coto ----------
def coto_search(term):
    for key in COTO_KEYS:
        url = (f"https://ac.cnstrc.com/search/{quote(term)}?key={key}"
               f"&c=ciojs-client-2.35.2&i={uuid.uuid4()}&s=1&num_results_per_page=100&page=1")
        try:
            return get_json(url)["response"]["results"]
        except Exception as e:
            print(f"Coto '{term}' with {key}: failed ({e})")
    return []


before = len(prices)
for term in SEARCHES:
    for res in coto_search(term):
        data = res.get("data", {})
        store_prices = [x for x in data.get("price", []) if x.get("formatPrice")]
        if not store_prices or ("Coto", data.get("id")) in prices:
            continue
        sale = [x["formatPrice"] for x in store_prices]
        lists = [x.get("listPrice") or x["formatPrice"] for x in store_prices]
        # Every other field Coto sends (except the long list of store prices), saved for later
        other = {k: v for k, v in data.items() if k != "price" and not isinstance(v, (dict, list))}
        other.update({"price_min": min(sale), "price_max": max(sale), "n_stores": len(sale)})
        ean = next((v for k, v in data.items() if "ean" in k.lower() and isinstance(v, (str, int))), None)
        prices[("Coto", data.get("id"))] = {
            "date": today,
            "shop": "Coto",
            "search": term,
            "sku_id": data.get("id"),
            "ean": ean,
            "name": res.get("value"),
            "brand": data.get("brand") or data.get("marca"),
            "category": data.get("category") or data.get("categoria"),
            "unit": None,
            "unit_multiplier": None,
            "price": statistics.median(sale),       # typical price across Coto's stores
            "list_price": statistics.median(lists),
            "available": True,
            "extra": json.dumps(other, ensure_ascii=False),
        }
    time.sleep(2)
print(f"Coto: {len(prices) - before} prices")


# ---------- Save ----------
if not prices:
    sys.exit("Got no prices at all. Something is wrong.")

os.makedirs("data", exist_ok=True)
path = f"data/{today}.csv.gz"
with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(prices.values())
print(f"Saved {len(prices)} prices to {path}")
