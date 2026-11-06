// La Canasta's AI assistant, for the website and the iPhone/Android app (a Cloudflare Worker).
// The page sends the conversation (instructions + today's catalogue and prices + the person's message) and gets back
// the assistant's JSON answer: {reply, list, add, remove, mode, show}. The page itself works out totals and the
// cheapest shop from the real prices; the AI never writes them.
//
// Set up once (Cloudflare dashboard > Workers & Pages > Create > Worker, paste this file, Deploy):
//   1. Settings > Variables and Secrets > add a SECRET called ANTHROPIC_API_KEY (from console.anthropic.com).
//      Never paste the key anywhere else.
//   2. Copy the worker's address and put it in the website and the app as window.LC_AI_URL
//      (make_canastas_page.py and app/build-www.js read it from the AI_URL constant at the top).
// Cost: a few US cents for every hundred messages. Each visitor can send at most LIMIT messages an hour.

const MODEL = "claude-haiku-5-5";
const LIMIT = 30;                      // messages per visitor per hour
const ORIGINS = ["https://lacanastaindex.com", "https://www.lacanastaindex.com", "capacitor://localhost", "https://localhost", "http://localhost"];
const seen = new Map();                // visitor -> [timestamps] (best effort, per worker instance)

function cors(origin) {
  return { "Access-Control-Allow-Origin": ORIGINS.includes(origin) ? origin : ORIGINS[0], "Access-Control-Allow-Methods": "POST, OPTIONS",
           "Access-Control-Allow-Headers": "content-type", "Vary": "Origin" };
}
const json = (o, status, origin) => new Response(JSON.stringify(o), { status, headers: { "content-type": "application/json", ...cors(origin) } });

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    if (req.method === "OPTIONS") return new Response(null, { headers: cors(origin) });
    if (req.method !== "POST") return json({ error: "POST only" }, 405, origin);
    if (!ORIGINS.includes(origin)) return json({ error: "not allowed" }, 403, origin);
    const who = req.headers.get("CF-Connecting-IP") || "?", now = Date.now();
    const times = (seen.get(who) || []).filter(t => now - t < 3600e3);
    if (times.length >= LIMIT) return json({ error: "rate_limited" }, 429, origin);
    times.push(now); seen.set(who, times);
    const body = await req.text();
    if (body.length > 300000) return json({ error: "too large" }, 413, origin);
    let msgs;
    try { msgs = JSON.parse(body).messages; } catch (e) { return json({ error: "bad request" }, 400, origin); }
    if (!Array.isArray(msgs) || !msgs.length) return json({ error: "bad request" }, 400, origin);
    // the API wants turns that alternate user/assistant: join consecutive turns of the same role
    const turns = [];
    for (const m of msgs) {
      if (!m || (m.role !== "user" && m.role !== "assistant") || typeof m.content !== "string" || !m.content.trim()) continue;
      if (turns.length && turns[turns.length - 1].role === m.role) turns[turns.length - 1].content += "\n\n" + m.content;
      else turns.push({ role: m.role, content: m.content });
    }
    if (!turns.length || turns[0].role !== "user" || turns[turns.length - 1].role !== "user") return json({ error: "bad request" }, 400, origin);
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model: MODEL, max_tokens: 1500, messages: turns }),
    });
    if (!r.ok) return json({ error: "upstream_error" }, 502, origin);
    const out = await r.json();
    const text = (out.content || []).filter(c => c.type === "text").map(c => c.text).join("");
    const a = text.indexOf("{"), b = text.lastIndexOf("}");
    try { return json(JSON.parse(text.slice(a, b + 1)), 200, origin); }
    catch (e) { return json({ error: "invalid_json" }, 502, origin); }
  },
};
