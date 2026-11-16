# Videos de La Canasta (YouTube Shorts + X)

## FORMATO PRO (desde el 15/11/2026, pedido por Ramon): manda sobre todo lo de abajo

Ramon vio el ejemplo `ejemplos/pro-changuito/` (publicado el 15/11) y quiere TODOS los videos así: cortos, bien hechos,
calidad profesional, y que **cambien los colores y el concepto visual en cada video**. Lo de abajo sigue valiendo
(datos, reglas de contenido, miniatura, nunca publicar sin Ramon) salvo lo que este bloque cambia.

- **Duración: 20 a 30 segundos** (6 a 8 líneas cortas). Nada de 40-55 s.
- **Temas: lo que funcionó.** Los más vistos son comparaciones claras ("Mismo carrito en 4 súper", "¿Cuánto suben los precios?",
  "¿Qué es La Canasta?", "Armé un programa con IA"): 6.000 a 17.000 vistas. Las promos sueltas de un producto sacan 10-60.
  Preferí: la misma compra en los 4 súper, dónde conviene, cuánta plata de diferencia, rankings, "cuánto cuesta X en cada súper".
  Una promo suelta solo si es muy fuerte y le sirve a mucha gente.
- **Calidad visual (la vara es `ejemplos/pro-changuito/short.html`):** pantalla completa, sin la tarjeta vieja;
  logo arriba a la izquierda y la fecha en una pastilla;
  motion graphics de verdad (contadores, barras que corren, sellos, escaneos, zoom), un `render(t)` propio y determinista;
  subtítulos con la palabra que suena resaltada; la nota de fuente abajo; barra de progreso.
  **Cada video con su propia paleta y su propio concepto** (oscuro, claro, colores fuertes, pastel...): nunca la misma paleta
  ni el mismo concepto que alguno de los últimos 6 videos (anotalo en notas/videos-hechos.txt). La tapa de 0,8 s sigue siendo obligatoria.
