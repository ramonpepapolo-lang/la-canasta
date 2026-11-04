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


def upload_video(path):
    """Chunked upload (INIT, APPEND, FINALIZE, STATUS) done by hand, so every X answer is in the report."""
    import time, requests
    from requests_oauthlib import OAuth1
    auth = OAuth1(os.environ["X_API_KEY"], os.environ["X_API_SECRET"], os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    U = "https://upload.twitter.com/1.1/media/upload.json"
    size = os.path.getsize(path)
    r = requests.post(U, auth=auth, data={"command": "INIT", "media_type": "video/mp4", "total_bytes": size, "media_category": "tweet_video"})
    report.append(f"  INIT {r.status_code}: {r.text[:200]}")
    r.raise_for_status(); mid = r.json()["media_id_string"]
    with open(path, "rb") as f:
        i = 0
        while True:
            chunk = f.read(4 * 1024 * 1024)
            if not chunk: break
            r = requests.post(U, auth=auth, data={"command": "APPEND", "media_id": mid, "segment_index": i}, files={"media": chunk})
            if r.status_code >= 300: report.append(f"  APPEND {i} {r.status_code}: {r.text[:200]}"); r.raise_for_status()
            i += 1
    r = requests.post(U, auth=auth, data={"command": "FINALIZE", "media_id": mid})
    report.append(f"  FINALIZE {r.status_code}: {r.text[:300]}")
    r.raise_for_status(); info = r.json().get("processing_info")
    while info and info.get("state") in ("pending", "in_progress"):
        time.sleep(info.get("check_after_secs", 5))
        r = requests.get(U, auth=auth, params={"command": "STATUS", "media_id": mid}); info = r.json().get("processing_info")
    report.append(f"  STATUS: {json.dumps(info)[:300]}")
    if info and info.get("state") == "failed":
        raise RuntimeError(f"X rechazó el video: {info.get('error')}")
    return mid


def post_x(v):
    import requests
    from requests_oauthlib import OAuth1
    auth = OAuth1(os.environ["X_API_KEY"], os.environ["X_API_SECRET"], os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"])
    mid = upload_video("vd/" + v["file"])
    r = requests.post("https://api.twitter.com/2/tweets", auth=auth, json={"text": v["x_text"], "media": {"media_ids": [mid]}})
    if r.status_code >= 300:
        raise RuntimeError(f"X contestó {r.status_code}: {r.text[:400]}")
    tid = r.json()["data"]["id"]
    if v.get("x_reply") and os.environ.get("X_REPLY") == "si":
        requests.post("https://api.twitter.com/2/tweets", auth=auth, json={"text": v["x_reply"], "reply": {"in_reply_to_tweet_id": tid}})
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
        det = ""
        for k in ("api_messages", "api_errors", "api_codes"):
            if getattr(e, k, None): det += f" {k}={getattr(e, k)}"
        r = getattr(e, "response", None)
        if r is not None and getattr(r, "text", None): det += f" body={r.text[:300]}"
        report.append(f"  X: ERROR, no se publicó: {str(e)[:200]}{det}"[:700])

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
