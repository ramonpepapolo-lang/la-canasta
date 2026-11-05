"""Writes canastas/index.html: the "¿Dónde conviene comprar hoy?" page. The numbers come from canastas/datos.json
(made by make_canastas.py every day); this page only lays them out, with a microphone, a people selector and
maps links. Run after make_canastas.py (the header and footer are taken from metodo.html so they match the site)."""
import json, os
from make_price_pages import make_chrome, add_to_sitemap, SITE

ROOT = os.path.dirname(os.path.abspath(__file__))

BODY = r"""
<main class="container cn">
  <nav class="crumbs" aria-label="Ruta"><a href="../index.html">La Canasta</a> › <span class="es">Canastas</span><span class="en">Baskets</span></nav>
  <header class="cn-head">
    <h1><span class="es">¿Dónde conviene comprar hoy?</span><span class="en">Where is it cheapest to shop today?</span></h1>
    <p class="lede"><span class="es">Decile qué querés hacer y te dice a qué súper ir, cuánto sale y cómo llegar. Precios de hoy en Carrefour, Jumbo, ChangoMás y Día.</span><span class="en">Say what you want to do and it tells you which supermarket to go to, what it costs and how to get there. Today's prices at Carrefour, Jumbo, ChangoMás and Día.</span></p>
  </header>

  <section class="ask">
    <button type="button" id="mic" class="mic" aria-label="Hablar"><span class="mic-ic" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0M12 17v5M8 22h8"/></svg></span><span class="mic-t"><span class="es">Tocá y hablá</span><span class="en">Tap and speak</span></span></button>
    <p class="heard" id="heard" hidden></p>
    <form class="typed" id="typed"><label for="q" class="es">O escribilo:</label><label for="q" class="en">Or type it:</label><input id="q" type="text" placeholder="quiero hacer un asado para 5 personas" autocomplete="off"><button type="submit"><span class="es">Buscar</span><span class="en">Search</span></button></form>
    <p class="examples"><span class="es">Ejemplos: «quiero hacer un asado para 6», «una semana saludable para mi abuela», «comida barata de estudiante».</span><span class="en">Examples: "an asado for 6 people", "a healthy week for my grandmother", "cheap student food".</span></p>
  </section>

  <section class="pick">
    <div class="tabs" id="tabs" role="tablist"></div>
    <div class="people" id="people"><label for="n"><span class="es">¿Para cuántas personas?</span><span class="en">For how many people?</span></label><div class="stepper"><button type="button" id="minus" aria-label="Menos">−</button><input id="n" type="number" min="1" max="40" value="4"><button type="button" id="plus" aria-label="Más">+</button></div></div>
    <p class="bdesc" id="bdesc"></p>
  </section>

  <section class="result" id="result" hidden>
    <div class="win">
      <div class="lbl"><span class="es">Te conviene ir a</span><span class="en">Your best bet is</span></div>
      <div class="shopname" id="winShop"></div>
      <div class="total" id="winTotal"></div>
      <div class="sub" id="winSub"></div>
      <div class="maps"><a id="gmaps" class="mapbtn" target="_blank" rel="noopener">📍 Google Maps</a><a id="amaps" class="mapbtn" target="_blank" rel="noopener">🍎 Apple Maps</a><button type="button" id="say" class="mapbtn ghost">🔊 <span class="es">Escuchar</span><span class="en">Listen</span></button></div>
      <p class="warn" id="winWarn" hidden></p>
    </div>
    <div class="others" id="others"></div>
    <h2><span class="es">La lista de compras</span><span class="en">The shopping list</span></h2>
    <p class="muted" id="listIntro"></p>
    <div class="tbl-wrap"><table class="ptable"><thead><tr><th><span class="es">Qué</span><span class="en">What</span></th><th class="r"><span class="es">Cantidad</span><span class="en">Quantity</span></th><th><span class="es">Producto más barato hoy</span><span class="en">Cheapest product today</span></th><th class="r"><span class="es">Precio</span><span class="en">Price</span></th></tr></thead><tbody id="list"></tbody></table></div>
    <p class="kcal" id="kcal" hidden></p>
  </section>

  <section class="how">
    <h2><span class="es">Cómo se calcula</span><span class="en">How it is calculated</span></h2>
    <p class="es">Para cada cosa de la lista, en cada súper, se toma el producto más barato que había hoy en su página web, por kilo, por litro o por unidad, y se multiplica por la cantidad. Son precios online del día, sin promos bancarias. Un precio muy lejos del de los otros súper (menos del 40% o más del 250% de la mediana) se descarta como error de la web, igual que en el índice. Si a un súper le falta algo, se avisa y no compite por el primer puesto. Nada se estima.</p>
    <p class="en">For each item on the list, at each supermarket, we take the cheapest product on its website today, per kilo, per litre or per unit, and multiply by the quantity. These are the day's online prices, with no bank promotions. A price far from the other shops (under 40% or over 250% of the median) is discarded as a website error, as the index does. If a shop is missing something, we say so and it does not compete for first place. Nothing is estimated.</p>
    <p class="muted"><span class="es">Las calorías son valores aproximados de tablas estándar de alimentos, por kilo o litro de cada ingrediente. No es consejo médico.</span><span class="en">Calories are approximate values from standard food tables, per kilo or litre of each ingredient. Not medical advice.</span></p>
    <p><a href="../index.html#shops"><span class="es">Ranking de súper con la canasta completa</span><span class="en">Supermarket ranking with the full basket</span></a> · <a href="../precios/"><span class="es">Precio de cada producto hoy</span><span class="en">Today's price of each product</span></a> · <a href="../metodo.html"><span class="es">Metodología</span><span class="en">Methodology</span></a></p>
  </section>
</main>
<script>
(function () {
  const es = () => document.documentElement.lang !== "en";
  const money = x => "$" + Math.round(x).toLocaleString(es() ? "es-AR" : "en-US");
  const SHOP = { Carrefour: "Carrefour", Jumbo: "Jumbo", ChangoMas: "ChangoMás", Dia: "Día" };
  // always Argentina: Carrefour and Día also exist in Spain, and the page is opened from abroad too
  const QUERY = { Carrefour: "Supermercado Carrefour, Argentina", Jumbo: "Supermercado Jumbo, Argentina", ChangoMas: "Supermercado ChangoMás, Argentina", Dia: "Supermercado Día, Argentina" };
  let D = null, basket = "asado", people = 4, fromVoice = false;
  const $ = id => document.getElementById(id);
  const NUM = { uno: 1, una: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7, ocho: 8, nueve: 9, diez: 10, once: 11, doce: 12, trece: 13, catorce: 14, quince: 15, veinte: 20, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10, twelve: 12, fifteen: 15, twenty: 20 };
  function parse(text) {
    const t = text.toLowerCase();
    let b = null;
    if (/asado|parrill|barbecue|bbq|choriz/.test(t)) b = "asado";
    else if (/salud|sano|sana|healthy|abuel|jubil|pension|grand|dieta|diet|viej|mayor|elder/.test(t)) b = "saludable";
    else if (/estudiant|student|barat|cheap|econ[oó]m|budget|poca plata|universi/.test(t)) b = "estudiante";
    let n = null;
    const m = t.match(/(\d{1,2})\s*(personas?|people|amigos?|invitados?|pibes|chicos|gente|comensales|pax)?/);
    if (m) n = +m[1];
    if (!n) { for (const w in NUM) { if (new RegExp("\\b" + w + "\\b").test(t)) { n = NUM[w]; break; } } }
    if (/somos (dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|\d+)/.test(t) && !n) n = NUM[RegExp.$1] || +RegExp.$1;
    return { basket: b, people: n };
  }
  function render() {
    if (!D) return;
    const B = D.baskets.find(x => x.id === basket); if (!B) return;
    document.querySelectorAll("#tabs button").forEach(b => b.setAttribute("aria-selected", String(b.dataset.id === basket)));
    $("people").hidden = B.per !== "persona";
    $("bdesc").textContent = es() ? B.desc_es : B.desc_en;
    const mult = B.per === "persona" ? people : 1;
    const common = new Set(B.common);
    const tot = s => { const S = B.shops[s]; return S.items.reduce((a, it) => a + (it.missing || !common.has(it.ing) ? 0 : it.cost * (it.fixed ? 1 : mult)), 0); };
    const order = B.ranking.slice(); D.shops.forEach(s => { if (!order.includes(s)) order.push(s); });
    const win = order[0], W = B.shops[win];
    $("winShop").textContent = SHOP[win];
    $("winTotal").textContent = money(tot(win));
    $("winSub").textContent = B.per === "persona"
      ? (es() ? `para ${people} persona${people > 1 ? "s" : ""} · ${money(tot(win) / people)} por persona · precios del ${fmtDate(D.date)}` : `for ${people} ${people > 1 ? "people" : "person"} · ${money(tot(win) / people)} per person · prices of ${fmtDate(D.date)}`)
      : (es() ? `una persona, 7 días · precios del ${fmtDate(D.date)}` : `one person, 7 days · prices of ${fmtDate(D.date)}`);
    $("gmaps").href = "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(QUERY[win]);
    $("amaps").href = "https://maps.apple.com/?q=" + encodeURIComponent(QUERY[win]);
    const incomplete = D.shops.filter(s => !B.shops[s].complete);
    const warn = $("winWarn");
    if (B.missing_everywhere.length) {
      const names = B.missing_everywhere.map(k => (es() ? B.ingredients[k].es : B.ingredients[k].en).toLowerCase()).join(", ");
      warn.textContent = es() ? `Hoy no hay precio de: ${names}. No están en el total. Esos productos se empiezan a relevar y aparecen en cuanto hay datos.` : `No price today for: ${names}. They are not in the total. Those products are being added and appear as soon as there is data.`;
      warn.hidden = false;
    } else warn.hidden = true;
    const lacking = D.shops.filter(s => B.shops[s].lacks.length);
    if (lacking.length) {
      const txt = lacking.map(s => `${SHOP[s]}: ${B.shops[s].lacks.map(k => (es() ? B.ingredients[k].es : B.ingredients[k].en).toLowerCase()).join(", ")}`).join(" · ");
      warn.textContent = (warn.hidden ? "" : warn.textContent + " ") + (es() ? `Para comparar parejo, el total usa solo lo que tienen los 4 súper hoy. Hoy no tienen: ${txt}.` : `For a fair comparison the total uses only what all 4 shops have today. Missing today: ${txt}.`);
      warn.hidden = false;
    }
    const ot = $("others"); ot.textContent = "";
    order.slice(1).forEach(s => {
      const S = B.shops[s], d = document.createElement("div"); d.className = "oth" + (S.complete ? "" : " inc");
      const diff = (tot(s) / tot(win) - 1) * 100;
      d.innerHTML = `<b>${SHOP[s]}</b><span class="ot">${money(tot(s))}</span><span class="od">${(diff > 0.05 ? "+" : "") + diff.toFixed(1).replace(".", es() ? "," : ".") + "%"}${S.lacks.length ? " · " + (es() ? "no tiene " : "no ") + S.lacks.map(k => (es() ? B.ingredients[k].es : B.ingredients[k].en).toLowerCase()).join(", ") : ""}</span>`;
      ot.appendChild(d);
    });
    $("listIntro").textContent = es() ? `Lo que llevás en ${SHOP[win]}, con el producto más barato de hoy para cada cosa.` : `What you buy at ${SHOP[win]}, with today's cheapest product for each item.`;
    const tb = $("list"); tb.textContent = "";
    W.items.forEach(it => {
      const ing = B.ingredients[it.ing], q = it.qty * (it.fixed ? 1 : mult), tr = document.createElement("tr");
      const qty = ing.unit === "un" ? `${Math.round(q * 100) / 100} ${q === 1 ? (es() ? "unidad" : "unit") : (es() ? "unidades" : "units")}` : ing.unit === "kg" ? (q < 1 ? `${Math.round(q * 1000)} g` : `${Math.round(q * 100) / 100} kg`) : (q < 1 ? `${Math.round(q * 1000)} ml` : `${Math.round(q * 100) / 100} L`);
      const extra = !it.missing && !common.has(it.ing) ? `<br><small>${es() ? "no entra en la comparación: otro súper no lo tiene hoy" : "not in the comparison: another shop lacks it today"}</small>` : "";
      tr.innerHTML = it.missing
        ? `<td>${es() ? ing.es : ing.en}</td><td class="r">${qty}</td><td class="muted">${es() ? "sin precio hoy" : "no price today"}</td><td class="r">—</td>`
        : `<td>${es() ? ing.es : ing.en}</td><td class="r">${qty}</td><td>${it.name}${it.promo ? ' <span class="promo">promo</span>' : ""}<br><small>${money(it.unit_price)} ${ing.unit === "un" ? (es() ? "c/u" : "each") : (es() ? "por " : "per ") + (ing.unit === "kg" ? "kg" : es() ? "litro" : "litre")}</small>${extra}</td><td class="r"><strong>${money(it.cost * (it.fixed ? 1 : mult))}</strong></td>`;
      tb.appendChild(tr);
    });
    if (B.per === "semana" && W.kcal) { $("kcal").textContent = es() ? `Aporta unas ${Math.round(W.kcal / 7).toLocaleString("es-AR")} calorías por día (aproximado).` : `About ${Math.round(W.kcal / 7).toLocaleString("en-US")} calories a day (approximate).`; $("kcal").hidden = false; } else $("kcal").hidden = true;
    $("result").hidden = false;
    if (fromVoice) { speak(); fromVoice = false; }
  }
  function fmtDate(d) { const [y, m, dd] = d.split("-"); const MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"], MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]; return es() ? `${+dd} de ${MES[+m - 1]}` : `${+dd} ${MON[+m - 1]}`; }
  function speak() {
    if (!("speechSynthesis" in window)) return;
    const B = D.baskets.find(x => x.id === basket), mult = B.per === "persona" ? people : 1;
    const win = B.ranking[0] || D.shops[0]; const common = new Set(B.common); const total = B.shops[win].items.reduce((a, it) => a + (it.missing || !common.has(it.ing) ? 0 : it.cost * (it.fixed ? 1 : mult)), 0);
    const txt = es() ? `Te conviene ir a ${SHOP[win]}. ${B.per === "persona" ? `El asado para ${people} sale ` : "La semana sale "}${Math.round(total).toLocaleString("es-AR")} pesos.` : `Your best bet is ${SHOP[win]}. It costs ${Math.round(total).toLocaleString("en-US")} pesos.`;
    const u = new SpeechSynthesisUtterance(txt); u.lang = es() ? "es-AR" : "en-US"; speechSynthesis.cancel(); speechSynthesis.speak(u);
  }
  function apply(text, voice) {
    const p = parse(text); $("heard").textContent = (es() ? "Escuché: " : "Heard: ") + "«" + text + "»"; $("heard").hidden = false;
    if (p.basket) basket = p.basket;
    if (p.people) { people = Math.min(40, Math.max(1, p.people)); $("n").value = people; }
    fromVoice = !!voice; render();
    if (!p.basket && !p.people) { $("heard").textContent += es() ? " No entendí qué querés hacer: elegí una canasta abajo." : " I did not catch what you want: pick a basket below."; }
    $("result").scrollIntoView({ behavior: "smooth", block: "start" });
  }
  // voice
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const mic = $("mic");
  if (!SR) { mic.hidden = true; }
  else {
    let rec = null;
    mic.addEventListener("click", () => {
      if (rec) { rec.stop(); return; }
      rec = new SR(); rec.lang = es() ? "es-AR" : "en-US"; rec.interimResults = false; rec.maxAlternatives = 1;
      mic.classList.add("on"); mic.querySelector(".mic-t").textContent = es() ? "Escuchando…" : "Listening…";
      rec.onresult = e => { const t = e.results[0][0].transcript; $("q").value = t; apply(t, true); };
      rec.onerror = e => { $("heard").textContent = es() ? "No pude escuchar (" + e.error + "). Probá escribirlo." : "Could not hear (" + e.error + "). Try typing it."; $("heard").hidden = false; };
      rec.onend = () => { rec = null; mic.classList.remove("on"); mic.querySelector(".mic-t").innerHTML = es() ? "Tocá y hablá" : "Tap and speak"; };
      try { rec.start(); } catch (err) { rec = null; }
    });
  }
  $("typed").addEventListener("submit", e => { e.preventDefault(); const t = $("q").value.trim(); if (t) apply(t, false); });
  $("minus").addEventListener("click", () => { people = Math.max(1, people - 1); $("n").value = people; render(); });
  $("plus").addEventListener("click", () => { people = Math.min(40, people + 1); $("n").value = people; render(); });
  $("n").addEventListener("change", () => { people = Math.min(40, Math.max(1, +$("n").value || 1)); $("n").value = people; render(); });
  $("say").addEventListener("click", speak);
  document.querySelectorAll(".lang button").forEach(b => b.addEventListener("click", () => setTimeout(() => { buildTabs(); render(); }, 0)));
  function buildTabs() { const t = $("tabs"); t.textContent = ""; D.baskets.forEach(B => { const b = document.createElement("button"); b.type = "button"; b.role = "tab"; b.dataset.id = B.id; b.textContent = es() ? B.es : B.en; b.addEventListener("click", () => { basket = B.id; render(); }); t.appendChild(b); }); }
  fetch("datos.json", { cache: "no-store" }).then(r => r.json()).then(d => { D = d; buildTabs(); const h = location.hash.replace("#", ""); if (D.baskets.some(b => b.id === h)) basket = h; render(); });
})();
</script>
"""

