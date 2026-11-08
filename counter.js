// La Canasta visitor counter (GoatCounter, no cookies).
// When you have your GoatCounter code, put it between the quotes below, e.g. "lacanasta".
var GOATCOUNTER_CODE = "lacanasta";

// Email sign-up: the address the subscribe form sends to (from Brevo). Empty = the sign-up box stays hidden.
var SUBSCRIBE_ACTION = "https://d0cbcf18.sibforms.com/serve/" + [
  "MUIFAJ2G9E2LSize80XqnowNm0uTBtzGxHXvyjc-",
  "SAI7JFpiIQG6y87uWRfmx3HR-aY8PlhwirhDb24r",
  "oU7jCNV7w2Mfn5pcMNsHKNMtMloBhR23hvaKlU-n",
  "-_e_ajxlSANVbDurWVa2n5jmejSZwn4CTPWOKBfH",
  "Hh_vXy1pgmeyN8PeTQBEJYGNOHxIzu8R_K-vBf41",
  "nqpE9dKDdg=="
].join("");

// Email unsubscribe form address (from Brevo). Empty = the "Darme de baja" button explains how to unsubscribe instead.
var UNSUBSCRIBE_ACTION = "";

(function () {
  if (!GOATCOUNTER_CODE) return;
  if (window.top !== window.self) return; // the app shown inside the "Creá tu canasta" page: the page already counts the visit
  if (/admin\.html$/.test(location.pathname)) return; // don't count your own admin visits
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://gc.zgo.at/count.js";
  s.setAttribute("data-goatcounter", "https://" + GOATCOUNTER_CODE + ".goatcounter.com/count");
  document.head.appendChild(s);
})();

// ---------- Announcement bar at the top of every public page ----------
// "Próximo informe: 1 de diciembre (en 35 días) · Recibilo por email →"
// In the first days of a month, once the new report is out: "Nuevo: informe de noviembre 2026 →"
(function () {
  if (/admin\.html$/.test(location.pathname)) return;
  if (document.documentElement.hasAttribute("data-own-app")) return; // the "Mi canasta" page is the app itself: no bar
  var MES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];
  var MON = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  var latest = null;

  function arToday() {  // today's date in Argentina, as [year, monthIndex, day]
    var p = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Argentina/Buenos_Aires" }).format(new Date()).split("-");
    return [+p[0], +p[1] - 1, +p[2]];
  }

  var style = document.createElement("style");
  style.textContent =
    ".lc-bar{background:#2B3B5C;color:#fff;text-align:center;font:600 0.92rem/1.4 'DM Sans',system-ui,sans-serif;padding:0.55rem 1rem}" +
    ".lc-bar a{color:#7FB1C6;text-decoration:underline;text-underline-offset:3px;white-space:nowrap}" +
    ".lc-bar a:hover{color:#fff}.lc-bar .dot{opacity:.6;margin:0 .5rem}";
  document.head.appendChild(style);

  var bar = document.createElement("div");
  bar.className = "lc-bar"; bar.setAttribute("role", "note");
  document.body.insertBefore(bar, document.body.firstChild);

  function render() {
    var es = document.documentElement.lang !== "en";
    var t = arToday(), y = t[0], m = t[1], d = t[2];
    bar.textContent = "";
    var a = document.createElement("a");
    // A new report came out this month (shown from the 1st to the 7th)
    if (latest && d <= 7) {
      var lm = +latest.slice(5) - 1, ly = +latest.slice(0, 4);
      var prev = m === 0 ? [y - 1, 11] : [y, m - 1];
      if (ly === prev[0] && lm === prev[1]) {
        bar.append(es ? "Nuevo: " : "New: ");
        a.href = "informe.html?m=" + latest;
        a.textContent = es ? "informe de " + MES[lm] + " " + ly + " →" : MON[lm] + " " + ly + " report →";
        bar.append(a);
        return;
      }
    }
    // The report on the 1st covers the month that just ended. A month only gets a report if it has
    // at least 20 days of data, so October 2026 (collection started on the 24th) has none: skip it.
    var FIRST = [2026, 9, 24];
    var ry = y, rm = m;  // the month that the next report will cover
    if (ry === FIRST[0] && rm === FIRST[1] && FIRST[2] > 11) { rm += 1; if (rm > 11) { rm = 0; ry += 1; } }
    var ny = rm === 11 ? ry + 1 : ry, nm = (rm + 1) % 12;
    var days = Math.round((Date.UTC(ny, nm, 1) - Date.UTC(y, m, d)) / 864e5);
    var when = es ? (days === 1 ? "mañana" : "en " + days + " días") : (days === 1 ? "tomorrow" : "in " + days + " days");
    var nw = document.createElement("span"); nw.style.whiteSpace = "nowrap"; nw.textContent = "(" + when + ")";
    bar.append(es ? "Próximo informe: 1 de " + MES[nm] + " " : "Next report: 1 " + MON[nm] + " ", nw);
    var dot = document.createElement("span"); dot.className = "dot"; dot.textContent = "·"; bar.append(dot);
    a.href = "/informes.html#suscribirse";
    a.textContent = es ? "Recibilo por email →" : "Get it by email →";
    bar.append(a);
  }

  render();
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  fetch("/index/informes/lista.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : []; }).then(function (l) {
    var ready = (l || []).filter(function (x) { return x.publishable; });
    if (ready.length) { latest = ready[ready.length - 1].month; render(); }
  }).catch(function () {});
})();

