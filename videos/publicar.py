# La Canasta: publishes the day's Shorts ONLY after Ramon approves them.
# Run by .github/workflows/publicar.yml when Ramon (and only Ramon) opens an issue titled
# "publicar AAAA-MM-DD" (both videos) or "publicar AAAA-MM-DD 1" (only video 1).
# Reads posts.json and the mp4 files from the branch videos-dia (already in ./vd).
# X needs 4 secrets: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET.
# YouTube needs 3: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
# Without them that site is skipped and the report says what is missing. Nothing is published twice.
import json, os, re, sys

title = os.environ.get("ISSUE_TITLE", "")
m = re.match(r"\s*publicar\s+(\d{4}-\d{2}-\d{2})(?:\s+(\d))?\s*$", title, re.I)
report = []
if not m:
    print("Título no reconocido. Usá: publicar AAAA-MM-DD o publicar AAAA-MM-DD 1"); sys.exit(0)
day, only = m.group(1), m.group(2)
posts = json.load(open("vd/posts.json", encoding="utf-8"))
if posts.get("date") != day:
    print(f"Los videos guardados son del {posts.get('date')}, no del {day}. No se publicó nada."); sys.exit(0)
done_path = "notas/publicados.txt"
done = open(done_path, encoding="utf-8").read() if os.path.exists(done_path) else ""
new_lines = []

have_x = all(os.environ.get(k) for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"))
have_yt = all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))


def post_x(v):
    import tweepy
    auth = tweepy.OAuth1UserHandler(os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
                                    os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    media = tweepy.API(auth).media_upload("vd/" + v["file"], chunked=True, media_category="tweet_video")
    c = tweepy.Client(consumer_key=os.environ["X_API_KEY"], consumer_secret=os.environ["X_API_SECRET"],
                      access_token=os.environ["X_ACCESS_TOKEN"], access_token_secret=os.environ["X_ACCESS_SECRET"])
    t = c.create_tweet(text=v["x_text"], media_ids=[media.media_id])
    tid = t.data["id"]
    if v.get("x_reply"):
        c.create_tweet(text=v["x_reply"], in_reply_to_tweet_id=tid)
    return f"https://x.com/LaCanastaIndex/status/{tid}"


def post_yt(v):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    cr = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], token_uri="https://oauth2.googleapis.com/token",
                     client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"])
    yt = build("youtube", "v3", credentials=cr)
    body = {"snippet": {"title": v["yt_title"][:100], "description": v["yt_description"] + "\n\n" + v["hashtags"],
                        "categoryId": "25", "defaultLanguage": "es", "defaultAudioLanguage": "es-419"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    r = yt.videos().insert(part="snippet,status", body=body,
                           media_body=MediaFileUpload("vd/" + v["file"], chunksize=-1, resumable=True)).execute()
    return f"https://youtube.com/shorts/{r['id']}"


for i, v in enumerate(posts["videos"], 1):
    if only and str(i) != only:
        continue
    report.append(f"VIDEO {i}: {v['name']}")
    for site, ok, fn in (("X", have_x, post_x), ("YouTube", have_yt, post_yt)):
        key = f"{day} {i} {site}"
        if key in done:
            report.append(f"  {site}: ya estaba publicado, no se repite."); continue
        if not ok:
            report.append(f"  {site}: todavía no está conectado (faltan las claves). No se publicó."); continue
        try:
            url = fn(v)
            report.append(f"  {site}: publicado ✅ {url}"); new_lines.append(f"{key} {url}")
        except Exception as e:
            report.append(f"  {site}: ERROR, no se publicó: {str(e)[:300]}")

if new_lines:
    with open(done_path, "a", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
print("\n".join(report))
