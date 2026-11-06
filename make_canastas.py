"""Ready-made baskets (lacanastaindex.com/canastas/): what an asado, a healthy week or a student week
costs today at each of the 4 index supermarkets, and where it is cheapest.

For every ingredient and shop it takes the cheapest product in stock today that fits the ingredient
(the curated basket products when the ingredient is a basket type, otherwise the day's search results
filtered by name rules in canastas/canastas.json), priced per kilo, per litre or per unit. Prices far
away from the other shops (below 40% or above 250% of the median) are treated as website errors and
skipped, like the index does. Nothing is estimated: an ingredient with no price at a shop is reported
as missing and that shop's total is marked incomplete.

Writes canastas/datos.json. Run after compute_index.py. Test: python make_canastas.py --date 2026-11-05
"""
import csv, gzip, glob, json, math, os, re, statistics, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(ROOT, "canastas", "canastas.json"), encoding="utf-8"))
SHOPS = CFG["shops"]
SIZE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|kilo|kilos|grs|gr|g|lts|lt|l|ml|cc)\b", re.I)
COUNT_RE = re.compile(r"(?:x\s*|por\s+)(\d{1,3})\s*(?:un|u\b|unid|huevos|uds|ud\b)|(\d{1,3})\s*(?:un|u\b|unid|huevos|uds|ud\b)", re.I)


def size_of(name):
    """(amount, 'kg' or 'l') from the last size in the name, or None."""
    m = SIZE_RE.findall(name)
    if not m:
        return None
    n, u = m[-1]
    n = float(n.replace(",", "."))
    u = u.lower()
    if n <= 0:
        return None
    if u in ("kg", "kilo", "kilos"):
        return (n, "kg")
    if u in ("g", "gr", "grs"):
        return (n / 1000, "kg")
    if u in ("l", "lt", "lts"):
        return (n, "l")
    return (n / 1000, "l")


def count_of(name):
    m = COUNT_RE.search(name)
    if not m:
        return None
    n = int(m.group(1) or m.group(2))
    return n if n > 0 else None


def unit_price(r, ing):
    """Price per the ingredient's unit (kg, l or un), or None when the product does not fit."""
    price = float(r["price"])
    unit = (r.get("unit") or "").lower()
    mult = float(r.get("unit_multiplier") or 1)
    want = ing["unit"]
    if want == "un":
        if ing.get("count_required"):
            n = count_of(r["name"])
            return price / n if n else None
        return price if unit == "un" else None
    # kg or l
    if unit == "kg" and want == "kg":
        return price  # VTEX shops price weighed goods per kilo
    if ing.get("unit_required") and unit != ing["unit_required"]:
        return None
    if unit == "un":
        s = size_of(r["name"])
        if not s:
            return None if ing.get("size_required") or want in ("kg", "l") else price
        if s[1] != want:
            return None
        return price / s[0]
    return None


def load(date):
    path = os.path.join(ROOT, "data", f"{date}.csv.gz")
    rows = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["shop"] not in SHOPS or r.get("available") != "True":
                continue
            try:
                if float(r["price"]) <= 0:
                    continue
            except (TypeError, ValueError):
                continue
            rows.append(r)
    return rows


def candidates(rows, ing):
    out = []
    inc = re.compile(ing["include"], re.I) if ing.get("include") else None
    exc = re.compile(ing["exclude"], re.I) if ing.get("exclude") else None
    for r in rows:
        if ing.get("basket_type") and r.get("basket_type") != ing["basket_type"]:
            continue
        # search-based ingredients: any product of the day whose name fits (watch-list products arrive without a search term)
        name = r["name"] or ""
        if inc and not inc.search(name):
            continue
        if exc and exc.search(name):
            continue
        up = unit_price(r, ing)
        if up is None or up <= 0:
            continue
        if ing.get("min_size"):
            s = size_of(name)
            if not s or s[0] < ing["min_size"]:
                continue
        out.append((up, r))
    return out


def pick(rows, ing_id, quality=False):
    """Cheapest fitting product per shop, with the outlier guard across shops.
    quality=True: the cheapest product of a leading brand (the ingredient's "quality" rule), for "primera marca"."""
    ing = CFG["ingredients"][ing_id]
    cands = candidates(rows, ing)
    if not cands:
        return {}
    med = statistics.median([c[0] for c in cands])
    if quality:
        if not ing.get("quality"):
            return {}
        q = re.compile(ing["quality"], re.I)
        cands = [c for c in cands if q.search((c[1].get("name") or "") + " " + (c[1].get("brand") or ""))]
    best = {}
    for up, r in sorted(cands, key=lambda c: (c[0], c[1]["shop"], c[1]["sku_id"])):
        if not (0.4 * med <= up <= 2.5 * med):
            continue
        if r["shop"] not in best:
            best[r["shop"]] = {"name": re.sub(r"\s+", " ", r["name"]).strip(), "sku_id": r["sku_id"], "ean": r.get("ean"),
                               "unit_price": round(up, 2), "price": float(r["price"]), "unit": r.get("unit"),
                               "promo": bool(r.get("list_price")) and r["shop"] != "Jumbo" and float(r["list_price"]) > float(r["price"]) + 0.5}
    return best


