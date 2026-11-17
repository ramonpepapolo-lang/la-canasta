# python3 bed.py total "track1:t0,track2:t1,..."  -> bed.wav, crossfade 2 s at each boundary
import sys,subprocess
total=float(sys.argv[1]);segs=[(s.split(':')[0],float(s.split(':')[1])) for s in sys.argv[2].split(',')]
ins,fl=[],[]
for i,(tr,t0) in enumerate(segs):
    t1=segs[i+1][1] if i<len(segs)-1 else total
    ln=t1-t0+(2 if i<len(segs)-1 else 0)
    assert ln<=75.0, (tr,ln)
    ins+=['-i',f'/tmp/mus/{tr}.mp3'];fl.append(f'[{i}:a]atrim=0:{ln:.3f},asetpts=PTS-STARTPTS[s{i}]')
cur='s0'
for i in range(1,len(segs)):
    fl.append(f'[{cur}][s{i}]acrossfade=d=2:c1=tri:c2=tri[x{i}]');cur=f'x{i}'
fl.append(f'[{cur}]atrim=0:{total},afade=t=out:st={total-3.5}:d=3.5,aresample=48000[o]')
subprocess.run(['ffmpeg','-y','-v','error',*ins,'-filter_complex',';'.join(fl),'-map','[o]','-ac','2','bed.wav'],check=True)
print('bed ok')
