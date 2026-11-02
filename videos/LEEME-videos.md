# Videos de La Canasta (YouTube Shorts + X)

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

Música: cambiá el estilo y el tono en cada video. Opciones: `STYLE=` (vacío: house), `dembow`, `lofi`;
`BPM=` 80 a 132; `MINOR=1` tono menor; `TR=` de -5 a 7 transpone.

## Reglas de contenido (Ramon)

- Cada número sale de los datos del repo (`data/*.csv.gz`, `basket.csv`, `index/`) y se revisa dos veces. Nunca inventar.
- Un cambio diario o semanal NO es inflación. La inflación es solo la del informe mensual publicado.
- Neutral: nada de política, ni ataques a súper, marcas, el INDEC ni nadie.
- Siempre la fecha de los precios en pantalla, y una nota chica con la fuente ("Precios online de ... , fecha").
- NUNCA se publica nada: los videos se le mandan a Ramon y él los sube.
