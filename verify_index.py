# La Canasta: independent check of the index (runs every day after compute_index.py).
#
# It recalculates every published number a second time, with separate code written a different way
# (price ratios multiplied together instead of logarithms added up), and compares the results with
# index/daily.csv, index/monthly.csv and the monthly reports. It also checks the data files make sense.
#
# If anything does not match, it exits with an error: the daily email warns Ramon, and the monthly
# report email is NOT sent until it passes. The prices themselves are always saved anyway.
# Result written to index/verificacion.txt.

import csv
import glob
import gzip
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TOL = 0.002          # allowed difference in index points (rounding)
MAX_DAILY_MOVE = 5.0 # % change of the whole index in one day that is flagged as suspicious

problems, notes = [], []


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


basket = {(r["shop"], r["sku_id"]): r["type_id"] for r in rows("basket.csv")}
starts = {(r["shop"], r["sku_id"]): (r.get("from_date") or "").strip() for r in rows("basket.csv")}
CHANGE_DATE = "2026-10-24"  # from this day each product type counts once inside its group
grp, w = {}, {}
for r in rows("weights.csv"):
    w[r["group"]] = float(r["spending_2004_gba"]) if r["spending_2004_gba"] else 0.0
    for t in r["basket_types"].split(";"):
        grp[t] = r["group"]
skip = set()
if os.path.exists("notas/excluir.csv"):
    for r in rows("notas/excluir.csv"):
        kinds = ["paid", "regular"] if r["kind"].strip() == "both" else [r["kind"].strip()]
        if r["kind"].strip() not in ("paid", "regular", "both"):
            problems.append(f"notas/excluir.csv: tipo desconocido '{r['kind']}'")
        for k in kinds:
            skip.add((r["date"].strip(), r["shop"].strip(), str(r["sku_id"]).strip(), k))

# ---------- Data files ----------
files = sorted(glob.glob("data/????-??-??.csv.gz"))
dates = [os.path.basename(p)[:10] for p in files]
today_ar = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date().isoformat()
if any(d > today_ar for d in dates):
    problems.append(f"Hay archivos con fecha futura: {[d for d in dates if d > today_ar]}")
d0 = date.fromisoformat(dates[0])
expected = [(d0 + timedelta(days=i)).isoformat() for i in range((date.fromisoformat(dates[-1]) - d0).days + 1)]
missing = [d for d in expected if d not in dates]
if missing:
    notes.append(f"Días sin datos (el índice los saltea): {missing}")

prices = {}
for p, d in zip(files, dates):
    t = {}
    with gzip.open(p, "rt", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["shop"], str(r["sku_id"]))
            if k not in basket or r.get("available") != "True":
                continue
            try:
                paid = float(r["price"])
            except (TypeError, ValueError):
                continue
            if paid <= 0:
                continue
            try:
                reg = float(r["list_price"])
            except (TypeError, ValueError):
                reg = 0.0
            # Jumbo has no real list price (its field is the price without VAT x 100): no regular price
            t[k] = {"paid": paid} if k[0] == "Jumbo" else {"paid": paid, "regular": reg if reg > 0 else paid}
    prices[d] = t
    if len([k for k in t if starts[k] <= d]) < 100:
        problems.append(f"{d}: solo {len(t)} productos de la canasta con stock (mínimo 100)")

# ---------- Independent recalculation (ratios, not logs) ----------
shops = sorted({s for s, _ in basket})
level = {(s, k): 1.0 for s in ["all"] + shops for k in ("paid", "regular")}
prev = {}
calc = {}
def geo(rs):
    prod = 1.0
    for r in rs:
        prod *= r
    return prod ** (1 / len(rs))


def group_ratio(items, new):
    """items: list of (type, shop, ratio). Old: geometric mean of all. New: shop -> type -> group."""
    if not new:
        return geo([r for _, _, r in items])
    by_type = {}
    for t, shop, r in items:
        by_type.setdefault(t, {}).setdefault(shop, []).append(r)
    return geo([geo([geo(rs) for rs in by_shop.values()]) for by_shop in by_type.values()])


for d in dates:
    ratios = defaultdict(list)  # (scope, group, kind) -> [(type, shop, ratio)]
    for k, v in prices[d].items():
        use = {kind: v[kind] for kind in v if (d, k[0], k[1], kind) not in skip}
        comp = {kind: use[kind] / prev[(k, kind)] for kind in use if (k, kind) in prev}
        if any(r > 3 or r < 1 / 3 for r in comp.values()):
            continue
        if starts[k] <= d:  # products that start later are followed but not counted
            g = grp[basket[k]]
            for kind, r in comp.items():
                ratios[("all", g, kind)].append((basket[k], k[0], r))
                ratios[(k[0], g, kind)].append((basket[k], k[0], r))
        for kind, p in use.items():
            prev[(k, kind)] = p
    for s in ["all"] + shops:
        for kind in ("paid", "regular"):
            parts = []
            for g, wt in w.items():
                rs = ratios.get((s, g, kind))
                if rs and wt:
                    parts.append((wt, group_ratio(rs, d >= CHANGE_DATE)))
            if parts:
                total = sum(wt for wt, _ in parts)
                f = 1.0
                for wt, gm in parts:
                    f *= gm ** (wt / total)
                level[(s, kind)] *= f
    calc[d] = dict(level)