- **EL LOGO ES SIEMPRE EL OFICIAL, CON SUS COLORES (Ramon, 16/11):** azul de La Canasta + la bandera argentina (celeste, blanco,
  celeste y el sol). Los colores del video cambian, el logo NUNCA. Usá solo los archivos oficiales:
  `../assets/la-canasta-logo-horizontal.svg` arriba (dentro de una pastilla blanca) y `../assets/la-canasta-logo-stacked.svg`
  en el cierre (sobre una tarjeta blanca), como en `ejemplos/pro-changuito/`. Nunca el logo blanco, ni recoloreado, ni dibujado a mano.
  **Cierre obligatorio de cada video:** el logo oficial + lacanastaindex.com. La tapa (#thumb) va sin logo: thumb.js le pone el oficial.
- **Voz: Kokoro "em_alex"** (natural, español latino con la "sh" argentina), ya no Piper. Se hace en GitHub Actions:
  escribí `{"voice": "em_alex", "lines": [...]}` (mismas líneas que script.json: k, scene, sub, say; "gap" opcional por línea)
  como `<id>.json` en la rama `voz-pedidos` y hacé push; en 2-4 minutos aparecen `<id>/voice.wav` y `<id>/timeline.json`
  en la rama `voz-salida` (https://raw.githubusercontent.com/ramonpepapolo-lang/la-canasta/voz-salida/<id>/timeline.json).
  Copialos a la carpeta del video (reemplazan a gen.py). Revisá el campo "ps" de cada línea: si una palabra quedó rara, reescribila en "say".
  Números siempre en palabras en "say". Voseo argentino.
- **Música: temas reales** de la rama `musica` (Kevin MacLeod, CC BY 4.0, 75 s cada uno; `creditos.json` dice el clima de cada uno).
  Elegí uno que no se haya usado en los últimos 6 videos y que pegue con la historia. **El crédito de `creditos.json` va SIEMPRE
  al final de la yt_description.** Ya no se usa bed.py.
- **Efectos:** `sfx.json` en la carpeta del video (ver el ejemplo) y `python3 sfx_pro.py d-...`.
- **Mezcla:** `node render.js d-...` y después `sh mix_pro.sh d-... NOMBRE musica.mp3` (la música baja sola cuando habla la voz).

Cómo se hace cada video, paso a paso. Todo corre en una máquina Linux con Python, Node, Playwright y ffmpeg.

## 0. Preparar (una vez por sesión)

    cd videos && bash setup.sh

Instala la voz argentina (Piper, es_AR "daniela", se baja de GitHub) y levanta un servidor web en el puerto 8790,
con raíz en `videos/`. Las carpetas de trabajo van directo en `videos/` y se llaman `d-AAAA-MM-DD-N`
(git las ignora). Así `../assets/...` funciona en cada `short.html`.

## 1. El guion: `d-.../script.json`

Lista de líneas: `{"k": clave, "scene": escena, "sub": subtítulo, "say": lo que dice la voz}`.
- `sub` con números y signos ($1.650, 21%); `say` con los números en palabras ("mil seiscientos cincuenta").
- `sub` y `say` tienen que tener la misma puntuación (, . : ? !), porque se cortan en esos signos. Si no coincide,
  `gen.py` avisa "one part" y los subtítulos quedan desfasados: arreglalo.
- La primera línea lleva `"pre": 0.75`: deja el primer segundo para la miniatura.
- "lacanastaindex.com" se dice "la canasta index punto com". Jumbo, Carrefour y ChangoMás ya se corrigen solos.
- Voseo argentino, frases cortas, 40 a 55 segundos en total.

Después: `python3 gen.py d-... es` → escribe `voice.wav` y `timeline.json` (tiempos de cada línea).

## 2. La pantalla: `d-.../short.html` (1080 x 1920)

Usa `../assets/engine.js` (ver los comentarios al principio del archivo). Cada escena es `<div class="s" id="s-NOMBRE">`.
Animaciones con atributos: `data-at="clave:0.3"` (aparece al 30% de esa línea) + `data-pop`, `data-drop`, `data-left`;
`data-count="42"` cuenta hasta 42; `data-sfx="stamp|pop|whoosh|ding|buzz|tick|win|chaching"` agrega un sonido.
`window.EXTRA(t)` para animaciones propias, `window.SETUP()` para armar cosas al cargar. Subtítulos en `#cap`, barra en `#bar`.

**Miniatura al principio (obligatorio):** un `<div id="thumb">` a pantalla completa (z-index 20) con el título grande,
visible del segundo 0 al 0,8 y que se desvanece hasta 1,05 (ver `ejemplos/`). Es la tapa para YouTube y para X.

**Cada video con un formato visual distinto** a los anteriores (mirá `ejemplos/`: pizarrón, góndola, montaña rusa,
diario, quiz, ticket, cajas). Colores, fondo y tipografía nuevos. Nada de logos ni dibujos de marcas reales:
productos genéricos, los nombres sí se escriben.

Revisar ANTES de filmar: `node frames.js d-... 0.3 5 12 20 ...` (cuadros sueltos) y `python3 sheet.py d-... 0.3 5 12 ...`
(contacto). Abrí la imagen y revisá: nada cortado ni encimado, textos legibles, subtítulos legibles sobre el fondo.

## 3. Filmar y mezclar

    node render.js d-...            # raw.mp4 a 30 fps, con la voz (2-4 minutos)
    python3 sfx.py d-...            # sfx.wav
    BPM=... python3 bed.py d-.../bed.wav <duración+0.7>   # música
    sh mix2.sh d-... NOMBRE         # d-.../NOMBRE.mp4 final

Música: 8 estilos. `STYLE=` (vacío: house, BPM 118-128), `dembow` (95-105), `lofi` (75-85), `cumbia` (90-105),
`trap` (130-150), `disco` (112-124), `synthwave` (84-100), `chiptune` (120-150). Además `MINOR=1` tono menor
y `TR=` de -5 a 7 transpone.
**Un estilo no se repite hasta que pasen 6 videos** (mirá la columna de música en `notas/videos-hechos.txt`),
y nunca el mismo estilo en los 2 videos del mismo día. Cambiá también BPM, tono y TR cada vez.

## 4. Thumbnail oficial (obligatorio)

    node thumb.js d-.../NOMBRE.mp4 d-.../NOMBRE-thumbnail.jpg AAAA-MM-DD

Toma la tapa del video (segundo 0,3) y le pone arriba el logo oficial de La Canasta y abajo lacanastaindex.com,
@LaCanastaIndex y la fecha de los precios. Va en la rama videos-dia junto al mp4 y en el email de los Shorts.

## Reglas de contenido (Ramon)

- Cada número sale de los datos del repo (`data/*.csv.gz`, `basket.csv`, `index/`) y se revisa dos veces. Nunca inventar.
- Un cambio diario o semanal NO es inflación. La inflación es solo la del informe mensual publicado.
- Neutral: nada de política, ni ataques a súper, marcas, el INDEC ni nadie.
- Siempre la fecha de los precios en pantalla, y una nota chica con la fuente ("Precios online de ... , fecha").
- Siempre voz en español argentino (Piper es_AR "daniela"), con voseo y palabras de acá. Nunca otra voz ni otro idioma.
- Cada video distinto y creativo: **ni el formato visual ni la música se repiten hasta que pasen 6 videos**.
  Antes de empezar, leé las últimas 6 líneas de `notas/videos-hechos.txt`.
- Al terminar, anotá cada video en `notas/videos-hechos.txt`:
  `fecha | título | formato visual | música (STYLE BPM MINOR TR) | números usados`.
- NUNCA se publica nada sin Ramon: los videos le llegan por email y solo se publican cuando él aprieta el botón de aprobar.
