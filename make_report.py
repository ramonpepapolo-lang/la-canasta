# La Canasta: builds the monthly report numbers.
# Runs every day after compute_index.py. For every month it writes index/informes/YYYY-MM.json,
# which the page informe.html turns into the report. The current month is a draft until it ends.
#
# Monthly inflation, like INDEC: average of the month vs average of the month before
# (only when both months have at least 20 days of data).
# Always also given: "end to end" = last day of the month vs last day of the month before.
# When the month before is too short (November 2026, the first full month): "week" = each product's
# average price in the last 7 days of the month vs its average price on the same days of the month
# before (24-30 November vs 24-30 October). Same days of the week on both sides, so weekend promos
# do not bias it. Products are combined like the index: type, then group, then INDEC weights.

import calendar
import csv
import glob
import gzip
import json
import math
import os
from collections import defaultdict

MIN_DAYS = 20     # days of data a month needs to count as a full month
MAX_JUMP = 3.0    # same rule as the index: bigger jumps are treated as errors
TOP = 5           # how many products to show going up and going down
WEEK = 7          # days in each window of the "week" method
MIN_WEEK_DAYS = 5 # days with data each window needs
MIN_IN_STOCK = 4  # days in stock a product needs in each window to be compared


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pct(new, old):
    return round((new / old - 1) * 100, 2) if old else None


daily = read_csv("index/daily.csv")
groups = read_csv("index/groups.csv")
basket = {(r["shop"], r["sku_id"]): r for r in read_csv("basket.csv")}
shops = [c[:-5] for c in daily[0] if c.endswith("_paid") and c != "index_paid"]
group_of, weight = {}, {}
for r in read_csv("weights.csv"):
    weight[r["group"]] = float(r["spending_2004_gba"]) if r["spending_2004_gba"] else None
    for t in r["basket_types"].split(";"):
        group_of[t] = r["group"]

by_month = defaultdict(list)
for r in daily:
    by_month[r["date"][:7]].append(r)
months = sorted(by_month)
all_dates = [r["date"] for r in daily]

group_at = defaultdict(dict)  # date -> group -> row
for g in groups:
    group_at[g["date"]][g["group"]] = g

# Prices left out after the daily review (same file the index uses)
EXCL_PAID, EXCL_REG = set(), set()
if os.path.exists("notas/excluir.csv"):
    for r in read_csv("notas/excluir.csv"):
        k = (r["date"].strip(), r["shop"].strip(), str(r["sku_id"]).strip())
        if r["kind"].strip() in ("paid", "both"):
            EXCL_PAID.add(k)
        if r["kind"].strip() in ("regular", "both"):
            EXCL_REG.add(k)

# Basket prices for every day (price paid, in stock only), and how many prices were collected
prices = defaultdict(dict)    # date -> (shop, sku) -> price
regular = defaultdict(dict)   # date -> (shop, sku) -> regular price (list price, or the price paid)
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
                if p <= 0:
                    continue
                if (date, key[0], key[1]) not in EXCL_PAID:
                    prices[date][key] = p
                try:
                    lp = float(r["list_price"])
                except (TypeError, ValueError):
                    lp = 0.0
                if (date, key[0], key[1]) not in EXCL_REG:
                    regular[date][key] = lp if lp > 0 else p


def last_price(key, upto, since):
    """Last in-stock price of a product between two dates (both included)."""
    for d in sorted(prices, reverse=True):
        if since <= d <= upto and key in prices[d]:
            return prices[d][key]
    return None


def mean(xs):
    return sum(xs) / len(xs)


def week_windows(m, prev_m, end_date):
    """The last WEEK days up to end_date, and the same days of the month before (only days with data)."""
    last = int(end_date[8:])
    py, pm = int(prev_m[:4]), int(prev_m[5:])
    days_prev = calendar.monthrange(py, pm)[1]
    nums = [d for d in range(last - WEEK + 1, last + 1) if d >= 1]
    now = [f"{m}-{d:02d}" for d in nums if f"{m}-{d:02d}" in prices]
    before = [f"{prev_m}-{d:02d}" for d in nums if d <= days_prev and f"{prev_m}-{d:02d}" in prices]
    return now, before


