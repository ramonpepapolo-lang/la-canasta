# La Canasta: collects the numbers of the website, YouTube and X in one file (estadisticas.json).
# Runs on GitHub (workflow "Estadísticas"), with the same keys the videos are published with.
# The result goes to the separate branch "estadisticas", never to the website.
import datetime, json, os, re, urllib.parse

import requests

out = {"when_utc": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"), "errors": []}

# ---------- Website (GoatCounter's public counter) ----------
web = {}
for path in ["TOTAL", "/", "/precios/", "/canastas/", "/informes.html", "/metodo.html", "/articulos.html"]:
    try:
        r = requests.get("https://lacanasta.goatcounter.com/counter/" + urllib.parse.quote(path, safe="") + ".json", timeout=20)
        web[path] = int(str(r.json()["count"]).replace(" ", "").replace(",", "")) if r.ok else None
    except Exception as e:
        web[path] = None
out["website"] = web

# ---------- YouTube (the channel the videos are published to) ----------
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    cr = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], token_uri="https://oauth2.googleapis.com/token",
                     client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"])
    yt = build("youtube", "v3", credentials=cr, cache_discovery=False)
    ch = yt.channels().list(part="statistics,contentDetails,snippet", mine=True).execute()["items"][0]
    st = ch["statistics"]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        p = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=tok).execute()
        ids += [i["contentDetails"]["videoId"] for i in p["items"]]
        tok = p.get("nextPageToken")
        if not tok:
            break
    vids = []
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="statistics,snippet", id=",".join(ids[i:i + 50])).execute()["items"]:
            s = v.get("statistics", {})
            vids.append({"id": v["id"], "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"][:10],
                         "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)), "comments": int(s.get("commentCount", 0))})
    out["youtube"] = {"channel": ch["snippet"]["title"], "subscribers": int(st.get("subscriberCount", 0)),
                      "views": int(st.get("viewCount", 0)), "videos": int(st.get("videoCount", 0)), "list": vids}
except Exception as e:
    out["errors"].append("youtube: " + str(e)[:400])

# ---------- X (the account the videos are posted from) ----------
try:
    from requests_oauthlib import OAuth1
    auth = OAuth1(os.environ["X_API_KEY"], os.environ["X_API_SECRET"], os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    r = requests.get("https://api.twitter.com/2/users/me", auth=auth, params={"user.fields": "public_metrics,username"}, timeout=30)
    x = {"me_status": r.status_code}
    if r.ok:
        me = r.json()["data"]
        x.update({"username": me.get("username"), **me.get("public_metrics", {})})
        t = requests.get(f"https://api.twitter.com/2/users/{me['id']}/tweets", auth=auth, timeout=30,
                         params={"max_results": 5, "exclude": "replies", "tweet.fields": "public_metrics,created_at"})
        x["tweets_status"] = t.status_code
        if t.ok:
            x["last_posts"] = [{"date": p.get("created_at", "")[:10], "text": p["text"][:90], **p.get("public_metrics", {})}
                               for p in t.json().get("data", [])[:4]]
        else:
            x["tweets_error"] = t.text[:300]
    else:
        x["me_error"] = r.text[:300]
    out["x"] = x
except Exception as e:
    out["errors"].append("x: " + str(e)[:400])

json.dump(out, open("estadisticas.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "youtube"}, ensure_ascii=False)[:2000])
print("youtube:", {k: v for k, v in out.get("youtube", {}).items() if k != "list"})
