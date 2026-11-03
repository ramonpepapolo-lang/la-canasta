import numpy as np, wave, sys, os
SR=44100; BPM=float(os.environ.get('BPM',120)); TR=int(os.environ.get('TR',0)); B=60/BPM; DUR=float(sys.argv[2]) if len(sys.argv)>2 else 17.0
N=int(SR*DUR); out=np.zeros(N); rng=np.random.default_rng(7)
def add(sig,t,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig))
    if i<N: out[i:j]+=g*sig[:j-i]
def env(n,a=0.005,d=0.3):
    t=np.arange(n)/SR; e=np.minimum(1,t/a)*np.exp(-t/d); return e
try:
    from scipy.signal import lfilter
    def lp(x,c): return lfilter([c],[1,-(1-c)],x)  # one-pole lowpass, c in 0..1
except ImportError:
    def lp(x,c):
        y=np.zeros_like(x); s=0
        for k in range(len(x)): s+=c*(x[k]-s); y[k]=s
        return y
def hp(x): return x-lp(x,0.15)
def kick():
    n=int(.35*SR); t=np.arange(n)/SR; f=45+80*np.exp(-t*30); ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-t*9)
def clap():
    n=int(.2*SR); x=hp(rng.standard_normal(n)); return x*env(n,0.002,0.06)*0.6
def hat():
    n=int(.05*SR); x=hp(hp(rng.standard_normal(n))); return x*env(n,0.001,0.012)*0.35
def mtof(m): return 440*2**((m-69)/12)
def saw(f,n,det=0):
    t=np.arange(n)/SR; return sum(2*((t*f*(1+d))%1)-1 for d in (-det,0,det))/ (3 if det else 1)
def pluck(m,len_s=0.45,g=1):
    n=int(len_s*SR); x=saw(mtof(m),n,0.004); return lp(x,0.22)*env(n,0.004,0.22)*g
def bass(m,len_s):
    n=int(len_s*SR); t=np.arange(n)/SR; x=np.sin(2*np.pi*mtof(m)*t)+0.3*saw(mtof(m),n)
    return lp(x,0.08)*env(n,0.004,0.22)
def ding(m):
    n=int(1.0*SR); t=np.arange(n)/SR; f=mtof(m)
    return (np.sin(2*np.pi*f*t)+0.4*np.sin(2*np.pi*2*f*t)+0.2*np.sin(2*np.pi*3.01*f*t))*np.exp(-t*4)*0.5
def whoosh(len_s=0.6):
    n=int(len_s*SR); x=rng.standard_normal(n); t=np.arange(n)/n
    y=np.zeros(n); s=0
    for k in range(n): c=0.02+0.5*t[k]**2; s+=c*(x[k]-s); y[k]=s
    return y*np.sin(np.pi*t)**2*0.8
# C - G - Am - F, one chord per bar (4 beats = 2 s)
prog=[(r+TR,[n+TR for n in c]) for r,c in ([(45,[60,64,69]),(41,[60,65,69]),(48,[60,64,67]),(43,[59,62,67])] if os.environ.get('MINOR') else [(48,[60,64,67]),(43,[59,62,67]),(45,[60,64,69]),(41,[60,65,69])])]
bars=int(np.ceil(DUR/(4*B)))
STYLE=os.environ.get('STYLE','')
def rim():
    n=int(.08*SR); t=np.arange(n)/SR; return (np.sin(2*np.pi*1700*t)*0.5+hp(rng.standard_normal(n))*0.6)*env(n,0.001,0.025)
def marimba(m,g=1):
    n=int(.35*SR); t=np.arange(n)/SR; f=mtof(m); return (np.sin(2*np.pi*f*t)+0.25*np.sin(2*np.pi*4*f*t)*np.exp(-t*30))*np.exp(-t*9)*g
if STYLE=='lofi':
    SW=0.62  # swing: the off-beat 8th lands late
    for bar in range(bars):
        root,ch=prog[bar%4]; t0=bar*4*B
        drums=t0>=2*B
        for beat in range(4):
            tb=t0+beat*B
            if tb>=DUR-0.6: break
            if drums:
                if beat in (0,2): add(kick(),tb,0.45)
                if beat==2: add(kick(),tb-0.5*B*(1-SW)+0.5*B,0.0)
                if beat in (1,3): add(rim(),tb,0.42); add(clap(),tb,0.12)
                add(hat(),tb,0.25); add(hat(),tb+SW*B,0.18)
        # soft, long chords (rhodes-like) on 1 and on the swung "and" of 3
        for off,g in ((0,0.34),(2+SW,0.22)):
            if t0+off*B<DUR-0.6:
                for m in ch: add(lp(pluck(m,1.6,0.8),0.35),t0+off*B,g)
        if drums:
            add(bass(root,1.4),t0,0.45); add(bass(root+7,0.8),t0+2.5*B,0.35)
    bars=0
