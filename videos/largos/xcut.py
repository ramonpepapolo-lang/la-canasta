# python3 xcut.py in.mp4 out.mp4 "a-b,c-d,..."  (seconds) -> one video for X (<=140 s)
import sys,subprocess
src,out,segs=sys.argv[1],sys.argv[2],[tuple(map(float,s.split('-'))) for s in sys.argv[3].split(',')]
tot=sum(b-a for a,b in segs);assert tot<=139,tot
ins=[];f=[];cat=''
for i,(a,b) in enumerate(segs):
    d=b-a; ins+=['-ss',f'{a:.3f}','-t',f'{d:.3f}','-i',src]
    f.append(f'[{i}:v]setpts=PTS-STARTPTS[v{i}]')
    f.append(f'[{i}:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.12,afade=t=out:st={d-0.15:.3f}:d=0.15[a{i}]')
    cat+=f'[v{i}][a{i}]'
f.append(f'{cat}concat=n={len(segs)}:v=1:a=1[v][a]')
subprocess.run(['ffmpeg','-y','-v','error','-threads','1',*ins,'-filter_complex',';'.join(f),'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',out],check=True)
print(out,round(tot,1),'s')
