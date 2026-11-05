# La Canasta: builds the open dataset (datos-abiertos/la-canasta-datos.zip) for Kaggle and Zenodo.
# Run by the "Publish open dataset" workflow every Sunday (and on demand). The zip is not committed: it is a release asset.
# Everything comes from the files the index already uses; nothing is changed or recalculated here.

import csv
import glob
import gzip
import io
import os
import shutil
import zipfile
from datetime import date

OUT = "datos-abiertos"
ZIP = f"{OUT}/la-canasta-datos.zip"

os.makedirs(OUT, exist_ok=True)
files = sorted(glob.glob("data/????-??-??.csv.gz"))
first, last = os.path.basename(files[0])[:10], os.path.basename(files[-1])[:10]

# 1. Every price collected, all days in one file. Jumbo's list_price field is not a real list price
#    (it is the price without VAT times 100), so it is left empty in the open data.
COLUMNS = ["date", "shop", "search", "sku_id", "ean", "name", "brand", "category",
           "unit", "unit_multiplier", "price", "list_price", "available", "basket_type", "extra"]
# The first day's file (24 Oct) has no basket_type column: filled from the basket of that day
first_basket = {(b["shop"], b["sku_id"]): b["type_id"]
                for b in csv.DictReader(open("basket.csv", encoding="utf-8")) if not b.get("from_date")}
prices = io.StringIO()
w = csv.DictWriter(prices, fieldnames=COLUMNS, lineterminator="\n")
w.writeheader()
rows = 0
for path in files:
    with gzip.open(path, "rt", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["shop"] == "Jumbo":
                r["list_price"] = ""
            if "basket_type" not in r:
                r["basket_type"] = first_basket.get((r["shop"], r["sku_id"]), "")
            w.writerow({c: r.get(c, "") for c in COLUMNS})
            rows += 1

readme = open(f"{OUT}/LEEME.md", encoding="utf-8").read()
readme = readme.replace("{FIRST}", first).replace("{LAST}", last).replace("{DAYS}", str(len(files))) \
               .replace("{ROWS}", f"{rows:,}".replace(",", ".")).replace("{ROWS_EN}", f"{rows:,}")

with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("LEEME.md", readme)
    z.writestr("precios_diarios.csv", prices.getvalue())
    z.write("basket.csv", "canasta.csv")
    z.write("weights.csv", "ponderaciones.csv")
    z.write("index/daily.csv", "indice_diario.csv")
    z.write("index/groups.csv", "indice_por_grupo.csv")
    z.write("index/monthly.csv", "inflacion_mensual.csv")
    z.write("notas/excluir.csv", "precios_excluidos.csv")
    z.write(f"{OUT}/LICENCIA.txt", "LICENCIA.txt")

print(f"{ZIP}: {len(files)} days ({first} to {last}), {rows} prices, "
      f"{os.path.getsize(ZIP) / 1e6:.1f} MB")
