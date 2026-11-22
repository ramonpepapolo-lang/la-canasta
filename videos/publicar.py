# La Canasta: publishes the day's Shorts ONLY after Ramon approves them.
# Run by .github/workflows/publicar.yml when Ramon (and only Ramon) opens an issue titled
# "publicar AAAA-MM-DD" (both videos) or "publicar AAAA-MM-DD 1" (only video 1).
# Reads posts.json and the mp4 files from the branch videos-dia (already in ./vd).
# X needs 4 secrets: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET.
# YouTube needs 3: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
# Without them that site is skipped and the report says what is missing. Nothing is published twice.
import json, os, re, sys

title = os.environ.get("ISSUE_TITLE", "")
# Long videos (mini-docs, the Sunday "Reporte semanal"): "publicar largos AAAA-MM-DD" reads the branch videos-largos.
m = re.match(r"\s*publicar\s+(largos\s+)?(\d{4}-\d{2}-\d{2})(?:\s+(\d))?\s*$", title, re.I)
report = []
if not m:
    open("subject.txt", "w").write("⚠️ No se publicó nada | La Canasta")
    print("Ramon, ojo: no se publicó nada, ni en X ni en YouTube. Título no reconocido. Usá: publicar AAAA-MM-DD o publicar AAAA-MM-DD 1"); sys.exit(0)
largos, day, only = bool(m.group(1)), m.group(2), m.group(3)
tag = ("largos " if largos else "") + day
posts = json.load(open("vd/posts.json", encoding="utf-8"))
if posts.get("date") != day:
    open("subject.txt", "w").write(f"⚠️ No se publicó nada | La Canasta {day}")
    print(f"Ramon, ojo: no se publicó nada, ni en X ni en YouTube. Los videos guardados son del {posts.get('date')}, no del {day}."); sys.exit(0)
done_path = "notas/publicados.txt"
# exact keys ("{tag} {i} {site}" = each line without its URL), so "2026-11-22 1 X" is not mistaken for
# "largos 2026-11-22 1 X" (that bug skipped the 22 Nov Short)
done = {l.rsplit(" ", 1)[0].strip() for l in open(done_path, encoding="utf-8")} if os.path.exists(done_path) else set()
new_lines = []

have_x = all(os.environ.get(k) for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"))
have_yt = all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))
# Since 2 Nov 2026 Google no longer locks API uploads as private (no audit needed), so approved videos go to
# YouTube too (asked by Ramon, 13 Nov 2026). Setting the repo variable YT_ON to "no" turns YouTube off again.
yt_on = os.environ.get("YT_ON", "").strip().lower() != "no"


