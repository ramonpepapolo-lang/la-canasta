# Efectos de sonido "pro" (desde el 15/11/2026): whoosh, pop, hit (golpe grave), chime (campanita), tick.
# python3 sfx_pro.py <carpeta>  -> <carpeta>/sfx.wav (48 kHz estéreo), con los tiempos de timeline.json.
# Los efectos se piden en <carpeta>/sfx.json, una lista como:
#   [{"at": "jumbo:0.55", "s": "hit", "g": 0.75}, {"at": 0.82, "s": "whoosh"}, {"at": "n", "s": "tick", "n": 14, "every": 0.075}]
#   "at": segundos, o "clave:fracción" de una línea del guion (clave sola = su comienzo). "g" volumen (0-1), "pan" -1 a 1,
#   "d" duración (whoosh/hit/chime), "f" frecuencia (pop/chime), "n" y "every" para repetir. Sin sfx.json: un whoosh suave por línea.
import json, sys, wave
import numpy as np

D = sys.argv[1]
TL = json.load(open(f"{D}/timeline.json"))
L = {l["k"]: l for l in TL["lines"]}
SR = 48000
N = int((TL["total"] + 1) * SR)
out = np.zeros((N, 2))
rng = np.random.default_rng(3)


def at(k, f=0.0):
    return L[k]["start"] + f * L[k]["dur"]


def lp(x, a):  # one-pole low-pass, a in (0,1): higher = brighter
    y = np.zeros_like(x); s = 0.0
    for i, v in enumerate(x):
        s += a * (v - s); y[i] = s
    return y


def add(t, sig, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    sig = sig[: N - i] * gain
    out[i:i + len(sig), 0] += sig * (1 - max(0, pan))
    out[i:i + len(sig), 1] += sig * (1 + min(0, pan))


def whoosh(d=0.45, up=True):
    n = int(d * SR); x = rng.standard_normal(n)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    a = np.linspace(0.02, 0.25, n) if up else np.linspace(0.25, 0.02, n)
    y = np.zeros(n); s = 0.0
    for i in range(n):
        s += a[i] * (x[i] - s); y[i] = s
    return y * env * 1.6


def pop(f=520, d=0.09):
    n = int(d * SR); t = np.arange(n) / SR
    fr = f * (1 + 1.2 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 38) * 0.5


def hit(d=0.6):
    n = int(d * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (55 + 60 * np.exp(-t * 18)) * t) * np.exp(-t * 7)
    click = lp(rng.standard_normal(n), 0.3) * np.exp(-t * 60) * 0.6
    return (body + click) * 0.9


def chime(f=1318.5, d=1.2):
    n = int(d * SR); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * m * t) * a for m, a in ((1, 1), (2, .35), (3, .12)))
    return y * np.exp(-t * 4.5) * 0.22


def tick():
    n = int(0.03 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 200) * 0.18



def when(x):
    if isinstance(x, (int, float)): return float(x)
    k, _, f = str(x).partition(":")
    return at(k, float(f or 0))


FX = {"whoosh": lambda e: whoosh(e.get("d", 0.45)), "pop": lambda e: pop(e.get("f", 520)), "hit": lambda e: hit(e.get("d", 0.6)),
      "chime": lambda e: chime(e.get("f", 1318.5), e.get("d", 1.2)), "tick": lambda e: tick()}
import os
ev = json.load(open(f"{D}/sfx.json")) if os.path.exists(f"{D}/sfx.json") else \
    [{"at": 0.82, "s": "whoosh", "g": 0.5}] + [{"at": l["k"], "s": "whoosh", "g": 0.3} for l in TL["lines"][1:]]
for e in ev:
    for j in range(int(e.get("n", 1))):
        add(when(e["at"]) + j * float(e.get("every", 0)), FX[e["s"]](e), float(e.get("g", 0.5)), float(e.get("pan", 0)))

out = np.clip(out, -1, 1)
with wave.open(f"{D}/sfx.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("sfx.wav", round(N / SR, 2), "s")
