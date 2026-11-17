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



CARDS=TL.get("cards",{})
for k,d in CARDS.items():
    c0=L[k]["start"]-d
    add(c0-0.25, whoosh(0.5), 0.45); add(c0+0.05, hit(), 0.55)
def has(k): return k in L
# Generic events for the weekly report template (videos/largos/semana.html). Keys that are missing are skipped.
add(0.25, whoosh(0.7), 0.45); add(1.0, chime(1318.5,1.6), 0.6)
if has("i2"): add(at("i2"), whoosh(0.5), .4); add(at("i2",.55), hit(), .6)
if has("i3"): add(at("i3",.2), hit(), .6)
if has("i4"): add(at("i4"), pop(400), .5)
if has("n2"):
    for j in range(12): add(at("n2")+j*0.07, tick(), .45)
if has("n3"): add(at("n3"), hit(), .65)
if has("n4"): add(at("n4",.1), pop(620), .5)
if has("n5"):
    for f in (.05,.35,.65):
        for j in range(8): add(at("n5",f)+j*0.06, tick(), .35)
if has("n6"): add(at("n6"), whoosh(0.6), .3)
if has("g1"): add(at("g1"), whoosh(0.5), .3)
for k in ("g2","g3"):
    if has(k): add(at(k), pop(700), .5)
for k in ("u1","u3","d1","d2"):
    if has(k): add(at(k)-0.3, whoosh(0.45), .4); add(at(k,.45), hit(0.5), .5)
for k in ("u2",):
    if has(k): add(at(k)+0.9, chime(1567.98), .6)
for k in ("b2","b3"):
    if has(k): add(at(k,.15), whoosh(0.6), .35); add(at(k,.75), pop(560), .5)
if has("b4"): add(at("b4"), pop(500), .5); add(at("b4",.55), pop(760), .5)
if has("s1"):
    for i in range(4): add(at("s1",.15+i*.06), pop(480+60*i), .4)
if has("s2"): add(at("s2"), whoosh(0.4), .35)
if has("s3"):
    for f in (.3,.45,.55): add(at("s3",f), whoosh(0.4), .3)
if has("s4"): add(at("s4")+0.9, hit(), .65)
if has("e1"):
    for i in range(3): add(at("e1",.08+i*.28), pop(520+90*i), .5)
if has("e2"): add(at("e2"), whoosh(0.5), .4)
if has("e3"): add(at("e3"), whoosh(0.6), .45); add(at("e3")+.35, chime(1318.5,1.6), .8); add(at("e3")+.47, chime(1975.5,1.4), .5)

out = np.clip(out, -1, 1)
with wave.open(f"{D}/sfx.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("sfx.wav", round(N / SR, 2), "s")
