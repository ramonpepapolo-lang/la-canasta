# Public follower counts of the two outlets that confirmed (InfoBAN and Diario La Ciudad), from the official X API
# and InfoBAN's public YouTube channel page. Writes redes.json.
import json, os, re, requests
out = {}
try:
    from requests_oauthlib import OAuth1
    auth = OAuth1(os.environ["X_API_KEY"], os.environ["X_API_SECRET"], os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    r = requests.get("https://api.twitter.com/2/users/by", auth=auth, timeout=30,
                     params={"usernames": "Infobannoticias,LaCiudadDiario", "user.fields": "public_metrics,created_at"})
    out["x"] = {"status": r.status_code, "body": r.json() if "json" in r.headers.get("content-type", "") else r.text[:300]}
except Exception as e:
    out["x"] = {"error": str(e)[:200]}
try:
    t = requests.get("https://www.youtube.com/channel/UCeKMfKkv5oe_CAWi-Y7Zdbg/about?hl=en", timeout=30).text
    out["youtube_infoban"] = {k: (re.search(p, t).group(1) if re.search(p, t) else None) for k, p in
                              [("subscribers", r'([\d.,]+[KM]?) subscribers'), ("videos", r'([\d.,]+[KM]?) videos'),
                               ("views", r'([\d,]+) views"')]}
except Exception as e:
    out["youtube_infoban"] = {"error": str(e)[:200]}
json.dump(out, open("redes.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:3000])
