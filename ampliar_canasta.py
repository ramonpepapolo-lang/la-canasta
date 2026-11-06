# La Canasta: proposes extra products for the basket (run by hand, not every day).
#
# The scraper already collects ~20,000 prices a day. This script looks in those files for more
# products of the basket types (the 33 first ones and the ones in NEW_INFO), up to MAX_PER per type and supermarket.
# A product is only proposed if it is clearly that type (strict name + category rules), it was
# in stock almost every day, its name never changed, and its price never jumped 3x in a day.
# Usage: python ampliar_canasta.py            -> writes notas/canasta-propuesta.csv and prints a report
#        python ampliar_canasta.py --apply DATE -> adds the proposal to basket.csv, counting from DATE

import csv, glob, gzip, os, re, sys, unicodedata
from collections import defaultdict

MAX_PER = 5          # products per type and supermarket (the original one included)
MIN_DAYS_SHARE = 0.85  # in stock on at least 85% of the days
SHOPS = ["Carrefour", "Jumbo", "ChangoMas", "Dia"]


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s)


# type -> (must match in name, must NOT match in name, category must contain one of)
BEEF_NO = r"cerdo|porcin|pollo|cordero|lechon|chivit|wagyu|congel|cocid|rotiser|horno|rostiz|marinad|condiment|ternera|kobe|cerdito"
RULES = {
 "pan_lactal": (r"\blactal\b|pan de molde|pan blanco", r"rallad|pancho|hambur|tostad|budin|sin tacc|sin gluten|brioche|chip|grisin|tapa|pizza|arabe|baguet|artesan|masa madre", ["pan"]),
 "harina_000": (r"\bharina\b.*\b0{3,4}\b|\b0{3,4}\b.*\bharina\b", r"maiz|integral|leudante|pizza|premezcla|mandioca|arroz|almendra|garbanzo|avena|bizcochuel|polenta|coco|sin tacc|sin gluten|leche|pan\b", ["harina"]),
 "arroz": (r"^arroz\b", r"harina|galle|snack|leche|bebida|listo|instant|risott|preparad|barra|alfajor|tortita|crocante|sopa|con |sabor|salsa|integral premium", ["arroz"]),
 "fideos": (r"\bfideo|spaghetti|tallarin|mostachol|tirabuzon|codito|monito|dedalito|penne|moño|mono\b|letrita|cabello de angel|vermicelli|tiburon", r"arroz|sopa|instant|rellen|noqui|lasag|ravio|sorrent|capelet|fresco|integral|sin tacc|sin gluten|legumbre|lenteja|garbanzo|con salsa|vegetal", ["fideo", "pasta", "seca"]),
 "pollo_entero": (r"pollo entero|pollo fresco|^pollo x kg", r"trozad|suprema|pata|muslo|ala\b|pechuga|milanesa|hamburg|nugget|medallon|rebozad|marinad|condiment|caldo|sopa|salchicha|congel", ["pollo", "ave"]),
 "leche": (r"^leche\b", r"polvo|chocolat|cacao|condensad|dulce|vegetal|almendra|coco|soja|avena|lactosa|deslactos|bebe|infantil|crecimiento|fermentad|cultivo|nido|nutri|vitalcrem|proteina|sabor|frutilla|vainilla|banana|cafe|chai|kefir|zero|mas proteina|chocolotad|nesquik|protein|barista|200 ?ml|\b200\b|prebiot", ["leche"]),
 "manteca": (r"^manteca\b", r"mani|cacao|untable|light|sin sal|ghee|clarificad|vegetal|margarina", ["manteca", "lacteo"]),
 "queso_cremoso": (r"\bcremoso\b|\bcremon\b|port salut|por salut|cuartirolo", r"untable|rallado|crema de queso|azul|light|sin sal|pizza|fundido|lonchas|feteado", ["queso"]),
 "dulce_de_leche": (r"^dulce de leche\b", r"alfajor|galle|helado|bizcoch|oblea|budin|torta|bocadito|tableta|barra|relleno|bombon|chocolate|repostero|light|sin azucar|0%|cero|lactosa", ["dulce"]),
 "huevos": (r"^huevo", r"chocolat|pascua|kinder|codorniz|liquido|pasteuriz|en polvo|deshidrat|sorpresa", ["huevo"]),
 "aceite_girasol": (r"aceite.*girasol|girasol.*aceite", r"aerosol|spray|oliva|mezcla|maiz|soja|alto oleico|\b120\b", ["aceite"]),
 "banana": (r"^banana", r"chips|deshidrat|licuado|yogur|bocadito|helado|snack|liofiliz|chocolate|bañad|banad", ["fruta", "verdu"]),
 "manzana": (r"^manzana", r"jugo|sidra|pure|deshidrat|chips|compota|vinagre|gaseosa|snack|aguas", ["fruta", "verdu"]),
 "papa": (r"^papa\b|^papas\b", r"frita|chips|bast|noisette|pure|congel|snack|rejilla|lays|pay|smile|carita|bocado|kryzpo|pringles", ["verdu", "fruta"]),
 "cebolla": (r"^cebolla", r"frita|deshidrat|crisp|aros|polvo|salsa|sopa|caramel|en escabeche|pickle|picad|escama|congel|verdeo", ["verdu", "fruta"]),
 "tomate": (r"^tomate", r"pure|triturad|salsa|pelad|seco|cubetead|lata|extracto|deshidrat|ketchup|jugo|perita en|en conserva|tetra|cherry|cocktail|coctel|amarillo|morado|\braf\b", ["verdu", "fruta"]),
 "azucar": (r"^azucar\b", r"impalpable|mascabo|rubia|edulcor|stevia|sin azucar|light|glas|negra|organica|sobre|sobrecito|terron|caña|morena|integral", ["azucar", "endulz"]),
 "mayonesa": (r"\bmayonesa\b", r"vegana|ketchup|mostaza|savora|aderezo de|alioli|ajo|limon|light|0%|sin huevo|picante|dip|tasty|liviana|oliva|sabor", ["aderezo", "mayonesa", "salsa"]),
 "pure_tomate": (r"pure de tomate|pure tomate", r"salsa|pizza|con ", ["tomate", "pure", "conserva", "salsa"]),
 "yerba": (r"^yerba", r"cocido|saquit|compuesta|hierb|sabor|naranja|limon|menta|pomelo|serrana|boldo|peperina|energ|mate listo|frutal|cedron|tilo", ["yerba", "infusion"]),
 "cafe": (r"^cafe\b", r"capsula|capuch|capuc|latte|mocca|moka|bombon|leche|chocolat|cafetera|taza|dolce gusto|nespresso|sabor|vainilla|caramel|helado|licor|descafeinado|cappu|frappe|mix|instant 3", ["cafe", "infusion"]),
 "te": (r"^te\b", r"verde|frut|hierb|manzanilla|boldo|tilo|herbal|cedron|peperina|menta|mate cocido|helado|chai|frutos|rojo|limon|jengibre|naranja|canela|durazno|digest|relax|hebras|blend|detox|vainilla|dulce|sueno|zen|bee", ["te", "infusion"]),
 "agua": (r"^agua\b", r"sabor|saboriz|tonica|micelar|oxigenad|rosas|colonia|destilad|lavanda|limpia|perfum|termal|bebible|de coco|soda|gasificad|con gas|jabon|desmaquill", ["agua", "bebida"]),
 "coca_cola": (r"coca.?cola", r"zero|light|sin azucar|cafe|lima|cereza|vainilla|fanta|sprite|liviano|menos azucar", ["gaseosa", "bebida"]),
 "cerveza": (r"^cerveza\b", r"sin alcohol|0,0|0.0|vaso|kit|pack de vasos|copa|gift|caja regalo", ["cerveza", "bebida"]),
 "vino": (r"^vino\b", r"blanco|rosado|espumante|vinagre|cocina|dulce|naranja|cosecha tardia|frizzante|sangria|gasificado|bag in box", ["vino", "bebida"]),
 "detergente": (r"^detergente\b", r"ropa|lavarropas|polvo|pisos|maquina|lavavajilla|automatic|baño|vidrio|multiuso|desengras", ["detergente", "limpieza", "vajilla"]),
 "lavandina": (r"\blavandina\b", r"gel|limpiador|toallita|aerosol|pastilla|desodorante|aditivo|ropa|pisos|baño|cif|mr musculo", ["lavandina", "limpieza"]),
 "jabon_ropa": (r"jabon en polvo|jabon polvo", r"tocador|manos|barra|liquido", ["ropa", "lavado", "jabon"]),
 "shampoo": (r"^shampoo\b", r"acondicionador|kit|pack|seco|perro|mascota|gato|tratamiento|crema de peinar|bebe|baby|2 en 1|repuesto", ["shampoo", "cabello", "capilar"]),
 "pasta_dental": (r"pasta dental|crema dental|dentifrico", r"cepillo|kit|enjuague|hilo|infantil|kids|niño|bebe|blanqueador gel|harry|potter|disney|frozen", ["dental", "bucal", "oral"]),
 "jabon_tocador": (r"^jabon\b.*(tocador|barra)|^jabon de tocador|^jabon\b", r"polvo|ropa|liquido|lavarropas|manos liquido|intimo|bebe|repuesto|en barra para ropa|blanco para ropa|federal", ["jabon", "tocador", "higiene"]),
 "papel_higienico": (r"papel higienico", r"humedo|toallita|pañuelo|rollo de cocina|servilleta", ["papel", "higien"]),
 # ---- added 6 November 2026: beef (INDEC 112100), yoghurt, biscuits and chicken supremas ----
 # Beef: fresh cuts only (the "carne vacuna" or butcher's aisle, never frozen, cooked, pork, lamb or wagyu).
 "asado": (r"^asado\b", BEEF_NO, ["carne vacuna", "carniceria", "carnes/"]),
 "vacio": (r"^(bife de )?vacio\b", BEEF_NO, ["carne vacuna", "carniceria", "carnes/"]),
 "nalga": (r"^(tapa de )?nalga\b", BEEF_NO, ["carne vacuna", "carniceria", "carnes/"]),
 "carne_picada": (r"^(carne )?picada\b", BEEF_NO + r"|hamburg|mix", ["carne vacuna", "carniceria", "carnes/"]),
 "milanesa_carne": (r"^milanesas? (de )?(nalga|cuadrada|bola de lomo|peceto|carne|novill)", BEEF_NO + r"|pollo|soja|merluza|pescado|vegetal|legumbre|sin gluten|sin tacc|not|lenteja|arveja|calabaza", ["carne vacuna", "carniceria", "carnes/", "milanesas"]),
 "cuadril": (r"^(colita de )?cuadril\b|^colita\b", BEEF_NO, ["carne vacuna", "carniceria", "carnes/"]),
 "cortes_magros": (r"^(bola de lomo|cuadrada|peceto)\b", BEEF_NO, ["carne vacuna", "carniceria", "carnes/"]),
 "bifes": (r"^bife (de chorizo|angosto|ancho)\b", BEEF_NO, ["carne vacuna", "carniceria", "carnes/"]),
 "roast_paleta": (r"^(roast beef|paleta)\b", BEEF_NO + r"|cocida|jamon", ["carne vacuna", "carniceria", "carnes/"]),
 "yogur": (r"^yogur", r"helado|congel|postre|cereal|granola|alfajor|barra|galleta|snack|chocolate|bocadito|fruta seca|sin lactosa|vegetal|almendra|coco|soja|kefir|mascota|perro|gato", ["yogur", "lacteo"]),
 "galletitas": (r"^galletitas?\b", r"perro|gato|mascota|sin tacc|sin gluten|arroz|surtid|pack|x ?\d+ ?(u|un|paq)|caja|lata|navide|regalo|helado", ["galletit", "desayuno", "almacen"]),
 "suprema": (r"^supremas? (de )?pollo\b", r"rebozad|congel|milanesa|napolitana|rellen|cocid|nugget|apanad|empanad", ["pollo", "carniceria", "carnes/", "milanesas"]),
}
FRESH = {"asado", "vacio", "nalga", "carne_picada", "milanesa_carne", "cuadril", "cortes_magros", "bifes", "roast_paleta", "suprema"}
# product type and category for the types that are new to the basket
NEW_INFO = {
 "asado": ("Beef ribs (asado)", "Beef"), "vacio": ("Beef flank (vacío)", "Beef"), "nalga": ("Beef round (nalga)", "Beef"),
 "carne_picada": ("Minced beef", "Beef"), "milanesa_carne": ("Beef milanesas", "Beef"), "cuadril": ("Beef rump (cuadril)", "Beef"),
 "cortes_magros": ("Lean cuts (bola de lomo, cuadrada, peceto)", "Beef"), "bifes": ("Beef steaks (bife de chorizo, ancho)", "Beef"),
 "roast_paleta": ("Roast beef and paleta", "Beef"), "yogur": ("Yoghurt", "Dairy and eggs"), "galletitas": ("Biscuits", "Bread and cereals"),
 "suprema": ("Chicken breast fillet (suprema)", "Chicken"),
}


