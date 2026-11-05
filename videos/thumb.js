// node thumb.js <video.mp4> <out.jpg> [AAAA-MM-DD]
// Official thumbnail for a Short: the video's own cover (second 0.3) with the La Canasta logo on top
// and the site, the handle and the date of the prices at the bottom. 1080x1920 JPEG.
const { chromium } = require("playwright");
const { execFileSync } = require("child_process");
const fs = require("fs"), path = require("path"), os = require("os");
const [video, out, date] = process.argv.slice(2);
if (!video || !out) { console.log("usage: node thumb.js video.mp4 out.jpg [AAAA-MM-DD]"); process.exit(1); }
const H = __dirname, ROOT = path.join(H, "..");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "lc-thumb-"));
const frame = path.join(tmp, "f.png");
execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-ss", "0.3", "-i", video, "-frames:v", "1", frame]);
const b64 = f => fs.readFileSync(f).toString("base64");
const font = n => `url(data:font/woff2;base64,${b64(path.join(H, "assets", n))})`;
const MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
let when = "";
if (date) { const [y, m, d] = date.split("-").map(Number); when = `Precios del ${d} de ${MES[m - 1]} de ${y}`; }
const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:S;font-weight:700;src:${font("dm-sans-latin-700-normal.woff2")}}
@font-face{font-family:S;font-weight:600;src:${font("dm-sans-latin-600-normal.woff2")}}
*{margin:0;box-sizing:border-box}html,body{width:1080px;height:1920px;overflow:hidden}
body{background:url(data:image/png;base64,${b64(frame)}) center/cover;font-family:S;position:relative}
.top{position:absolute;left:0;right:0;top:0;height:300px;display:flex;align-items:flex-start;justify-content:center;padding-top:70px;
 background:linear-gradient(180deg,rgba(14,25,48,.55),rgba(14,25,48,0))}
.pill{background:#fff;border-radius:999px;padding:20px 46px;box-shadow:0 18px 40px rgba(0,0,0,.35);display:flex;align-items:center}
.pill img{height:92px;display:block}
.bot{position:absolute;left:0;right:0;bottom:0;padding:0 60px 80px;display:grid;gap:18px;justify-items:center;
 background:linear-gradient(0deg,rgba(14,25,48,.85) 0%,rgba(14,25,48,.55) 60%,rgba(14,25,48,0) 100%);padding-top:140px}
.site{background:#E09A3A;color:#1A1206;font-weight:700;font-size:50px;border-radius:999px;padding:14px 44px;letter-spacing:-.5px}
.row{display:flex;gap:26px;align-items:center;color:#fff;font-weight:600;font-size:34px;opacity:.95}
.row i{width:10px;height:10px;border-radius:50%;background:#7FB1C6;display:inline-block}
</style></head><body>
<div class="top"><div class="pill"><img src="data:image/png;base64,${b64(path.join(ROOT, "la-canasta-logo", "la-canasta-logo-horizontal.png"))}"></div></div>
<div class="bot"><div class="site">lacanastaindex.com</div><div class="row"><span>@LaCanastaIndex</span>${when ? `<i></i><span>${when}</span>` : ""}</div></div>
</body></html>`;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.setContent(html, { waitUntil: "load" }); await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: out, type: "jpeg", quality: 92 });
  await b.close(); fs.rmSync(tmp, { recursive: true, force: true });
  console.log("thumbnail", out);
})();
