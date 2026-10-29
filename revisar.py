# La Canasta: daily review of suspicious price moves (used by the review agent).
#
#   python revisar.py              review the latest day
#   python revisar.py 2026-10-25   review a given day
#
# Lists every basket price that, on that day:
#   - changed more than 25% (paid or regular price), or
#   - moved the whole index by more than 0.25 points on its own.
# For each one it prints the evidence needed to decide if it is real or a data problem:
# the last 10 days of that product, the same product type at the other shops, and any name change.
# It does not change anything. Decisions go in notas/excluir.csv (see REGLAS at the end).

import csv
import glob
import gzip
import math
import os
import sys
from collections import defaultdict

BIG_CHANGE = 0.25   # 25%
BIG_POINTS = 0.25   # index points

basket, names = {}, {}
for r in csv.DictReader(open("basket.csv", newline="", encoding="utf-8")):
    basket[(r["shop"], r["sku_id"])] = r["type_id"]
group_of, weight = {}, {}
for r in csv.DictReader(open("weights.csv", newline="", encoding="utf-8")):
    weight[r["group"]] = float(r["spending_2004_gba"]) if r["spending_2004_gba"] else None
    for t in r["basket_types"].split(";"):
        group_of[t] = r["group"]
excluded = set()
if os.path.exists("notas/excluir.csv"):
    for r in csv.DictReader(open("notas/excluir.csv", newline="", encoding="utf-8")):
        for k in (("paid", "regular") if r["kind"].strip() == "both" else (r["kind"].strip(),)):
            excluded.add((r["date"].strip(), r["shop"].strip(), str(r["sku_id"]).strip(), k))


def num(x):
    try:
        v = float(x)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


days = {}
for path in sorted(glob.glob("data/????-??-??.csv.gz")):
    d = os.path.basename(path)[:10]
    t = {}
    with gzip.open(path, "rt", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["shop"], str(r["sku_id"]))
            if key not in basket or r.get("available") != "True":
                continue
            paid, reg = num(r["price"]), num(r["list_price"])
            if paid:
                t[key] = {"paid": paid, "regular": reg or paid, "name": r["name"]}
    days[d] = t
dates = sorted(days)
target = sys.argv[1] if len(sys.argv) > 1 else dates[-1]
if target not in days:
    raise SystemExit(f"No data for {target}")

# Replay the chain up to the target day to know each price's "before" and its weight that day.
last = {}
flags = []
for d in dates:
    items = defaultdict(list)  # group -> [(key, kind, logchange, before, now)]
    for key, now in days[d].items():
        for kind in ("paid", "regular"):
            if (d, key[0], key[1], kind) in excluded:
                continue
            if (key, kind) in last:
                lc = math.log(now[kind] / last[(key, kind)])
                if abs(lc) < math.log(3):
                    items[group_of[basket[key]]].append((key, kind, lc, last[(key, kind)], now[kind]))
            last[(key, kind)] = now[kind]
    if d != target:
        continue
    for kind in ("paid", "regular"):
        groups = {g for g, its in items.items() if weight.get(g) and any(k == kind for _, k, *_ in its)}
        den = sum(weight[g] for g in groups)
        for g in groups:
            its = [x for x in items[g] if x[1] == kind]
            for key, k, lc, before, now in its:
                pts = weight[g] / den * lc / len(its) * 100
                if abs(math.exp(lc) - 1) > BIG_CHANGE or abs(pts) > BIG_POINTS:
                    flags.append((abs(pts), key, kind, before, now, pts))
    break

print(f"REVISION DE {target}: {len(flags)} movimiento(s) para revisar")
if not flags:
    print("Nada raro: ningun precio cambio mas de 25% ni movio el indice mas de 0,25 puntos.")
seen = set()
for _, key, kind, before, now, pts in sorted(flags, reverse=True):
    print("\n" + "=" * 70)
    print(f"{key[0]} | {basket[key]} | sku {key[1]} | precio {kind}: {before:g} -> {now:g} "
          f"({(now / before - 1) * 100:+.1f}%) | mueve el indice {pts:+.2f} puntos")
    if key in seen:
        continue
    seen.add(key)
    print("Historia (fecha: pagado / lista / nombre):")
    for d in dates[-10:]:
        x = days[d].get(key)
        if x:
            flag = " <- lista = pagado" if x["paid"] == x["regular"] else ""
            print(f"  {d}: {x['paid']:g} / {x['regular']:g} / {x['name'][:50]}{flag}")
        else:
            print(f"  {d}: sin stock / no encontrado")
    print(f"Mismo producto ({basket[key]}) en los otros super, {target}:")
    for k2, t2 in basket.items():
        if t2 == basket[key] and k2 != key:
            x = days[target].get(k2)
            print(f"  {k2[0]}: " + (f"{x['paid']:g} / {x['regular']:g} / {x['name'][:50]}" if x else "sin stock"))

print("""
REGLAS (ver notas/LEEME-revision.md):
  A. Error de dato (otro producto, otro tamano, precio x10/x100, por unidad vs por kg): excluir 'both' esos dias.
  B. Promo no marcada: lista = pagado, el precio sale de su nivel 1 a 3 dias (tipico fin de semana) y vuelve
     o se queda en otro nivel estable, y los otros super no se movieron igual: excluir 'regular' esos dias.
  C. Todo lo demas es un cambio real: NO se excluye. Ante la duda, no se excluye.
""")
