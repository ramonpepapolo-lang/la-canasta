// Builds app/www (what goes inside the iPhone and Android app) from the website's assistant page.
// The app keeps the page inside it, so it opens instantly and offline; prices come from lacanastaindex.com
// every time there is signal, with the copy bundled at build time as a fallback.
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, ".."), WWW = path.join(__dirname, "www"), SITE = "https://lacanastaindex.com";
fs.rmSync(WWW, { recursive: true, force: true });
fs.mkdirSync(path.join(WWW, "canastas"), { recursive: true });
const cp = (from, to) => { fs.mkdirSync(path.dirname(path.join(WWW, to)), { recursive: true }); fs.copyFileSync(path.join(ROOT, from), path.join(WWW, to)); };
// assets used by the page
["la-canasta-logo/la-canasta-logo-horizontal.svg", "la-canasta-logo/la-canasta-logo-horizontal-white.svg", "la-canasta-logo/la-canasta-icon.svg",
 "la-canasta-logo/la-canasta-icon-32.png", "app-icons/icon-180.png", "app-icons/icon-192.png", "counter.js", "canastas/datos.json", "canastas/catalogo.json"].forEach(f => cp(f, f));
let html = fs.readFileSync(path.join(ROOT, "canastas", "index.html"), "utf8");
// links to other pages of the site open the live website; local assets stay local
html = html.replace(/(href)="\.\.\/((?!la-canasta-logo|app-icons|counter\.js)[^"]*)"/g, (m, a, p) => `${a}="${SITE}/${p}"`);
html = html.replace(/href="\/(informes\.html[^"]*)"/g, `href="${SITE}/$1"`);
html = html.replace('<link rel="manifest" href="/manifest.webmanifest">', "");
// app mode from the first frame, and today's prices from the website (bundled copy if offline)
html = html.replace("<head>", `<head>\n<script>try{sessionStorage.setItem("lc-app","1")}catch(e){}document.documentElement.classList.add("lc-app");window.LC_NATIVE=true;</script>`);
html = html.replace('fetch("datos.json", { cache: "no-store" }).then(r => r.json())',
  `fetch("${SITE}/canastas/datos.json", { cache: "no-store" }).then(r => { if (!r.ok) throw 0; return r.json(); }).catch(() => fetch("datos.json").then(r => r.json()))`);
html = html.replace('fetch("catalogo.json", { cache: "no-store" }).then(r => r.json())',
  `fetch("${SITE}/canastas/catalogo.json", { cache: "no-store" }).then(r => { if (!r.ok) throw 0; return r.json(); }).catch(() => fetch("catalogo.json").then(r => r.json()))`);
if (!html.includes(`${SITE}/canastas/datos.json`)) throw new Error("datos.json fetch not found: update build-www.js");
fs.writeFileSync(path.join(WWW, "canastas", "index.html"), html);
fs.writeFileSync(path.join(WWW, "index.html"), '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=canastas/index.html"><script>location.replace("canastas/index.html")</script>');
console.log("app/www built from canastas/index.html, data of", JSON.parse(fs.readFileSync(path.join(ROOT, "canastas/datos.json"))).date);