def load_days():
    days = {}
    for path in sorted(glob.glob("data/????-??-??.csv.gz")):
        d = os.path.basename(path)[:10]
        with gzip.open(path, "rt", newline="", encoding="utf-8") as f:
            days[d] = {(r["shop"], r["sku_id"]): r for r in csv.DictReader(f) if r["shop"] in SHOPS}
    return days


def main():
    basket = list(csv.DictReader(open("basket.csv", encoding="utf-8")))
    have = {(r["shop"], r["sku_id"]) for r in basket}
    count = defaultdict(int)
    info = {}
    for r in basket:
        count[(r["type_id"], r["shop"])] += 1
        info[r["type_id"]] = (r["product_type"], r["category"])
    for t, v in NEW_INFO.items():
        info.setdefault(t, v)
    days = load_days(); dates = sorted(days)
    # every product seen in the period
    seen = {}
    for d in dates:
        for k, r in days[d].items():
            seen.setdefault(k, r)
    cands = defaultdict(list)  # (type, shop) -> [(score, row)]
    report = []
    for k, r in seen.items():
        if k in have:
            continue
        name, cat = norm(r["name"]), norm(r["category"])
        if "congelad" in cat:
            continue  # frozen food is never one of the basket types
        matches = [t for t, (inc, exc, cats) in RULES.items()
                   if re.search(inc, name) and not re.search(exc, name) and any(c in cat for c in cats)]
        if len(matches) != 1:
            continue  # unclear: fits no type or more than one
        if matches[0] in FRESH and matches[0] != "suprema" and re.search(r"cerdo|porcin|pollo|cordero|lechon|congel|rotiser|elaboracion|especiales", cat):
            continue  # beef only from the beef aisle (Dia sells "vacio" of pork in its pork aisle)
        for t in matches:
            hist = [days[d].get(k) for d in dates]
            inst = [h for h in hist if h and h["available"] == "True" and float(h["price"] or 0) > 0]
            if len(inst) < MIN_DAYS_SHARE * len(dates):
                continue
            if len({h["name"] for h in hist if h}) > 1:
                continue  # the name changed: maybe a different product
            ps = [float(h["price"]) for h in inst]
            if any(b / a > 3 or b / a < 1 / 3 for a, b in zip(ps, ps[1:])):
                continue
            if (not r["ean"] or not r["ean"].isdigit()) and t not in FRESH:
                continue  # packaged goods need a barcode; fresh meat sold by weight often has none (the shop's own code is enough)
            # how many supermarkets carry the same barcode (popular products first)
            shops_with = sum(1 for s in SHOPS if any(kk[0] == s and vv["ean"] == r["ean"] for kk, vv in seen.items()))
            cands[(t, k[0])].append((len(inst), shops_with, r))
    added = []
    for (t, s), lst in sorted(cands.items()):
        room = MAX_PER - count[(t, s)]
        lst.sort(key=lambda x: (-x[0], -x[1], x[2]["name"]))
        for n, sw, r in lst[:max(0, room)]:
            added.append({"type_id": t, "product_type": info[t][0], "category": info[t][1], "shop": s,
                          "sku_id": r["sku_id"], "ean": r["ean"], "name": r["name"]})
    with open("notas/canasta-propuesta.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(added[0].keys())); w.writeheader(); w.writerows(added)
    tot = defaultdict(int)
    for a in added: tot[(a["type_id"], a["shop"])] += 1
    print(f"{len(dates)} days ({dates[0]} to {dates[-1]}). Proposed: {len(added)} new products.")
    for t in RULES:
        print(f"{t:16} " + "  ".join(f"{s[:4]} {count[(t,s)]}+{tot[(t,s)]}" for s in SHOPS))
    if len(sys.argv) == 3 and sys.argv[1] == "--apply":
        start = sys.argv[2]
        rows = basket
        for r in rows: r.setdefault("from_date", r.get("from_date", "") or "")
        for a in added: a["from_date"] = start
        cols = ["type_id", "product_type", "category", "shop", "sku_id", "ean", "name", "from_date"]
        with open("basket.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(rows + added)
        print(f"basket.csv now has {len(rows) + len(added)} products ({len(added)} count from {start}).")


if __name__ == "__main__":
    main()
