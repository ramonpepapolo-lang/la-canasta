# Round 3 (12 Nov 2026): big Argentine outlets (Spanish) and international outlets (English). Writes emails3.json.
import json

SUBJ_ES = "Inflación del súper de noviembre, dos semanas antes que el INDEC (para el 1 de diciembre)"
SUBJ_EN = "Argentina's November supermarket inflation, two weeks before the official figure (embargo 1 Dec)"


def es(saludo, line, vos=False):
    t = (lambda pl, sg: sg if vos else pl)
    return f"""{saludo}

Soy Ramon Pepa, argentino. En octubre arranqué La Canasta (lacanastaindex.com), un índice diario de precios de supermercados: todos los días un programa que armé junta más de 20.000 precios online de Carrefour, Jumbo, ChangoMás y Día, compara los mismos productos (con el mismo código de barras) y los resume en un número, con las ponderaciones del INDEC. Los datos y el método son abiertos y gratis.

{line}

Por qué {t("les", "te")} puede servir: la inflación es un tema muy sensible en Argentina, y el dato oficial sale una vez por mes, semanas después. La Canasta muestra cómo se mueven los precios del súper todos los días. El 1 de diciembre sale su primer informe mensual: cuánto subió el súper en noviembre, qué productos subieron más y qué súper conviene, unas dos semanas antes que el INDEC. Y compara cadenas: todas las semanas desde que empezamos, la misma compra salió entre 15% y 20% más cara en Jumbo que en Día.

Si {t("les", "te")} interesa, {t("se lo", "te lo")} mando la noche del 30 de noviembre, apenas cierra el mes, con embargo hasta el 1 de diciembre. Si antes {t("necesitan", "necesitás")} algún dato puntual, también.

A cambio solo {t("les", "te")} pido que {t("citen", "cites")} la fuente como "La Canasta, de Ramon Pepa", con el enlace a lacanastaindex.com, y si {t("pueden", "podés")}, que {t("mencionen", "menciones")} que la app de La Canasta llega muy pronto, gratis. En lacanastaindex.com/prensa.html están el logo y cómo citarnos.

No es un mail masivo: {t("se lo escribo a cada medio", "te lo escribo a vos")}, y las respuestas las leo y las contesto yo.

¿{t("Les", "Te")} interesa que {t("se lo", "te lo")} mande?

Gracias,
Ramon Pepa
La Canasta · lacanastaindex.com"""


def en(line, tech=False, short=False):
    built = (" The whole thing is run by one person, with seven AI agents that look after it every day: they make sure no day is missed,"
             " review every doubtful price and verify the report before it goes out.") if tech else ""
    if short:
        return f"""Hello,

I'm Ramon Pepa, from Argentina. In October I started La Canasta (lacanastaindex.com), an independent daily supermarket price index for Argentina: every day it collects more than 20,000 online prices from Carrefour, Jumbo, ChangoMás and Día, matches the same products by barcode, and weights them with INDEC's official weights. The data and method are open.

{line} On 1 December La Canasta publishes its first monthly report on November supermarket inflation, about two weeks before INDEC's figure. It also compares chains: every week since we started, the same basket has cost between 15% and 20% more at Jumbo than at Día. I can send the report on the night of 30 November, under embargo until 1 December. All I ask is a credit to "La Canasta, by Ramon Pepa" with a link to lacanastaindex.com (logo and details at lacanastaindex.com/prensa.html).

This isn't a mass email: I'm writing to each outlet myself, and I read and answer the replies.

Thanks,
Ramon Pepa
La Canasta · lacanastaindex.com"""
    return f"""Hello,

I'm Ramon Pepa, from Argentina. In October I started La Canasta (lacanastaindex.com), a daily supermarket price index for Argentina. Every day a program I built collects more than 20,000 online prices from the country's biggest chains (Carrefour, Jumbo, ChangoMás and Día), matches the same products by barcode, and turns them into one number using INDEC's official weights. The data and the method are open and free.

{line}

Why it could be a story: inflation is the most sensitive topic in Argentina, and the official figure comes out once a month, weeks later. La Canasta shows supermarket prices moving day by day. On 1 December it publishes its first monthly report on November supermarket inflation, about two weeks before INDEC's figure. It also compares chains: every week since we started, the exact same basket (same products, same barcodes) has cost between 15% and 20% more at Jumbo than at Día.{built}

If it's useful, I can send you the November report on the night of 30 November, under embargo until 1 December, and answer any questions before then.

All I ask in return is that you credit "La Canasta, by Ramon Pepa" with a link to lacanastaindex.com, and if you can, mention that the La Canasta app is coming soon, for free. The logo and citation details are at lacanastaindex.com/prensa.html.

This isn't a mass email: I'm writing to each outlet myself, and I read and answer the replies.

Would you like me to send it?

Thanks,
Ramon Pepa
La Canasta · lacanastaindex.com"""


