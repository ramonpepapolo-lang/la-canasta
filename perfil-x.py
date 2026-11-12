# Updates the bio and link of @LaCanastaIndex on X (asked by Ramon, 12 Nov 2026). Writes perfil-x.json.
import json, os, requests
from requests_oauthlib import OAuth1
auth = OAuth1(os.environ["X_API_KEY"], os.environ["X_API_SECRET"], os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
BIO = "Índice diario de precios del súper en Argentina, creado por Ramon Pepa. Más de 20.000 precios por día. Datos abiertos.\n\n📺 youtube.com/@LaCanastaIndex"
out = {}
r = requests.get("https://api.twitter.com/2/users/me", auth=auth, params={"user.fields": "description,url,entities"}, timeout=30)
out["before"] = r.json() if r.ok else {"status": r.status_code, "text": r.text[:300]}
u = requests.post("https://api.twitter.com/1.1/account/update_profile.json", auth=auth, timeout=30,
                  data={"description": BIO, "url": "https://lacanastaindex.com"})
out["update"] = {"status": u.status_code, "text": u.text[:400]}
r = requests.get("https://api.twitter.com/2/users/me", auth=auth, params={"user.fields": "description,url"}, timeout=30)
out["after"] = r.json() if r.ok else {"status": r.status_code}
json.dump(out, open("perfil-x.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))
