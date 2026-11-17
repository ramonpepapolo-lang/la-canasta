# Videos largos de La Canasta (horizontales, 16:9)

Pedido de Ramon (17/11/2026): además de los Shorts diarios (que siguen IGUAL), un video largo por semana:
el **"Reporte semanal"**, cada domingo, en **español y en inglés**, en YouTube y en X.
El primero (semana del 8 al 14 de noviembre) y el mini-doc "Una persona, 7 agentes de IA y 20.000 precios"
se hicieron el 17/11 con estas herramientas. A Ramon le encantaron: mantené este estilo.

## Reglas (las mismas de siempre)

- Números SOLO de los datos (index/semanas/AAAA-MM-DD.json y data/). Nunca inventar. Un cambio semanal NO es "inflación".
- Logo oficial siempre (assets/la-canasta-logo-*.svg). Los colores de fondo cambian en cada video; el logo nunca.
- Nada se publica sin que Ramon abra el issue "publicar largos AAAA-MM-DD" desde su cuenta (publicar.yml).
- Sin logos de supermercados. Sin polo. Sin em dashes en los textos.
- Música de la rama `musica` (Kevin MacLeod, CC BY 4.0): el crédito de CADA tema usado va en la descripción de YouTube.

## Reporte semanal: paso a paso (domingo)

1. **Datos**: la semana que terminó el sábado: `index/semanas/<domingo de esa semana>.json` (paid, regular, groups,
   products_up/down/same, top_up, top_down con regular_pct, promos_now/before, series, ranking). Si no existe, no hay video:
   avisale a Ramon.
2. **Historia**: buscá lo más interesante de la semana (un producto que subió en un súper y bajó en otro, una promo que
   terminó, un grupo que se movió mucho, el ranking). Gancho fuerte en los primeros 5 segundos, una pregunta nueva cada
   30 a 45 segundos, cierre con el informe mensual (día 1) y "un reporte nuevo cada domingo".
   Si `top_up` tiene `regular_pct` cerca de 0, la suba es una promo que terminó: decilo así.
3. **Guion**: dos pedidos de voz como `ejemplo-voz-es.json` (em_alex, español rioplatense) y `ejemplo-voz-en.json`
   (`"lang": "en"`, voz af_heart). En el "say": números en palabras; en inglés "Día" se escribe "Dee-ah" y "ChangoMás"
   "Chango Mas". Subilos a la rama `voz-pedidos` como `semanal-es-<id>.json` y `semanal-en-<id>.json`; en 2 a 4 minutos
   aparecen en `voz-salida/<id>/` (voice.wav + timeline.json).
4. **Pausas para los capítulos**: `python3 pauses.py '{"n1":1.4,...}' '{"n1":1.6,...}'` (dentro de la carpeta de trabajo).
5. **Visuales**: copiá `semana.html` y adaptá los datos de `TX` (es y en), `SHOPCH`, `RANK`, `SERIES` y las escenas a la
   historia de esa semana (las claves de las líneas del guion manejan los tiempos). Misma página para los dos idiomas:
   `semana.html` (español) y `semana.html?lang=en`. Cambiá los colores de `:root` cada semana. Mirá cuadros sueltos
   antes de filmar (que nada se tape con los subtítulos).
6. **Filmar**: carpeta con semana.html + timeline.json + voice.wav + fuentes y logos de `../assets/`; servirla con
   `python3 -m http.server 8793` y `PORT=8793 node render_largo.js 0 <cuadros> A` (cuadros = total × 30).
   Para inglés, PAGE='semana.html?lang=en'.
7. **Sonido**: `python3 sfx_semana.py .`; música con `python3 bed.py <total> "Tema:0,Tema2:<seg>,..."`
   (máximo 75 s por tema, cambiá en los capítulos); mezcla con `sh mix_largo.sh salida.mp4`.
8. **X**: X acepta hasta 140 s: `python3 xcut.py salida.mp4 x.mp4 "0-<capítulo 1>,<inicio>-<fin>,..."`.
9. **Miniatura** 1280×720 como `thumb-semana.html` (?lang=en para inglés).
10. **Publicación**: subí a la rama `videos-largos` los mp4, las x-*.mp4, las miniaturas y `posts.json`:
    `{"date": "AAAA-MM-DD", "videos": [{"name", "file", "x_file", "thumb", "lang": "es"|"en", "long": true,
    "yt_title", "yt_description" (con capítulos 0:00 y créditos de música), "hashtags", "x_text"}]}`.
    Mandale a Ramon por mail (workflow alert.yml) el link para aprobar:
    https://github.com/ramonpepapolo-lang/la-canasta/issues/new?title=publicar%20largos%20AAAA-MM-DD
    Título de YouTube: "Reporte semanal: <gancho> | Semana del D al D de <mes>" y en inglés
    "Weekly report: <hook> | Week of <Mon> D to D".

`minidoc-ejemplo.html` y `thumb-minidoc.html` son el mini-doc del 17/11, como ejemplo de otro formato.
