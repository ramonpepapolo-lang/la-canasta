# La Canasta: the index as it would be WITH Coto (not published, not used by the website).
# Coto's products are matched to the basket by barcode (same product as in the other supermarkets),
# in stock at least 85% of the days. Everything else is the normal calculation (compute_index.py),
# run in a separate folder so the real index is never touched.
# Usage: python sombra_coto.py   -> prints the official index next to the one with Coto
import csv, glob, gzip, json, os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.abspath(__file__))
T = tempfile.mkdtemp()
for x in ("data", "notas", "index"):
    shutil.copytree(os.path.join(ROOT, x), os.path.join(T, x))
for x in ("compute_index.py", "basket.csv", "weights.csv"):
    shutil.copy(os.path.join(ROOT, x), T)
basket = list(csv.DictReader(open(os.path.join(T, "basket.csv"), encoding="utf-8")))
ean_type = {}
for r in basket:
    if r["ean"]:
        ean_type.setdefault(r["ean"], r["type_id"])
files = sorted(glob.glob(os.path.join(T, "data", "*.csv.gz")))
coto = {}
for p in files:
    for r in csv.DictReader(gzip.open(p, "rt", encoding="utf-8")):
        if r["shop"] != "Coto":
            continue
        try:
            ex = json.loads(r["extra"] or "{}")
        except ValueError:
            ex = {}
        c = coto.setdefault(r["sku_id"], [0, "", ""])
        c[1] = c[1] or str(ex.get("product_main_ean") or r["ean"] or "")
        c[2] = r["name"]
        c[0] += r["available"] == "True"
cols = list(basket[0].keys())
added = 0
with open(os.path.join(T, "basket.csv"), "a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    for sku, (n, e, name) in coto.items():
        if e in ean_type and n >= 0.85 * len(files):
            w.writerow({c: {"type_id": ean_type[e], "shop": "Coto", "sku_id": sku, "ean": e, "name": name}.get(c, "") for c in cols})
            added += 1
subprocess.run([sys.executable, "compute_index.py"], cwd=T, check=True, capture_output=True)
off = {r["date"]: r for r in csv.DictReader(open(os.path.join(ROOT, "index", "daily.csv")))}
sh = {r["date"]: r for r in csv.DictReader(open(os.path.join(T, "index", "daily.csv")))}
print(f"Coto products added (same barcode as the basket): {added}")
print("date        official  with Coto  Coto alone")
for d in sorted(sh):
    print(d, f'{float(off[d]["index_paid"]):8.2f} {float(sh[d]["index_paid"]):10.2f} {float(sh[d]["Coto_paid"]):10.2f}')
shutil.rmtree(T)
