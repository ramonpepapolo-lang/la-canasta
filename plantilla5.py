# Round 5 (13 Nov 2026): small and medium Argentine outlets, none contacted before. Same text as rounds 3 and 4. Writes emails5.json.
import json
from plantilla3 import es, SUBJ_ES

REG = " Son precios online, sobre todo de Gran Buenos Aires, pero muestran cómo se mueven los precios de las cadenas grandes en todo el país."
PAT = "Como en la Patagonia el súper es de los más caros del país, pensé que esto les puede servir." + REG
H = "Hola, ¿cómo andan?"
M = [
    ("Pilar a Diario (Pilar)", "info@pilaradiario.com", es(H,
        "Vi su nota del 7 de noviembre sobre las pymes de Pilar que se atrasan con sus deudas, y pensé que esto les puede servir: cuánto cuesta hoy llenar el changuito, súper por súper, medido todos los días.")),
    ("Agencia Comunas (GBA)", "agenciacomunas9@gmail.com", es(H,
        "Como cubren los municipios del conurbano, pensé que esto les puede servir: los precios que mide La Canasta son sobre todo de Gran Buenos Aires, en las cadenas donde compra la mayoría de los vecinos.")),
    ("El Auditor (CABA)", "info@elauditor.info", es(H,
        "Como trabajan con datos públicos y transparencia, pensé que esto les puede interesar: todos los datos y el método de La Canasta están publicados, cualquiera puede revisar cada precio.")),
    ("El Norte (San Nicolás)", "redaccion@diarioelnorte.com.ar", es(H,
        "Con la inflación de octubre en 2,2% y los alimentos todavía en suba, pensé que esto les puede servir para San Nicolás y la región." + REG)),
    ("Diario Núcleo (Pergamino)", "redaccion@diarionucleo.com", es(H,
        "Con la inflación de octubre en 2,2% y los alimentos todavía en suba, pensé que esto les puede servir para Pergamino." + REG)),
    ("Puntal (Río Cuarto)", "puntalweb@puntal.com.ar", es(H,
        "Con la inflación de octubre en 2,2% y los alimentos todavía en suba, pensé que esto les puede servir para Río Cuarto y el sur de Córdoba." + REG)),
    ("El Diario (Paraná)", "coordinacion@eldiario.com.ar", es(H,
        "Con la inflación de octubre en 2,2% y los alimentos todavía en suba, pensé que esto les puede servir para Entre Ríos." + REG)),
    ("Diario UNO (Mendoza)", "contacto@diariouno.com.ar", es(H,
        "Con la inflación de octubre en 2,2% y los alimentos todavía en suba, pensé que esto les puede servir para Mendoza." + REG)),
    ("Región (Santa Rosa, La Pampa)", "info@region.com.ar", es(H,
        "Con la inflación de octubre en 2,2% y los alimentos todavía en suba, pensé que esto les puede servir para La Pampa." + REG)),
    ("Diario Norte (Resistencia, Chaco)", "webchaco@diarionorte.com", es(H,
        "Con la inflación de octubre en 2,2% y los alimentos todavía en suba, pensé que esto les puede servir para el Chaco y el NEA." + REG)),
    ("Contexto (Tucumán)", "revista@contextotucuman.com", es(H,
        "Con la inflación de octubre en 2,2% y los alimentos todavía en suba, pensé que esto les puede servir para Tucumán y el NOA." + REG)),
    ("Diario Panorama (Santiago del Estero)", "diariopanoramacom@gmail.com", es(H,
        "Con la inflación de octubre en 2,2% y los alimentos todavía en suba, pensé que esto les puede servir para Santiago del Estero." + REG)),
    ("ADNSUR (Comodoro Rivadavia, Noelia Rivera)", "nrivera@adnsur.com.ar", es("Hola Noelia, ¿cómo estás?",
        "Como en la Patagonia el súper es de los más caros del país, pensé que esto te puede servir para ADNSUR." + REG, vos=True)),
    ("El Diario de Madryn (Puerto Madryn)", "redaccion@eldiarioweb.com", es(H, PAT)),
    ("Cholila Online (Chubut)", "cholilaonline@gmail.com", es(H, PAT)),
    ("Tiempo Fueguino (Río Grande)", "tiempo.fueguino@tiempofueguino.com", es(H,
        "Como en Tierra del Fuego el súper es de los más caros del país, pensé que esto les puede servir." + REG)),
]

if __name__ == "__main__":
    out = [{"outlet": o, "to": to, "subject": SUBJ_ES, "text": t} for o, to, t in M]
    for m in out:
        assert "—" not in m["text"] and "–" not in m["text"]
    assert len({m["to"] for m in out}) == len(out)
    json.dump(out, open("emails5.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(out), "emails")
