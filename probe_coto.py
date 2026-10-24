# La Canasta: one-off investigation of how Coto's website gets its prices.
# The results get saved to coto_probe.txt so Claude can read them.

import json
import re
import uuid
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
s = requests.Session()
s.headers["User-Agent"] = UA

home = s.get("https://www.coto.com.ar/", timeout=30).text
js_files = re.findall(r'src="([^"]+\.js)"', home)
print("JS files:", js_files)

texts = {}
for f in js_files:
    url = f if f.startswith("http") else "https://www.coto.com.ar/" + f.lstrip("/")
    try:
        texts[url] = s.get(url, timeout=90).text
        print("Downloaded", url, len(texts[url]), "characters")
    except Exception as e:
        print("Failed", url, e)
everything = "\n".join(texts.values())

keys = sorted(set(re.findall(r"key_[A-Za-z0-9]{8,}", everything)))
print("\nKeys found:", keys)

print("\nInteresting web addresses:")
for m in sorted(set(re.findall(r"https?://[a-zA-Z0-9.\-]+[a-zA-Z0-9_\-/.]*", everything))):
    if any(w in m.lower() for w in ["api", "cnstrc", "coto", "search", "price", "precio"]):
        print("  ", m)

print("\nText around the word 'cnstrc' or 'apiKey':")
for m in re.finditer(r".{0,120}(cnstrc|apiKey|apikey).{0,120}", everything):
    print("  ", m.group(0))

for k in keys:
    url = (f"https://ac.cnstrc.com/search/leche%20la%20serenisima?key={k}"
           f"&c=ciojs-client-2.35.2&i={uuid.uuid4()}&s=1&num_results_per_page=5&page=1")
    r = s.get(url, timeout=30)
    print(f"\nSearch with {k}: status {r.status_code}")
    try:
        results = r.json()["response"]["results"]
        print("Number of results:", len(results))
        print(json.dumps(results[0], ensure_ascii=False, indent=1)[:4000])
    except Exception:
        print(r.text[:800])
