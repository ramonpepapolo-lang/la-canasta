# La Canasta: calculates the index from the daily price files.
#
# Method, in plain words:
# 1. For every basket product, compare today's price with the last day it was collected (in stock both days).
# 2. Inside each INDEC group (e.g. "Dairy and eggs"), average those changes (geometric mean).
# 3. Combine the groups using INDEC's official weights (how much Buenos Aires households spend on each).
# 4. Chain the days together. Day 1 = 100.
# Done twice: with the price people pay (promotions included) and with the regular price.
# Each shop is only ever compared with itself.

import csv
import glob
import gzip
import math
import os
from collections import defaultdict

MAX_JUMP = 3.0  # a price that triples or falls to a third overnight is treated as a data error

# ---------- Read the basket and the weights ----------
basket = {}  # (shop, sku_id) -> type_id
with open("basket.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        basket[(r["shop"], r["sku_id"])] = r["type_id"]

group_of, weight, group_name = {}, {}, {}
with open("weights.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        group_name[r["group"]] = r["group_name"]
        weight[r["group"]] = float(r["spending_2004_gba"]) if r["spending_2004_gba"] else None
        for t in r["basket_types"].split(";"):
            group_of[t] = r["group"]


def number(x):
    try:
        v = float(x)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


# ---------- Read every day's prices (basket products only) ----------
days = {}  # date -> {(shop, sku): {"paid": price, "regular": price}}
for path in sorted(glob.glob("data/????-??-??.csv.gz")):
    date = os.path.basename(path)[:10]
    today = {}
    with gzip.open(path, "rt", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["shop"], str(r["sku_id"]))
            if key not in basket or r.get("available") != "True":
                continue  # not in the basket, or out of stock: skipped, never guessed
            paid, regular = number(r["price"]), number(r["list_price"])
            if paid:
                today[key] = {"paid": paid, "regular": regular or paid}
    days[date] = today

dates = sorted(days)
if not dates:
    raise SystemExit("No data files found.")

# ---------- Chain the days ----------
SHOP_NAMES = sorted({shop for shop, _ in basket})
SCOPES = ["all"] + SHOP_NAMES  # the whole index, plus one index per shop
level = {(s, kind): 100.0 for s in SCOPES for kind in ("paid", "regular")}
group_level = {(g, kind): 100.0 for g in group_name for kind in ("paid", "regular")}
last_seen = {}  # (shop, sku) -> (date, prices) from the last day it was in stock
daily_rows, group_rows, checks = [], [], []

for i, date in enumerate(dates):
    changes = defaultdict(list)  # (scope, group, kind) -> list of log price changes
    n_used = 0
    for key, now in days[date].items():
        if key in last_seen:
            _, before = last_seen[key]
            ok = True
            for kind in ("paid", "regular"):
                ratio = now[kind] / before[kind]
                if ratio > MAX_JUMP or ratio < 1 / MAX_JUMP:
                    checks.append(f"{date} {key[0]} {basket[key]} ({kind}): {before[kind]} -> {now[kind]}, left out")
                    ok = False
            if not ok:
                continue  # keep comparing against the last good price
            n_used += 1
            g = group_of[basket[key]]
            for kind in ("paid", "regular"):
                lc = math.log(now[kind] / before[kind])
                changes[("all", g, kind)].append(lc)
                changes[(key[0], g, kind)].append(lc)
        last_seen[key] = (date, now)

    # Groups: geometric mean of their products' changes
    for g in group_name:
        for kind in ("paid", "regular"):
            c = changes.get(("all", g, kind))
            if c:
                group_level[(g, kind)] *= math.exp(sum(c) / len(c))

    # Whole index and each shop: weighted average of group changes (only groups with an official weight)
    for s in SCOPES:
        for kind in ("paid", "regular"):
            num = den = 0.0
            for g in group_name:
                c = changes.get((s, g, kind))
                if c and weight[g]:
                    num += weight[g] * sum(c) / len(c)
                    den += weight[g]
            if den:
                level[(s, kind)] *= math.exp(num / den)

    row = {"date": date, "index_paid": round(level[("all", "paid")], 3),
           "index_regular": round(level[("all", "regular")], 3),
           "products_in_stock": len(days[date]), "products_compared": n_used}
    for s in SHOP_NAMES:
        row[f"{s}_paid"] = round(level[(s, "paid")], 3)
    daily_rows.append(row)
    for g in group_name:
        group_rows.append({"date": date, "group": g, "group_name": group_name[g],
                           "in_headline_index": "yes" if weight[g] else "no (weight pending)",
                           "index_paid": round(group_level[(g, "paid")], 3),
                           "index_regular": round(group_level[(g, "regular")], 3)})

# ---------- Monthly inflation: average of the month vs average of the month before ----------
months = defaultdict(list)
for r in daily_rows:
    months[r["date"][:7]].append(r)
monthly_rows, prev = [], None
for m in sorted(months):
    rows = months[m]
    avg_paid = sum(r["index_paid"] for r in rows) / len(rows)
    avg_reg = sum(r["index_regular"] for r in rows) / len(rows)
    out = {"month": m, "days_of_data": len(rows),
           "avg_index_paid": round(avg_paid, 3), "avg_index_regular": round(avg_reg, 3),
           "last_index_paid": rows[-1]["index_paid"],
           "inflation_paid_pct": "", "inflation_regular_pct": "", "end_to_end_paid_pct": ""}
    if prev and prev["days_of_data"] >= 20 and len(rows) >= 20:  # INDEC-style: needs two full-ish months
        out["inflation_paid_pct"] = round((avg_paid / prev["avg_index_paid"] - 1) * 100, 2)
        out["inflation_regular_pct"] = round((avg_reg / prev["avg_index_regular"] - 1) * 100, 2)
    if prev and len(rows) >= 20:  # last day of this month vs last day of the month before
        out["end_to_end_paid_pct"] = round((rows[-1]["index_paid"] / prev["last_index_paid"] - 1) * 100, 2)
    monthly_rows.append(out)
    prev = out

# ---------- Save ----------
os.makedirs("index", exist_ok=True)
for name, rows in [("daily", daily_rows), ("groups", group_rows), ("monthly", monthly_rows)]:
    with open(f"index/{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
with open("index/checks.txt", "w", encoding="utf-8") as f:
    f.write("Prices left out because they looked like errors:\n")
    f.write("\n".join(checks) if checks else "None")
    f.write("\n")

last = daily_rows[-1]
print(f"{len(dates)} days. Latest ({last['date']}): index {last['index_paid']} "
      f"(regular price {last['index_regular']}), {last['products_compared']} products compared.")
print(f"{len(checks)} suspicious prices left out.")

# ---------- Monthly report numbers (never stops the daily save if something goes wrong) ----------
import subprocess
import sys
result = subprocess.run([sys.executable, "make_report.py"])
if result.returncode != 0:
    print("WARNING: the monthly report could not be built today. The index is saved anyway.")
