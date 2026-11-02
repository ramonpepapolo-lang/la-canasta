// node frames.js <folder> t1 t2 ... : full-size stills, then a contact sheet
const {chromium}=require('playwright');const dir=process.argv[2];const ts=process.argv.slice(3);
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto(`http://localhost:${process.env.PORT||8790}/${dir}/short.html`);await p.waitForFunction(()=>window.READY);
 for(const t of ts){await p.evaluate(t=>render(t),+t);await p.screenshot({path:`${dir}/f_${t}.png`});}
 await b.close();})();
