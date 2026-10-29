# La Canasta: emails to Ramon about the daily collection (through Brevo).
#
#   python alert_email.py --ok            after today's prices are saved: checks them and sends
#                                         "datos de hoy guardados" (or a warning if something looks wrong)
#   python alert_email.py --fail "why"    a run could not save today's prices
#   python alert_email.py --msg "subject" "text"   any message (used by the guardian agent)
#
# Who receives them: the GitHub secret ALERT_EMAILS (comma separated). Never written in this public repo.
# Needs only Python's standard library, so it works even if an earlier step failed.

import csv
import glob
import gzip
import html
import json
import os
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

AR = ZoneInfo("America/Argentina/Buenos_Aires")
SHOPS = ["Carrefour", "Jumbo", "ChangoMas", "Dia", "Coto"]
SITE = "https://lacanastaindex.com"
NAVY, MUTED, OK, BAD = "#2B3B5C", "#5D6A84", "#2D7A57", "#B2462B"


def send(subject, body_html):
    key = os.environ.get("BREVO_API_KEY", "").strip()
    sender = os.environ.get("BREVO_SENDER", "").strip()
    to = [e.strip() for e in os.environ.get("ALERT_EMAILS", "").split(",") if e.strip()]
    if not (key and sender and to):
        print("Alert email not sent: BREVO_API_KEY, BREVO_SENDER or ALERT_EMAILS missing.")
        return False
    page = (f'<div style="font-family:Helvetica,Arial,sans-serif;color:{NAVY};font-size:15px;line-height:1.55;max-width:560px">'
            f'{body_html}<p style="color:{MUTED};font-size:12px;margin-top:24px">La Canasta · aviso automático · '
            f'<a href="{SITE}/admin.html" style="color:{MUTED}">admin</a></p></div>')
    data = json.dumps({"sender": {"name": "La Canasta", "email": sender},
                       "to": [{"email": e} for e in to],
                       "subject": subject, "htmlContent": page}).encode()
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=data, method="POST",
                                 headers={"api-key": key, "content-type": "application/json", "accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"Alert email sent ({r.status}) to {len(to)} address(es): {subject}")
            return True
    except Exception as e:
        detail = e.read().decode()[:300] if hasattr(e, "read") else ""
        print(f"WARNING: alert email failed: {e} {detail}")
        return False


def rows_of(path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def daily_check():
    today = datetime.now(AR).date().isoformat()
    path = f"data/{today}.csv.gz"
    if not os.path.exists(path):
        return send(f"❌ La Canasta: falta el dato de hoy ({today})",
                    f"<h2 style='color:{BAD}'>No se guardaron los precios de hoy</h2><p>El archivo de hoy no existe. "
                    "Las próximas corridas automáticas lo van a intentar de nuevo.</p>")
    rows = rows_of(path)
    by_shop = Counter(r["shop"] for r in rows)
    basket_found = sum(1 for r in rows if r["basket_type"] and not r["basket_type"].startswith("watch"))
    watch_found = sum(1 for r in rows if r["basket_type"].startswith("watch"))

    # Average rows per shop over the previous 7 days
    past = sorted(p for p in glob.glob("data/????-??-??.csv.gz") if os.path.basename(p)[:10] < today)[-7:]
    avg = defaultdict(float)
    for p in past:
        for s, n in Counter(r["shop"] for r in rows_of(p)).items():
            avg[s] += n / len(past)

    daily = list(csv.DictReader(open("index/daily.csv", encoding="utf-8")))
    last = daily[-1] if daily else {}
    prev = daily[-2] if len(daily) > 1 else None
    in_stock = int(last.get("products_in_stock") or 0)
    checks = [l for l in open("index/checks.txt", encoding="utf-8").read().splitlines() if l.startswith(today)]

    problems = []
    if last.get("date") != today:
        problems.append("El índice no se actualizó con el día de hoy.")
    for s in SHOPS:
        if by_shop[s] == 0:
            problems.append(f"{s} no devolvió ningún precio.")
        elif avg[s] and by_shop[s] < 0.7 * avg[s]:
            problems.append(f"{s} devolvió {by_shop[s]} precios, bastante menos que lo normal ({avg[s]:.0f}).")
    if basket_found < 120:
        problems.append(f"Solo se encontraron {basket_found} de 129 productos de la canasta.")
    if in_stock < 110:
        problems.append(f"Solo {in_stock} de 129 productos con stock.")
    if checks:
        problems.append(f"{len(checks) // 2 or 1} precio(s) dejados afuera por parecer errores (ver index/checks.txt).")
    if os.environ.get("VERIFY") == "failure":
        detail_v = ""
        if os.path.exists("index/verificacion.txt"):
            detail_v = " ".join(l for l in open("index/verificacion.txt", encoding="utf-8").read().splitlines() if l.startswith("PROBLEMA"))[:600]
        problems.append("La verificación independiente del índice NO coincide. El informe mensual no se va a enviar hasta que se arregle. " + detail_v)

    change = ""
    if prev and last.get("date") == today:
        d = (float(last["index_paid"]) / float(prev["index_paid"]) - 1) * 100
        change = f" ({'+' if d >= 0 else ''}{d:.2f}".replace(".", ",") + "% contra el día anterior)"
    hora = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%H:%M")
    shop_lines = "".join(f"<li>{s}: {by_shop[s]:,}".replace(",", ".") + "</li>" for s in SHOPS)
    detail = (f"<ul style='padding-left:18px'>{shop_lines}</ul>"
              f"<p>Productos de la canasta encontrados: <b>{basket_found}/129</b> · con stock: <b>{in_stock}/129</b> · "
              f"lista de observación: {watch_found}/31<br>Índice de hoy: <b>{last.get('index_paid', '?')}</b>{html.escape(change)}</p>")

    if not problems:
        return send(f"✅ La Canasta: datos de hoy guardados ({today})",
                    f"<h2 style='color:{OK}'>Datos de hoy guardados. Todo bien.</h2>"
                    f"<p>Se guardaron <b>{len(rows):,}</b> precios a las {hora} (hora de España) y pasaron todos los controles. "
                    "No tenés que hacer nada.</p>".replace(",", ".") + detail +
                    f"<p style='color:{MUTED};font-size:13px'>Controles: los 5 súper respondieron normal, la canasta está completa, "
                    "el índice se actualizó, la verificación independiente coincide y no hubo precios raros. Cada noche el revisor mira los cambios grandes y cada domingo el auditor revisa todo.</p>")
    items = "".join(f"<li>{html.escape(p)}</li>" for p in problems)
    return send(f"⚠️ La Canasta: datos guardados, pero revisá ({today})",
                f"<h2 style='color:{BAD}'>Los datos de hoy se guardaron, pero algo no está normal</h2>"
                f"<ul style='padding-left:18px'>{items}</ul>{detail}"
                "<p>Abrí un chat con Claude y decile: <b>\"La Canasta: revisá los datos de hoy\"</b>.</p>")


if __name__ == "__main__":
    try:
        if "--ok" in sys.argv:
            daily_check()
        elif "--fail" in sys.argv:
            why = sys.argv[sys.argv.index("--fail") + 1] if len(sys.argv) > sys.argv.index("--fail") + 1 else ""
            today = datetime.now(AR).date().isoformat()
            send(f"❌ La Canasta: falló la corrida de hoy ({today})",
                 f"<h2 style='color:{BAD}'>Una corrida no pudo guardar los precios de hoy</h2><p>{html.escape(why)}</p>"
                 "<p>No te preocupes todavía: hay más intentos automáticos durante el día y el guardián la vuelve a arrancar. "
                 "Si a la noche seguís sin un email ✅, abrí un chat con Claude y decile <b>\"La Canasta falló hoy\"</b>.</p>")
        elif "--msg" in sys.argv:
            i = sys.argv.index("--msg")
            subject, text = sys.argv[i + 1], sys.argv[i + 2] if len(sys.argv) > i + 2 else ""
            paras = "".join(f"<p>{html.escape(p)}</p>" for p in text.split("\n") if p.strip())
            send(subject, paras)
    except Exception as e:  # an alert must never break the daily run
        print(f"WARNING: alert step failed: {e}")
