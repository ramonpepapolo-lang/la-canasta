# La Canasta: emails the monthly report to subscribers (through Brevo).
#
# Runs every day after the index. It only sends when ALL of these are true:
#   1. A finished monthly report exists that has not been emailed yet.
#   2. We are already in the next month (so you get until the next run, on the 1st, to check it and write your note).
#   3. The file notas/pausar-email.txt does NOT exist (create that file to stop sending).
#   4. The Brevo secrets are set in GitHub (BREVO_API_KEY, BREVO_LIST_ID, BREVO_SENDER).
# Every day it also saves a preview of the email: index/informes/email-YYYY-MM.html
# If anything goes wrong it just prints a warning. It never stops the daily prices from being saved.
#
# Test mode: "python send_report_email.py --prueba" creates a [PRUEBA] email in Brevo
# with the latest numbers but does NOT send it to anyone. Used by the "Test email" button in GitHub Actions.

import datetime
import html
import json
import os
import sys

PRUEBA = "--prueba" in sys.argv

SITE = "https://lacanastaindex.com"
MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MONTH = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
SHOP = {"Carrefour": "Carrefour", "Jumbo": "Jumbo", "ChangoMas": "ChangoMás", "Dia": "Día"}
GROUP = {"pan_cereales": "Pan y cereales", "carne_ave": "Pollo", "lacteos": "Lácteos y huevos", "aceites": "Aceites", "frutas": "Frutas",
         "verduras": "Verduras", "azucar": "Azúcar y dulces", "otros_alimentos": "Otros alimentos", "cafe_te_yerba": "Café, té y yerba",
         "aguas_gaseosas": "Aguas y gaseosas", "alcohol": "Bebidas alcohólicas", "limpieza": "Limpieza", "cuidado_personal": "Cuidado personal"}
TYPE_ES = {"pan_lactal": "Pan lactal blanco", "harina_000": "Harina 000, 1 kg", "arroz": "Arroz, 1 kg", "fideos": "Fideos tallarín, 500 g",
           "pollo_entero": "Pollo entero, por kg", "leche": "Leche entera, 1 L", "manteca": "Manteca, 200 g", "queso_cremoso": "Queso cremoso",
           "dulce_de_leche": "Dulce de leche, 400 g", "huevos": "Huevos blancos x12", "aceite_girasol": "Aceite de girasol, 1,5 L",
           "papa": "Papa, por kg", "cebolla": "Cebolla, por kg", "tomate": "Tomate redondo, por kg", "banana": "Banana, por kg",
           "manzana": "Manzana roja, por kg", "azucar": "Azúcar, 1 kg", "yerba": "Yerba mate, 1 kg", "cafe": "Café instantáneo, 170 g",
           "te": "Té en saquitos", "mayonesa": "Mayonesa, 500 g", "pure_tomate": "Puré de tomate, 520 g", "coca_cola": "Coca-Cola, 2,25 L",
           "agua": "Agua mineral, 2 L", "cerveza": "Cerveza rubia, 1 L", "vino": "Vino tinto, 1 L", "papel_higienico": "Papel higiénico 4 x 30 m",
           "detergente": "Detergente, 500 ml", "lavandina": "Lavandina, 1 L", "jabon_ropa": "Jabón en polvo, 800 g", "shampoo": "Shampoo",
           "pasta_dental": "Pasta dental, 90 g", "jabon_tocador": "Jabón de tocador"}
NAVY, CELESTE, MUTED, RULE, UP, DOWN = "#2B3B5C", "#7FB1C6", "#5D6A84", "#DCE4EA", "#B2462B", "#2D7A57"


