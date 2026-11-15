# Voice tests: Kokoro (natural neural voice) with Latin American Spanish phonemes and Argentine "sh" (sheísmo).
import json, os, sys, numpy as np, soundfile as sf
from kokoro import KPipeline
from misaki import espeak
os.makedirs("out", exist_ok=True)
lines = json.load(open("lines.json"))
g2p = espeak.EspeakG2P(language="es-419")
pipe = KPipeline(lang_code="e", repo_id="hexgrad/Kokoro-82M")
def phon(text, sh):
    ps, _ = g2p(text)
    if sh:  # rioplatense: ll / y -> "sh"
        for a in ["ʝ", "ɟʝ", "ʎ", "j͡"]:
            ps = ps.replace(a, "ʃ")
    return ps
for voice in ["em_alex", "ef_dora", "em_santa"]:
    for sh in [True, False]:
        tag = f"{voice}{'-sh' if sh else ''}"
        meta = []
        for i, L in enumerate(lines):
            ps = phon(L["say"], sh)
            audio = []
            for r in pipe.generate_from_tokens(ps, voice=voice, speed=1.0):
                audio.append(r.audio.numpy() if hasattr(r.audio, "numpy") else np.asarray(r.audio))
            a = np.concatenate(audio)
            sf.write(f"out/{tag}-{i}.wav", a, 24000)
            meta.append({"k": L["k"], "ps": ps, "dur": len(a) / 24000})
        json.dump(meta, open(f"out/{tag}.json", "w"), ensure_ascii=False, indent=1)
        print(tag, round(sum(m["dur"] for m in meta), 1), "s")
