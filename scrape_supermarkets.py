# La Canasta: every day, collects prices from Jumbo, Carrefour, ChangoMas, Dia and Coto
# and saves them in the "data" folder, one file per day.
# It also makes sure every product in basket.csv is collected, even if a search misses it.

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
    "coca cola", "chimichurri", "asado", "nalga", "vacio", "milanesa",
]

COLUMNS = ["date", "shop", "search", "sku_id", "ean", "name", "brand", "category",
           "unit", "unit_multiplier", "price", "list_price", "available", "basket_type", "extra"]

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
                    "basket_type": "",
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
        store_prices = [x for x in data.get("price", []) if x.get("listPrice")]
        if not store_prices or ("Coto", data.get("id")) in prices:
            continue
        shelf = [x["listPrice"] for x in store_prices]                                  # price on the shelf
        per_unit = [x["formatPrice"] for x in store_prices if x.get("formatPrice")]    # price per kg or litre
        # Every other field Coto sends (except the long list of store prices), saved for later
        other = {k: v for k, v in data.items() if k != "price" and not isinstance(v, (dict, list))}
        other.update({"price_min": min(shelf), "price_max": max(shelf), "n_stores": len(shelf),
                      "price_per_unit": statistics.median(per_unit) if per_unit else None})
        prices[("Coto", data.get("id"))] = {
            "date": today,
            "shop": "Coto",
            "search": term,
            "sku_id": data.get("id"),
            "ean": None,  # Coto doesn't send barcodes
            "name": res.get("value"),
            "brand": data.get("product_brand"),
            "category": None,
            "unit": data.get("product_format"),
            "unit_multiplier": data.get("product_format_quantity"),
            "price": statistics.median(shelf),  # typical shelf price across Coto's stores
            "list_price": data.get("product_list_price"),
            "available": True,
            "basket_type": "",
            "extra": json.dumps(other, ensure_ascii=False),
        }
    time.sleep(2)
print(f"Coto: {len(prices) - before} prices")


# ---------- Part 3: make sure every basket product is collected ----------
def vtex_row(shop, p, item, term):
    offer = item["sellers"][0]["commertialOffer"]
    return {
        "date": today, "shop": shop, "search": term, "sku_id": item.get("itemId"),
        "ean": item.get("ean"), "name": item.get("nameComplete") or p.get("productName"),
        "brand": p.get("brand"), "category": (p.get("categories") or [""])[0],
        "unit": item.get("measurementUnit"), "unit_multiplier": item.get("unitMultiplier"),
        "price": offer.get("Price"), "list_price": offer.get("ListPrice"),
        "available": offer.get("IsAvailable"), "basket_type": "", "extra": "",
    }


missing = 0
with open("basket.csv", newline="", encoding="utf-8") as f:
    basket = list(csv.DictReader(f))
for b in basket:
    key = (b["shop"], b["sku_id"])
    if key not in prices and b["shop"] in SHOPS:
        url = f"{SHOPS[b['shop']]}/api/catalog_system/pub/products/search?fq=skuId:{b['sku_id']}"
        try:
            for p in get_json(url):
                for item in p.get("items", []):
                    if str(item.get("itemId")) == b["sku_id"]:
                        prices[key] = vtex_row(b["shop"], p, item, "basket")
        except Exception as e:
            print(f"Basket {b['type_id']} at {b['shop']}: failed ({e})")
        time.sleep(1)
    if key in prices:
        prices[key]["basket_type"] = b["type_id"]
    else:
        missing += 1
        print(f"Basket {b['type_id']} at {b['shop']}: not found today")
print(f"Basket: {len(basket) - missing} of {len(basket)} products found")


# ---------- Part 4 (one time only): save raw Coto data to investigate old prices ----------
debug_path = "data/coto_debug.json.gz"
if not os.path.exists(debug_path):
    raw = {}
    for term in ["yogur bebible", "pan lactal", "leche entera", "harina 000", "aceite girasol"]:
        for key in COTO_KEYS:
            url = (f"https://ac.cnstrc.com/search/{quote(term)}?key={key}"
                   f"&c=ciojs-client-2.35.2&i={uuid.uuid4()}&s=1&num_results_per_page=40&page=1")
            try:
                raw[f"{term}|{key}"] = get_json(url)
            except Exception as e:
                raw[f"{term}|{key}"] = str(e)
        time.sleep(2)
    os.makedirs("data", exist_ok=True)
    with gzip.open(debug_path, "wt", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False)
    print("Saved Coto investigation file")


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
