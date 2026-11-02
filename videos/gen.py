# Narration for a Short: python gen.py <folder> <es|en>
# Reads <folder>/script.json, writes <folder>/voice.wav and <folder>/timeline.json.
# Spanish: Argentine "y/ll" (sh sound), real pauses after punctuation.
import json, wave, re, sys, os, numpy as np
from piper import PiperVoice, SynthesisConfig

folder, lang = sys.argv[1], sys.argv[2]
H = os.path.dirname(os.path.abspath(__file__))
TTS = os.environ.get('TTS_DIR', H + '/tts')
if lang == 'es':
    base = TTS + '/vits-piper-es_AR-daniela-high/es_AR-daniela-high'
    cfg = SynthesisConfig(length_scale=0.95, noise_scale=0.62, noise_w_scale=0.8)
    FIX = [(r'\bJumbo\b', 'Yumbo'), (r'\bCarrefour\b', 'Carrefur'), (r'\bChangoMás\b', 'Chango Más')]
else:
    base = TTS + '/vits-piper-en_US-lessac-high/en_US-lessac-high'
    cfg = SynthesisConfig(length_scale=0.93, noise_scale=0.6, noise_w_scale=0.8)
    FIX = []
v = PiperVoice.load(base + '.onnx', config_path=base + '.onnx.json')
SR = v.config.sample_rate
PAUSE = {',': 0.2, ':': 0.3, ';': 0.3, '.': 0.42, '?': 0.42, '!': 0.42}
LINE_GAP = 0.3
split = lambda t: [c for c in re.split(r'(?<=[,.:;?!])\s+', t.strip()) if c]

def synth(text):
    for a, b in FIX: text = re.sub(a, b, text)
    out = []
    for sent in v.phonemize(text):
        ph = ['ʃ' if (lang == 'es' and p == 'ʝ') else p for p in sent]
        out.append(np.asarray(v.phoneme_ids_to_audio(v.phonemes_to_ids(ph), cfg), dtype=np.float32).ravel())
    a = np.concatenate(out)
    e = np.abs(a) > 0.01; i = np.argmax(e); j = len(a) - np.argmax(e[::-1])
    return a[max(0, i - 200):min(len(a), j + 300)]

S = json.load(open(f'{folder}/script.json', encoding='utf-8'))
t = 0.35; pieces = []
for l in S:
    t += l.get('pre', 0)
    says, subs = split(l['say']), split(l['sub'])
    if len(says) != len(subs): says, subs = [l['say']], [l['sub']]; print('one part:', l['sub'])
    l['start'] = round(t, 3); l['parts'] = []
    for k, (sy, sb) in enumerate(zip(says, subs)):
        a = synth(sy); pieces.append((t, a))
        l['parts'].append({'sub': sb, 'start': round(t, 3), 'end': round(t + len(a) / SR, 3)})
        t += len(a) / SR
        if k < len(says) - 1: t += PAUSE.get(sy[-1], 0.15)
    l['end'] = round(t, 3); l['dur'] = round(l['end'] - l['start'], 3)
    t += LINE_GAP + PAUSE.get(l['say'].strip()[-1], 0) * 0.3 + l.get('post', 0)
total = t + 1.8
out = np.zeros(int(total * SR))
for st, a in pieces:
    i = int(st * SR); out[i:i + len(a)] += a
with wave.open(f'{folder}/voice.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
fps = 30; hop = SR // fps; env = []
for k in range(int(total * fps)):
    seg = out[k * hop:(k + 1) * hop]; env.append(float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0)
m = max(env) or 1; env = [round(min(1, e / m * 1.8), 3) for e in env]
json.dump({'total': round(total, 3), 'lines': S, 'mouth': env}, open(f'{folder}/timeline.json', 'w'), ensure_ascii=False)
for i, l in enumerate(S): print(f"{i:2} {l['k']:8} {l['start']:6.2f}-{l['end']:6.2f}  {l['sub'][:60]}")
print('total', round(total, 1))
