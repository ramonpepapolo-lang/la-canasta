// La Canasta: live numbers for the admin page (Cloudflare Worker, free).
//
// Why this exists: the admin page is a public web page, so it can't hold secret keys.
// This tiny worker keeps the keys secret and only ever answers with a few NUMBERS:
//   { "subscribers": 6, "visits": { "total": 412, "today": 37, "pages": { "/": 250, ... } } }
// Never any emails or personal data.
//   - Subscribers come live from Brevo.
//   - Visits come live from GoatCounter's API (the public counter only refreshes every ~4 hours).
//
// Setup (about 10 minutes):
//   1. Make a free account at dash.cloudflare.com
//   2. Workers & Pages > Create > Create Worker > name it "la-canasta-admin" > Deploy
//   3. Edit code > delete everything > paste this whole file > Deploy
//   4. Settings > Variables and Secrets > add these SECRETS:
//        BREVO_API_KEY      = your Brevo API key (Brevo > SMTP y API > API keys)
//        BREVO_LIST_ID      = 3
//        GOATCOUNTER_TOKEN  = a GoatCounter API token with "Read statistics" permission
//   5. Copy the worker's address (like https://la-canasta-admin.YOURNAME.workers.dev)
//      and put it in admin.html, in ADMIN_WORKER_URL.

const ALLOWED = ["https://lacanastaindex.com", "https://www.lacanastaindex.com"];
const GOATCOUNTER_SITE = "https://lacanasta.goatcounter.com";
const START = "2026-10-24";

function madridToday() {
  // Today's date in Spain, as YYYY-MM-DD (en-CA formats dates that way)
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Madrid" }).format(new Date());
}

async function goat(env, path) {
  const res = await fetch(GOATCOUNTER_SITE + "/api/v0" + path, {
    headers: { Authorization: "Bearer " + env.GOATCOUNTER_TOKEN, "Content-Type": "application/json" }
  });
  if (!res.ok) throw new Error("goatcounter " + res.status);
  return res.json();
}

async function visits(env) {
  if (!env.GOATCOUNTER_TOKEN) return null;
  const tomorrow = new Date(Date.now() + 864e5).toISOString().slice(0, 10);
  const today = madridToday();
  const out = {};
  try { out.total = (await goat(env, `/stats/total?start=${START}&end=${tomorrow}`)).total; } catch (e) { out.error = String(e); }
  try { out.today = (await goat(env, `/stats/total?start=${today}&end=${tomorrow}`)).total; } catch (e) {}
  try {
    const hits = await goat(env, `/stats/hits?start=${START}&end=${tomorrow}&limit=20`);
    out.pages = {};
    for (const h of hits.hits || []) out.pages[h.path] = h.count;
  } catch (e) {}
  return out;
}

async function subscribers(env) {
  if (!env.BREVO_API_KEY || !env.BREVO_LIST_ID) return null;
  const res = await fetch("https://api.brevo.com/v3/contacts/lists/" + parseInt(env.BREVO_LIST_ID, 10), {
    headers: { "api-key": env.BREVO_API_KEY, accept: "application/json" }
  });
  if (!res.ok) return null;
  const info = await res.json();
  return info.uniqueSubscribers ?? info.totalSubscribers ?? null;
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const headers = {
      "Access-Control-Allow-Origin": ALLOWED.includes(origin) ? origin : ALLOWED[0],
      "Cache-Control": "no-store",
      "Content-Type": "application/json"
    };
    const [s, v] = await Promise.all([subscribers(env).catch(() => null), visits(env).catch(() => null)]);
    return new Response(JSON.stringify({ subscribers: s, visits: v }), { headers });
  }
};
