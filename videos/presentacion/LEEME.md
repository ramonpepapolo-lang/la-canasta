# Video de presentación de La Canasta

Cuatro versiones del mismo video: qué es La Canasta, el programa, la web, los 7 agentes y el fundador.

- `short-es/`, `short-en/`: vertical 1080x1920, menos de 60 segundos (YouTube Shorts, X, TikTok, Instagram).
- `wide-es/`, `wide-en/`: horizontal 1920x1080, unos 3 minutos (video principal del canal y de la web).

Cada carpeta tiene su `script.json` (líneas con `sub` y `say`). La pantalla es una sola para las cuatro: `pres.html`
(elige idioma y formato por el nombre de la carpeta). Para rehacer todo:

    cd videos && bash setup.sh                    # voz es_AR daniela; la voz en inglés es en_US lessac (ver gen.py)
    bash presentacion/build.sh                    # copia pres.html a cada carpeta como short.html
    for v in short-es short-en wide-es wide-en; do
      python3 gen.py presentacion/$v ${v#*-}      # voice.wav + timeline.json
      python3 sfx.py presentacion/$v
      D=$(python3 -c "import json;print(json.load(open('presentacion/$v/timeline.json'))['total']+0.7)")
      STYLE=cumbia BPM=92 TR=-2 python3 bed.py presentacion/$v/bed.wav $D   # cumbia lenta
      node presentacion/render2.js presentacion/$v                            # raw.mp4
      sh mix2.sh presentacion/$v la-canasta-presentacion-$v                   # final
    done

Las capturas de la web que aparecen en el video salen de `shots.js` (filma el sitio local en `presentacion/shots/`).
Para revisar cuadros antes de filmar: `node presentacion/frames2.js presentacion/wide-es 5 20 60`.

Estos videos no se publican solos: Ramon los sube a mano.
