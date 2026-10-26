# La Canasta: builds the monthly report numbers.
# Runs every day after compute_index.py. For every month it writes index/informes/YYYY-MM.json,
# which the page informe.html turns into the report. The current month is a draft until it ends.
#
# Monthly inflation, like INDEC: average of the month vs average of the month before
# (only when both months have at least 20 days of data).
# Always also given: "end to end" = last day of the month vs last day of the month before.

import calendar
import csv
import glob
import gzip
import json
import os
from collections import defaultdict

MIN_DAYS = 20     # days of data a month needs to count as a full month
MAX_JUMP = 3.0    # same rule as the index: bigger jumps are treated as errors
TOP = 5           # how many products to show going up and going down


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pct(new, old):
    return round((new / old - 1) * 100, 2) if old else None


daily = read_csv("index/daily.csv")
groups = read_csv("index/groups.csv")
basket = {(r["shop"], r["sku_id"]): r for r in read_csv("basket.csv")}
shops = [c[:-5] for c in daily[0] if c.endswith("_paid") and c != "index_paid"]

by_month = defaultdict(list)
for r in daily:
    by_month[r["date"][:7]].append(r)
months = sorted(by_month)
all_dates = [r["date"] for r in daily]

group_at = defaultdict(dict)  # date -> group -> row
for g in groups:
    group_at[g["date"]][g["group"]] = g

# Basket prices for every day (price paid, in stock only), and how many prices were collected
prices = defaultdict(dict)    # date -> (shop, sku) -> price
collected = defaultdict(int)  # date -> number of prices saved that day
for path in sorted(glob.glob("data/????-??-??.csv.gz")):
    date = os.path.basename(path)[:10]
    with gzip.open(path, "rt", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            collected[date] += 1
            key = (r["shop"], str(r["sku_id"]))
            if key in basket and r.get("available") == "True":
                try:
                    p = float(r["price"])
                except (TypeError, ValueError):
                    continue
                if p > 0:
                    prices[date][key] = p


def last_price(key, upto, since):
    """Last in-stock price of a product between two dates (both included)."""
    for d in sorted(prices, reverse=True):
        if since <= d <= upto and key in prices[d]:
            return prices[d][key]
    return None


os.makedirs("index/informes", exist_ok=True)
listing = []
for i, m in enumerate(months):
    rows = by_month[m]
    prev = by_month.get(months[i - 1], []) if i > 0 else []
    y, mo = int(m[:4]), int(m[5:])
    month_end = f"{m}-{calendar.monthrange(y, mo)[1]:02d}"
    complete = rows[-1]["date"] == month_end or any(d > month_end for d in all_dates)

    base = prev[-1] if prev else rows[0]   # last day of the month before (or the very first day)
    end = rows[-1]
    full = len(rows) >= MIN_DAYS and len(prev) >= MIN_DAYS

    headline = {
        "end_to_end_paid": pct(float(end["index_paid"]), float(base["index_paid"])),
        "end_to_end_regular": pct(float(end["index_regular"]), float(base["index_regular"])),
        "avg_paid": None, "avg_regular": None,
    }
    if full:
        avg = lambda rs, k: sum(float(r[k]) for r in rs) / len(rs)
        headline["avg_paid"] = pct(avg(rows, "index_paid"), avg(prev, "index_paid"))
        headline["avg_regular"] = pct(avg(rows, "index_regular"), avg(prev, "index_regular"))
    method = "average" if full else "end_to_end"
    main = headline["avg_paid"] if full else headline["end_to_end_paid"]

    shop_changes = [{"shop": s, "pct": pct(float(end[f"{s}_paid"]), float(base[f"{s}_paid"]))} for s in shops]

    group_changes = []
    for g, gr in group_at[end["date"]].items():
        b = group_at[base["date"]].get(g)
        if b:
            group_changes.append({"group": g, "in_headline": gr["in_headline_index"] == "yes",
                                  "pct": pct(float(gr["index_paid"]), float(b["index_paid"]))})
    group_changes.sort(key=lambda x: -x["pct"])

    # Each product: last price of this month vs last price of the month before
    month_start = f"{m}-01"
    prev_start = f"{months[i - 1]}-01" if i > 0 else month_start
    products = []
    for key, b in basket.items():
        if key[0] not in shops:
            continue  # Coto is not in the index
        now = last_price(key, end["date"], month_start)
        before = last_price(key, base["date"], prev_start) if prev else last_price(key, rows[0]["date"], month_start)
        if not now or not before or not (1 / MAX_JUMP <= now / before <= MAX_JUMP):
            continue
        products.append({"type": b["type_id"], "type_en": b["product_type"], "shop": key[0], "name": b["name"],
                         "before": before, "now": now, "pct": pct(now, before)})
    products.sort(key=lambda x: -x["pct"])
    up = [p for p in products if p["pct"] > 0]
    down = [p for p in products if p["pct"] < 0]

    report = {
        "month": m, "complete": complete, "full_month": full, "method": method, "inflation": main,
        "base_date": base["date"], "end_date": end["date"], "days_of_data": len(rows),
        "prices_collected": sum(collected[r["date"]] for r in rows),
        "headline": headline, "shops": shop_changes, "groups": group_changes,
        "products_compared": len(products), "products_up": len(up), "products_down": len(down),
        "products_same": len(products) - len(up) - len(down),
        "top_up": up[:TOP], "top_down": sorted(down, key=lambda x: x["pct"])[:TOP],
        "series": [{"date": r["date"], "paid": float(r["index_paid"]), "regular": float(r["index_regular"])}
                   for r in ([base] if prev else []) + rows],
    }
    with open(f"index/informes/{m}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    listing.append({"month": m, "complete": complete, "days_of_data": len(rows),
                    "publishable": complete and len(rows) >= MIN_DAYS, "inflation": main, "method": method})

with open("index/informes/lista.json", "w", encoding="utf-8") as f:
    json.dump(listing, f, ensure_ascii=False, indent=1)
print("Monthly reports:", ", ".join(f"{x['month']} ({'ready' if x['publishable'] else 'draft'})" for x in listing))
