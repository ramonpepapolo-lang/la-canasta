// Generic engine for La Canasta Shorts (no mascot).
// Scenes: <div class="s" id="s-NAME">; script lines have {k, scene, sub}.
// data-at="k:frac" (+ data-pop | data-left | data-drop), data-count (+data-from, data-dur, data-fmt money|int|pct1),
// data-grow="w:80" or "h:300", data-type="k:frac" (typing), data-strike="k:frac" (.strike), window.EXTRA(t,L).
let TL; const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)); const ease=x=>1-Math.pow(1-clamp(x),3);
const back=x=>{x=clamp(x);const c=1.7;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
const fmtN=(n,f)=>f==="money"?"$"+Math.round(n).toLocaleString("es-AR"):f==="pct1"?n.toLocaleString("es-AR",{minimumFractionDigits:1,maximumFractionDigits:1})+"%":Math.round(n).toLocaleString("es-AR");
function at(spec){const [k,fr]=spec.split(":");const l=TL.lines.find(x=>x.k===k);return l?l.start+parseFloat(fr||0)*l.dur:1e9;}
function prep(){
  TL.lines.forEach(l=>{const parts=l.parts||[{sub:l.sub,start:l.start,end:l.end}];l.words=[];
    parts.forEach(p=>{const ws=p.sub.split(" ");const tot=ws.reduce((a,w)=>a+w.length+2,0);let acc=0;const d=p.end-p.start;
      ws.forEach(w=>{const s=p.start+acc/tot*d;acc+=w.length+2;l.words.push({w,s,e:p.start+acc/tot*d});});});
    l.chunks=[];let cur=[];const N=window.CHUNK||3;l.words.forEach((x,j)=>{cur.push(j);if(cur.length===N||/[.,:;?!]$/.test(x.w)){l.chunks.push(cur);cur=[];}});if(cur.length)l.chunks.push(cur);});
  document.querySelectorAll("[data-at]").forEach(e=>e._t=at(e.dataset.at));
  document.querySelectorAll("[data-type]").forEach(e=>{e._t=at(e.dataset.type);e._full=e.textContent;e.textContent="";});
  document.querySelectorAll("[data-strike]").forEach(e=>e._s=at(e.dataset.strike));
  document.querySelectorAll(".s").forEach(c=>{const f=TL.lines.find(l=>l.scene===c.id.slice(2));c._t=f?f.start-0.2:1e9;});
}
function lineAt(t){let L=TL.lines[0];for(const l of TL.lines){if(t>=l.start-0.12)L=l;}return L;}
function render(t){
  const L=lineAt(t);
  document.querySelectorAll(".s").forEach(c=>{const on=c.id==="s-"+L.scene;const p=(t-c._t)/0.4;
    c.style.opacity=on?ease(p):0; if(!c.hasAttribute("data-still")) c.style.transform=on?`scale(${0.96+0.04*ease(p)})`:"none";});
  document.querySelectorAll("[data-at]").forEach(e=>{const p=(t-e._t)/0.3;const isSvg=e instanceof SVGElement;
    if(e.hasAttribute("data-pop")){e.style.opacity=ease(p*1.6);const sc=0.35+0.65*back(p);
      if(isSvg){if(!e._bb){try{e._bb=e.getBBox()}catch(x){e._bb={x:0,y:0,width:0,height:0}}}const cx=e._bb.x+e._bb.width/2,cy=e._bb.y+e._bb.height/2;e.setAttribute("transform",`translate(${cx},${cy}) scale(${sc}) translate(${-cx},${-cy})`);}
      else e.style.transform=(e.dataset.rot?`rotate(${e.dataset.rot}deg) `:"")+`scale(${sc})`;}
    else if(e.hasAttribute("data-drop")){e.style.opacity=ease(p*2);e.style.transform=(e.dataset.rot?`rotate(${e.dataset.rot}deg) `:"")+`scale(${2.2-1.2*ease(p*1.4)})`;}
    else if(isSvg){e.style.opacity=ease(p);}
    else if(e.hasAttribute("data-left")){e.style.opacity=ease(p);e.style.transform=`translateX(${(1-ease(p))*-70}px)`;}
    else if(e.hasAttribute("data-fade")){e.style.opacity=ease(p);}
    else {e.style.opacity=ease(p);e.style.transform=`translateY(${(1-ease(p))*30}px)`;}
    if(e.dataset.count!==undefined){const from=+(e.dataset.from||0),to=+e.dataset.count,d=+(e.dataset.dur||1.4);e.textContent=fmtN(from+(to-from)*ease((t-e._t)/d),e.dataset.fmt);}
    if(e.dataset.grow){const [ax,v]=e.dataset.grow.split(":");const g=ease((t-e._t-0.1)/0.9);if(ax==="h")e.style.height=(+v*g)+"px";else e.style.width=(+v*g)+"%";}
  });
  document.querySelectorAll("[data-type]").forEach(e=>{const n=Math.floor(clamp((t-e._t)/(+(e.dataset.tdur||0.5)))*e._full.length);e.textContent=e._full.slice(0,n);});
  document.querySelectorAll("[data-strike]").forEach(e=>e.style.setProperty("--s",ease((t-e._s)/0.3)));
  if(window.EXTRA) window.EXTRA(t,L);
  const cap=document.getElementById("cap");
  if(cap){cap.innerHTML="";
    if(t<=L.end+0.15&&t>=L.start-0.05){let ci=L.chunks.findIndex(ch=>t<L.words[ch[ch.length-1]].e);if(ci<0)ci=L.chunks.length-1;
      const ch=L.chunks[ci];const wi=L.words.findIndex(x=>t>=x.s&&t<x.e);
      ch.forEach(j=>{const s=document.createElement("span");s.textContent=L.words[j].w;if(j===wi)s.className="w";cap.appendChild(s);});
      cap.style.transform="none";const w=cap.scrollWidth,mw=(window.CAPW||1000);if(w>mw)cap.style.transform=`scale(${mw/w})`;cap.style.visibility="visible";}
    else cap.style.visibility="hidden";}
  const bar=document.getElementById("bar"); if(bar) bar.style.width=(clamp(t/TL.total)*1080)+"px";
}
async function init(){TL=await (await fetch("timeline.json")).json();await document.fonts.ready;if(window.SETUP)window.SETUP();prep();window.TOTAL=TL.total;window.READY=true;render(0);}
window.render=render;init();
