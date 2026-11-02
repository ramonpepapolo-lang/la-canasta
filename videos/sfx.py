# python sfx.py <folder> : builds <folder>/sfx.wav from data-sfx="sound" elements in short.html
# (time from data-at / data-ln / data-strike / data-sfxat), plus <folder>/sfx_extra.json [[spec,sound],...]
import re, json, sys, os, numpy as np, wave
d = sys.argv[1]; SR = 44100
TL = json.load(open(f'{d}/timeline.json')); L = {l['k']: l for l in TL['lines']}
def at(spec):
    k, fr = spec.split(':'); l = L[k]; return l['start'] + float(fr) * l['dur']
html = open(f'{d}/short.html', encoding='utf-8').read()
ev = []
for tag in re.findall(r'<[^>]*data-sfx="[^"]+"[^>]*>', html):
    snd = re.search(r'data-sfx="([^"]+)"', tag).group(1)
    m = re.search(r'data-sfxat="([^"]+)"', tag) or re.search(r'data-(?:ln|at|strike|type)="([^"]+)"', tag)
    if m and ':' in m.group(1) and m.group(1).split(':')[0] in L: ev.append((at(m.group(1)), snd))
if os.path.exists(f'{d}/sfx_extra.json'):
    for spec, snd in json.load(open(f'{d}/sfx_extra.json')): ev.append((at(spec) if isinstance(spec, str) else spec, snd))
rng = np.random.default_rng(3); T = lambda s: np.arange(int(s * SR)) / SR
def env(n, a, dcy): t = np.arange(n) / SR; return np.minimum(1, t / a) * np.exp(-t / dcy)
def lp(x, c):
    y = np.zeros_like(x); s = 0
    for i in range(len(x)): s += c * (x[i] - s); y[i] = s
    return y
def S(name):
    if name == 'print':
        n = int(.16 * SR); x = rng.standard_normal(n); t = T(.16)
        return (x - lp(x, .3)) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 70 * t))) * env(n, .005, .06) * .22
    if name == 'stamp':
        n = int(.3 * SR); t = T(.3); return (np.sin(2 * np.pi * (90 + 60 * np.exp(-t * 30)) * t) + .4 * lp(rng.standard_normal(n), .1)) * env(n, .002, .07) * .9
    if name == 'scratch':
        n = int(.22 * SR); x = rng.standard_normal(n); return (x - lp(x, .5)) * env(n, .01, .08) * .18
    if name == 'beep':
        t = T(.09); return np.sin(2 * np.pi * 2350 * t) * env(len(t), .002, .05) * .22
    if name == 'tick':
        t = T(.06); return np.sin(2 * np.pi * 1400 * t) * env(len(t), .001, .015) * .45
    if name == 'ding':
        t = T(1.0); f = 1318.5; return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 4) * .3
    if name == 'win':
        out = np.zeros(int(1.0 * SR))
        for k, f in enumerate([784, 988, 1175, 1568]):
            t = T(.5); s = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) * .22; i = int(k * .09 * SR); out[i:i + len(s)] += s
        return out
    if name == 'buzz':
        t = T(.45); return np.sign(np.sin(2 * np.pi * 110 * t)) * env(len(t), .01, .25) * .12
    if name == 'whoosh':
        n = int(.5 * SR); x = rng.standard_normal(n); tt = np.arange(n) / n; y = np.zeros(n); s = 0
        for i in range(n): c = .02 + .4 * tt[i] ** 2; s += c * (x[i] - s); y[i] = s
        return y * np.sin(np.pi * tt) ** 2 * .5
    if name == 'chaching':
        a = S('stamp') * .5; t = T(.8); b = (np.sin(2 * np.pi * 2093 * t) + np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 6) * .18
        out = np.zeros(int(.9 * SR)); out[:len(a)] += a; i = int(.08 * SR); out[i:i + len(b)] += b[:len(out) - i]; return out
    if name == 'pop':
        t = T(.12); return np.sin(2 * np.pi * (600 + 900 * t / .12) * t) * env(len(t), .002, .04) * .3
    raise ValueError(name)
cache = {}
out = np.zeros(int((TL['total'] + 1) * SR))
for t0, snd in ev:
    s = cache.setdefault(snd, S(snd)); i = int(t0 * SR); j = min(len(out), i + len(s))
    if i < len(out): out[i:j] += s[:j - i]
out = np.clip(out, -1, 1)
with wave.open(f'{d}/sfx.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
print(d, len(ev), 'sounds')
