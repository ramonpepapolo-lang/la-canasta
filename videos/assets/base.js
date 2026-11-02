// Shared engine for La Canasta Shorts. A page defines:
//   cards: <div class="c" id="c-NAME">, script lines (timeline.json) have {k, scene, sub, face}
//   data-at="k:frac"            element appears at that moment of line k (fade/slide; data-pop = pop)
//   data-count="to" data-at=..  number counts up (data-from, data-dur, data-fmt: money|int|pct1|pct0)
//   data-grow="h:400" / "w:80"  bar grows (px height or % width) from its data-at moment
//   data-strike="k:frac"        red line crosses the element (.strike)
//   window.EXTRA(t, L)          optional per-page animation hook
const SVG_MASCOT = `
<svg width="1080" height="720" viewBox="0 0 1080 720" style="position:absolute;left:0;top:0">
  <circle cx="860" cy="120" r="70" fill="#D98A2B" opacity=".9"/>
  <path d="M0 330 Q200 250 420 320 T820 300 T1080 290 V720 H0Z" fill="#33496E"/>
  <path d="M0 410 Q260 340 520 400 T1080 380 V720 H0Z" fill="#3C5A82"/>
  <path d="M0 500 Q300 450 600 490 T1080 470 V720 H0Z" fill="#4A6E96"/>
  <g id="masc" transform="translate(150,90)">
    <ellipse cx="190" cy="420" rx="170" ry="22" fill="#000" opacity=".22"/>
    <g id="body">
      <rect x="104" y="40" width="44" height="72" fill="#2B3B5C" stroke="#F6F1E7" stroke-width="6"/>
      <rect x="168" y="0" width="44" height="112" fill="#2B3B5C" stroke="#F6F1E7" stroke-width="6"/>
      <rect x="232" y="-36" width="44" height="148" fill="#2B3B5C" stroke="#F6F1E7" stroke-width="6"/>
      <path d="M40 128 V112 A150 150 0 0 1 340 112 V128" fill="none" stroke="#F6F1E7" stroke-width="16"/>
      <rect x="16" y="112" width="348" height="26" rx="6" fill="#F6F1E7"/>
      <clipPath id="bk"><path d="M30 150 H350 L316 400 H64Z"/></clipPath>
      <g clip-path="url(#bk)"><rect x="0" y="150" width="380" height="84" fill="#7FB1C6"/><rect x="0" y="234" width="380" height="84" fill="#FFFFFF"/><rect x="0" y="318" width="380" height="90" fill="#7FB1C6"/></g>
      <path d="M30 150 H350 L316 400 H64Z" fill="none" stroke="#F6F1E7" stroke-width="6" stroke-linejoin="round"/>
      <ellipse id="e1" cx="140" cy="250" rx="34" ry="40" fill="#fff" stroke="#2B3B5C" stroke-width="5"/>
      <ellipse id="e2" cx="240" cy="250" rx="34" ry="40" fill="#fff" stroke="#2B3B5C" stroke-width="5"/>
      <circle id="p1" cx="146" cy="256" r="14" fill="#1E2B45"/><circle id="p2" cx="246" cy="256" r="14" fill="#1E2B45"/>
      <path id="b1" d="M108 200 L170 196" stroke="#1E2B45" stroke-width="9" stroke-linecap="round"/>
      <path id="b2" d="M210 196 L272 200" stroke="#1E2B45" stroke-width="9" stroke-linecap="round"/>
      <ellipse id="mouth" cx="190" cy="335" rx="34" ry="6" fill="#7A2A20" stroke="#1E2B45" stroke-width="5"/>
    </g>
    <text id="sym" x="350" y="40" font-family="Sans" font-weight="700" font-size="96" fill="#D98A2B" opacity="0">!</text>
  </g>
</svg>`;
let TL; const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)); const ease=x=>1-Math.pow(1-clamp(x),3);
const easeIO=x=>{x=clamp(x);return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2};
const back=x=>{x=clamp(x);const c=1.7;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
const FACES={normal:{b:[0,0],sym:""},wow:{b:[-16,-16],sym:"!"},sad:{b:[10,-10],sym:"…"},think:{b:[-14,6],sym:"?"},happy:{b:[-6,-6],sym:"✓"}};
const LOCALE=document.documentElement.lang==="en"?"en-US":"es-AR";
const fmtN=(n,f)=>f==="money"?"$"+Math.round(n).toLocaleString(LOCALE):f==="pct1"?n.toLocaleString(LOCALE,{minimumFractionDigits:1,maximumFractionDigits:1})+" %":f==="pct0"?Math.round(n)+" %":Math.round(n).toLocaleString(LOCALE);
function at(spec){const [k,fr]=spec.split(":");const l=TL.lines.find(x=>x.k===k);if(!l)return 1e9;return l.start+parseFloat(fr||0)*l.dur;}
function prep(){
  TL.lines.forEach(l=>{const parts=l.parts||[{sub:l.sub,start:l.start,end:l.end}];l.words=[];
    parts.forEach(p=>{const ws=p.sub.split(" ");const tot=ws.reduce((a,w)=>a+w.length+2,0);let acc=0;const d=p.end-p.start;
      ws.forEach(w=>{const s=p.start+acc/tot*d;acc+=w.length+2;l.words.push({w,s,e:p.start+acc/tot*d});});});
    l.chunks=[];let cur=[];l.words.forEach((x,j)=>{cur.push(j);if(cur.length===3||/[.,:;?!]$/.test(x.w)){l.chunks.push(cur);cur=[];}});if(cur.length)l.chunks.push(cur);});
  document.querySelectorAll("[data-at]").forEach(e=>e._t=at(e.dataset.at));
  document.querySelectorAll("[data-strike]").forEach(e=>e._s=at(e.dataset.strike));
  document.querySelectorAll(".c").forEach(c=>{const f=TL.lines.find(l=>l.scene===c.id.slice(2));c._t=f?f.start-0.18:1e9;});
}
function lineAt(t){let L=TL.lines[0];for(const l of TL.lines){if(t>=l.start-0.05)L=l;}return L;}
function render(t){
  const L=lineAt(t);
  document.querySelectorAll(".c").forEach(c=>{const on=c.id==="c-"+L.scene; const p=(t-c._t)/0.35;
    c.style.opacity=on?ease(p):0; c.style.transform=on?`translateY(${(1-ease(p))*60}px) scale(${0.96+0.04*ease(p)+0.012*clamp((t-c._t)/8)})`:"none";});
  document.querySelectorAll("[data-at]").forEach(e=>{const p=(t-e._t)/0.32;
    if(e.hasAttribute("data-pop")){e.style.opacity=ease(p*1.6);e.style.transform=(e.dataset.rot?`rotate(${e.dataset.rot}deg) `:"")+`scale(${0.35+0.65*back(p)})`;}
    else if(e.hasAttribute("data-left")){e.style.opacity=ease(p);e.style.transform=`translateX(${(1-ease(p))*-80}px)`;}
    else {e.style.opacity=ease(p);e.style.transform=`translateY(${(1-ease(p))*34}px)`;}
    if(e.dataset.count!==undefined){const from=+(e.dataset.from||0),to=+e.dataset.count,d=+(e.dataset.dur||1.4);e.textContent=fmtN(from+(to-from)*ease((t-e._t)/d),e.dataset.fmt);}
    if(e.dataset.grow){const [ax,v]=e.dataset.grow.split(":");const g=ease((t-e._t-0.1)/0.9);if(ax==="h")e.style.height=(+v*g)+"px";else e.style.width=(+v*g)+"%";}
  });
  document.querySelectorAll("[data-strike]").forEach(e=>e.style.setProperty("--s",ease((t-e._s)/0.35)));
  if(window.EXTRA) window.EXTRA(t,L);
  // captions
  const cap=document.getElementById("cap"); cap.innerHTML="";
  if(t<=L.end+0.15&&t>=L.start-0.05){let ci=L.chunks.findIndex(ch=>t<L.words[ch[ch.length-1]].e);if(ci<0)ci=L.chunks.length-1;
    const ch=L.chunks[ci]; const wi=L.words.findIndex(x=>t>=x.s&&t<x.e);
    ch.forEach(j=>{const s=document.createElement("span");s.textContent=L.words[j].w;if(j===wi)s.className="w";cap.appendChild(s);});
    const w=cap.scrollWidth; cap.style.transform=w>980?`scale(${980/w})`:"none";}
  // mascot
  const f=FACES[L.face]||FACES.normal; const m=TL.mouth[Math.floor(t*30)]||0; const $=id=>document.getElementById(id);
  $("mouth").setAttribute("ry",6+m*30); $("mouth").setAttribute("rx",30+m*8);
  if(L.face==="happy"&&m<0.08)$("mouth").setAttribute("ry",10);
  $("body").setAttribute("transform",`translate(0,${Math.sin(t*5)*6}) scale(1,${1+m*0.03})`);
  $("b1").setAttribute("transform",`translate(0,${f.b[0]}) rotate(${L.face==="sad"?10:L.face==="think"?-6:0} 140 198)`);
  $("b2").setAttribute("transform",`translate(0,${f.b[1]}) rotate(${L.face==="sad"?-10:0} 240 198)`);
  const blink=(t%3.3)<0.12; ["e1","e2"].forEach(id=>$(id).setAttribute("ry",blink?5:(L.face==="wow"?46:40))); ["p1","p2"].forEach(id=>$(id).setAttribute("r",blink?0:(L.face==="wow"?11:14)));
  const look=Math.sin(t*0.7)*5; $("p1").setAttribute("cx",146+look); $("p2").setAttribute("cx",246+look);
  const sym=$("sym"); sym.textContent=f.sym; const ps=(t-L.start)/0.3; sym.setAttribute("opacity",f.sym?ease(ps)*0.9:0);
  sym.setAttribute("transform",`translate(0,${-ease(ps)*20+Math.sin(t*6)*4})`);
  // floating price tags in the background
  document.querySelectorAll("#bg .tagf").forEach((e,i)=>{const sp=+e.dataset.sp;e.style.transform=`translateY(${-((t*sp+i*137)%2200)+1900}px)`;});
  $("bar").style.width=(clamp(t/TL.total)*1080)+"px";
  const cta=$("cta"); if(cta){const k=t-cta._t-0.8; cta.style.transform+= k>0?` scale(${1+0.05*Math.sin(k*7)})`:"";}
}
async function init(){
  document.getElementById("scene").innerHTML=SVG_MASCOT;
  const bg=document.getElementById("bg"); (window.BGTAGS||[]).forEach((s,i)=>{const d=document.createElement("div");d.className="tagf";d.textContent=s;
    d.style.left=((i*263)%960)+"px";d.style.fontSize=(34+(i*17)%40)+"px";d.dataset.sp=(40+(i*29)%60);bg.appendChild(d);});
  TL=await (await fetch("timeline.json")).json();prep();window.TOTAL=TL.total;await document.fonts.ready;window.READY=true;render(0);
}
window.render=render;init();