EXTRA_CSS = """<style>
.cn { display: grid; gap: 2.4rem; padding-block: 2rem 0; max-width: 60rem; }
.cn h1 { font-size: clamp(2.3rem, 5.5vw, 3.6rem); }
.cn h2 { font-size: clamp(1.5rem, 3.5vw, 2rem); }
.cn-head { display: grid; gap: 0.7rem; }
.crumbs { font-size: 0.9rem; color: var(--muted); } .crumbs a { color: var(--muted); }
.ask { display: grid; gap: 1rem; justify-items: center; text-align: center; background: var(--band); border: 1px solid var(--rule); border-radius: var(--radius); padding: 1.6rem 1.2rem; }
.mic { display: inline-flex; align-items: center; gap: 0.9rem; background: var(--navy); color: #fff; border: 0; border-radius: 999px; padding: 0.9rem 1.6rem 0.9rem 0.9rem; font: 700 1.15rem var(--body); cursor: pointer; box-shadow: 0 14px 30px -14px rgba(43,59,92,.7); }
.mic .mic-ic { width: 3.2rem; height: 3.2rem; border-radius: 50%; background: var(--sun); display: grid; place-items: center; }
.mic .mic-ic svg { width: 1.6rem; height: 1.6rem; }
.mic.on .mic-ic { animation: pulse 1s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(217,138,43,.6); } 100% { box-shadow: 0 0 0 16px rgba(217,138,43,0); } }
.heard { font-weight: 600; max-width: 60ch; }
.typed { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0.5rem; width: 100%; max-width: 34rem; align-items: center; }
.typed label { grid-column: 1 / -1; font-size: 0.9rem; color: var(--muted); font-weight: 600; text-align: left; }
.typed input { min-width: 0; width: 100%; font: 1rem var(--body); padding: 0.7rem 0.9rem; border: 1.5px solid var(--rule); border-radius: 10px; }
.typed button { font: 700 0.95rem var(--body); background: var(--bg); border: 1.5px solid var(--navy); color: var(--navy); border-radius: 10px; padding: 0.7rem 1rem; cursor: pointer; }
.examples { font-size: 0.88rem; color: var(--muted); max-width: 60ch; }
.pick { display: grid; gap: 1rem; }
.tabs { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.tabs button { font: 700 0.95rem var(--body); border: 1.5px solid var(--rule); background: var(--bg); color: var(--navy); border-radius: 999px; padding: 0.6rem 1.1rem; cursor: pointer; }
.tabs button[aria-selected="true"] { background: var(--navy); color: #fff; border-color: var(--navy); }
.people { display: flex; flex-wrap: wrap; align-items: center; gap: 0.8rem 1.2rem; font-weight: 600; }
.stepper { display: inline-flex; border: 1.5px solid var(--rule); border-radius: 999px; overflow: hidden; }
.stepper button { width: 2.8rem; height: 2.8rem; border: 0; background: var(--band); font: 700 1.3rem var(--body); color: var(--navy); cursor: pointer; }
.stepper input { width: 4rem; border: 0; text-align: center; font: 700 1.2rem var(--body); color: var(--navy); -moz-appearance: textfield; }
.stepper input::-webkit-outer-spin-button, .stepper input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.bdesc { color: var(--muted); max-width: 62ch; }
.result { display: grid; gap: 1.2rem; }
.win { background: var(--navy); color: #fff; border-radius: var(--radius); padding: 1.6rem 1.6rem 1.4rem; display: grid; gap: 0.35rem; box-shadow: 0 30px 60px -36px rgba(43,59,92,.8); }
.win .lbl { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--celeste); }
.win .shopname { font-family: var(--display); font-size: clamp(2.4rem, 6vw, 3.6rem); line-height: 1; }
.win .total { font-size: clamp(2rem, 5vw, 2.8rem); font-weight: 700; font-variant-numeric: tabular-nums; color: var(--sun); }
.win .sub { font-size: 0.95rem; color: rgba(255,255,255,.82); }
.maps { display: flex; flex-wrap: wrap; gap: 0.6rem; margin-top: 0.8rem; }
.mapbtn { display: inline-flex; align-items: center; gap: 0.4rem; background: #fff; color: var(--navy); text-decoration: none; font: 700 0.92rem var(--body); padding: 0.6rem 1rem; border-radius: 999px; border: 0; cursor: pointer; }
.mapbtn.ghost { background: transparent; color: #fff; border: 1.5px solid rgba(255,255,255,.5); }
.win .warn { font-size: 0.9rem; background: rgba(255,255,255,.12); border-radius: 10px; padding: 0.6rem 0.8rem; margin-top: 0.6rem; }
.others { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.7rem; }
.oth { border: 1px solid var(--rule); border-radius: 12px; padding: 0.9rem 1rem; display: grid; gap: 0.15rem; }
.oth b { font-size: 1.05rem; } .oth .ot { font-weight: 700; font-variant-numeric: tabular-nums; } .oth .od { font-size: 0.85rem; color: var(--muted); }
.oth.inc { background: var(--band); }
.ptable td { vertical-align: top; } .ptable td.r { white-space: nowrap; }
.ptable small { color: var(--muted); font-size: 0.82rem; }
.promo { display: inline-block; background: var(--sun); color: #fff; font-weight: 700; font-size: 0.72rem; border-radius: 6px; padding: 0.05rem 0.4rem; vertical-align: middle; }
.kcal { font-weight: 600; }
.how { display: grid; gap: 0.8rem; }
@media (max-width: 640px) { .others { grid-template-columns: 1fr; } .win { padding: 1.3rem 1.2rem; } }
@media (max-width: 560px) {
  .ptable thead { display: none; }
  .ptable, .ptable tbody, .ptable tr, .ptable td { display: block; }
  .ptable tr { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0.1rem 0.8rem; padding: 0.7rem 0.9rem; border-bottom: 1px solid var(--rule); }
  .ptable td, .ptable td.r { border: 0; padding: 0; min-width: 0 !important; text-align: left; white-space: normal; }
  .ptable td:first-child { font-weight: 700; } .ptable td:nth-child(2) { text-align: right; color: var(--muted); }
  .ptable td:nth-child(3) { grid-column: 1 / -1; font-size: 0.92rem; } .ptable td:nth-child(4) { grid-column: 1 / -1; text-align: right; }
}
</style>"""


