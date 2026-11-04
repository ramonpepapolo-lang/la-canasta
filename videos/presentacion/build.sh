#!/bin/bash
# copies pres.html into each variant folder as short.html (what render.js, frames.js and sfx.py expect)
cd "$(dirname "$0")"
for v in short-es short-en wide-es wide-en; do cp pres.html $v/short.html; done
