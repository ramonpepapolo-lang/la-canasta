# SEPA probe (step 1): what files exist, how far back, and how well they match La Canasta's basket.
import urllib.parse
import json, os, sys, urllib.request, re
out = {"datasets": {}}
def get(u, t=60):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (La Canasta research)"})
    return urllib.request.urlopen(req, timeout=t).read()
for host, pid in [("datos.produccion.gob.ar", "sepa-precios"), ("datos.produccion.gob.ar", "precios-claros-sepa-mayoristas"),
                  ("datos.gob.ar", "produccion-precios-claros---base-sepa")]:
    try:
        j = json.loads(get(f"https://{host}/api/3/action/package_show?id={pid}"))
        res = j["result"]["resources"]
        out["datasets"][f"{host}/{pid}"] = [{k: r.get(k) for k in ("name", "url", "size", "created", "last_modified", "format", "description")} for r in res]
        print(host, pid, len(res), "resources")
    except Exception as e:
        out["datasets"][f"{host}/{pid}"] = {"error": str(e)[:300]}; print(host, pid, "ERROR", e)
# also search the catalogue for other SEPA datasets (semestral / historical)
for q in ["sepa", "precios claros"]:
    try:
        j = json.loads(get(f"https://datos.produccion.gob.ar/api/3/action/package_search?q={urllib.parse.quote(q)}&rows=50"))
        out.setdefault("search", {})[q] = [{"name": p["name"], "title": p["title"], "n": len(p.get("resources", [])),
                                            "resources": [(r.get("name"), r.get("url"), r.get("size")) for r in p.get("resources", [])][:80]} for p in j["result"]["results"]]
    except Exception as e:
        out.setdefault("search", {})[q] = str(e)[:300]
json.dump(out, open("out/catalogo.json", "w"), ensure_ascii=False, indent=1)
