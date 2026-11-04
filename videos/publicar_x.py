# La Canasta: publishes a one-off set of videos on X (not YouTube), after Ramon gave his OK in a chat with Claude.
# Reads vd/posts.json (cloned from the branch given to the workflow). Nothing is published twice:
# notas/publicados.txt keeps one line per video, keyed "<set> <n> X".
import json, os, sys

which = os.environ.get("WHICH", "todos").strip().lower()  # "todos", "1" or "2"
posts = json.load(open("vd/posts.json", encoding="utf-8"))
tag = posts.get("date", "set")
done_path = "notas/publicados.txt"
done = open(done_path, encoding="utf-8").read() if os.path.exists(done_path) else ""
have_x = all(os.environ.get(k) for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"))
report, new_lines = [], []


def post_x(v):
    import tweepy
    auth = tweepy.OAuth1UserHandler(os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
                                    os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    media = tweepy.API(auth).media_upload("vd/" + v["file"], chunked=True, media_category="tweet_video")
    c = tweepy.Client(consumer_key=os.environ["X_API_KEY"], consumer_secret=os.environ["X_API_SECRET"],
                      access_token=os.environ["X_ACCESS_TOKEN"], access_token_secret=os.environ["X_ACCESS_SECRET"])
    t = c.create_tweet(text=v["x_text"], media_ids=[media.media_id])
    tid = t.data["id"]
    if v.get("x_reply") and os.environ.get("X_REPLY") == "si":
        c.create_tweet(text=v["x_reply"], in_reply_to_tweet_id=tid)
    return f"https://x.com/LaCanastaIndex/status/{tid}"


for i, v in enumerate(posts["videos"], 1):
    if which not in ("todos", "") and str(i) != which:
        continue
    report.append(f"VIDEO {i}: {v['name']}")
    key = f"{tag} {i} X"
    if key in done:
        report.append("  X: ya estaba publicado, no se repite."); continue
    if not have_x:
        report.append("  X: faltan las claves. No se publicó."); continue
    try:
        url = post_x(v)
        report.append(f"  X: publicado ✅ {url}"); new_lines.append(f"{key} {url}")
    except Exception as e:
        report.append(f"  X: ERROR, no se publicó: {str(e)[:400]}")

if new_lines:
    with open(done_path, "a", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
ok = sum(1 for l in report if "publicado ✅" in l or "ya estaba publicado" in l)
n = sum(1 for l in report if l.startswith("VIDEO"))
if ok == n:
    head, subj = f"Ramon, todo bien: se publicaron los {n} videos en X." if n > 1 else "Ramon, todo bien: se publicó el video en X.", "✅ Publicados en X"
elif ok:
    head, subj = f"Ramon, ojo: se publicó {ok} de {n} en X. Mirá abajo por qué el otro no.", "⚠️ Publicado en X a medias"
else:
    head, subj = "Ramon, ojo: no se publicó nada en X. Mirá abajo por qué.", "⚠️ No se publicó nada en X"
open("subject.txt", "w", encoding="utf-8").write(f"{subj} | La Canasta {tag}")
print(head + "\n\n" + "\n".join(report))
