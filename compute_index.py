# La Canasta: calculates the index from the daily price files.
#
# Method, in plain words:
# 1. For every basket product, compare today's price with the last day it was collected (in stock both days).
# 2. Inside each INDEC group (e.g. "Dairy and eggs"), average those changes (geometric mean).
# 3. Combine the groups using INDEC's official weights (how much Buenos Aires households spend on each).
# 4. Chain the days together. The first full week (24 to 30 October 2026, one of each weekday) = 100 on
#    average, so the start does not depend on one day's offers (24 October was a Saturday full of promotions).
# Done twice: with the price people pay (promotions included) and with the regular price.
# Jumbo is left out of the regular-price index: its list_price field is not a real list price
# (it is the price paid without VAT, times 100), so it would carry Jumbo's promotions.
# Each shop is only ever compared with itself.
# The basket has up to 5 products of each type per shop (567 in all). Each type counts once inside
# its group, whatever the number of products: first the average of each type (each shop counting
# the same), then the average of the types in the group. The bigger basket was added on 1 November
# 2026 and the whole index was recalculated with it from the first day (24 October 2026).
# A product added later gets a from_date in basket.csv: it is followed before that day, but not counted.
# Doubtful prices listed in notas/excluir.csv (found by the daily review) are left out, never replaced:
# that product is simply not compared on that day, for that kind of price.

import csv
import glob
import gzip
import math
import os
from collections import defaultdict

MAX_JUMP = 3.0  # a price that triples or falls to a third overnight is treated as a data error
CHANGE_DATE = "2026-10-24"  # type-by-type averaging applies from this day (the first day of data)
BASE_WEEK = ("2026-10-24", "2026-10-30")  # the average of these 7 days = 100
NO_REGULAR = {"Jumbo"}  # shops without a real list price: not in the regular-price index