if STYLE=='dembow':
    S=B/4  # sixteenth
    mel=[0,3,7,10,7,3,5,7]
    for bar in range(bars):
        root,ch=prog[bar%4]; t0=bar*4*B
        drums=t0>=2*B
        for beat in range(4):
            tb=t0+beat*B
            if tb>=DUR-0.6: break
            if drums:
                add(kick(),tb,0.6)
                add(hat(),tb+2*S,0.35); add(hat(),tb+3*S,0.2)
            # dembow snare: 16ths 3 and 6 of every 8 (the "boom ch boom chick")
            if drums and beat%2==0:
                add(rim(),tb+3*S,0.5); add(clap(),tb+6*S,0.32)
            if beat%2==0 or not drums:
                pass
        # sub bass: root on 1, octave on the "a" of 2, fifth on 3
        if drums:
            for off,m,l in ((0,root,0.5),(1.75,root+12,0.2),(2,root+7,0.4),(3.5,root,0.3)):
                if t0+off*B<DUR-0.6: add(bass(m,l),t0+off*B,0.5)
        # marimba line on the off-beats
        for i in range(8):
            tt=t0+i*0.5*B+0.25*B
            if tt<DUR-0.6: add(marimba(ch[(0,1,2,1,2,1,0,2)[i]]+12),tt,0.22)
        # soft pad stab on 1
        for m in ch: add(pluck(m,0.9,0.6),t0,0.25)
    bars=0
def sq(f,n):  # soft square (organ / chiptune)
    t=np.arange(n)/SR; return np.tanh(4*np.sin(2*np.pi*f*t))*0.5
def organ(m,len_s,g=1):
    n=int(len_s*SR); f=mtof(m); return lp(sq(f,n)+0.4*sq(2*f,n),0.25)*env(n,0.003,len_s*0.5)*g
def guiro(len_s=0.12):  # scraped noise: a rising filtered burst
    n=int(len_s*SR); x=hp(rng.standard_normal(n)); t=np.arange(n)/n
    return x*(0.3+0.7*np.abs(np.sin(np.pi*t*6)))*np.minimum(1,t*8)*np.exp(-t*3)*0.35
def snare(dec=0.12,g=1):
    n=int((dec*3)*SR); t=np.arange(n)/SR
    x=hp(rng.standard_normal(n))*0.8+np.sin(2*np.pi*190*t)*0.5
    return x*env(n,0.001,dec)*g
def b808(m,len_s,glide=0):
    n=int(len_s*SR); t=np.arange(n)/SR; f=mtof(m)*(1+glide*np.minimum(1,t/0.12))
    x=np.sin(2*np.pi*np.cumsum(f)/SR); return np.tanh(1.6*x)*np.minimum(1,t/0.004)*np.exp(-t*1.2)
def pad(m,len_s,g=1):
    n=int(len_s*SR); t=np.arange(n)/SR; x=lp(saw(mtof(m),n,0.006),0.06)
    return x*np.minimum(1,t/0.25)*np.minimum(1,(len_s-t)/0.3)*g
def openhat():
    n=int(.18*SR); x=hp(hp(rng.standard_normal(n))); return x*env(n,0.001,0.06)*0.3
def ok(t): return t<DUR-0.6
if STYLE=='cumbia':  # BPM 90-105: guiro 8ths, bass on 1 and 3, organ on the off-beats, timbal fill
    for bar in range(bars):
        root,ch=prog[bar%4]; t0=bar*4*B; drums=t0>=2*B
        for beat in range(4):
            tb=t0+beat*B
            if not ok(tb): break
            add(guiro(0.5*B*0.9),tb,0.5); add(guiro(0.25*B),tb+0.5*B,0.3); add(guiro(0.25*B),tb+0.75*B,0.25)
            if drums:
                add(kick(),tb,0.4 if beat in (0,2) else 0.2)
                if beat in (1,3): add(rim(),tb+0.5*B,0.35)
            if ok(tb+0.5*B):
                for m in ch: add(organ(m+12,0.35*B),tb+0.5*B,0.16)
        if drums:
            for off,m,l in ((0,root,0.9),(1.5,root+7,0.4),(2,root+7,0.9),(3.5,root,0.4)):
                if ok(t0+off*B): add(bass(m,l*B+0.1),t0+off*B,0.55)
            if bar%4==3:  # timbal roll into the next bar
                for k in range(4): add(rim(),t0+3*B+k*0.25*B,0.25+0.08*k)
    bars=0
