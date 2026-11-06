"""Data for the La Canasta app (app/datos.json on the website), rebuilt every day after the index.

Everything comes from files the site already publishes and checks: index/daily.csv, index/semana.json,
index/semanas/ranking.json and the day's prices in data/. Nothing is estimated.
  - index: today's index (price paid and list price), its date, and the change against the base week
    (24-30 Oct = 100) or, from day 14 on, the last 7 days against the 7 before (index/semana.json).
  - ranking: this week's supermarket ranking (same products, same barcode, average price of the week).
  - moves: the basket products whose price paid changed most since the day before, down and up, with
    whether it is a promotion starting or ending (list price unchanged) or a list price change.
Run: python make_app_data.py
"""
import csv, gzip, glob, json, os
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
SHOPS = ["Carrefour", "Jumbo", "ChangoMas", "Dia"]


def day_prices(d, basket):
    out = {}
    with gzip.open(os.path.join(ROOT, "data", f"{d}.csv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["shop"], r["sku_id"])
            if k not in basket or k in out or r.get("available") != "True":
                continue
            try:
                p = float(r["price"])
            except (TypeError, ValueError):
                continue
            if p <= 0:
                continue
            lp = None
            if r["shop"] != "Jumbo":
                try:
                    lp = float(r["list_price"])
                except (TypeError, ValueError):
                    lp = None
            out[k] = (p, lp, r["name"].strip())
    return out


def main():
    daily = list(csv.DictReader(open(os.path.join(ROOT, "index", "daily.csv"), encoding="utf-8")))
    last, prev = daily[-1], daily[-2]
    semana = json.load(open(os.path.join(ROOT, "index", "semana.json"), encoding="utf-8"))
    idx = {"date": last["date"], "paid": float(last["index_paid"]), "regular": float(last["index_regular"]),
           "day_change": round((float(last["index_paid"]) / float(prev["index_paid"]) - 1) * 100, 2),
           "days_of_data": len(daily), "series": [[r["date"], float(r["index_paid"]), float(r["index_regular"])] for r in daily]}
    if semana.get("ready"):
        idx.update({"mode": "week", "week_paid": semana["paid"], "week_regular": semana["regular"],
                    "now": semana["now"], "before": semana["before"]})
    else:
        idx.update({"mode": "base", "base_paid": round(float(last["index_paid"]) - 100, 2), "base_regular": round(float(last["index_regular"]) - 100, 2)})
    ranking = json.load(open(os.path.join(ROOT, "index", "semanas", "ranking.json"), encoding="utf-8"))
    rk = ranking[0] if ranking else None  # newest first
    rank = rk and {"label_es": rk["label_es"], "label_en": rk["label_en"], "days": rk["days"], "n_products": rk["n_products"], "shops": rk["shops"]}
    basket = {(b["shop"], b["sku_id"]): b for b in csv.DictReader(open(os.path.join(ROOT, "basket.csv"), encoding="utf-8")) if b["shop"] in SHOPS}
    files = sorted(glob.glob(os.path.join(ROOT, "data", "????-??-??.csv.gz")))
    d1, d0 = os.path.basename(files[-1])[:10], os.path.basename(files[-2])[:10]
    a, z = day_prices(d0, basket), day_prices(d1, basket)
    moves = []
    for k, (p1, l1, name) in z.items():
        if k not in a:
            continue
        p0, l0, _ = a[k]
        ch = (p1 / p0 - 1) * 100
        if abs(ch) < 5 or not (1 / 3 <= p1 / p0 <= 3):
            continue
        if l0 and l1 and abs(l1 - l0) < 0.5:
            why = "promo_start" if p1 < p0 else "promo_end"
        elif l0 and l1:
            why = "list_down" if l1 < l0 else "list_up"
        else:
            why = "price"
        moves.append({"shop": k[0], "name": name, "type": basket[k]["type_id"], "before": p0, "now": p1, "pct": round(ch, 1), "why": why})
    moves.sort(key=lambda m: (m["pct"], m["shop"], m["name"]))
    out = {"date": d1, "previous": d0, "index": idx, "ranking": rank,
           "down": moves[:12], "up": sorted([m for m in moves if m["pct"] > 0], key=lambda m: -m["pct"])[:12],
           "n_down": sum(1 for m in moves if m["pct"] < 0), "n_up": sum(1 for m in moves if m["pct"] > 0)}
    os.makedirs(os.path.join(ROOT, "app-datos"), exist_ok=True)
    with open(os.path.join(ROOT, "app-datos", "datos.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"app-datos/datos.json: {d1}, index {idx['paid']}, {out['n_down']} down / {out['n_up']} up, ranking {rk and rk['id']}")


if __name__ == "__main__":
    main()
