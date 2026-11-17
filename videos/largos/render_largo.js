const {chromium}=require('playwright');const {spawn}=require('child_process');const fs=require('fs');
const [a,b,name]=[+process.argv[2],+process.argv[3],process.argv[4]];
(async()=>{const fps=30;const br=await chromium.launch();const p=await br.newPage({viewport:{width:1920,height:1080}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto(`http://localhost:${process.env.PORT||8793}/${process.env.PAGE||'semana.html'}`);await p.waitForFunction(()=>window.READY,{timeout:60000});
 const tmp=`parts/${name}.tmp.mp4`;
 const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate','30','-c:v','mjpeg','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-r','30',tmp],{stdio:['pipe','inherit','inherit']});
 for(let i=a;i<b;i++){await p.evaluate(t=>render(t),i/fps);const buf=await p.screenshot({type:'jpeg',quality:92});
  if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));}
 ff.stdin.end();const code=await new Promise(r=>ff.on('close',r));await br.close();
 if(code===0){fs.renameSync(tmp,`parts/${name}.mp4`);console.log('done',name);}else console.log('ffmpeg failed',code);
})();
