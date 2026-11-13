# Round 4 (13 Nov 2026): more Argentine outlets, Buenos Aires and provinces. Same text as round 3. Writes emails4.json.
import json
from plantilla3 import es, SUBJ_ES

REG = " Son precios online, sobre todo de Gran Buenos Aires, pero muestran cómo se mueven los precios de las cadenas grandes en todo el país."
H = "Hola, ¿cómo andan?"
M = [
    ("El Destape", "redaccion@eldestapeweb.com", es(H,
        "Vi su nota del 12 de noviembre sobre la suba de la canasta básica, 3,5% en octubre, y pensé que esto les puede servir: el mismo tema, medido todos los días en los supermercados.")),
    ("Letra P", "redaccion@letrap.com.ar", es(H,
        "Vi la nota de Lorena Hak en LetraE sobre la inflación de octubre, que volvió a acelerar al 2,2%, y pensé que esto les puede servir: un dato de noviembre medido todos los días, antes que el INDEC.")),
    ("0221 (La Plata)", "redaccion@0221.com.ar", es(H,
        "Vi su nota sobre la caída de las ventas en los comercios de La Plata y la de la inflación de octubre, y pensé que esto les puede servir: cuánto cuesta llenar el changuito, súper por súper.")),
    ("Noticias Argentinas (Jorge García)", "jorge.garcia@alphamedia.com.ar", es("Hola Jorge, ¿cómo estás?",
        "Vi la nota de NA sobre los productos que empujaron la Canasta Básica Alimentaria en octubre, y pensé que esto te puede servir para la agencia.", vos=True)),
    ("Río Negro (Diego Penizzotto)", "diegopenizzotto@rionegro.com.ar", es("Hola Diego, ¿cómo estás?",
        "Vi las notas de Río Negro sobre la venta de Carrefour y sus sucursales en la Patagonia, y pensé que esto te puede interesar: Carrefour es una de las cuatro cadenas que La Canasta sigue todos los días." + REG, vos=True)),
    ("El Tribuno (Pablo Juárez)", "pjuarez@eltribuno.com.ar", es("Hola Pablo, ¿cómo estás?",
        "Vi la nota de El Tribuno sobre la inflación de octubre y qué pasó en el NOA, y pensé que esto te puede servir." + REG, vos=True)),
    ("Rosario3", "editor@rosario3.com", es(H,
        "Vi su nota sobre la canasta básica, que saltó 3,5% en octubre, y pensé que esto les puede servir." + REG)),
    ("Diario de Cuyo", "web@diariodecuyo.com.ar", es(H,
        "Vi que siguen de cerca los precios del súper en su sección de supermercados, y pensé que esto les puede servir." + REG)),
    ("Diario Jornada (Chubut)", "info@diariojornada.com.ar", es(H,
        "Como en la Patagonia el súper es de los más caros del país, pensé que esto les puede servir." + REG)),
    ("Hoy Día Córdoba", "redaccion@hoydiacordoba.info", es(H,
        "Con la inflación de octubre en 2,2% y los alimentos todavía en suba, pensé que esto les puede servir para Córdoba." + REG)),
    ("Fortuna", "contacto@fortunaweb.com.ar", es(H,
        "Vi la nota de Tomás Berenguer del 27 de octubre sobre la diferencia de precios de la canasta básica entre provincias, y pensé que esto les puede servir: La Canasta compara todos los días la misma compra, con el mismo código de barras, en cuatro cadenas.")),
]

if __name__ == "__main__":
    out = [{"outlet": o, "to": to, "subject": SUBJ_ES, "text": t} for o, to, t in M]
    for m in out:
        assert "—" not in m["text"] and "–" not in m["text"]
    json.dump(out, open("emails4.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(out), "emails")
