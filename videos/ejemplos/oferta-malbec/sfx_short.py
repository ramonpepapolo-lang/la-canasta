# Soft, modern sound effects for the "pro" Short: whooshes, pops, a low hit and a bright chime.
# python3 sfx_pro.py <folder>  -> <folder>/sfx.wav (48 kHz stereo), timed from timeline.json
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



add(0.0, hit(0.5), .55); add(0.05, pop(620), .5)
add(at("h2",.05), pop(520), .45); add(at("h2",.55), pop(380), .45)
add(at("w1")-0.15, whoosh(0.4), .4)
for k,f in (("w1",.35),("w2",0),("w2",.55)): add(at(k,f), whoosh(0.35), .3)
add(at("b1")-0.15, whoosh(0.4), .4); add(at("b1",.6), hit(0.5), .55); add(at("b1",.85), pop(700), .5)
for i in range(8): add(at("b2",.05+i*.06), tick(), .5)
add(at("p1")-0.15, whoosh(0.45), .4)
for j in range(12): add(at("p1",.1)+j*0.05, tick(), .45)
add(at("p1",.55), chime(1567.98), .7)
add(L["p1"]["end"]+0.35, chime(1318.5,1.4), .6)

out = np.clip(out, -1, 1)
with wave.open(f"{D}/sfx.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("sfx.wav", round(N / SR, 2), "s")
