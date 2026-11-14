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
        web[path] = int(re.sub(r"\D", "", str(r.json()["count"]))) if r.ok else None
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
    out["errors"].append("youtube api: " + str(e)[:200])
    # The key only allows uploading: read the channel's public pages instead (what anyone sees on YouTube)
    try:
        H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
             "Accept-Language": "en-US,en;q=0.9"}
        CK = {"CONSENT": "YES+cb", "SOCS": "CAI"}
        get = lambda u: requests.get(u, headers=H, cookies=CK, timeout=30).text
        ids = []
        def add(found):
            for i in found:
                if i not in ids:
                    ids.append(i)
        page = get("https://www.youtube.com/@LaCanastaIndex")
        subs = re.search(r'([\d.,]+[KM]?) subscribers', page)
        cid = re.search(r'"(?:channelId|externalId)":"(UC[\w-]{22})"', page)
        about = get("https://www.youtube.com/@LaCanastaIndex/about")
        total = re.search(r'"viewCountText":"([\d,]+) views"', about) or re.search(r'([\d,]+) views"', about)
        info = {}  # video id -> what the public pages show
        def num(txt):
            m = re.match(r"([\d.,]+)\s*([KM]?)", txt.replace(",", ""))
            return round(float(m.group(1)) * {"": 1, "K": 1e3, "M": 1e6}[m.group(2)]) if m else None
        for tab in ("videos", "shorts"):
            t = get("https://www.youtube.com/@LaCanastaIndex/" + tab)
            add(re.findall(r'"reelWatchEndpoint":\{"videoId":"([\w-]{11})"', t))
            add(re.findall(r'"videoRenderer":\{"videoId":"([\w-]{11})"', t))
            # Shorts list: title and views ("12K views") of each Short
            for m in re.finditer(r'"entityId":"shorts-shelf-item-([\w-]{11})"(.{0,4000}?)"secondaryText":\{"content":"([^"]+) views"', t, re.S):
                ti = re.search(r'"primaryText":\{"content":"((?:[^"\\]|\\.)*)"', m.group(2))
                info.setdefault(m.group(1), {})["views_list"] = num(m.group(3))
                if ti:
                    info[m.group(1)]["title"] = json.loads('"' + ti.group(1) + '"')
            for m in re.finditer(r'"videoRenderer":\{"videoId":"([\w-]{11})".{0,3000}?"title":\{"runs":\[\{"text":"((?:[^"\\]|\\.)*)"\}.{0,3000}?"viewCountText":\{"simpleText":"([\d,]+) views"', t, re.S):
                info.setdefault(m.group(1), {}).update({"title": json.loads('"' + m.group(2) + '"'), "views_list": num(m.group(3))})
        # The channel's public feed: exact views and likes of the latest 15 videos
        if cid:
            feed = get("https://www.youtube.com/feeds/videos.xml?channel_id=" + cid.group(1))
            for e in re.findall(r"<entry>(.*?)</entry>", feed, re.S):
                vid = re.search(r"<yt:videoId>([\w-]{11})</yt:videoId>", e).group(1)
                add([vid])
                d = info.setdefault(vid, {})
                ti, pub = re.search(r"<title>(.*?)</title>", e, re.S), re.search(r"<published>(\d{4}-\d\d-\d\d)", e)
                vw, lk = re.search(r'<media:statistics views="(\d+)"', e), re.search(r'<media:starRating count="(\d+)"', e)
                import html as _h
                d.update({"title": _h.unescape(ti.group(1)) if ti else d.get("title", ""), "published": pub.group(1) if pub else "",
                          "views": int(vw.group(1)) if vw else None, "likes": int(lk.group(1)) if lk else None})
        # Videos the feed does not cover (older ones): read their own page
        for vid in ids:
            if info.get(vid, {}).get("views") is not None:
                continue
            w = get("https://www.youtube.com/shorts/" + vid)
            if '"viewCount"' not in w:
                w = get("https://www.youtube.com/watch?v=" + vid + "&hl=en")
            d = info.setdefault(vid, {})
            vc = re.search(r'"viewCount":"(\d+)"', w)
            lk = (re.search(r'along with ([\d,]+) other (?:people|person)', w) or re.search(r'"likeCount":"?(\d+)', w))
            ti = re.search(r'"videoDetails":\{"videoId":"[\w-]{11}","title":"((?:[^"\\]|\\.)*)"', w)
            pub = re.search(r'"(?:publishDate|uploadDate)":"(\d{4}-\d\d-\d\d)', w)
            if vc:
                d["views"] = int(vc.group(1))
            if lk:
                d["likes"] = int(lk.group(1).replace(",", ""))
            if ti and not d.get("title"):
                d["title"] = json.loads('"' + ti.group(1) + '"')
            if pub and not d.get("published"):
                d["published"] = pub.group(1)
            if not vc:
                d["debug"] = (re.search(r"<title>(.*?)</title>", w, re.S).group(1)[:80] if "<title>" in w else w[:120])
        # Number of comments, from each video's public watch page
        for vid in ids:
            try:
                w = get("https://www.youtube.com/watch?v=" + vid + "&hl=en")
                m = (re.search(r'"commentCount":\{"simpleText":"([\d,.KM]+)"', w) or re.search(r'"contextualInfo":\{"runs":\[\{"text":"([\d,.KM]+)"\}\]\}', w)
                     or re.search(r'"commentCount":"?(\d+)', w))
                info.setdefault(vid, {})["comments"] = num(m.group(1)) if m else None
            except Exception:
                pass
        vids = [{"id": vid, "debug": info.get(vid, {}).get("debug"), "title": info.get(vid, {}).get("title", ""), "published": info.get(vid, {}).get("published", ""),
                 "views": info.get(vid, {}).get("views", info.get(vid, {}).get("views_list")),
                 "views_exact": "views" in info.get(vid, {}), "likes": info.get(vid, {}).get("likes"),
                 "comments": info.get(vid, {}).get("comments")} for vid in ids]
        out["youtube"] = {"source": "public pages", "subscribers_text": subs.group(1) if subs else None,
                          "views_total_text": total.group(1) if total else None,
                          "views_sum_of_videos": sum(v["views"] or 0 for v in vids), "videos": len(vids), "list": vids}
    except Exception as e2:
        out["errors"].append("youtube pages: " + str(e2)[:300])

