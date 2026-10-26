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