// Top menu always fits: if the links do not fit next to the language buttons, the least important ones
// are hidden first; on the homepage the whole menu then turns into the menu button. Works at any width,
// in Spanish and English.
(function () {
  var tb = document.querySelector("header.topbar"); if (!tb) return;
  var nav = tb.querySelector("nav"); if (!nav) return;
  var hasMenu = !!tb.querySelector(".menu-btn");
  var st = document.createElement("style");
  st.textContent = ".lc-hide{display:none!important}" +
    "header.topbar nav{min-width:0;overflow:hidden}header.topbar nav a{white-space:nowrap;flex-shrink:0}" +
    ".topbar.lc-compact .mainnav,.topbar.lc-compact .btn-sub{display:none!important}" +
    ".topbar.lc-compact .head-actions{margin-left:auto}" +
    ".topbar.lc-compact .menu-btn{display:inline-flex!important}";
  document.head.appendChild(st);
  var order = hasMenu ? ["metodo.html", "precios/"] :
    ["metodo.html", "#index", "precios/"];
  function links() { return Array.prototype.slice.call(nav.querySelectorAll("a")); }
  function over() { return nav.scrollWidth > nav.clientWidth + 1; }
  function fit() {
    tb.classList.remove("lc-compact");
    links().forEach(function (a) { a.classList.remove("lc-hide"); });
    if (getComputedStyle(nav).display === "none") return;
    for (var i = 0; i < order.length && over(); i++) {
      links().forEach(function (a) { var h = a.getAttribute("href") || ""; if (h.slice(-order[i].length) === order[i]) a.classList.add("lc-hide"); });
    }
    if (over() && hasMenu) tb.classList.add("lc-compact");
  }
  fit();
  window.addEventListener("resize", fit);
  window.addEventListener("load", fit);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
  try { new MutationObserver(fit).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] }); } catch (e) {}
})();

// App mode: when La Canasta is opened from the phone's home screen (or the App Store app), it looks like an app:
// no website bar or footer, a tab bar at the bottom, and it works offline with the last prices.
(function () {
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
    window.addEventListener("load", function () { navigator.serviceWorker.register("/sw.js").catch(function () {}); });
  }
  var app = /[?&]app=1\b/.test(location.search) || (window.matchMedia && matchMedia("(display-mode: standalone)").matches) || navigator.standalone === true;
  try { if (app) sessionStorage.setItem("lc-app", "1"); else if (sessionStorage.getItem("lc-app") === "1") app = true; } catch (e) {}
  if (!app || document.documentElement.hasAttribute("data-own-app")) return; // the app page has its own tab bar
  document.documentElement.classList.add("lc-app");
  var st = document.createElement("style");
  st.textContent =
    "html.lc-app .lc-bar,html.lc-app footer,html.lc-app .crumbs,html.lc-app header.topbar nav,html.lc-app .btn-sub,html.lc-app .menu-btn,html.lc-app .lang-label,html.lc-app .admin-link{display:none!important}" +
    "html.lc-app header.topbar{padding-top:env(safe-area-inset-top,0px)}" +
    "html.lc-app body{padding-bottom:calc(76px + env(safe-area-inset-bottom,0px))}" +
    ".lc-tabs{position:fixed;left:0;right:0;bottom:0;z-index:50;display:grid;grid-template-columns:repeat(3,1fr);background:rgba(255,255,255,.97);border-top:1px solid #DCE4EA;padding:6px 6px calc(6px + env(safe-area-inset-bottom,0px));backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}" +
    ".lc-tabs a{display:grid;justify-items:center;gap:2px;text-decoration:none;color:#5D6A84;font:600 0.72rem 'DM Sans',system-ui,sans-serif;padding:6px 0;border-radius:12px}" +
    ".lc-tabs a svg{width:24px;height:24px}.lc-tabs a.on{color:#2B3B5C}.lc-tabs a.on svg{color:#D98A2B}";
  document.head.appendChild(st);
  function tabs() {
    var es = document.documentElement.lang !== "en", p = location.pathname;
    // inside the iPhone/Android app the assistant is bundled; prices and index open the live website
    var nat = window.LC_NATIVE === true, site = nat ? "https://lacanastaindex.com" : "";
    var T = [
      [nat ? "/canastas/index.html" : "/canastas/?app=1", es ? "Asistente" : "Assistant", /^\/canastas/.test(p), '<path d="M4 5h16v11H8l-4 4z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><circle cx="9" cy="10.5" r="1.2" fill="currentColor"/><circle cx="12" cy="10.5" r="1.2" fill="currentColor"/><circle cx="15" cy="10.5" r="1.2" fill="currentColor"/>'],
      [site + "/precios/?app=1", es ? "Precios" : "Prices", /^\/precios/.test(p), '<path d="M3 12l9-9h7v7l-9 9z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><circle cx="15.5" cy="8.5" r="1.6" fill="currentColor"/>'],
      [site + "/?app=1#index", es ? "Índice" : "Index", p === "/" || /index\.html$/.test(p), '<path d="M4 19V5M4 19h16M8 15l3-4 3 2 5-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>']
    ];
    var nav = document.querySelector(".lc-tabs") || document.createElement("nav");
    nav.className = "lc-tabs"; nav.setAttribute("aria-label", "App");
    nav.innerHTML = T.map(function (x) { return '<a href="' + x[0] + '"' + (x[2] ? ' class="on" aria-current="page"' : "") + '><svg viewBox="0 0 24 24">' + x[3] + "</svg>" + x[1] + "</a>"; }).join("");
    if (!nav.parentNode) document.body.appendChild(nav);
  }
  if (document.body) tabs(); else document.addEventListener("DOMContentLoaded", tabs);
  new MutationObserver(tabs).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
})();
