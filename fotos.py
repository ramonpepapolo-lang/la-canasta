# One-off test: download small product photos (one per barcode) for a preview. Never touches the website.
import json, os, re, requests
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SHOPS = {"Jumbo": "https://www.jumbo.com.ar", "Carrefour": "https://www.carrefour.com.ar",
         "ChangoMas": "https://www.masonline.com.ar", "Dia": "https://diaonline.supermercadosdia.com.ar"}
os.makedirs("img", exist_ok=True)
log, done = [], set()
for s in json.load(open("skus.json")):
    if s["ean"] in done:
        continue
    try:
        r = requests.get(f"{SHOPS[s['shop']]}/api/catalog_system/pub/products/search?fq=skuId:{s['sku_id']}", headers={"User-Agent": UA}, timeout=30)
        p = r.json()[0]
        url = next(i["images"][0]["imageUrl"] for i in p["items"] if i["itemId"] == s["sku_id"])
        small = re.sub(r"/arquivos/ids/(\d+)(-\d+-\d+)?/", r"/arquivos/ids/\1-200-200/", url)
        img = requests.get(small, headers={"User-Agent": UA}, timeout=30)
        open(f"img/{s['ean']}.jpg", "wb").write(img.content)
        done.add(s["ean"]); log.append({**s, "url": small, "bytes": len(img.content), "type": img.headers.get("content-type")})
    except Exception as e:
        log.append({**s, "error": str(e)[:200]})
json.dump(log, open("fotos.json", "w"), indent=1)
print(json.dumps(log, indent=1))