# ---------- Read the basket and the weights ----------
basket = {}  # (shop, sku_id) -> type_id
from_date = {}  # (shop, sku_id) -> first day the product counts ("" = from the start)
with open("basket.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        basket[(r["shop"], r["sku_id"])] = r["type_id"]
        from_date[(r["shop"], r["sku_id"])] = (r.get("from_date") or "").strip()

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
                today[key] = {"paid": paid} if key[0] in NO_REGULAR else {"paid": paid, "regular": regular or paid}
    days[date] = today

dates = sorted(days)
if not dates:
    raise SystemExit("No data files found.")

# ---------- Prices left out after review (notas/excluir.csv) ----------
# Columns: date, shop, sku_id, kind (paid, regular or both), reason
EXCLUDED = set()
if os.path.exists("notas/excluir.csv"):
    with open("notas/excluir.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            kinds = ("paid", "regular") if r["kind"].strip() == "both" else (r["kind"].strip(),)
            for k in kinds:
                EXCLUDED.add((r["date"].strip(), r["shop"].strip(), str(r["sku_id"]).strip(), k))

# ---------- Chain the days ----------
SHOP_NAMES = sorted({shop for shop, _ in basket})
SCOPES = ["all"] + SHOP_NAMES  # the whole index, plus one index per shop
level = {(s, kind): 100.0 for s in SCOPES for kind in ("paid", "regular")}
group_level = {(g, kind): 100.0 for g in group_name for kind in ("paid", "regular")}
last_seen = {}  # ((shop, sku), kind) -> price on the last day it was in stock (and not left out)
daily_rows, group_rows, checks = [], [], []
n_excluded = 0

def mean(xs):
    return sum(xs) / len(xs)


def group_change(c, scope):
    """c: list of (type, shop, log change). Old method: plain average. New: type by type."""
    if date < CHANGE_DATE:
        return mean([x for _, _, x in c])
    per_type = defaultdict(lambda: defaultdict(list))
    for t, shop, x in c:
        per_type[t][shop].append(x)
    # inside a type: average per shop, then each shop counts the same (for one shop: just its average)
    return mean([mean([mean(v) for v in shops.values()]) for shops in per_type.values()])


for i, date in enumerate(dates):
    changes = defaultdict(list)  # (scope, group, kind) -> list of (type, shop, log price change)
    n_used = 0
    n_active = sum(1 for key in days[date] if from_date[key] <= date)
    for key, now in days[date].items():
        active = from_date[key] <= date
        usable = {}
        for kind in now:
            if (date, key[0], key[1], kind) in EXCLUDED:
                n_excluded += 1
            else:
                usable[kind] = now[kind]
        comparable = [kind for kind in usable if (key, kind) in last_seen]
        ok = True
        for kind in comparable:
            before = last_seen[(key, kind)]
            ratio = usable[kind] / before
            if ratio > MAX_JUMP or ratio < 1 / MAX_JUMP:
                if active:
                    checks.append(f"{date} {key[0]} {basket[key]} ({kind}): {before} -> {usable[kind]}, left out")
                ok = False
        if not ok:
            continue  # keep comparing against the last good price
        if comparable and active:
            n_used += 1
            t = basket[key]
            g = group_of[t]
            for kind in comparable:
                lc = math.log(usable[kind] / last_seen[(key, kind)])
                changes[("all", g, kind)].append((t, key[0], lc))
                changes[(key[0], g, kind)].append((t, key[0], lc))
        for kind, v in usable.items():
            last_seen[(key, kind)] = v

    # Groups: geometric mean of their products' changes
    for g in group_name:
        for kind in ("paid", "regular"):
            c = changes.get(("all", g, kind))
            if c:
                group_level[(g, kind)] *= math.exp(group_change(c, "all"))

    # Whole index and each shop: weighted average of group changes (only groups with an official weight)
    for s in SCOPES:
        for kind in ("paid", "regular"):
            num = den = 0.0
            for g in group_name:
                c = changes.get((s, g, kind))
                if c and weight[g]:
                    num += weight[g] * group_change(c, s)
                    den += weight[g]
            if den:
                level[(s, kind)] *= math.exp(num / den)

    row = {"date": date, "index_paid": level[("all", "paid")],
           "index_regular": level[("all", "regular")],
           "products_in_stock": n_active, "products_compared": n_used}
    for s in SHOP_NAMES:
        row[f"{s}_paid"] = level[(s, "paid")]
    daily_rows.append(row)
    for g in group_name:
        group_rows.append({"date": date, "group": g, "group_name": group_name[g],
                           "in_headline_index": "yes" if weight[g] else "no (weight pending)",
                           "index_paid": group_level[(g, "paid")],
                           "index_regular": group_level[(g, "regular")]})

# ---------- Base: the average of the first full week = 100 (each series on its own) ----------
in_base = lambda r: BASE_WEEK[0] <= r["date"] <= BASE_WEEK[1]
if sum(1 for r in daily_rows if in_base(r)) == 7:
    for col in [c for c in daily_rows[0] if c.startswith("index_") or c.endswith("_paid")]:
        b = mean([r[col] for r in daily_rows if in_base(r)])
        for r in daily_rows:
            r[col] = r[col] / b * 100
    for g in group_name:
        rows_g = [r for r in group_rows if r["group"] == g]
        for col in ("index_paid", "index_regular"):
            b = mean([r[col] for r in rows_g if in_base(r)])
            for r in rows_g:
                r[col] = r[col] / b * 100
for r in daily_rows + group_rows:
    for col in r:
        if col.startswith("index_") or col.endswith("_paid"):
            r[col] = round(r[col], 3)

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
print(f"{n_excluded} prices left out after review (notas/excluir.csv).")

# ---------- Monthly report numbers (never stops the daily save if something goes wrong) ----------
import subprocess
import sys
result = subprocess.run([sys.executable, "make_report.py"])
if result.returncode != 0:
    print("WARNING: the monthly report could not be built today. The index is saved anyway.")
