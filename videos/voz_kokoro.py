# Voz "pro" de los Shorts (desde el 15/11/2026): Kokoro (voz neuronal natural), español latino con la "sh" argentina.
# Corre en GitHub Actions (necesita internet para bajar el modelo): workflow .github/workflows/voz.yml.
#   python voz_kokoro.py pedido.json salida/
# pedido.json: {"voice": "em_alex", "speed": 1.0, "pre": 0.95, "gap": 0.28, "tail": 1.7,
#               "lines": [{"k": "hook", "sub": "...", "say": "...", "gap": 0.42 (opcional), ...otros campos}]}
# Escribe salida/voice.wav (48 kHz, ya ecualizada) y salida/timeline.json {"total", "lines": [... + start, end, dur]}.
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from kokoro import KPipeline
from misaki import espeak

req = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
voice = req.get("voice", "em_alex"); speed = float(req.get("speed", 1.0))
pre, gap, tail = float(req.get("pre", 0.95)), float(req.get("gap", 0.28)), float(req.get("tail", 1.7))
lang = req.get("lang", "es")  # "es" (Argentine Spanish, default) or "en" (American English, for the English versions)
if lang == "en":
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
else:
    g2p = espeak.EspeakG2P(language="es-419")
    pipe = KPipeline(lang_code="e", repo_id="hexgrad/Kokoro-82M")
SR = 24000


def phon(text):
    if lang == "en":
        return " ".join(r.phonemes for r in pipe(text, voice=voice, speed=speed))
    ps, _ = g2p(text)
    for a in ["jj", "ʝ", "ɟʝ", "ʎ"]:  # rioplatense: "ll" / "y" suenan "sh"
        ps = ps.replace(a, "ʃ")
    return ps


parts = [np.zeros(int(pre * SR))]; t = pre; lines = []
for L in req["lines"]:
    if lang == "en":
        audio = [np.asarray(r.audio) for r in pipe(L["say"], voice=voice, speed=speed)]
    else:
        audio = [np.asarray(r.audio) for r in pipe.generate_from_tokens(phon(L["say"]), voice=voice, speed=speed)]
    a = np.concatenate(audio)
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, idx[0] - 240): idx[-1] + 480]
    d = len(a) / SR
    lines.append({**L, "start": round(t, 3), "end": round(t + d, 3), "dur": round(d, 3), "ps": phon(L["say"])})
    g = float(L.get("gap", gap))
    parts += [a, np.zeros(int(g * SR))]; t += d + g
parts.append(np.zeros(int(tail * SR)))
v = np.concatenate(parts)
sf.write(f"{out}/voice24.wav", v, SR)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{out}/voice24.wav", "-af",
                "highpass=f=70,equalizer=f=3500:t=q:w=1:g=2.5,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=2",
                "-ar", "48000", "-ac", "1", f"{out}/voice.wav"], check=True)
os.remove(f"{out}/voice24.wav")
json.dump({"total": round(len(v) / SR, 3), "voice": voice, "lines": lines}, open(f"{out}/timeline.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(out, round(len(v) / SR, 2), "s")