if STYLE=='trap':  # BPM 130-150, half-time: 808 slides, hi-hat rolls, clap on 3
    S=B/4
    for bar in range(bars):
        root,ch=prog[bar%4]; t0=bar*4*B; drums=t0>=2*B
        for m in ch: add(pad(m-12,4*B,0.22),t0)
        if not drums: continue
        add(kick(),t0,0.6); add(kick(),t0+2.75*B,0.45)
        add(b808(root-12,1.8*B),t0,0.55); add(b808(root-12,1.2*B,0.5 if bar%2 else -0.25),t0+2.75*B,0.45)
        if ok(t0+2*B): add(clap(),t0+2*B,0.5); add(snare(0.08,0.4),t0+2*B)
        for k in range(16):
            tt=t0+k*S
            if not ok(tt): break
            roll = bar%2==1 and k in (13,14,15)
            add(hat(),tt,0.3 if k%2==0 else 0.18)
            if roll:
                for r in (1,2): add(hat(),tt+r*S/3,0.15)
        # bell melody on top
        for i,(off,dm) in enumerate(((0,12),(1.5,15),(3,19))):
            if ok(t0+off*B): add(ding(ch[0]+dm-12),t0+off*B,0.12)
    bars=0
if STYLE=='disco':  # BPM 112-124: four on the floor, open hats, octave bass, chord chops
    S=B/4
    for bar in range(bars):
        root,ch=prog[bar%4]; t0=bar*4*B; drums=t0>=2*B
        for m in ch: add(pad(m+12,4*B,0.12),t0)
        for beat in range(4):
            tb=t0+beat*B
            if not ok(tb): break
            if drums:
                add(kick(),tb,0.55); add(openhat(),tb+0.5*B,0.5)
                if beat in (1,3): add(clap(),tb,0.32); add(snare(0.07,0.25),tb)
                for e in (0,0.5): add(bass(root+(12 if e else 0),0.45*B),tb+e*B,0.45)
            for k in (1,3):  # guitar-like chops on the 16th off-beats
                if ok(tb+k*S):
                    for m in ch: add(pluck(m+12,0.12,0.7),tb+k*S,0.18)
    bars=0
if STYLE=='synthwave':  # BPM 84-100: 80s, gated snare on 2 and 4, 16th arpeggio, long pad
    S=B/4
    for bar in range(bars):
        root,ch=prog[bar%4]; t0=bar*4*B; drums=t0>=2*B
        for m in ch: add(pad(m,4*B,0.25),t0)
        arp=[ch[0],ch[1],ch[2],ch[1]+12]
        for k in range(16):
            tt=t0+k*S
            if ok(tt): add(pluck(arp[k%4]+12,0.18,0.8),tt,0.16)
        if not drums: continue
        for beat in range(4):
            tb=t0+beat*B
            if not ok(tb): break
            if beat in (0,2): add(kick(),tb,0.55)
            if beat in (1,3): add(snare(0.22,0.55),tb)
            add(hat(),tb+0.5*B,0.2)
            for e in (0,0.5): add(bass(root,0.45*B),tb+e*B,0.42)
    bars=0
if STYLE=='chiptune':  # BPM 120-150: 8-bit game music, square lead, noise drums
    S=B/4; lead=[0,4,7,12,7,4,9,7]
    for bar in range(bars):
        root,ch=prog[bar%4]; t0=bar*4*B; drums=t0>=2*B
        for i in range(8):
            tt=t0+i*0.5*B
            if ok(tt): add(organ(ch[0]+lead[i]+12,0.42*B,0.8),tt,0.14)
        for k in range(8):
            tt=t0+k*0.5*B
            if ok(tt): add(organ(root+(12 if k%2 else 0),0.4*B),tt,0.22)
        if not drums: continue
        for beat in range(4):
            tb=t0+beat*B
            if not ok(tb): break
            add(kick(),tb,0.4 if beat in (0,2) else 0.0)
            if beat in (1,3): add(snare(0.05,0.35),tb)
            add(hat(),tb+0.5*B,0.22)
    bars=0
for bar in range(bars):
    root,ch=prog[bar%4]; t0=bar*4*B
    for beat in range(4):
        t=t0+beat*B
        if t>=DUR-0.6: break
        drums = t>=2.0  # intro: chords only for the first bar
        if drums: add(kick(),t,0.55)
        if drums and beat in (1,3): add(clap(),t,0.28)
        if drums:
            for h in (0.5,):
                add(hat(),t+h*B,0.45)
        # chord stabs on 1, the "and" of 2, and 4
        for off in (0,1.5,3):
            if beat==int(off) and t0+off*B<DUR-0.6:
                for m in ch: add(pluck(m),t0+off*B,0.42)
        # bass 8ths
        if t>=2.0:
            for e in (0,0.5):
                add(bass(root if e==0 else root+12,0.24),t+e*B,0.42)
# transitions: whoosh into each scene, ding on the price reveals
# final chord
for m in (60,64,67,72): add(pluck(m,2.5,1)*1,DUR-2.2,0.2)
out=np.tanh(out*0.7); out*=0.85/np.max(np.abs(out))
rms=np.sqrt(np.mean(out**2)); out*=0.08/rms  # every style the same loudness: about 16 dB under the voice in mix2.sh
out*=min(1,0.99/np.max(np.abs(out)))
fade=int(0.8*SR); out[-fade:]*=np.linspace(1,0,fade)
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes())
print('ok')
