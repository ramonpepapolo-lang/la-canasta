# Sends the emails in emails.json one by one through Brevo, from hola@lacanastaindex.com only.
# If the first one fails, nothing else is sent. Result: resultados.json
import json, os, time, urllib.request, urllib.error
KEY = os.environ["BREVO_API_KEY"].strip()
FROM = {"name": "Ramon Pepa · La Canasta", "email": "hola@lacanastaindex.com"}
res = []
for i, m in enumerate(json.load(open("emails.json", encoding="utf-8"))):
    msg = {"sender": FROM, "replyTo": {"email": FROM["email"], "name": "Ramon Pepa"},
           "to": [{"email": m["to"], "name": m["outlet"]}], "subject": m["subject"], "textContent": m["text"]}
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(msg).encode(), method="POST",
                                 headers={"api-key": KEY, "content-type": "application/json", "accept": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=30); ok, info = True, json.loads(r.read() or b"{}").get("messageId", "")
    except urllib.error.HTTPError as e:
        ok, info = False, f"{e.code} {e.read()[:300].decode(errors='replace')}"
    res.append({"outlet": m["outlet"], "to": m["to"], "sent": ok, "info": info})
    print(m["outlet"], ok, info)
    if not ok and i == 0:
        print("First email failed: nothing else sent."); break
    time.sleep(20)
json.dump(res, open("resultados.json", "w"), ensure_ascii=False, indent=1)