def post_x(v):
    import tweepy
    auth = tweepy.OAuth1UserHandler(os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
                                    os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    # X takes videos of up to 140 s: long videos bring a shorter cut for X in "x_file"
    media = tweepy.API(auth).media_upload("vd/" + v.get("x_file", v["file"]), chunked=True, media_category="tweet_video")
    c = tweepy.Client(consumer_key=os.environ["X_API_KEY"], consumer_secret=os.environ["X_API_SECRET"],
                      access_token=os.environ["X_ACCESS_TOKEN"], access_token_secret=os.environ["X_ACCESS_SECRET"])
    t = c.create_tweet(text=v["x_text"], media_ids=[media.media_id])
    tid = t.data["id"]
    # X charges about 13 times more for a post with a link ($0.20 vs $0.015), so the reply with the link
    # is only posted if the repo variable X_REPLY is "si". The link is in the profile anyway.
    if v.get("x_reply") and os.environ.get("X_REPLY") == "si":
        c.create_tweet(text=v["x_reply"], in_reply_to_tweet_id=tid)
    return f"https://x.com/LaCanastaIndex/status/{tid}"


def post_yt(v):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    cr = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], token_uri="https://oauth2.googleapis.com/token",
                     client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"])
    yt = build("youtube", "v3", credentials=cr)
    lang = v.get("lang", "es")
    tags = v.get("hashtags", "")
    if isinstance(tags, list):  # the daily agent sometimes writes the hashtags as a list
        tags = " ".join(tags)
    body = {"snippet": {"title": v["yt_title"][:100], "description": v["yt_description"] + ("\n\n" + tags if tags else ""),
                        "categoryId": "25", "defaultLanguage": lang, "defaultAudioLanguage": "en" if lang == "en" else "es-419"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    r = yt.videos().insert(part="snippet,status", body=body,
                           media_body=MediaFileUpload("vd/" + v["file"], chunksize=-1, resumable=True)).execute()
    thumb = v.get("thumb") or v.get("thumbnail")
    if thumb:  # custom thumbnail, also for Shorts (YouTube only allows it on verified channels; if it fails the video stays up)
        try:
            yt.thumbnails().set(videoId=r["id"], media_body=MediaFileUpload("vd/" + thumb)).execute()
        except Exception as e:
            report.append(f"  (miniatura no subida: {str(e)[:160]})")
    return f"https://youtube.com/watch?v={r['id']}" if v.get("long") else f"https://youtube.com/shorts/{r['id']}"


for i, v in enumerate(posts["videos"], 1):
    if only and str(i) != only:
        continue
    report.append(f"VIDEO {i}: {v['name']}")
    for site, ok, fn in (("X", have_x, post_x), ("YouTube", have_yt, post_yt)):
        key = f"{tag} {i} {site}"
        if key in done:
            report.append(f"  {site}: ya estaba publicado, no se repite."); continue
        if not ok:
            report.append(f"  {site}: todavía no está conectado (faltan las claves). No se publicó."); continue
        if site == "YouTube" and not yt_on:
            report.append("  YouTube: apagado a propósito (variable YT_ON = no). No se publicó."); continue
        try:
            url = fn(v)
            report.append(f"  {site}: publicado ✅ {url}"); new_lines.append(f"{key} {url}")
        except Exception as e:
            report.append(f"  {site}: ERROR, no se publicó: {str(e)[:300]}")

# X posts with an image (a chart) and our own comment, no video (Ramon, 18 Nov 2026). posts.json "x_posts":
# [{"image": "file.png", "x_text": "..."}]. Published on X only, with the same approval as the day's Short.
def post_x_image(p):
    import tweepy
    auth = tweepy.OAuth1UserHandler(os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
                                    os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    media = tweepy.API(auth).media_upload("vd/" + p["image"])
    c = tweepy.Client(consumer_key=os.environ["X_API_KEY"], consumer_secret=os.environ["X_API_SECRET"],
                      access_token=os.environ["X_ACCESS_TOKEN"], access_token_secret=os.environ["X_ACCESS_SECRET"])
    t = c.create_tweet(text=p["x_text"], media_ids=[media.media_id])
    return f"https://x.com/LaCanastaIndex/status/{t.data['id']}"


if not only:
    for j, p in enumerate(posts.get("x_posts", []), 1):
        report.append(f"POST CON GRÁFICO {j} (solo X)")
        key = f"{tag} img{j} X"
        if key in done:
            report.append("  X (gráfico): ya estaba publicado, no se repite."); continue
        if not have_x:
            report.append("  X (gráfico): faltan las claves. No se publicó."); continue
        try:
            url = post_x_image(p)
            report.append(f"  X (gráfico): publicado ✅ {url}"); new_lines.append(f"{key} {url}")
        except Exception as e:
            report.append(f"  X (gráfico): ERROR, no se publicó: {str(e)[:300]}")

if new_lines:
    with open(done_path, "a", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

# One clear line on top for Ramon: where it was published (X, YouTube, both or nowhere)
n = len([v for i, v in enumerate(posts["videos"], 1) if not only or str(i) == only])
# counts both new uploads and ones already published by an earlier approval
sites = {s: sum(1 for l in report if l.startswith(f"  {s}: ") and ("publicado ✅" in l or "ya estaba publicado" in l))
         for s in ("X", "YouTube")}
videos = "el video" if n == 1 else f"los {n} videos"
if sites["X"] and sites["YouTube"]:
    head, subj = f"Ramon, todo bien: se publicaron {videos} en X y en YouTube.", "✅ Publicados en X y YouTube"
elif sites["X"]:
    head, subj = f"Ramon, todo bien: se publicaron {videos} solo en X. YouTube no (mirá abajo por qué).", "✅ Publicados en X (YouTube no)"
elif sites["YouTube"]:
    head, subj = f"Ramon, ojo: se publicaron {videos} solo en YouTube. En X no (mirá abajo por qué).", "⚠️ Publicados solo en YouTube"
else:
    head, subj = "Ramon, ojo: no se publicó nada, ni en X ni en YouTube. Mirá abajo por qué.", "⚠️ No se publicó nada"
if sites["X"] and sites["X"] < n or sites["YouTube"] and sites["YouTube"] < n:
    head += " Alguno no salió en todos lados, mirá el detalle."
open("subject.txt", "w", encoding="utf-8").write(f"{subj} | La Canasta {day}")
# Promotion suggestion for today (written by the daily video agent in posts.json, see videos/LEEME-videos.md).
# Nothing is ever paid automatically: Ramon decides and taps Promote himself in the YouTube Studio app.
promo = posts.get("promo") or {}
if promo.get("budget_gbp"):
    report += ["", "💸 ¿PROMOCIONAMOS HOY? (lo decidís vos, nada se paga solo)",
               f"  Video: {promo.get('video', '')}",
               f"  Objetivo: {promo.get('goal', '')}",
               f"  Gasto sugerido hoy: £{promo['budget_gbp']}",
               f"  Por qué: {promo.get('why', '')}",
               "  Cómo: app YouTube Studio en el celu → el video → Promocionar. Después contale a Claude cuánto gastaste."]
print(head + "\n\n" + "\n".join(report))