def main():
    date = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else sorted(glob.glob(os.path.join(ROOT, "data", "????-??-??.csv.gz")))[-1][-17:-7]
    rows = load(date)
    picks = {k: pick(rows, k) for k in CFG["ingredients"]}
    out = {"date": date, "shops": SHOPS, "baskets": []}
    for b in CFG["baskets"]:
        items = dict(b["items"])
        fixed = dict(b.get("fixed", {}))
        shops = {}
        missing_any = set()
        for shop in SHOPS:
            total, kcal, lines, missing = 0.0, 0.0, [], []
            for ing_id, qty in list(items.items()) + list(fixed.items()):
                ing = CFG["ingredients"][ing_id]
                p = picks[ing_id].get(shop)
                if not p:
                    missing.append(ing_id); missing_any.add(ing_id)
                    lines.append({"ing": ing_id, "qty": qty, "fixed": ing_id in fixed, "missing": True})
                    continue
                cost = p["unit_price"] * qty
                total += cost
                kcal += ing.get("kcal", 0) * qty
                lines.append({"ing": ing_id, "qty": qty, "fixed": ing_id in fixed, "unit_price": p["unit_price"], "cost": round(cost, 2),
                              "name": p["name"], "sku_id": p["sku_id"], "promo": p["promo"]})
            shops[shop] = {"total": round(total, 2), "complete": not missing, "missing": missing, "kcal": round(kcal), "items": lines}
        # Fair comparison: the ranking uses only the items that ALL shops have today (the same list for everyone).
        # Items a shop lacks are listed next to it; items nobody has yet are listed for the basket.
        nowhere = {k for k in missing_any if all(k in shops[s]["missing"] for s in SHOPS)}
        common = [k for k in list(items) + list(fixed) if all(k not in shops[s]["missing"] for s in SHOPS)]
        for s in SHOPS:
            shops[s]["complete"] = all(k in nowhere for k in shops[s]["missing"])
            shops[s]["lacks"] = [k for k in shops[s]["missing"] if k not in nowhere]
            shops[s]["total"] = round(sum(l["cost"] for l in shops[s]["items"] if not l.get("missing") and l["ing"] in common and not l["fixed"]), 2)
            shops[s]["fixed_total"] = round(sum(l["cost"] for l in shops[s]["items"] if not l.get("missing") and l["ing"] in common and l["fixed"]), 2)
        complete = [s for s in SHOPS if shops[s]["complete"]]
        ranked = sorted(SHOPS, key=lambda s: shops[s]["total"] + shops[s]["fixed_total"])
        out["baskets"].append({
            "id": b["id"], "es": b["es"], "en": b["en"], "per": b["per"], "desc_es": b["desc_es"], "desc_en": b["desc_en"],
            "ingredients": {k: {"es": CFG["ingredients"][k]["es"], "en": CFG["ingredients"][k]["en"], "unit": CFG["ingredients"][k]["unit"]} for k in list(items) + list(fixed)},
            "shops": shops, "ranking": ranked, "cheapest": ranked[0], "common": common,
            "all_complete": len(complete) == len(SHOPS), "missing_everywhere": sorted(nowhere),
        })
    os.makedirs(os.path.join(ROOT, "canastas"), exist_ok=True)
    with open(os.path.join(ROOT, "canastas", "datos.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    # "Armá la tuya": every product, every shop, the cheapest option and the leading-brand option
    catalog = {}
    for k, ing in CFG["ingredients"].items():
        qual = pick(rows, k, quality=True)
        shops = {}
        for s in SHOPS:
            c, q = picks[k].get(s), qual.get(s)
            if c or q:
                shops[s] = {"cheap": c and {x: c[x] for x in ("name", "unit_price", "promo")}, "quality": q and {x: q[x] for x in ("name", "unit_price", "promo")}}
        catalog[k] = {"es": ing["es"], "en": ing["en"], "unit": ing["unit"], "cat": ing.get("cat", "almacen"), "q": ing.get("q", 1),
                      "has_quality": bool(ing.get("quality")), "shops": shops}
    with open(os.path.join(ROOT, "canastas", "catalogo.json"), "w", encoding="utf-8") as f:
        json.dump({"date": date, "shops": SHOPS, "categories": CFG.get("categories", []), "items": catalog}, f, ensure_ascii=False, indent=1)
    print("catalog:", sum(1 for v in catalog.values() if len(v["shops"]) == len(SHOPS)), "of", len(catalog), "products at all 4 shops;",
          sum(1 for v in catalog.values() if any(x.get("quality") for x in v["shops"].values())), "with a leading-brand option")
    for b in out["baskets"]:
        print(f"{b['id']:11} cheapest={b['cheapest']} " + "  ".join(f"{s}:{b['shops'][s]['total']:.0f}{'' if b['shops'][s]['complete'] else '*'}" for s in SHOPS)
              + (f"  missing everywhere: {b['missing_everywhere']}" if b["missing_everywhere"] else ""))
        for s in SHOPS:
            for l in b["shops"][s]["items"]:
                if not l.get("missing"):
                    print(f"   {s:9} {l['ing']:12} {l['unit_price']:>9.0f} x {l['qty']:<5} = {l['cost']:>8.0f}  {l['name'][:50]}")


if __name__ == "__main__":
    main()