def sp(v):
    """+2,74% in Argentine format."""
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("+" if v > 0 else "−" if v < 0 else "") + s + "%"


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def build_email(r, unsubscribe):
    m = r["month"]
    mi, y = int(m[5:]) - 1, m[:4]
    link = f"{SITE}/informe.html?m={m}"
    reg = r["headline"]["avg_regular"] if r["method"] == "average" else r["headline"]["end_to_end_regular"]
    word = "Suba" if r["inflation"] >= 0 else "Baja"
    color = lambda v: UP if v > 0 else DOWN if v < 0 else MUTED

    def rows(items):
        return "".join(
            f'<tr><td style="padding:7px 0;border-bottom:1px solid {RULE};color:{NAVY}">{html.escape(a)}</td>'
            f'<td style="padding:7px 0;border-bottom:1px solid {RULE};text-align:right;font-weight:700;color:{color(v)}">{sp(v)}</td></tr>'
            for a, v in items)

    groups = [(GROUP.get(g["group"], g["group"]), g["pct"]) for g in r["groups"] if g["in_headline"]]
    shops = [(SHOP.get(s["shop"], s["shop"]), s["pct"]) for s in sorted(r["shops"], key=lambda s: -s["pct"])]
    up = [(f'{TYPE_ES.get(p["type"], p["type_en"])} ({SHOP.get(p["shop"], p["shop"])})', p["pct"]) for p in r["top_up"][:3]]
    down = [(f'{TYPE_ES.get(p["type"], p["type_en"])} ({SHOP.get(p["shop"], p["shop"])})', p["pct"]) for p in r["top_down"][:3]]

    note = read(f"notas/{m}-es.txt")
    note_html = ""
    if note and note.strip():
        paras = "".join(f'<p style="margin:0 0 10px">{html.escape(p.strip())}</p>' for p in note.strip().split("\n\n") if p.strip())
        note_html = (f'<div style="border-left:4px solid {CELESTE};padding:4px 0 4px 16px;margin:26px 0">{paras}'
                     f'<p style="margin:0;font-weight:700">Ramon Pepa</p></div>')

    h3 = lambda t: f'<h3 style="font-family:Georgia,serif;font-weight:400;font-size:20px;color:{NAVY};margin:28px 0 6px">{t}</h3>'
    table = lambda items: f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:15px">{rows(items)}</table>'

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>La Canasta: {MES[mi]} {y}</title></head>
<body style="margin:0;background:#F3F7F9;font-family:Helvetica,Arial,sans-serif;color:{NAVY}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F3F7F9"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#FFFFFF;border-radius:14px;border:1px solid {RULE}">
<tr><td style="padding:28px 32px 8px"><img src="{SITE}/la-canasta-logo/la-canasta-logo-horizontal.png" alt="La Canasta" height="40" style="height:40px;display:block"></td></tr>
<tr><td style="padding:12px 32px 32px;font-size:16px;line-height:1.55">
<p style="margin:0;font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{MUTED}">Informe mensual</p>
<h1 style="font-family:Georgia,serif;font-weight:400;font-size:30px;line-height:1.15;margin:6px 0 18px">Informe de {MES[mi]} de {y}</h1>
<p style="font-family:Georgia,serif;font-size:64px;line-height:1;margin:0">{sp(r["inflation"])}</p>
<p style="margin:8px 0 0;color:{MUTED}">{word} de los precios del súper en {MES[mi]}. Precio de lista: {sp(reg)}.</p>
{note_html}
{h3("Por grupo")}{table(groups)}
{h3("Por supermercado")}{table(shops)}
{h3("Los que más subieron")}{table(up)}
{h3("Los que más bajaron")}{table(down)}
<p style="margin:30px 0 0"><a href="{link}" style="background:{NAVY};color:#FFFFFF;text-decoration:none;font-weight:700;padding:13px 22px;border-radius:10px;display:inline-block">Leer el informe completo</a></p>
<p style="margin:26px 0 0;padding-top:18px;border-top:1px solid {RULE};font-size:14px;color:{MUTED}"><strong style="color:{NAVY}">In English:</strong>
supermarket prices in Argentina {"rose" if r["inflation"] >= 0 else "fell"} {sp(r["inflation"]).replace(",", ".")} in {MONTH[mi]} {y}. <a href="{link}" style="color:{NAVY}">Read the full report</a> (switch to English at the top).</p>
</td></tr></table>
<p style="max-width:600px;font-size:12px;color:{MUTED};line-height:1.5;margin:16px auto 0">La Canasta es un proyecto independiente de Ramon Pepa. Sin vínculo con ningún supermercado, el INDEC ni el gobierno.<br>
Recibís este email porque te suscribiste en lacanastaindex.com. <a href="{unsubscribe}" style="color:{MUTED}">Darte de baja</a></p>
</td></tr></table></body></html>"""


def create_campaign(m, headers, list_id, sender, test=False):
    """Creates the email in Brevo (not sent yet). Returns its id, or None if Brevo said no."""
    import requests
    r = json.loads(read(f"index/informes/{m}.json"))
    mi = int(m[5:]) - 1
    subject = f"La Canasta · {MES[mi].capitalize()} {m[:4]}: {sp(r['inflation'])}"
    body = {
        "name": ("PRUEBA " if test else "") + f"Informe {m}",
        "subject": ("[PRUEBA] " if test else "") + subject,
        "previewText": f"Cuánto subieron los precios del súper en {MES[mi]}.",
        "sender": {"name": "La Canasta", "email": sender},
        "htmlContent": build_email(r, "{{ unsubscribe }}"),
        "recipients": {"listIds": [int(list_id)]},
    }
    res = requests.post("https://api.brevo.com/v3/emailCampaigns", headers=headers, json=body, timeout=60)
    if res.status_code not in (200, 201):
        print(f"WARNING: Brevo did not create the email ({res.status_code}): {res.text[:300]}")
        return None
    return res.json()["id"]


def main():
    listing = json.loads(read("index/informes/lista.json") or "[]")
    if not listing:
        print("Email: no reports yet.")
        return
    # Preview of the latest month (draft or finished), so you can see what will be sent
    latest = listing[-1]["month"]
    rep = json.loads(read(f"index/informes/{latest}.json"))
    with open(f"index/informes/email-{latest}.html", "w", encoding="utf-8") as f:
        f.write(build_email(rep, "#"))

    if PRUEBA:
        key, list_id, sender = (os.environ.get(k, "").strip() for k in ("BREVO_API_KEY", "BREVO_LIST_ID", "BREVO_SENDER"))
        if not (key and list_id and sender):
            print("PRUEBA: missing secrets. Check BREVO_API_KEY, BREVO_LIST_ID and BREVO_SENDER in GitHub.")
            sys.exit(1)
        headers = {"api-key": key, "accept": "application/json", "content-type": "application/json"}
        cid = create_campaign(latest, headers, list_id, sender, test=True)
        if not cid:
            sys.exit(1)
        print(f"PRUEBA OK: Brevo created the test email (campaign {cid}). It was NOT sent to anyone.")
        print("Look for it in Brevo: Marketing > Campañas.")
        return

    ready = [x for x in listing if x["publishable"]]
    if not ready:
        print("Email: no finished report yet, nothing to send.")
        return
    m = ready[-1]["month"]
    sent = (read("index/informes/enviados.txt") or "").split()
    if m in sent:
        print(f"Email: {m} was already sent.")
        return
    today = datetime.date.today()
    y, mo = int(m[:4]), int(m[5:])
    next_month = datetime.date(y + mo // 12, mo % 12 + 1, 1)
    if today < next_month:
        print(f"Email: {m} will be sent on {next_month} (gives you time to check it and write your note).")
        return
    if (today - next_month).days > 20:
        print(f"Email: {m} is too old to send now, skipping.")
        return
    if os.path.exists("notas/pausar-email.txt"):
        print("Email: PAUSED (notas/pausar-email.txt exists). Delete that file to send.")
        return
    key, list_id, sender = (os.environ.get(k, "").strip() for k in ("BREVO_API_KEY", "BREVO_LIST_ID", "BREVO_SENDER"))
    if not (key and list_id and sender):
        print("Email: Brevo is not connected yet (secrets missing), not sending.")
        return

    headers = {"api-key": key, "accept": "application/json", "content-type": "application/json"}
    cid = create_campaign(m, headers, list_id, sender)
    if not cid:
        return
    import requests
    res = requests.post(f"https://api.brevo.com/v3/emailCampaigns/{cid}/sendNow", headers=headers, timeout=60)
    if res.status_code not in (200, 202, 204):
        print(f"WARNING: Brevo created the email (campaign {cid}) but did not send it ({res.status_code}): {res.text[:300]}")
        return
    with open("index/informes/enviados.txt", "a", encoding="utf-8") as f:
        f.write(m + "\n")
    print(f"Email: report {m} sent to the subscriber list.")


try:
    main()
except SystemExit:
    raise
except Exception as e:  # never break the daily run
    print(f"WARNING: email step failed: {e}", file=sys.stderr)
    if PRUEBA:
        sys.exit(1)
