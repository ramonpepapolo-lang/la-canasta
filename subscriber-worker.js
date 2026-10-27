// La Canasta: live subscriber count for the admin page (Cloudflare Worker, free).
//
// Why this exists: the admin page can't ask Brevo directly, because that would put
// the Brevo API key inside a public web page. This tiny worker keeps the key secret
// and only ever answers with ONE number: { "subscribers": 6 }. Never any emails.
//
// Setup (about 5 minutes):
//   1. Make a free account at dash.cloudflare.com
//   2. Workers & Pages > Create > Create Worker > name it "la-canasta-subs" > Deploy
//   3. Edit code > delete everything > paste this whole file > Deploy
//   4. Settings > Variables and Secrets > add two SECRETS:
//        BREVO_API_KEY  = your Brevo API key (Brevo > SMTP & API > API keys)
//        BREVO_LIST_ID  = the same list number you put in GitHub
//   5. Copy the worker's address (like https://la-canasta-subs.YOURNAME.workers.dev)
//      and paste it into admin.html, in SUBS_LIVE_URL.

const ALLOWED = ["https://lacanastaindex.com", "https://www.lacanastaindex.com"];

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const headers = {
      "Access-Control-Allow-Origin": ALLOWED.includes(origin) ? origin : ALLOWED[0],
      "Cache-Control": "no-store",
      "Content-Type": "application/json"
    };
    if (!env.BREVO_API_KEY || !env.BREVO_LIST_ID) {
      return new Response(JSON.stringify({ error: "missing secrets" }), { status: 500, headers });
    }
    const res = await fetch("https://api.brevo.com/v3/contacts/lists/" + parseInt(env.BREVO_LIST_ID, 10), {
      headers: { "api-key": env.BREVO_API_KEY, accept: "application/json" }
    });
    if (!res.ok) {
      return new Response(JSON.stringify({ error: "brevo " + res.status }), { status: 502, headers });
    }
    const info = await res.json();
    const n = info.uniqueSubscribers ?? info.totalSubscribers;
    return new Response(JSON.stringify({ subscribers: n }), { headers });
  }
};
