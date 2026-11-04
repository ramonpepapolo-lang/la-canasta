const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const c = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const p = await c.newPage();
  const out = process.argv[2];
  const shots = [
    ["index.html", "home", 0], ["index.html", "home-chart", 900], ["index.html", "rank", "#shops"], ["index.html", "basket", "#basket"],
    ["precios/leche.html", "leche", 0], ["informes.html", "informes", 0], ["index.html", "data", "#data"], ["metodo.html", "metodo", 0]
  ];
  for (const [pg, name, y] of shots) {
    await p.goto(`http://localhost:8766/${pg}`, { waitUntil: "networkidle" }); await p.waitForTimeout(1500);
    if (typeof y === "string") { await p.evaluate(s => { const e = document.querySelector(s); window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - 90); }, y); }
    else await p.evaluate(v => window.scrollTo(0, v), y);
    await p.waitForTimeout(900);
    await p.screenshot({ path: `${out}/${name}.jpg`, type: "jpeg", quality: 92 });
  }
  await b.close();
})();
