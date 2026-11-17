import json,sys,numpy as np,soundfile as sf
ins=json.loads(sys.argv[1]);cards=json.loads(sys.argv[2])
t=json.load(open('timeline.json'));v,sr=sf.read('voice.wav')
L={l['k']:l for l in t['lines']}
for k in sorted(ins,key=lambda k:-L[k]['start']):
    i=int((L[k]['start']-0.15)*sr); v=np.concatenate([v[:i],np.zeros(int(ins[k]*sr)),v[i:]])
shift=0
for l in t['lines']:
    shift+=ins.get(l['k'],0); l['start']=round(l['start']+shift,3); l['end']=round(l['end']+shift,3)
t['total']=round(len(v)/sr,3); t['cards']=cards
sf.write('voice.wav',v,sr); json.dump(t,open('timeline.json','w'),ensure_ascii=False,indent=1)
print(t['total'])
