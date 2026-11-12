"""Finds the store's own photo of each product shown on the price pages (precios/), one per barcode.

Writes precios/fotos.json: {ean: photo address}. The pages load each photo straight from the store's
own address (nothing is copied onto the site). Only barcodes without a photo yet are looked up, so the
daily run is quick. With --copy DIR it also saves small copies in DIR (only for the in-Claude preview,
never for the website).
"""
import csv, json, os, re, sys, time
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "precios", "fotos.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SHOPS = {"Carrefour": "https://www.carrefour.com.ar", "Dia": "https://diaonline.supermercadosdia.com.ar",
         "ChangoMas": "https://www.masonline.com.ar", "Jumbo": "https://www.jumbo.com.ar"}
ORDER = ["Carrefour", "Dia", "ChangoMas", "Jumbo"]  # which shop's photo to try first


def kinds():
    from make_price_pages import KINDS
    return {k[1] for k in KINDS}


def main():
    copy_dir = sys.argv[sys.argv.index("--copy") + 1] if "--copy" in sys.argv else None
    tids = kinds()
    rows = [r for r in csv.DictReader(open(os.path.join(ROOT, "basket.csv"), encoding="utf-8"))
            if r["type_id"] in tids and r["shop"] in SHOPS and r["ean"]]
    fotos = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    by_ean = {}
    for r in rows:
        by_ean.setdefault(r["ean"], []).append(r)
    found = missing = 0
    for ean, rs in sorted(by_ean.items()):
        if ean not in fotos:
            for r in sorted(rs, key=lambda r: ORDER.index(r["shop"])):
                try:
                    j = requests.get(f"{SHOPS[r['shop']]}/api/catalog_system/pub/products/search?fq=skuId:{r['sku_id']}",
                                     headers={"User-Agent": UA}, timeout=30).json()
                    url = next(i["images"][0]["imageUrl"] for p in j for i in p["items"] if i["itemId"] == r["sku_id"] and i.get("images"))
                    fotos[ean] = re.sub(r"/arquivos/ids/(\d+)(-\d+-\d+)?/", r"/arquivos/ids/\1-200-200/", url).replace("http://", "https://")
                    found += 1
                    break
                except Exception:
                    continue
                finally:
                    time.sleep(0.3)
            else:
                missing += 1
        if copy_dir and ean in fotos:
            os.makedirs(copy_dir, exist_ok=True)
            dest = os.path.join(copy_dir, ean + ".jpg")
            if not os.path.exists(dest):
                try:
                    open(dest, "wb").write(requests.get(fotos[ean], headers={"User-Agent": UA}, timeout=30).content)
                except Exception:
                    pass
    json.dump(dict(sorted(fotos.items())), open(OUT, "w", encoding="utf-8"), indent=0)
    print(f"{len(by_ean)} barcodes, {found} new photos, {missing} without photo, {len(fotos)} in fotos.json")


if __name__ == "__main__":
    main()