H = "Hola, ¿cómo andan?"
M = [
    ("Infobae", "redaccion@infobae.com", SUBJ_ES, es(H,
        "Vi la nota de Lucrecia Eterovich del 10 de noviembre sobre la buena señal de los precios en la primera semana de noviembre, con los relevamientos de LCG y Analytica, y pensé que esto les puede servir: es el mismo tipo de dato, pero todos los días, con más de 20.000 precios y todo publicado.")),
    ("La Nación (Esteban Lafuente)", "elafuente@lanacion.com.ar", SUBJ_ES, es("Hola Esteban, ¿cómo estás?",
        "Vi tu nota del 6 de noviembre sobre la inflación de octubre en la Ciudad, y como seguís consumo e innovación, pensé que esto te puede interesar.", vos=True)),
    ("El Cronista (Patricia Valli)", "pvalli@cronista.com", SUBJ_ES, es("Hola Patricia, ¿cómo estás?",
        "Vi la nota de Fernando Garcia del 24 de octubre sobre los alimentos que subieron por séptima semana consecutiva, con el relevamiento de LCG en cinco cadenas, y pensé que esto te puede servir para Economía: La Canasta mide más de 20.000 precios por día y publica todos los datos.", vos=True)),
    ("iProfesional", "contacto@iprofesional.com", SUBJ_ES, es(H,
        "Vi la nota de Mariano Jaimovich sobre lo que esperan los economistas para la inflación de octubre y noviembre, y pensé que esto les puede servir: un dato de noviembre medido todos los días en los supermercados, antes que el INDEC.")),
    ("Página/12", "redactor@pagina12.com.ar", SUBJ_ES, es(H,
        "Vi su nota del 12 de noviembre sobre el poder de compra y la caída del consumo en los supermercados, y pensé que esto les puede servir: muestra, producto por producto, cuánto cuesta llenar el changuito.")),
    ("elDiarioAR", "comunidad@eldiarioar.com", SUBJ_ES, es(H,
        "Vi su nota del 6 de noviembre sobre la inflación de octubre en la Ciudad, y pensé que esto les puede servir: el mismo tema, medido todos los días en los supermercados.")),
    ("Chequeado", "info@chequeado.com", SUBJ_ES, es(H,
        "Vi su explicador sobre la inflación de septiembre, y como en Chequeado verifican datos, pensé que les puede interesar algo hecho para poder verificarse: cada número de La Canasta se puede comprobar, porque los datos y el método completo están publicados.")),
    ("Bloomberg News", "tips2@bloomberg.net", SUBJ_EN, en(
        "Bloomberg follows Argentina's inflation closely, and I thought an independent, daily supermarket number could be useful to your Buenos Aires team.")),
    ("Rest of World", "hello@restofworld.org", SUBJ_EN, en(
        "Rest of World covers how technology is being used outside the West to deal with real problems, and in Argentina few problems are as real as prices at the supermarket.", tech=True)),
    ("TechCrunch", "tips@techcrunch.com", SUBJ_EN, en(
        "I'm writing to TechCrunch because of how it's built, which I think is the interesting part for you: it is a one-person project that runs itself.", tech=True)),
    ("Americas Quarterly", "AQeditors@as-coa.org", SUBJ_EN, en(
        "AQ follows Argentina's economy closely, and an independent, daily measure of supermarket prices could be useful for your coverage of inflation under Milei.", short=True)),
    ("Buenos Aires Herald", "newsroom@buenosairesherald.com", SUBJ_EN, en(
        "You cover Argentina's inflation in English every month, and I thought an independent, daily supermarket number could be useful to your readers.")),
]

if __name__ == "__main__":
    out = [{"outlet": o, "to": to, "subject": s, "text": t} for o, to, s, t in M]
    json.dump(out, open("emails3.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(out), "emails")
