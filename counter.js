// La Canasta visitor counter (GoatCounter, no cookies).
// When you have your GoatCounter code, put it between the quotes below, e.g. "lacanasta".
var GOATCOUNTER_CODE = "lacanasta";

(function () {
  if (!GOATCOUNTER_CODE) return;
  if (/admin\.html$/.test(location.pathname)) return; // don't count your own admin visits
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://gc.zgo.at/count.js";
  s.setAttribute("data-goatcounter", "https://" + GOATCOUNTER_CODE + ".goatcounter.com/count");
  document.head.appendChild(s);
})();
