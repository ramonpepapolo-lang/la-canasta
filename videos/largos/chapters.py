import json,sys
def chapters(folder,names,intro):
    t=json.load(open(f'{folder}/timeline.json'));L={l['k']:l for l in t['lines']};C=t['cards']
    out=[f"0:00 {intro}"]
    for k,n in names:
        s=int(L[k]['start']-C.get(k,0)); out.append(f"{s//60}:{s%60:02d} {n}")
    return "\n".join(out)
