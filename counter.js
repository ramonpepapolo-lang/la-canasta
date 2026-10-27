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
    a.href = "informes.html#suscribirse";
    a.textContent = es ? "Recibilo por email →" : "Get it by email →";
    bar.append(a);
  }

  render();
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  fetch("index/informes/lista.json", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : []; }).then(function (l) {
    var ready = (l || []).filter(function (x) { return x.publishable; });
    if (ready.length) { latest = ready[ready.length - 1].month; render(); }
  }).catch(function () {});
})();
