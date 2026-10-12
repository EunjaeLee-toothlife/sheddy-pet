"use strict";
// 24초 주기의 절대 시각으로 360프레임을 렌더링한다. 실시간 녹화의 프레임 누락을 피한다.
const {spawn, execFileSync} = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const {once} = require("node:events");
const {findChrome, serve} = require("./widget_check.js");
const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "output/broadcast/sheddy-just-chatting");
const QA = path.join(OUT, "qa");
const keys = ["lab", "lecture", "cafe", "mountain"];
const selected = process.argv.filter(a=>keys.includes(a));
const scenes = selected.length ? selected : keys;
const qaOnly = process.argv.includes("--qa");
const delay = ms=>new Promise(r=>setTimeout(r,ms));

async function main(){
  fs.mkdirSync(QA,{recursive:true});
  const server=await serve();
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),"sheddy-broadcast-"));
  const chrome=spawn(findChrome(),["--headless=new","--no-first-run","--no-default-browser-check","--remote-debugging-port=0",`--user-data-dir=${profile}`,"--autoplay-policy=no-user-gesture-required","--enable-unsafe-swiftshader","about:blank"],{stdio:["ignore","ignore","pipe"]});
  let stderr="";chrome.stderr.on("data",b=>stderr+=b);
  let ws;
  try{
    let port;
    for(let i=0;i<100;i++){
      const f=path.join(profile,"DevToolsActivePort");
      if(fs.existsSync(f)){port=fs.readFileSync(f,"utf8").split("\n")[0];break;}
      await delay(100);
    }
    if(!port)throw new Error("Chrome 시작 실패: "+stderr.slice(-1000));
    const pages=await fetch(`http://127.0.0.1:${port}/json/list`).then(r=>r.json());
    ws=new WebSocket(pages.find(p=>p.type==="page").webSocketDebuggerUrl);
    await new Promise((resolve,reject)=>{ws.addEventListener("open",resolve,{once:true});ws.addEventListener("error",reject,{once:true});});
    let id=0;const pending=new Map();
    ws.addEventListener("message",e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const {resolve,reject}=pending.get(m.id);pending.delete(m.id);m.error?reject(new Error(m.error.message)):resolve(m.result);}});
    const send=(method,params={})=>new Promise((resolve,reject)=>{pending.set(++id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const r=await send("Runtime.evaluate",{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw new Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result.value;};
    await send("Page.enable");
    await send("Emulation.setDeviceMetricsOverride",{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
    await send("Page.navigate",{url:`http://127.0.0.1:${server.address().port}/tools/broadcast_renderer.html?scene=${scenes[0]}`});
    for(let i=0;i<100;i++){if(await evaluate("Boolean(window.ready)"))break;await delay(100);}
    await evaluate("window.ready");
    const report={width:1920,height:1080,fps:15,duration:24,scenes:{}};
    for(const key of scenes){
      console.log("장면 로드",key);
      await evaluate(`broadcast.loadScene(${JSON.stringify(key)})`);
      for(const [label,t,blink] of [["open",0,0],["half",0,.5],["blink",0,1],["breath",1.5,0]]){
        const data=await evaluate(`broadcast.renderAt(${t},${blink}); broadcast.canvas.toDataURL("image/png").split(",")[1]`);
        fs.writeFileSync(path.join(QA,`${key}-${label}.png`),Buffer.from(data,"base64"));
      }
      const checks=await evaluate(`(()=>{
        const context=broadcast.canvas.getContext('2d');
        const frame=t=>{broadcast.renderAt(t);return new Uint8Array(context.getImageData(0,0,1920,1080).data);};
        const first=frame(0),loop=frame(24),last=frame(24-1/15),moving=frame(1.5);
        let seamMax=0,seamSum=0,movingPixels=0,exact=true;
        for(let i=0;i<first.length;i+=4){
          if(first[i]!==loop[i]||first[i+1]!==loop[i+1]||first[i+2]!==loop[i+2])exact=false;
          const d=Math.max(Math.abs(first[i]-last[i]),Math.abs(first[i+1]-last[i+1]),Math.abs(first[i+2]-last[i+2]));
          seamMax=Math.max(seamMax,d);seamSum+=d;
          if(Math.max(Math.abs(first[i]-moving[i]),Math.abs(first[i+1]-moving[i+1]),Math.abs(first[i+2]-moving[i+2]))>2)movingPixels++;
        }
        return {exactPeriodic:exact,seamMax,seamMean:seamSum/(1920*1080),movingPixels};
      })()`);
      if(!checks.exactPeriodic||checks.movingPixels<1000)throw new Error(key+" 루프/움직임 검사 실패: "+JSON.stringify(checks));
      report.scenes[key]=checks;console.log("루프 검사",key,JSON.stringify(checks));
      if(qaOnly)continue;
      console.log("15fps 렌더링",key);
      const chunks=await evaluate(`(async()=>{
        const config={codec:'vp09.00.40.08',width:1920,height:1080,bitrate:14000000,framerate:15,latencyMode:'realtime'};
        if(!(await VideoEncoder.isConfigSupported(config)).supported)throw new Error('VP9 WebCodecs 인코더 없음');
        const chunks=[];let failure;
        const encoder=new VideoEncoder({output:chunk=>{
          const data=new Uint8Array(chunk.byteLength);chunk.copyTo(data);
          let raw='';for(let i=0;i<data.length;i+=8192)raw+=String.fromCharCode(...data.subarray(i,i+8192));
          chunks.push({timestamp:chunk.timestamp,data:btoa(raw)});
        },error:error=>failure=error});
        encoder.configure(config);
        for(let i=0;i<360;i++){
          if(failure)throw failure;
          broadcast.renderAt(i/15);
          const frame=new VideoFrame(broadcast.canvas,{timestamp:Math.round(i*1000000/15),duration:Math.round(1000000/15)});
          encoder.encode(frame,{keyFrame:i%60===0});frame.close();
          if(encoder.encodeQueueSize>4)await new Promise(r=>encoder.addEventListener('dequeue',r,{once:true}));
        }
        await encoder.flush();encoder.close();if(failure)throw failure;return chunks;
      })()`);
      if(chunks.length!==360)throw new Error(key+" 프레임 수 오류: "+chunks.length);
      const ivf=path.join(QA,key+".ivf"),header=Buffer.alloc(32);
      header.write("DKIF");header.writeUInt16LE(32,6);header.write("VP90",8);header.writeUInt16LE(1920,12);header.writeUInt16LE(1080,14);header.writeUInt32LE(15,16);header.writeUInt32LE(1,20);header.writeUInt32LE(chunks.length,24);
      const fd=fs.openSync(ivf,"w");fs.writeSync(fd,header);
      for(const chunk of chunks){const data=Buffer.from(chunk.data,"base64"),h=Buffer.alloc(12);h.writeUInt32LE(data.length);h.writeBigUInt64LE(BigInt(Math.round(chunk.timestamp*15/1000000)),4);fs.writeSync(fd,h);fs.writeSync(fd,data);}
      fs.closeSync(fd);
      const movie=path.join(OUT,`sheddy-${key}-1080p15.mp4`);
      const ffmpeg=spawn("ffmpeg",["-hide_banner","-loglevel","error","-y","-i",ivf,"-an","-c:v","libx264","-preset","slow","-crf","18","-pix_fmt","yuv420p","-r","15","-movflags","+faststart",movie],{stdio:["ignore","inherit","inherit"]});
      const [code]=await once(ffmpeg,"exit");if(code!==0)throw new Error("ffmpeg 실패: "+key);
      const info=JSON.parse(execFileSync("ffprobe",["-v","error","-count_frames","-show_streams","-show_format","-of","json",movie],{encoding:"utf8"}));
      const video=info.streams.find(s=>s.codec_type==="video");
      if(video.width!==1920||video.height!==1080||video.avg_frame_rate!=="15/1"||Number(video.nb_read_frames)!==360||info.streams.some(s=>s.codec_type==="audio"))throw new Error(key+" 영상 규격 오류");
      report.scenes[key].video={file:path.basename(movie),frames:Number(video.nb_read_frames),duration:Number(info.format.duration),codec:video.codec_name,bytes:Number(info.format.size)};
      fs.unlinkSync(ivf);console.log("완료",key,report.scenes[key].video);
    }
    fs.writeFileSync(path.join(QA,qaOnly?"render-checks.json":"verification.json"),JSON.stringify(report,null,2)+"\n");
  }finally{
    // Chrome 보조 프로세스가 stderr 파이프를 물고 있어도 렌더러가 종료되도록 닫는다.
    ws?.close();chrome.kill();chrome.stderr.destroy();server.close();await delay(300);fs.rmSync(profile,{recursive:true,force:true});
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
