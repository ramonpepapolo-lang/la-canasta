# Tests which other supermarket websites can be collected like the 4 VTEX shops. Result: probe-tiendas.json
import json, requests
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
C = {"Disco": "https://www.disco.com.ar", "Vea": "https://www.vea.com.ar", "Libertad": "https://www.hiperlibertad.com.ar",
     "Toledo": "https://www.toledodigital.com.ar", "LaAnonima": "https://supermercado.laanonimaonline.com",
     "CoopObrera": "https://www.lacoopeencasa.coop", "Makro": "https://www.makro.com.ar", "Atomo": "https://atomoconviene.com",
     "Dino": "https://www.dinoonline.com.ar", "Vital": "https://www.vital.com.ar", "Maxiconsumo": "https://maxiconsumo.com",
     "Diarco": "https://www.diarco.com.ar", "Cordiez": "https://www.cordiez.com.ar", "ElNene": "https://www.supermercadoselnene.com.ar"}
out = {}
for name, base in C.items():
    r = {"base": base}
    try:
        h = requests.get(base, headers={"User-Agent": UA}, timeout=25)
        r["home"] = h.status_code
        r["vtex_hint"] = "vtex" in h.text.lower()
    except Exception as e:
        r["home"] = str(e)[:80]
    try:
        s = requests.get(base + "/api/catalog_system/pub/products/search?ft=leche&_from=0&_to=49", headers={"User-Agent": UA}, timeout=25)
        r["search_status"] = s.status_code
        d = s.json()
        if isinstance(d, list):
            items = [(p.get("productName"), (p.get("items") or [{}])[0].get("sellers", [{}])[0].get("commertialOffer", {}).get("Price")) for p in d]
            r["n"] = len(d); r["sample"] = items[:3]
            r["eans"] = sum(1 for p in d for i in p.get("items", []) if i.get("ean"))
    except Exception as e:
        r["search_err"] = str(e)[:80]
    out[name] = r
    print(name, r)
json.dump(out, open("probe-tiendas.json", "w"), ensure_ascii=False, indent=1)
