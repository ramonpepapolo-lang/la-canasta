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
    <div class="chat" id="chat" hidden aria-live="polite"></div>
    <p class="heard" id="heard" hidden></p>
    <form class="typed" id="typed"><label for="q" class="es">O escribilo:</label><label for="q" class="en">Or type it:</label><input id="q" type="text" placeholder="quiero hacer un asado para 5 personas, sin alcohol" autocomplete="off"><button type="submit"><span class="es">Enviar</span><span class="en">Send</span></button></form>
    <div class="install" id="install" hidden>
      <button type="button" id="installBtn" class="install-btn"><img src="/app-icons/icon-192.png" alt="" width="28" height="28"><span class="es">Instalá la app en tu celular</span><span class="en">Install the app on your phone</span></button>
      <p class="install-ios" id="installIos" hidden><span class="es">En iPhone: tocá <b>Compartir</b> (el cuadrado con la flecha) y después <b>Agregar a inicio</b>.</span><span class="en">On iPhone: tap <b>Share</b> (the square with the arrow), then <b>Add to Home Screen</b>.</span></p>
    </div>
    <p class="examples"><span class="es">Ejemplos: «quiero hacer un asado para 6», «una semana saludable para mi abuela», «comida barata de estudiante».</span><span class="en">Examples: "an asado for 6 people", "a healthy week for my grandmother", "cheap student food".</span></p>
  </section>

  <section class="pick">
    <div class="tabs" id="tabs" role="tablist"></div>
    <div class="people" id="people"><label for="n"><span class="es">¿Para cuántas personas?</span><span class="en">For how many people?</span></label><div class="stepper"><button type="button" id="minus" aria-label="Menos">−</button><input id="n" type="number" min="1" max="40" value="4"><button type="button" id="plus" aria-label="Más">+</button></div></div>
    <p class="bdesc" id="bdesc"></p>
    <button type="button" class="editb" id="editB"><span class="es">✏️ Editar esta canasta: cambiá cosas, cantidades y marcas</span><span class="en">✏️ Edit this basket: change items, quantities and brands</span></button>
    <div class="builder" id="builder" hidden>
      <div class="modeall"><span class="es">Para todo:</span><span class="en">For everything:</span>
        <button type="button" data-all="cheap"><span class="es">💸 Lo más barato</span><span class="en">💸 Cheapest</span></button>
        <button type="button" data-all="quality"><span class="es">⭐ Primera marca</span><span class="en">⭐ Leading brand</span></button>
        <button type="button" id="clearL" class="ghost"><span class="es">Vaciar</span><span class="en">Clear</span></button></div>
      <div class="addbox"><input id="addq" type="search" autocomplete="off" placeholder="Agregá: yerba, asado, leche, detergente…"><div class="addres" id="addres"></div></div>
      <div class="cats" id="cats"></div>
      <h3 class="mylist-h"><span class="es">Tu canasta</span><span class="en">Your basket</span> <span id="lcount" class="muted"></span></h3>
      <div class="mylist" id="mylist"></div>
    </div>
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
  let D = null, C = null, basket = "asado", people = 4, fromVoice = false, excluded = new Set(), started = false;
  // "Armá la tuya": the person's own list, kept on this phone: {ingredient: {qty, mode: "cheap" | "quality"}}
  let custom = null;
  const STARTER = { leche: 2, yerba: 1, pan_lactal: 1, arroz: 1, fideos: 1, aceite: 1.5, huevos: 12, azucar: 1 };
  try { custom = JSON.parse(localStorage.getItem("lc-lista") || "null"); } catch (e) {}
  if (!custom || typeof custom !== "object") { custom = {}; for (const k in STARTER) custom[k] = { qty: STARTER[k], mode: "cheap" }; }
  const saveL = () => { try { localStorage.setItem("lc-lista", JSON.stringify(custom)); } catch (e) {} };
  const CUSTOM = { id: "custom", es: "✨ Creá tu canasta", en: "✨ Create your basket" };
  function customB() {
    const ks = Object.keys(custom).filter(k => C && C.items[k]);
    const B = { id: "custom", per: "lista", es: "Tu canasta personalizada", en: "Your custom basket", ingredients: {}, shops: {}, ranking: [], common: [], missing_everywhere: [],
      desc_es: "Creá tu canasta personalizada: elegí qué llevás, cuánto, y si querés lo más barato o primera marca. Te decimos en qué súper te sale menos.", desc_en: "Create your custom basket: pick what you buy, how much, and whether you want the cheapest or a leading brand. We tell you where it costs least." };
    ks.forEach(k => { const it = C.items[k]; B.ingredients[k] = { es: it.es, en: it.en, unit: it.unit }; });
    (C ? C.shops : []).forEach(sh => {
      const items = ks.map(k => {
        const e = C.items[k].shops[sh] || {}, want = custom[k].mode === "quality" ? e.quality : e.cheap, opt = want || e.cheap;
        if (!opt) return { ing: k, qty: custom[k].qty, fixed: false, missing: true };
        return { ing: k, qty: custom[k].qty, fixed: false, unit_price: opt.unit_price, cost: opt.unit_price * custom[k].qty, name: opt.name, promo: opt.promo, fallback: custom[k].mode === "quality" && !want };
      });
      B.shops[sh] = { items, kcal: 0, lacks: [], complete: true };
    });
    const shops = C ? C.shops : [];
    B.missing_everywhere = ks.filter(k => shops.every(sh => B.shops[sh].items.find(i => i.ing === k).missing));
    B.common = ks.filter(k => shops.every(sh => !B.shops[sh].items.find(i => i.ing === k).missing));
    shops.forEach(sh => { B.shops[sh].lacks = ks.filter(k => B.shops[sh].items.find(i => i.ing === k).missing && !B.missing_everywhere.includes(k)); B.shops[sh].complete = !B.shops[sh].lacks.length; });
    const tt = sh => B.shops[sh].items.reduce((a, i) => a + (B.common.includes(i.ing) ? i.cost : 0), 0);
    B.ranking = shops.slice().sort((a, b) => tt(a) - tt(b));
    return B;
  }
  const getB = () => basket === "custom" ? customB() : D.baskets.find(x => x.id === basket);
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
    const B = getB(); if (!B) return;
    document.querySelectorAll("#tabs button").forEach(b => b.setAttribute("aria-selected", String(b.dataset.id === basket)));
    $("people").hidden = B.per !== "persona";
    $("bdesc").textContent = es() ? B.desc_es : B.desc_en;
    $("builder").hidden = basket !== "custom"; $("editB").hidden = basket === "custom";
    if (basket === "custom") drawBuilder();
    if (basket === "custom" && !B.common.length) { $("result").hidden = true; return; }
    const mult = B.per === "persona" ? people : 1;
    const common = new Set(B.common);
    const tot = s => { const S = B.shops[s]; return S.items.reduce((a, it) => a + (it.missing || !common.has(it.ing) || excluded.has(it.ing) ? 0 : it.cost * (it.fixed ? 1 : mult)), 0); };
    const order = B.ranking.slice(); D.shops.forEach(s => { if (!order.includes(s)) order.push(s); });
    const win = order[0], W = B.shops[win];
    $("winShop").textContent = SHOP[win];
    $("winTotal").textContent = money(tot(win));
    $("winSub").textContent = B.per === "persona"
      ? (es() ? `para ${people} persona${people > 1 ? "s" : ""} · ${money(tot(win) / people)} por persona · precios del ${fmtDate(D.date)}` : `for ${people} ${people > 1 ? "people" : "person"} · ${money(tot(win) / people)} per person · prices of ${fmtDate(D.date)}`)
      : B.per === "lista" ? (es() ? `tu canasta, ${B.common.length} productos · precios del ${fmtDate(D.date)}` : `your basket, ${B.common.length} items · prices of ${fmtDate(D.date)}`)
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
    W.items.filter(it => !excluded.has(it.ing)).forEach(it => {
      const ing = B.ingredients[it.ing], q = it.qty * (it.fixed ? 1 : mult), tr = document.createElement("tr");
      const qty = ing.unit === "un" ? `${Math.round(q * 100) / 100} ${q === 1 ? (es() ? "unidad" : "unit") : (es() ? "unidades" : "units")}` : ing.unit === "kg" ? (q < 1 ? `${Math.round(q * 1000)} g` : `${Math.round(q * 100) / 100} kg`) : (q < 1 ? `${Math.round(q * 1000)} ml` : `${Math.round(q * 100) / 100} L`);
      const fb = it.fallback ? `<br><small>${es() ? "acá no hay primera marca: va la más barata" : "no leading brand here: cheapest instead"}</small>` : "";
      const extra = fb + (!it.missing && !common.has(it.ing) ? `<br><small>${es() ? "no entra en la comparación: otro súper no lo tiene hoy" : "not in the comparison: another shop lacks it today"}</small>` : "");
      tr.innerHTML = it.missing
        ? `<td>${es() ? ing.es : ing.en}</td><td class="r">${qty}</td><td class="muted">${es() ? "sin precio hoy" : "no price today"}</td><td class="r">—</td>`
        : `<td>${es() ? ing.es : ing.en}</td><td class="r">${qty}</td><td>${it.name}${it.promo ? ' <span class="promo">promo</span>' : ""}<br><small>${money(it.unit_price)} ${ing.unit === "un" ? (es() ? "c/u" : "each") : (es() ? "por " : "per ") + (ing.unit === "kg" ? "kg" : es() ? "litro" : "litre")}</small>${extra}</td><td class="r"><strong>${money(it.cost * (it.fixed ? 1 : mult))}</strong></td>`;
      tb.appendChild(tr);
    });
    if (B.per === "semana" && W.kcal) { $("kcal").textContent = es() ? `Aporta unas ${Math.round(W.kcal / 7).toLocaleString("es-AR")} calorías por día (aproximado).` : `About ${Math.round(W.kcal / 7).toLocaleString("en-US")} calories a day (approximate).`; $("kcal").hidden = false; } else $("kcal").hidden = true;
    $("result").hidden = false;
  }
  function fmtDate(d) { const [y, m, dd] = d.split("-"); const MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"], MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]; return es() ? `${+dd} de ${MES[+m - 1]}` : `${+dd} ${MON[+m - 1]}`; }
  // ---------- The assistant: understands what you ask, remembers the conversation, answers in full sentences ----------
  const ALIASES = {
    alcohol: ["vino", "cerveza"], "bebida alcoh": ["vino", "cerveza"], vino: ["vino"], cerveza: ["cerveza"], birra: ["cerveza"],
    gaseosa: ["gaseosa"], coca: ["gaseosa"], bebida: ["vino", "cerveza", "gaseosa"], carb: ["carbon"], pan: ["pan", "pan_lactal"],
    provoleta: ["provoleta"], queso: ["provoleta", "queso"], ensalada: ["tomate", "cebolla", "lechuga"], verdura: ["tomate", "cebolla", "lechuga", "zanahoria"],
    chorizo: ["chorizo"], morcilla: ["morcilla"], achura: ["chorizo", "morcilla"], vac: ["vacio"], "asado de tira": ["asado_tira"], chimichurri: ["chimichurri"], sal: ["sal_gruesa"],
    yerba: ["yerba"], leche: ["leche"], huevo: ["huevos"], pollo: ["pollo", "pechuga"], atun: ["atun"], "atún": ["atun"], fruta: ["banana", "manzana", "naranja"],
    gallet: ["galletitas"], mayonesa: ["mayonesa"], carne: ["asado_tira", "vacio", "carne_picada"], picada: ["carne_picada"], azucar: ["azucar"], "azúcar": ["azucar"],
    wine: ["vino"], beer: ["cerveza"], soda: ["gaseosa"], charcoal: ["carbon"], bread: ["pan", "pan_lactal"], salad: ["tomate", "cebolla", "lechuga"], drinks: ["vino", "cerveza", "gaseosa"]
  };
  function ingsIn(t) { const out = new Set(); for (const k in ALIASES) if (t.includes(k)) ALIASES[k].forEach(x => out.add(x)); return [...out]; }
  function understand(text) {
    const t = " " + text.toLowerCase().normalize("NFC") + " ";
    const p = parse(text), r = { basket: p.basket, people: p.people, remove: [], add: [], shop: null, ask: null, greet: false, thanks: false, reset: false };
    let m;
    const neg = /(?:^|\s)(?:sin|no quiero|sac[aá](?:le)?|quit[aá](?:le)?|ya tengo|tengo|no hace falta|without|no|skip|remove)\s([^.,;?!]*)/g;
    while ((m = neg.exec(t))) { const rest = m[1] || ""; if (/^\s*(s[eé]|entend|sab|me |te |le |hay|tiene)/.test(rest)) continue; r.remove.push(...ingsIn(rest)); }
    const pos = /(?:^|\s)(?:con|agreg[aá](?:le)?|pon[eé](?:le)?|sum[aá](?:le)?|with|add)\s([^.,;?!]*)/g;
    while ((m = pos.exec(t))) r.add.push(...ingsIn(m[1] || ""));
    if (/\b(d[ií]a)\b/.test(t) && /(en|y|cuanto|cuánto|sale|precio|at)\s+d[ií]a\b/.test(t)) r.shop = "Dia";
    if (/carrefour|carre/.test(t)) r.shop = "Carrefour"; if (/jumbo/.test(t)) r.shop = "Jumbo"; if (/chango/.test(t)) r.shop = "ChangoMas";
    if (/(m[aá]s caro|lo que m[aá]s|qu[eé] pesa|most expensive|biggest)/.test(t)) r.ask = "priciest";
    if (/(por qu[eé]|why|c[oó]mo sab|de d[oó]nde)/.test(t)) r.ask = "why";
    if (/(calor|kcal|nutri)/.test(t)) r.ask = "kcal";
    if (/(d[oó]nde queda|c[oó]mo llego|m[aá]s cerca|direcci[oó]n|mapa|where is|how do i get|nearest)/.test(t)) r.ask = "where";
    if (/(qu[eé] (llevo|compro|incluye|tiene|hay)|lista|what('s| is) in|shopping list)/.test(t)) r.ask = "list";
    if (/(empez[aá] de nuevo|de cero|reset|start over|borr[aá])/.test(t)) r.reset = true;
    if (/(arm[aá]r?( mi| la| una)? (lista|canasta|compra)|cre[aá]r?( mi| la| una)? canasta|personalizad|mi lista|mi canasta|mi changuito|changuito|compra del mes|build (my|your) own|create (my|a|your) basket|my list|my basket)/.test(t)) r.basket = "custom";
    if (/(primera marca|primeras marcas|calidad|buena marca|mejor marca|marcas buenas|de marca|quality|premium|leading brand)/.test(t)) r.mode = "quality";
    else if (/(lo m[aá]s barato|cualquier marca|la m[aá]s barata|lo mas economico|lo m[aá]s econ[oó]mico|cheapest|any brand)/.test(t) && !r.basket) r.mode = "cheap";
    if (/^\s*(hola|buenas|buen d[ií]a|hello|hi|hey)\b/.test(t)) r.greet = true;
    if (/(gracias|genial|perfecto|b[aá]rbaro|thanks|thank you|great)/.test(t)) r.thanks = true;
    return r;
  }
  function state() {
    const B = getB(), mult = B.per === "persona" ? people : 1, common = new Set(B.common);
    const tot = s => B.shops[s].items.reduce((a, it) => a + (it.missing || !common.has(it.ing) || excluded.has(it.ing) ? 0 : it.cost * (it.fixed ? 1 : mult)), 0);
    const order = D.shops.slice().sort((a, b) => tot(a) - tot(b));
    return { B, mult, tot, order, win: order[0] };
  }
  const say0 = n => (es() ? Math.round(n).toLocaleString("es-AR") : Math.round(n).toLocaleString("en-US")) + (es() ? " pesos" : " pesos");
  const ingName = (B, k) => ((es() ? (B.ingredients[k] || {}).es : (B.ingredients[k] || {}).en) || k || "").replace(/\s*\(.*\)/, "").toLowerCase();
  const told = new Set();
  function reply(r) {
    const { B, mult, tot, order, win } = state();
    const E = es(), what = B.id === "custom" ? (E ? "tu canasta" : "your basket") : B.id === "asado" ? (E ? `el asado para ${people}` : `the asado for ${people}`) : B.id === "saludable" ? (E ? "la semana saludable" : "the healthy week") : (E ? "la semana de estudiante" : "the student week");
    const second = order[1], save = tot(second) - tot(win);
    const main = E ? `Te conviene ir a ${SHOP[win]}: ${what} sale ${say0(tot(win))}${B.per === "persona" ? `, unos ${say0(tot(win) / people)} por persona` : ""}. Te ahorrás ${say0(save)} contra ${SHOP[second]}, que es el segundo.`
                   : `Your best bet is ${SHOP[win]}: ${what} costs ${say0(tot(win))}${B.per === "persona" ? `, about ${say0(tot(win) / people)} per person` : ""}. You save ${say0(save)} compared with ${SHOP[second]}, the runner-up.`;
    const parts = [];
    if (r.greet && !r.basket && !r.people) return E ? "¡Hola! Decime qué querés hacer: un asado, una semana saludable o comida barata de estudiante, y para cuántas personas." : "Hi! Tell me what you want to do: an asado, a healthy week or cheap student food, and for how many people.";
    if (r.thanks && !r.basket && !r.people && !r.remove.length && !r.add.length && !r.ask) return E ? "¡De nada! Si querés cambiar algo, decime, por ejemplo: «sin alcohol» o «somos 8»." : "You're welcome! If you want to change something, tell me, for example: \"no alcohol\" or \"we are 8\".";
    if (r.remove.length) parts.push(E ? `Listo, saqué ${[...new Set(r.remove)].map(k => ingName(B, k)).filter(Boolean).join(", ")}.` : `Done, I took out ${[...new Set(r.remove)].map(k => ingName(B, k)).filter(Boolean).join(", ")}.`);
    if (r.mode && B.id === "custom") parts.push(E ? (r.mode === "quality" ? "Listo, puse primera marca en todo." : "Listo, puse lo más barato en todo.") : (r.mode === "quality" ? "Done, leading brands for everything." : "Done, cheapest for everything."));
    if (r.add.length) parts.push(B.id === "custom" ? (E ? `Listo, agregué ${[...new Set(r.add)].map(k => ingName(B, k)).filter(Boolean).join(", ")}.` : `Done, I added ${[...new Set(r.add)].map(k => ingName(B, k)).filter(Boolean).join(", ")}.`) : E ? `Listo, volví a poner ${[...new Set(r.add)].map(k => ingName(B, k)).filter(Boolean).join(", ")}.` : `Done, I put back ${[...new Set(r.add)].map(k => ingName(B, k)).filter(Boolean).join(", ")}.`);
    if (r.shop) {
      const d = (tot(r.shop) / tot(win) - 1) * 100;
      parts.push(r.shop === win ? (E ? `${SHOP[r.shop]} es justamente el más barato: ${say0(tot(r.shop))}.` : `${SHOP[r.shop]} is the cheapest: ${say0(tot(r.shop))}.`)
        : (E ? `En ${SHOP[r.shop]} sale ${say0(tot(r.shop))}, un ${d.toFixed(0)}% más que en ${SHOP[win]}.` : `At ${SHOP[r.shop]} it costs ${say0(tot(r.shop))}, ${d.toFixed(0)}% more than at ${SHOP[win]}.`));
      return parts.join(" ");
    }
    if (r.ask === "priciest") {
      const items = B.shops[win].items.filter(it => !it.missing && !excluded.has(it.ing)).map(it => [it.ing, it.cost * (it.fixed ? 1 : mult)]).sort((a, b) => b[1] - a[1]);
      if (items.length) parts.push(E ? `Lo que más pesa es ${ingName(B, items[0][0])}: ${say0(items[0][1])} de ${say0(tot(win))}.` : `The biggest cost is ${ingName(B, items[0][0])}: ${say0(items[0][1])} of ${say0(tot(win))}.`);
      return parts.join(" ");
    }
    if (r.ask === "why") return E ? `Porque para cada cosa de la lista tomé el producto más barato que hay hoy en la web de cada súper, y sumé. Con los precios de hoy, ${SHOP[win]} da el total más bajo.` : `Because for each item I took the cheapest product on each shop's website today and added them up. With today's prices, ${SHOP[win]} gives the lowest total.`;
    if (r.ask === "kcal") { const k = B.shops[win].kcal; return k ? (E ? `Aporta unas ${Math.round((B.per === "semana" ? k / 7 : k * mult / people)).toLocaleString("es-AR")} calorías ${B.per === "semana" ? "por día" : "por persona"}, aproximado.` : `About ${Math.round((B.per === "semana" ? k / 7 : k * mult / people)).toLocaleString("en-US")} calories ${B.per === "semana" ? "a day" : "per person"}, approximately.`) : (E ? "Para esta canasta no tengo las calorías todavía." : "I do not have calories for this basket yet."); }
    if (r.ask === "where") return E ? `Tocá el botón de Google Maps o Apple Maps y te muestra el ${SHOP[win]} más cerca tuyo.` : `Tap the Google Maps or Apple Maps button and it shows the ${SHOP[win]} nearest to you.`;
    if (r.ask === "list") {
      const items = B.shops[win].items.filter(it => !it.missing && !excluded.has(it.ing)).map(it => ingName(B, it.ing));
      return (E ? `En ${SHOP[win]} llevás: ${items.join(", ")}. Tenés el detalle con cantidades y precios acá abajo.` : `At ${SHOP[win]} you buy: ${items.join(", ")}. The detail with quantities and prices is below.`);
    }
    if (B.id === "custom" && !B.common.length) return E ? "Tu canasta está vacía. Decime qué querés llevar, por ejemplo: «agregá yerba, leche y asado»." : "Your basket is empty. Tell me what to add, for example: \"add yerba, milk and asado\".";
    if (!r.basket && !r.people && !r.remove.length && !r.add.length && !r.reset && !r.mode) {
      return E ? "Perdón, no te entendí bien. ¿Querés hacer un asado, armar una semana saludable o comida barata de estudiante? Y decime para cuántos." : "Sorry, I did not quite get that. Do you want an asado, a healthy week or cheap student food? And tell me for how many.";
    }
    parts.push(main);
    if (B.missing_everywhere.length && !told.has("miss" + B.id) && told.add("miss" + B.id)) parts.push(E ? `Ojo: hoy todavía no tengo precio de ${B.missing_everywhere.map(k => ingName(B, k)).join(", ")}.` : `Note: I do not have a price yet today for ${B.missing_everywhere.map(k => ingName(B, k)).join(", ")}.`);
    if (B.id === "asado" && !r.people && !told.has("people") && told.add("people")) parts.push(E ? "¿Para cuántos es?" : "How many people is it for?");
    return parts.join(" ");
  }
  function bubble(who, text) {
    const c = $("chat"); c.hidden = false;
    const d = document.createElement("div"); d.className = "msg " + who; d.textContent = text; c.appendChild(d);
    while (c.children.length > 30) c.removeChild(c.firstChild);
    c.scrollTop = c.scrollHeight;
  }
  let listenAfter = false;
  function speak(text) {
    if (!("speechSynthesis" in window)) { if (listenAfter) startListening(); return; }
    if (!text) { const r = { basket, people }; text = reply(Object.assign(understand(""), { basket })); }
    const u = new SpeechSynthesisUtterance(text); u.lang = es() ? "es-AR" : "en-US"; u.rate = 1.02;
    u.onend = () => { if (listenAfter) { listenAfter = false; startListening(); } };
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  }
  function apply(text, voice) {
    const r = understand(text);
    bubble("you", text);
    if (r.reset) { excluded = new Set(); people = 4; $("n").value = 4; }
    if (r.basket && r.basket !== basket) { basket = r.basket; excluded = new Set(); }
    if (r.people) { people = Math.min(40, Math.max(1, r.people)); $("n").value = people; }
    if (basket === "custom") {
      r.remove.forEach(k => delete custom[k]);
      r.add.forEach(k => { if (C && C.items[k] && !custom[k]) custom[k] = { qty: C.items[k].q, mode: r.mode || "cheap" }; });
      if (r.mode) Object.keys(custom).forEach(k => custom[k].mode = r.mode);
      saveL();
    } else { r.remove.forEach(k => excluded.add(k)); r.add.forEach(k => excluded.delete(k)); }
    render();
    const ans = reply(r); started = true;
    bubble("bot", ans);
    // a question back keeps the conversation going: after speaking, it listens again
    listenAfter = !!voice && /\?$/.test(ans.trim());
    if (voice) speak(ans);
  }
  // ---------- "Armá la tuya": add, remove, quantities, cheapest or leading brand ----------
  const fmtQ = (u, q) => u === "un" ? `${Math.round(q * 100) / 100}` : u === "kg" ? (q < 1 ? `${Math.round(q * 1000)} g` : `${Math.round(q * 100) / 100} kg`) : (q < 1 ? `${Math.round(q * 1000)} ml` : `${Math.round(q * 100) / 100} L`);
  const stepOf = (u, q0) => u === "un" ? 1 : q0 >= 1 ? 0.5 : q0 >= 0.2 ? 0.1 : 0.05;
  const nm = k => (es() ? C.items[k].es : C.items[k].en);
  function addItem(k) { if (!custom[k]) { custom[k] = { qty: C.items[k].q, mode: "cheap" }; saveL(); render(); } }
  function drawBuilder() {
    if (!C) { $("mylist").textContent = es() ? "Cargando productos…" : "Loading products…"; return; }
    const cats = $("cats"); cats.textContent = "";
    (C.categories || []).forEach(([id, ces, cen]) => {
      const ks = Object.keys(C.items).filter(k => C.items[k].cat === id && !custom[k] && Object.keys(C.items[k].shops).length);
      if (!ks.length) return;
      const g = document.createElement("div"); g.className = "catg";
      g.innerHTML = `<b>${es() ? ces : cen}</b>`;
      ks.forEach(k => { const b = document.createElement("button"); b.type = "button"; b.textContent = "+ " + nm(k).replace(/\s*\(.*\)/, ""); b.addEventListener("click", () => addItem(k)); g.appendChild(b); });
      cats.appendChild(g);
    });
    const ml = $("mylist"); ml.textContent = "";
    const ks = Object.keys(custom).filter(k => C.items[k]);
    $("lcount").textContent = `(${ks.length})`;
    if (!ks.length) { ml.innerHTML = `<p class="muted">${es() ? "Todavía no agregaste nada. Tocá un producto de arriba o buscalo." : "Nothing added yet. Tap a product above or search for it."}</p>`; }
    ks.forEach(k => {
      const it = C.items[k], c = custom[k], st = stepOf(it.unit, it.q), row = document.createElement("div"); row.className = "li";
      row.innerHTML = `<div class="li-n"><b>${nm(k)}</b><div class="seg">
          <button type="button" data-m="cheap" aria-pressed="${c.mode !== "quality"}">${es() ? "Más barata" : "Cheapest"}</button>
          <button type="button" data-m="quality" aria-pressed="${c.mode === "quality"}" ${it.has_quality ? "" : "disabled title='" + (es() ? "Sin primera marca para este producto" : "No leading brand for this item") + "'"}>${es() ? "Primera marca" : "Leading brand"}</button></div></div>
        <div class="stepper sm"><button type="button" data-d="-1" aria-label="−">${c.qty <= st + 1e-9 ? "🗑" : "−"}</button><span>${fmtQ(it.unit, c.qty)}</span><button type="button" data-d="1" aria-label="+">+</button></div>`;
      row.querySelectorAll("[data-m]").forEach(b => b.addEventListener("click", () => { c.mode = b.dataset.m; saveL(); render(); }));
      row.querySelectorAll("[data-d]").forEach(b => b.addEventListener("click", () => {
        if (+b.dataset.d < 0 && c.qty <= st + 1e-9) delete custom[k];
        else c.qty = Math.max(st, Math.round((c.qty + st * +b.dataset.d) * 100) / 100);
        saveL(); render(); }));
      ml.appendChild(row);
    });
  }
  $("addq").addEventListener("input", () => {
    const q = $("addq").value.trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""), box = $("addres"); box.textContent = "";
    if (!q || !C) return;
    Object.keys(C.items).filter(k => (C.items[k].es + " " + C.items[k].en).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").includes(q)).slice(0, 8).forEach(k => {
      const b = document.createElement("button"); b.type = "button"; b.textContent = (custom[k] ? "✓ " : "+ ") + nm(k);
      b.addEventListener("click", () => { addItem(k); $("addq").value = ""; box.textContent = ""; }); box.appendChild(b); });
    if (!box.children.length) box.innerHTML = `<span class="muted">${es() ? "Todavía no seguimos ese producto. Lo sumamos pronto." : "We do not track that product yet."}</span>`;
  });
  document.querySelectorAll("[data-all]").forEach(b => b.addEventListener("click", () => { Object.keys(custom).forEach(k => custom[k].mode = b.dataset.all); saveL(); render(); }));
  $("clearL").addEventListener("click", () => { custom = {}; saveL(); render(); });
  $("editB").addEventListener("click", () => {
    const B = D.baskets.find(x => x.id === basket), mult = B.per === "persona" ? people : 1;
    custom = {};
    Object.keys(B.ingredients).forEach(k => { if (excluded.has(k) || !C || !C.items[k]) return; const it = B.shops[B.ranking[0]].items.find(i => i.ing === k); custom[k] = { qty: Math.round((it ? it.qty : 1) * (it && it.fixed ? 1 : mult) * 100) / 100, mode: "cheap" }; });
    saveL(); basket = "custom"; render(); $("builder").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  // voice
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const mic = $("mic");
  let rec = null;
  function startListening() {
    if (!SR || rec) return;
    rec = new SR(); rec.lang = es() ? "es-AR" : "en-US"; rec.interimResults = false; rec.maxAlternatives = 1;
    mic.classList.add("on"); mic.querySelector(".mic-t").textContent = es() ? "Te escucho…" : "Listening…";
    rec.onresult = e => { const t = e.results[0][0].transcript; apply(t, true); };
    rec.onerror = e => { if (e.error !== "no-speech" && e.error !== "aborted") bubble("bot", es() ? "No te pude escuchar. Probá de nuevo o escribilo." : "I could not hear you. Try again or type it."); };
    rec.onend = () => { rec = null; mic.classList.remove("on"); mic.querySelector(".mic-t").textContent = es() ? "Tocá y hablá" : "Tap and speak"; };
    try { rec.start(); } catch (err) { rec = null; }
  }
  if (!SR) { mic.hidden = true; }
  else mic.addEventListener("click", () => { if (rec) { rec.stop(); return; } if ("speechSynthesis" in window) speechSynthesis.cancel(); startListening(); });
  $("typed").addEventListener("submit", e => { e.preventDefault(); const t = $("q").value.trim(); if (t) { apply(t, false); $("q").value = ""; } });
  $("minus").addEventListener("click", () => { people = Math.max(1, people - 1); $("n").value = people; render(); });
  $("plus").addEventListener("click", () => { people = Math.min(40, people + 1); $("n").value = people; render(); });
  $("n").addEventListener("change", () => { people = Math.min(40, Math.max(1, +$("n").value || 1)); $("n").value = people; render(); });
  $("say").addEventListener("click", () => { const r = understand(""); r.basket = basket; started = true; speak(reply(r)); });
  document.querySelectorAll(".lang button").forEach(b => b.addEventListener("click", () => setTimeout(() => { buildTabs(); render(); }, 0)));
  function buildTabs() { const t = $("tabs"); t.textContent = ""; D.baskets.concat([CUSTOM]).forEach(B => { const b = document.createElement("button"); b.type = "button"; b.role = "tab"; b.dataset.id = B.id; b.textContent = es() ? B.es : B.en; b.addEventListener("click", () => { basket = B.id; render(); }); t.appendChild(b); }); }
  // install: Android/Chrome gives a prompt; iPhone needs Share > Add to Home Screen
  (function () {
    if (document.documentElement.classList.contains("lc-app")) return;
    const box = $("install"), btn = $("installBtn"), ios = /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream;
    let ev = null;
    window.addEventListener("beforeinstallprompt", e => { e.preventDefault(); ev = e; box.hidden = false; });
    if (ios) box.hidden = false;
    btn.addEventListener("click", async () => { if (ev) { ev.prompt(); await ev.userChoice; ev = null; box.hidden = true; } else if (ios) $("installIos").hidden = false; });
  })();
  fetch("catalogo.json", { cache: "no-store" }).then(r => r.json()).then(c => { C = c; if (D) render(); }).catch(() => {});
  fetch("datos.json", { cache: "no-store" }).then(r => r.json()).then(d => { D = d; buildTabs(); const h = location.hash.replace("#", ""); if (D.baskets.some(b => b.id === h) || h === "custom") basket = h; render(); });
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
.chat { width: 100%; max-width: 40rem; display: grid; gap: 0.5rem; max-height: 22rem; overflow-y: auto; text-align: left; padding: 0.2rem; }
.msg { max-width: 85%; padding: 0.7rem 0.95rem; border-radius: 16px; font-size: 1rem; line-height: 1.45; }
.msg.you { justify-self: end; background: var(--navy); color: #fff; border-bottom-right-radius: 4px; }
.msg.bot { justify-self: start; background: #fff; border: 1px solid var(--rule); border-bottom-left-radius: 4px; }
.msg.bot::before { content: "La Canasta"; display: block; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--sun); margin-bottom: 0.2rem; }
.typed { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0.5rem; width: 100%; max-width: 34rem; align-items: center; }
.typed label { grid-column: 1 / -1; font-size: 0.9rem; color: var(--muted); font-weight: 600; text-align: left; }
.typed input { min-width: 0; width: 100%; font: 1rem var(--body); padding: 0.7rem 0.9rem; border: 1.5px solid var(--rule); border-radius: 10px; }
.typed button { font: 700 0.95rem var(--body); background: var(--bg); border: 1.5px solid var(--navy); color: var(--navy); border-radius: 10px; padding: 0.7rem 1rem; cursor: pointer; }
.install { display: grid; gap: 0.5rem; justify-items: center; }
.install-btn { display: inline-flex; align-items: center; gap: 0.6rem; background: #fff; border: 1.5px solid var(--navy); color: var(--navy); border-radius: 999px; padding: 0.45rem 1rem 0.45rem 0.5rem; font: 700 0.95rem var(--body); cursor: pointer; }
.install-btn img { border-radius: 7px; }
.install-ios { font-size: 0.9rem; max-width: 40ch; }
html.lc-app .cn { padding-top: 1rem; gap: 1.6rem; }
html.lc-app .cn-head .lede { display: none; }
html.lc-app .cn h1 { font-size: 2rem; }
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
.editb { justify-self: start; font: 700 0.92rem var(--body); background: var(--bg); color: var(--navy); border: 1.5px dashed var(--celeste); border-radius: 12px; padding: 0.6rem 0.9rem; cursor: pointer; text-align: left; }
.builder { display: grid; gap: 1rem; }
.modeall { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; font-weight: 600; font-size: 0.92rem; }
.modeall button { font: 700 0.88rem var(--body); border: 1.5px solid var(--navy); background: var(--bg); color: var(--navy); border-radius: 999px; padding: 0.45rem 0.85rem; cursor: pointer; }
.modeall button.ghost { border-color: var(--rule); color: var(--muted); }
.addbox input { width: 100%; font: 1rem var(--body); padding: 0.75rem 0.95rem; border: 1.5px solid var(--rule); border-radius: 12px; }
.addres { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
.addres button, .catg button { font: 600 0.88rem var(--body); background: var(--band); border: 1px solid var(--rule); color: var(--navy); border-radius: 999px; padding: 0.4rem 0.75rem; cursor: pointer; }
.cats { display: grid; gap: 0.7rem; }
.catg { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; }
.catg b { width: 100%; font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
.mylist-h { font-family: var(--body); font-size: 1.15rem; font-weight: 700; }
.mylist { display: grid; border: 1px solid var(--rule); border-radius: var(--radius); overflow: hidden; }
.li { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0.8rem; align-items: center; padding: 0.8rem 0.9rem; border-bottom: 1px solid var(--rule); background: var(--bg); }
.li:last-child { border-bottom: 0; }
.li-n { display: grid; gap: 0.35rem; min-width: 0; }
.seg { display: inline-flex; border: 1px solid var(--rule); border-radius: 999px; overflow: hidden; justify-self: start; }
.seg button { font: 600 0.76rem var(--body); border: 0; background: var(--bg); color: var(--muted); padding: 0.32rem 0.6rem; cursor: pointer; white-space: nowrap; }
.seg button[aria-pressed="true"] { background: var(--navy); color: #fff; }
.seg button:disabled { opacity: 0.4; cursor: not-allowed; }
.stepper.sm { align-items: center; }
.stepper.sm button { width: 2.4rem; height: 2.4rem; font-size: 1.1rem; }
.stepper.sm span { min-width: 3.6rem; text-align: center; font-weight: 700; font-variant-numeric: tabular-nums; }
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