# Base: each series divided by its own average over the first full week (24 to 30 October 2026), times 100
base_days = [d for d in dates if "2026-10-24" <= d <= "2026-10-30"]
if len(base_days) == 7:
    for key in level:
        b = sum(calc[d][key] for d in base_days) / 7
        for d in dates:
            calc[d][key] = calc[d][key] / b * 100
else:
    for d in dates:
        calc[d] = {key: v * 100 for key, v in calc[d].items()}

# ---------- "Week" method of the monthly report, recalculated another way ----------
def direct_week(now_days, old_days, min_stock=4):
    """Every product's average price in two windows, combined type -> group -> weights (ratios, not logs)."""
    tree = {}  # group -> type -> shop -> [ratio]
    for k, t in basket.items():
        if k[0] not in shops:
            continue
        pn = [prices[x][k]["paid"] for x in now_days if k in prices[x] and (x, k[0], k[1], "paid") not in skip]
        po = [prices[x][k]["paid"] for x in old_days if k in prices[x] and (x, k[0], k[1], "paid") not in skip]
        if len(pn) < min_stock or len(po) < min_stock:
            continue
        r = (sum(pn) / len(pn)) / (sum(po) / len(po))
        if 1 / 3 <= r <= 3:
            tree.setdefault(grp[t], {}).setdefault(t, {}).setdefault(k[0], []).append(r)
    total = sum(w[g] for g in tree if w.get(g))
    f = 1.0
    for g, types in tree.items():
        if w.get(g):
            f *= geo([geo([geo(rs) for rs in by_shop.values()]) for by_shop in types.values()]) ** (w[g] / total)
    return round((f - 1) * 100, 2)


def week_check(rep, m, prev_m):
    """Same days of two months, every product's average price, combined type -> group -> weights.
    Written separately from make_report.py: works on price ratios, not logs."""
    a, b = rep["headline"]["week_now"], rep["headline"]["week_before"]
    end_day = int(rep["end_date"][8:])
    if a[1] != rep["end_date"]:
        problems.append(f"Informe {m}: la semana no termina el último día ({a[1]} vs {rep['end_date']})")
    nums = range(end_day - 6, end_day + 1)
    now_days = [x for x in (f"{m}-{n:02d}" for n in nums) if x in prices]
    old_days = [x for x in (f"{prev_m}-{n:02d}" for n in nums) if x in prices]
    if [now_days[0], now_days[-1]] != a or [old_days[0], old_days[-1]] != b:
        problems.append(f"Informe {m}: ventanas de semana distintas a las recalculadas")
    return direct_week(now_days, old_days)


# ---------- Compare with what is published ----------
daily = rows("index/daily.csv")
if [r["date"] for r in daily] != dates:
    problems.append("index/daily.csv no tiene exactamente los mismos días que data/")
for r in daily:
    c = calc.get(r["date"])
    if not c:
        continue
    checks = [("index_paid", ("all", "paid")), ("index_regular", ("all", "regular"))] + \
             [(f"{s}_paid", (s, "paid")) for s in shops if f"{s}_paid" in r]
    for col, key in checks:
        if abs(float(r[col]) - c[key]) > TOL:
            problems.append(f"{r['date']} {col}: publicado {r[col]}, recalculado {c[key]:.3f}")
for a, b in zip(daily, daily[1:]):
    move = (float(b["index_paid"]) / float(a["index_paid"]) - 1) * 100
    if abs(move) > MAX_DAILY_MOVE:
        problems.append(f"{b['date']}: el índice se movió {move:+.2f}% en un día (más de {MAX_DAILY_MOVE}%), revisar")

# Monthly averages and reports
by_m = defaultdict(list)
for r in daily:
    by_m[r["date"][:7]].append(r)
monthly = {r["month"]: r for r in rows("index/monthly.csv")}
ms = sorted(by_m)
for i, m in enumerate(ms):
    avg = sum(float(r["index_paid"]) for r in by_m[m]) / len(by_m[m])
    if m in monthly and abs(float(monthly[m]["avg_index_paid"]) - avg) > TOL:
        problems.append(f"{m}: promedio publicado {monthly[m]['avg_index_paid']}, recalculado {avg:.3f}")
    rep_path = f"index/informes/{m}.json"
    if os.path.exists(rep_path):
        rep = json.load(open(rep_path, encoding="utf-8"))
        prev_rows = by_m[ms[i - 1]] if i > 0 else []
        full = len(by_m[m]) >= 20 and len(prev_rows) >= 20
        if rep.get("method") == "week":
            expect = week_check(rep, m, ms[i - 1])
        elif full:
            a1 = avg
            a0 = sum(float(r["index_paid"]) for r in prev_rows) / len(prev_rows)
            expect = round((a1 / a0 - 1) * 100, 2)
        else:
            base = prev_rows[-1] if prev_rows else by_m[m][0]
            expect = round((float(by_m[m][-1]["index_paid"]) / float(base["index_paid"]) - 1) * 100, 2)
        if rep.get("inflation") is not None and abs(rep["inflation"] - expect) > 0.011:
            problems.append(f"Informe {m}: dice {rep['inflation']}%, recalculado {expect}%")