def week_compare(now_days, before_days):
    """Each product: average price in one window vs the other. Returns products and the combined changes."""
    products = []
    logs = {"paid": defaultdict(list), "regular": defaultdict(list)}  # kind -> (type, shop) -> logs
    for key, b in basket.items():
        if key[0] not in shops:
            continue
        for kind, src in (("paid", prices), ("regular", regular)):
            pn = [src[d][key] for d in now_days if key in src[d]]
            pb = [src[d][key] for d in before_days if key in src[d]]
            if len(pn) < MIN_IN_STOCK or len(pb) < MIN_IN_STOCK:
                continue
            ratio = mean(pn) / mean(pb)
            if not (1 / MAX_JUMP <= ratio <= MAX_JUMP):
                continue
            logs[kind][(b["type_id"], key[0])].append(math.log(ratio))
            if kind == "paid":
                products.append({"type": b["type_id"], "type_en": b["product_type"], "shop": key[0],
                                 "name": b["name"], "before": round(mean(pb), 2), "now": round(mean(pn), 2),
                                 "pct": pct(mean(pn), mean(pb))})

    def combine(kind, shop=None, only_group=None):
        per_type = defaultdict(list)  # type -> [shop average]
        for (t, s), xs in logs[kind].items():
            if shop is None or s == shop:
                per_type[t].append(mean(xs))
        per_group = defaultdict(list)
        for t, xs in per_type.items():
            per_group[group_of[t]].append(mean(xs))
        if only_group:
            xs = per_group.get(only_group)
            return round((math.exp(mean(xs)) - 1) * 100, 2) if xs else None
        num = den = 0.0
        for g, xs in per_group.items():
            if weight.get(g):
                num += weight[g] * mean(xs)
                den += weight[g]
        return round((math.exp(num / den) - 1) * 100, 2) if den else None

    return products, combine


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
    week_now, week_before = week_windows(m, months[i - 1], end["date"]) if prev else ([], [])
    use_week = (not full and len(week_now) >= MIN_WEEK_DAYS and len(week_before) >= MIN_WEEK_DAYS)
    if use_week:
        week_products, combine = week_compare(week_now, week_before)
        headline["week_paid"] = combine("paid")
        headline["week_regular"] = combine("regular")
        headline["week_now"] = [week_now[0], week_now[-1]]
        headline["week_before"] = [week_before[0], week_before[-1]]
    method = "average" if full else ("week" if use_week else "end_to_end")
    main = {"average": headline["avg_paid"], "week": headline.get("week_paid"),
            "end_to_end": headline["end_to_end_paid"]}[method]

    if use_week:
        shop_changes = [{"shop": s, "pct": combine("paid", shop=s)} for s in shops]
    else:
        shop_changes = [{"shop": s, "pct": pct(float(end[f"{s}_paid"]), float(base[f"{s}_paid"]))} for s in shops]

    group_changes = []
    for g, gr in group_at[end["date"]].items():
        b = group_at[base["date"]].get(g)
        if use_week:
            v = combine("paid", only_group=g)
            if v is not None:
                group_changes.append({"group": g, "in_headline": gr["in_headline_index"] == "yes", "pct": v})
        elif b:
            group_changes.append({"group": g, "in_headline": gr["in_headline_index"] == "yes",
                                  "pct": pct(float(gr["index_paid"]), float(b["index_paid"]))})
    group_changes.sort(key=lambda x: -x["pct"])

    # Each product: last price of this month vs last price of the month before
    month_start = f"{m}-01"
    prev_start = f"{months[i - 1]}-01" if i > 0 else month_start
    products = week_products if use_week else []
    for key, b in ([] if use_week else basket.items()):
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

# The "week" figure also goes into index/monthly.csv (column week_paid_pct), next to the other methods
monthly_path = "index/monthly.csv"
if os.path.exists(monthly_path):
    mrows = read_csv(monthly_path)
    week_by_month = {x["month"]: x["inflation"] for x in listing if x["method"] == "week"}
    for r in mrows:
        r["week_paid_pct"] = week_by_month.get(r["month"], "")
    with open(monthly_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(mrows[0].keys()))
        w.writeheader()
        w.writerows(mrows)
