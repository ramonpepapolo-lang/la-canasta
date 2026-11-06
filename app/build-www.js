// Builds app/www (what goes inside the iPhone and Android app) from app/src/app.html, the app's own screens.
// The app keeps everything inside it (screens, logo, fonts), so it opens instantly and offline. Prices come
// from lacanastaindex.com every time there is signal (window.LC_NATIVE), with the copy bundled here as a fallback.
// Run: node build-www.js   (then: npx cap sync)
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), WWW = path.join(__dirname, "www");
// the AI assistant (app/ai-worker.js on Cloudflare): its address once it is set up; empty = the built-in assistant answers
const AI_URL = "";
fs.rmSync(WWW, { recursive: true, force: true });
const cp = (from, to) => { const t = path.join(WWW, to || from); fs.mkdirSync(path.dirname(t), { recursive: true }); fs.copyFileSync(path.join(ROOT, from), t); };
// data the app reads (fallback copy) and the logo
["app-datos/datos.json", "canastas/datos.json", "canastas/catalogo.json",
 "la-canasta-logo/la-canasta-logo-horizontal.svg", "la-canasta-logo/la-canasta-logo-horizontal-white.svg",
 "la-canasta-logo/la-canasta-logo-stacked.svg", "la-canasta-logo/la-canasta-icon.svg"].forEach(f => cp(f));
// fonts inside the app, so it looks the same without signal
const FONTS = { "400": "dm-sans-latin-400-normal.woff2", "500 600": "dm-sans-latin-600-normal.woff2", "700": "dm-sans-latin-700-normal.woff2" };
Object.values(FONTS).concat(["dm-serif-display-latin-400-normal.woff2"]).forEach(f => cp(path.join("videos", "assets", f), path.join("fonts", f)));
const face = Object.entries(FONTS).map(([w, f]) => `@font-face{font-family:"DM Sans";font-weight:${w};font-display:swap;src:url(fonts/${f}) format("woff2")}`).join("\n")
  + `\n@font-face{font-family:"DM Serif Display";font-weight:400;font-display:swap;src:url(fonts/dm-serif-display-latin-400-normal.woff2) format("woff2")}`;
let app = fs.readFileSync(path.join(__dirname, "src", "app.html"), "utf8");
const before = app.length;
app = app.replace(/<link rel="preconnect"[^>]*>\s*<link rel="stylesheet" href="https:\/\/fonts\.googleapis\.com[^>]*>/, `<style>\n${face}\n</style>`);
if (app.length === before) throw new Error("Google Fonts link not found in app/src/app.html: update build-www.js");
const html = `<!doctype html>
<html lang="es" class="native">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<meta name="theme-color" content="#FFFFFF">
<script>window.LC_NATIVE = true;${AI_URL ? " window.LC_AI_URL = " + JSON.stringify(AI_URL) + ";" : ""}</script>
<style>[hidden]{display:none!important}</style>
${app}
</html>
`;
fs.writeFileSync(path.join(WWW, "index.html"), html);
console.log("app/www built from app/src/app.html, data of", JSON.parse(fs.readFileSync(path.join(ROOT, "app-datos/datos.json"))).date);
