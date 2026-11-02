#!/bin/bash
# La Canasta videos: one-time setup in a fresh machine (2-3 minutes). Run from the videos/ folder.
#   bash setup.sh
set -e
cd "$(dirname "$0")"
pip install --quiet --break-system-packages piper-tts==1.8.0 numpy pillow 2>/dev/null || pip install --quiet piper-tts==1.8.0 numpy pillow
if [ ! -f tts/vits-piper-es_AR-daniela-high/es_AR-daniela-high.onnx ]; then
  mkdir -p tts && cd tts
  curl -sSL -o v.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-es_AR-daniela-high.tar.bz2
  tar xjf v.tar.bz2 && rm v.tar.bz2 && cd ..
fi
which ffmpeg >/dev/null || (apt-get install -y -qq ffmpeg >/dev/null 2>&1 || pip install --quiet --break-system-packages imageio-ffmpeg)
node -e "require('playwright')" 2>/dev/null || (npm i -g playwright >/dev/null 2>&1 && npx playwright install chromium >/dev/null 2>&1)
# local web server for rendering (pages are filmed from http://localhost:8790/<folder>/short.html)
(curl -s localhost:8790 >/dev/null) || (nohup python3 -m http.server 8790 >/dev/null 2>&1 &)
echo "setup ok"