# The website's 7-day box (index/semana.json)
if os.path.exists("index/semana.json"):
    sem = json.load(open("index/semana.json", encoding="utf-8"))
    if len(dates) >= 14:
        expect = direct_week(dates[-7:], dates[-14:-7])
        if not sem.get("ready") or sem.get("now") != [dates[-7], dates[-1]] or sem.get("before") != [dates[-14], dates[-8]]:
            problems.append("index/semana.json: las semanas no son las últimas dos con datos")
        elif sem.get("paid") is None or abs(sem["paid"] - expect) > 0.011:
            problems.append(f"Cuadro de 7 días: dice {sem.get('paid')}%, recalculado {expect}%")

# Weekly reports (index/semanas/AAAA-MM-DD.json): the same 7-day method, recalculated here, and the
# supermarket ranking (identical barcodes at the 4 shops) recalculated from the raw files.
week_files = sorted(p for p in glob.glob("index/semanas/????-??-??.json"))
listed = json.load(open("index/semanas/lista.json", encoding="utf-8")) if os.path.exists("index/semanas/lista.json") else []
if sorted(x["id"] for x in listed) != sorted(os.path.basename(p)[:10] for p in week_files):
    problems.append("index/semanas/lista.json no coincide con los informes semanales guardados")
for p in week_files:
    wr = json.load(open(p, encoding="utf-8"))
    n = len(wr["days_now"]) and (date.fromisoformat(wr["end"]) - date.fromisoformat(wr["start"])).days + 1
    shift = lambda d: (date.fromisoformat(d) - timedelta(days=7)).isoformat()
    if wr["before_start"] != shift(wr["start"]) or wr["before_end"] != shift(wr["end"]):
        problems.append(f"Informe semanal {wr['id']}: la semana anterior no son los mismos días 7 días antes")
    now_ok = [d for d in dates if wr["start"] <= d <= wr["end"]]
    old_ok = [d for d in dates if wr["before_start"] <= d <= wr["before_end"]]
    if now_ok != wr["days_now"] or old_ok != wr["days_before"]:
        problems.append(f"Informe semanal {wr['id']}: los días usados no coinciden con los archivos de datos")
    expect = direct_week(now_ok, old_ok, wr["min_in_stock"])
    if wr.get("paid") is None or abs(wr["paid"] - expect) > 0.011:
        problems.append(f"Informe semanal {wr['id']}: dice {wr.get('paid')}%, recalculado {expect}%")

rk_path = "index/semanas/ranking.json"
if os.path.exists(rk_path):
    RS = ["Carrefour", "Jumbo", "ChangoMas", "Dia"]
    eprice = {}  # date -> {(ean, shop): price}
    for p_, d_ in zip(files, dates):
        t = {}
        with gzip.open(p_, "rt", newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if (r["shop"] in RS and r.get("ean") and r.get("available") == "True"
                        and (r.get("unit") or "").lower() == "un" and str(r.get("unit_multiplier")) in ("1", "1.0")):
                    try:
                        v = float(r["price"])
                    except (TypeError, ValueError):
                        continue
                    if v > 0:
                        t[(r["ean"], r["shop"])] = v
        eprice[d_] = t
    for wk in json.load(open(rk_path, encoding="utf-8")):
        have = [d_ for d_ in dates if wk["start"] <= d_ <= wk["end"]]
        need = -(-len(have) // 2)
        tot, n_ok = {s_: 0.0 for s_ in RS}, 0
        for e in {e for d_ in have for (e, _s) in eprice[d_]}:
            avgs = {}
            for s_ in RS:
                ps = [eprice[d_][(e, s_)] for d_ in have if (e, s_) in eprice[d_]]
                if len(ps) >= need:
                    avgs[s_] = sum(ps) / len(ps)
            if len(avgs) == 4 and max(avgs.values()) <= 3 * min(avgs.values()):
                n_ok += 1
                for s_ in RS:
                    tot[s_] += avgs[s_]
        pub = {x["shop"]: x["total"] for x in wk["shops"]}
        if n_ok != wk["n_products"] or any(abs(pub[s_] - tot[s_]) > 0.05 for s_ in RS):
            problems.append(f"Ranking de súper {wk['id']}: no coincide con el recálculo ({n_ok} productos)")

# ---------- Result ----------
out = [f"Verificación independiente del índice ({datetime.now(ZoneInfo('Europe/Madrid')):%Y-%m-%d %H:%M} España)",
       f"Días: {len(dates)} ({dates[0]} a {dates[-1]}). Precios dejados afuera por revisión: {len(skip)}."]
out += ["PROBLEMA: " + p for p in problems] or ["OK: todos los números publicados coinciden con el recálculo."]
out += ["Nota: " + n for n in notes]
os.makedirs("index", exist_ok=True)
open("index/verificacion.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
sys.exit(1 if problems else 0)