def main():
    chrome = make_chrome()
    d = json.load(open(os.path.join(ROOT, "canastas", "datos.json"), encoding="utf-8"))
    title = "¿Dónde conviene comprar hoy? Asado, semana saludable y de estudiante en Carrefour, Jumbo, ChangoMás y Día · La Canasta"
    desc = ("Decí qué querés hacer (un asado para 6, una semana saludable, comida de estudiante) y La Canasta te dice a qué supermercado ir, "
            f"cuánto sale hoy y cómo llegar. Precios del {d['date']} en Carrefour, Jumbo, ChangoMás y Día.")
    ld = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "WebApplication", "name": "La Canasta: ¿Dónde conviene comprar hoy?",
          "url": f"{SITE}/canastas/", "applicationCategory": "ShoppingApplication", "operatingSystem": "Web", "inLanguage": ["es", "en"],
          "offers": {"@type": "Offer", "price": "0", "priceCurrency": "ARS"}, "creator": {"@type": "Person", "name": "Ramon Pepa"}}, ensure_ascii=False) + "</script>"
    html = chrome(title, desc, "canastas/", BODY, ld + "\n" + EXTRA_CSS)
    # the shared chrome hides .es/.en through html[lang]; make sure the rule exists in this page too
    html = html.replace("</style>\n<header", 'html:not([lang=en]) .en{display:none!important} html[lang=en] .es{display:none!important}\n</style>\n<header', 1)
    open(os.path.join(ROOT, "canastas", "index.html"), "w", encoding="utf-8").write(html)
    add_to_sitemap(["canastas/"], d["date"])
    print("canastas/index.html written")


if __name__ == "__main__":
    main()