# ---------- X (the account the videos are posted from) ----------
try:
    from requests_oauthlib import OAuth1
    auth = OAuth1(os.environ["X_API_KEY"], os.environ["X_API_SECRET"], os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    r = requests.get("https://api.twitter.com/2/users/me", auth=auth, params={"user.fields": "public_metrics,username,created_at"}, timeout=30)
    x = {"me_status": r.status_code}
    if r.ok:
        me = r.json()["data"]
        x.update({"username": me.get("username"), "created_at": me.get("created_at"), **me.get("public_metrics", {})})
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

# Email subscribers (the website's sign-up list in Brevo): only the count, never any address
try:
    import requests as _rq
    key, lid = os.environ.get("BREVO_API_KEY", "").strip(), os.environ.get("BREVO_LIST_ID", "").strip()
    if key and lid:
        r = _rq.get(f"https://api.brevo.com/v3/contacts/lists/{lid}", headers={"api-key": key, "accept": "application/json"}, timeout=30)
        j = r.json()
        out["email"] = {"status": r.status_code, "list_name": j.get("name"), "subscribers": j.get("uniqueSubscribers", j.get("totalSubscribers")),
                        "blacklisted": j.get("totalBlacklisted")}
except Exception as e:
    out["errors"].append("email: " + str(e)[:200])

json.dump(out, open("estadisticas.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "youtube"}, ensure_ascii=False)[:2000])
print("youtube:", {k: v for k, v in out.get("youtube", {}).items() if k != "list"})
