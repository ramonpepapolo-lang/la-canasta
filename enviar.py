# Sends the emails in emails.json one by one through Brevo, from hola@lacanastaindex.com only.
# If the first one fails, nothing else is sent. Result: resultados.json
import json, os, sys, time, urllib.request, urllib.error
SRC = sys.argv[1] if len(sys.argv) > 1 else "emails.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "resultados.json"
BCC = sys.argv[3] if len(sys.argv) > 3 else ""
KEY = os.environ["BREVO_API_KEY"].strip()
FROM = {"name": "Ramon Pepa · La Canasta", "email": "hola@lacanastaindex.com"}
res = []
for i, m in enumerate(json.load(open(SRC, encoding="utf-8"))):
    msg = {"sender": FROM, "replyTo": {"email": FROM["email"], "name": "Ramon Pepa"},
           "to": [{"email": m["to"], "name": m["outlet"]}], "subject": m["subject"], "textContent": m["text"]}
    if BCC:
        msg["bcc"] = [{"email": BCC}]
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
json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
