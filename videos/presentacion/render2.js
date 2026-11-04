// node render2.js <folder> : films <folder>/short.html at 30 fps into <folder>/raw.mp4 (with voice). wide-* folders are 1920x1080.
const {chromium}=require('playwright');const {spawn}=require('child_process');const fs=require('fs');
const dir=process.argv[2];const wide=dir.includes('wide-');
(async()=>{const fps=30;const b=await chromium.launch();const p=await b.newPage({viewport:wide?{width:1920,height:1080}:{width:1080,height:1920}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto(`http://localhost:${process.env.PORT||8790}/${dir}/short.html`);await p.waitForFunction(()=>window.READY,{timeout:60000});
 const total=await p.evaluate(()=>TOTAL),N=Math.round(total*fps);
 const tmp=`${dir}/raw.tmp.mp4`;
 const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-','-i',`${dir}/voice.wav`,
  '-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000','-shortest','-movflags','+faststart',tmp],{stdio:['pipe','inherit','inherit']});
 const t0=Date.now();
 for(let i=0;i<N;i++){await p.evaluate(t=>render(t),i/fps);const buf=await p.screenshot({type:'jpeg',quality:92});
  if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));
  if(i%600===0)console.log(dir,i,'/',N,Math.round((Date.now()-t0)/1000)+'s');}
 ff.stdin.end();const code=await new Promise(r=>ff.on('close',r));await b.close();
 if(code===0){fs.renameSync(tmp,`${dir}/raw.mp4`);console.log('done',dir,N,'frames',Math.round((Date.now()-t0)/1000)+'s');}else console.log('ffmpeg failed',code);
})();
