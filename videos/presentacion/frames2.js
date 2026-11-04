// node frames2.js <folder> t1 t2 ... : stills at the folder's size (wide-* folders are 1920x1080)
const {chromium}=require('playwright');const dir=process.argv[2];const ts=process.argv.slice(3);
const wide=dir.includes('wide-');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:wide?{width:1920,height:1080}:{width:1080,height:1920}});p.on('pageerror',e=>console.log('ERR',e.message));p.on('console',m=>{if(m.type()==='error')console.log('CONSOLE',m.text())});
 await p.goto(`http://localhost:${process.env.PORT||8790}/${dir}/short.html`);await p.waitForFunction(()=>window.READY,{timeout:30000});
 for(const t of ts){await p.evaluate(t=>render(t),+t);await p.screenshot({path:`${dir}/f_${t}.png`});}
 await b.close();})();
