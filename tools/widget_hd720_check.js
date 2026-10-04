"use strict";
// 반응형 합성·등록된 모든 영상의 실제 재생과 같은 버퍼의 반복 재생을 검사한다.
const { spawn } = require("child_process");
const fs = require("fs"), os = require("os"), path = require("path");
const { findChrome, serve } = require("./widget_check");
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const ROOT = path.join(__dirname, "..");
async function main() {
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "anims/hd720_manifest.json"), "utf8"));
  const prefixIndex = process.argv.indexOf("--prefix");
  const prefix = prefixIndex < 0 ? "" : process.argv[prefixIndex + 1];
  const assetsIndex = process.argv.indexOf("--assets");
  const assets = assetsIndex < 0 ? "hd720" : process.argv[assetsIndex + 1];
  if (!["hd720", "rebuilt", "original"].includes(assets)) throw new Error("알 수 없는 자산 경로");
  const pageIndex = process.argv.indexOf("--page");
  const page = pageIndex < 0 ? "widget.html" : process.argv[pageIndex + 1];
  const fallback = process.argv.includes("--fallback");
  const size = assets === "hd720" ? 720 : 512;
  const endings = process.argv.includes("--endings");
  const rootClips = process.argv.includes("--root") ? new Set(JSON.parse(
    fs.readFileSync(path.join(ROOT, "anims/hd720_root.json"), "utf8")).clips.map(c => c.clip)) : null;
  const clips = manifest.clips.filter(clip => clip.clip.startsWith(prefix) && (!rootClips || rootClips.has(clip.clip)));
  if (!clips.length) throw new Error("검사할 클립이 없습니다.");
  const server = await serve();
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "widget-hd720-"));
  const chrome = spawn(findChrome(), ["--headless=new", "--remote-debugging-port=0", `--user-data-dir=${profile}`,
    "--autoplay-policy=no-user-gesture-required", "--no-first-run", "--no-default-browser-check", "--mute-audio", "about:blank"], { stdio: "ignore" });
  let ws;
  try {
    let port;
    for (let i = 0; i < 80 && !port; i++) {
      await sleep(250);
      try { port = Number(fs.readFileSync(path.join(profile, "DevToolsActivePort"), "utf8").split("\n")[0]); } catch (_) {}
    }
    if (!port) throw new Error("Chrome 기동 실패");
    const target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === "page");
    ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
    let serial = 0; const pending = new Map();
    ws.onmessage = event => { const result = JSON.parse(event.data); if (pending.has(result.id)) { pending.get(result.id)(result); pending.delete(result.id); } };
    const send = (method, params = {}) => new Promise(resolve => { const id = ++serial; pending.set(id, resolve); ws.send(JSON.stringify({ id, method, params })); });
    const evaluate = async expression => {
      const result = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
      if (result.result.exceptionDetails) throw new Error(result.result.exceptionDetails.exception?.description || result.result.exceptionDetails.text);
      return result.result.result.value;
    };
    await send("Page.enable");
    if (fallback) await send("Page.addScriptToEvaluateOnNewDocument", { source: "delete HTMLVideoElement.prototype.requestVideoFrameCallback; delete HTMLVideoElement.prototype.cancelVideoFrameCallback;" });
    await send("Page.navigate", { url: `http://127.0.0.1:${server.address().port}/${page}?dice=0&assets=${assets}` });
    await evaluate(`(async()=>{const until=Date.now()+30000;while((!current||transitioning)&&Date.now()<until)await new Promise(r=>setTimeout(r,20));if(ASSET_SET!==${JSON.stringify(assets)}||RESOLUTION!==720||vids[front].videoWidth!==${size})throw Error('자산 경로/해상도 오류');return ASSET_SET;})()`);
    console.log(`CHECK ${page} assets=${assets} fallback=${fallback} clips=${clips.length}`);
    for (const [width, height, dpr, expected] of [[1280,720,1,720], [720,1280,1,720], [320,640,1,320], [1280,720,2,720]]) {
      await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: dpr, mobile: false });
      const value = await evaluate(`fitCanvas();({canvas:[screen.width,screen.height],fit:getComputedStyle(screen).objectFit})`);
      if (value.canvas[0] !== expected || value.canvas[1] !== expected || value.fit !== "contain") throw new Error(`합성 해상도 오류 ${JSON.stringify(value)}`);
      console.log(`PASS canvas ${width}×${height} DPR${dpr} → ${expected}²`);
    }
    const filenames = await evaluate(`Object.values(ANIMS).flatMap(a=>['start','loop','end','outro'].flatMap(p=>a[p]||[])).sort()`);
    if (JSON.stringify(filenames) !== JSON.stringify(manifest.clips.map(c=>path.basename(c.candidate)).sort())) throw new Error("전체 등록 경로 불일치");
    if (endings) {
      if (assets !== "hd720") throw new Error("--endings는 hd720 상태 전환 검사입니다.");
      // 실제 상태 전환은 그대로 실행하고 원래 playClip에 위임하는 관측기만 붙인다.
      await evaluate(`window.__hdWarnings=[];window.__hdEndingCase=null;
        const hdOriginalWarn=console.warn;
        console.warn=(...args)=>{window.__hdWarnings.push(args.join(' '));hdOriginalWarn.apply(console,args);};
        const hdOriginalPlayClip=playClip;
        playClip=function(file,options={}){
          const record=window.__hdEndingCase;
          if(!record)return hdOriginalPlayClip(file,options);
          record.calls.push(file);
          const startDraws=drawCount;
          return hdOriginalPlayClip(file,{...options,onEnded:function(){
            const video=vids[front],pixels=sctx.getImageData(0,0,screen.width,screen.height).data;
            let opaque=0;for(let i=3;i<pixels.length;i+=4)if(pixels[i]>240)opaque++;
            const corners=[3,(screen.width-1)*4+3,(screen.height-1)*screen.width*4+3,pixels.length-1];
            record.completed.push({file,ended:video.ended,width:video.videoWidth,height:video.videoHeight,
              rate:video.playbackRate,duration:video.duration,time:video.currentTime,error:video.error?.code||null,
              alphaOK:opaque>0&&corners.every(i=>pixels[i]===0),draws:drawCount-startDraws});
            if(options.onEnded)return options.onEnded.apply(this,arguments);
          }});
        };`);
      for (const [state, count] of [["chem1", 3], ["pastry1", 10]]) {
        for (let ending = 1; ending <= count; ending++) {
          const result = await evaluate(`(async()=>{
            const waitFor=async(test,label,ms=20000)=>{const end=Date.now()+ms;
              while(!test()){if(Date.now()>end)throw Error(label+' 시간 초과');await new Promise(r=>setTimeout(r,20));}};
            await waitFor(()=>current==='idle1'&&!transitioning,'초기 idle');
            const initial=vids[front];if(initial.videoWidth!==720||initial.error)throw Error('초기 idle 영상 오류');
            params.set('ending',${ending});
            const record={calls:[],completed:[],warningStart:window.__hdWarnings.length};
            window.__hdEndingCase=record;
            const animation=ANIMS[${JSON.stringify(state)}],rate=animation.rate??1;
            await setState(${JSON.stringify(state)},{pin:false});
            await waitFor(()=>current===${JSON.stringify(state)}&&!transitioning,'loop 진입');
            await waitFor(()=>record.completed.some(e=>e.file===animation.loop),'loop 완주');
            await setState('idle1',{pin:false});
            await waitFor(()=>current==='idle1'&&!transitioning,'idle 복귀');
            await waitFor(()=>record.completed.some(e=>e.file===ANIMS.idle1.loop),'복귀 idle 완주');
            const expected=[animation.start,animation.loop,animation.end[${ending}-1],animation.outro,ANIMS.idle1.loop].filter(Boolean);
            if(JSON.stringify(record.calls)!==JSON.stringify(expected))throw Error('클립 순서 오류 '+JSON.stringify(record.calls));
            for(const file of expected){
              const event=record.completed.find(e=>e.file===file);
              const expectedRate=file===ANIMS.idle1.loop?(ANIMS.idle1.rate??1):rate;
              if(!event||!event.ended||event.error||event.width!==720||event.height!==720||!event.alphaOK||event.draws<=0||
                event.rate!==expectedRate||Math.abs(event.time-event.duration)>.05)throw Error('실제 완주/720/알파 오류 '+file+' '+JSON.stringify(event));
            }
            const warnings=window.__hdWarnings.slice(record.warningStart);if(warnings.length)throw Error(warnings.join('\\n'));
            window.__hdEndingCase=null;
            return {calls:record.calls,completed:record.completed.length,warnings:warnings.length};
          })()`);
          console.log(`PASS ending ${state}/${ending} ${result.calls.join(" -> ")} (${result.completed} ended, warnings ${result.warnings})`);
        }
      }
      console.log("PASS all 13 actual state ending transitions / idle return");
      return;
    }
    if (process.argv.includes("--states")) {
      const modeIndex = process.argv.indexOf("--mode");
      const modes = modeIndex < 0 ? ["", "halloween", "seollal", "christmas", "childrensday", "summer"]
        : [process.argv[modeIndex + 1] === "normal" ? "" : process.argv[modeIndex + 1]];
      if (modes.some(mode=>!["", "halloween", "seollal", "christmas", "childrensday", "summer"].includes(mode))) throw new Error("알 수 없는 검사 모드");
      // 관측기만 추가하고 실제 상태 머신의 반복·종료 콜백은 그대로 호출한다.
      await evaluate(`window.__stateWarnings=[];window.__stateCase=null;
        const stateWarn=console.warn;
        console.warn=(...args)=>{window.__stateWarnings.push(args.join(' '));stateWarn.apply(console,args);};
        const statePlay=playClip;
        playClip=function(file,options={}){
          if(window.__stateCase)window.__stateCase.calls.push(file);
          return statePlay(file,{...options,onEnded:function(){
            const v=vids[front];if(window.__stateCase)window.__stateCase.completed.push({file,ended:v.ended,error:v.error?.code||null,
              width:v.videoWidth,height:v.videoHeight,rate:v.playbackRate,time:v.currentTime,duration:v.duration});
            if(options.onEnded)return options.onEnded.apply(this,arguments);
          }});
        };`);
      let states = 0;
      for (const mode of modes) {
        await evaluate(`(async()=>{window.__stateCase=null;talkActive=false;pinnedUntil=Infinity;
          await switchMode(${JSON.stringify(mode)});
          const until=Date.now()+20000;
          while((modeSwitching||transitioning||current!==DEFAULT_STATE)&&Date.now()<until)await new Promise(r=>setTimeout(r,20));
          if((ACTIVE_MODE||'')!==${JSON.stringify(mode)}||modeSwitching||transitioning||current!==DEFAULT_STATE)throw Error('모드 진입 실패');
        })()`);
        const names = await evaluate("[...Object.keys(ACTIVE_ANIMS).filter(name=>name!==DEFAULT_STATE),DEFAULT_STATE]");
        for (const name of names.filter(name=>name.startsWith(prefix))) {
          const result = await evaluate(`(async()=>{
            const wait=async(test,label)=>{const until=Date.now()+45000;while(!test()){
              if(Date.now()>until)throw Error(label+' 시간 초과');await new Promise(r=>setTimeout(r,20));}};
            const name=${JSON.stringify(name)},animation=ACTIVE_ANIMS[name],start=drawCount;
            const record={calls:[],completed:[]},warningStart=window.__stateWarnings.length;
            window.__stateCase=record;pinnedUntil=Infinity;talkActive=name===TALK_STATE;
            await setState(name,{pin:false});
            await wait(()=>current===name&&!transitioning,'상태 진입 '+name);
            await wait(()=>record.completed.filter(e=>e.file===animation.loop).length>=2,'두 사이클 '+name);
            talkActive=false;pinnedUntil=0;
            await setState(DEFAULT_STATE,{pin:false});
            await wait(()=>current===DEFAULT_STATE&&!transitioning,'대기 복귀 '+name);
            if(name!==DEFAULT_STATE)await wait(()=>record.completed.some(e=>e.file===ACTIVE_ANIMS[DEFAULT_STATE].loop),'복귀 대기 완주 '+name);
            if(record.completed.some(e=>!e.ended||e.error||e.width!==${size}||e.height!==${size}||Math.abs(e.time-e.duration)>.05))throw Error('실제 완주 오류 '+name+' '+JSON.stringify(record)+' warnings='+JSON.stringify(window.__stateWarnings.slice(warningStart)));
            if(record.completed.filter(e=>e.file===animation.loop).some(e=>e.rate!==(animation.rate??1)))throw Error('재생 배율 오류 '+name);
            const expected=[animation.start,animation.loop,
              name!==DEFAULT_STATE&&animation.end&&(Array.isArray(animation.end)?animation.end.find(f=>record.calls.includes(f)):animation.end),
              name!==DEFAULT_STATE&&animation.outro,name!==DEFAULT_STATE&&ACTIVE_ANIMS[DEFAULT_STATE].loop].filter(Boolean);
            if(name!==DEFAULT_STATE&&JSON.stringify(record.calls)!==JSON.stringify(expected))throw Error('전환 순서 오류 '+JSON.stringify(record.calls));
            const warnings=window.__stateWarnings.slice(warningStart);
            if(warnings.length||cacheBytes>CACHE_LIMIT||drawCount===start)throw Error('경고/캐시/그리기 오류 '+warnings.join(' | '));
            window.__stateCase=null;
            return {cycles:record.completed.filter(e=>e.file===animation.loop).length,ended:record.completed.length};
          })()`);
          console.log(`PASS state ${mode || "normal"}/${name} ${result.cycles} cycles / ${result.ended} ended / idle return`);
          states++;
        }
      }
      const warnings = await evaluate("window.__stateWarnings");
      if (warnings.length) throw new Error(warnings.join("\n"));
      console.log(`PASS all ${states} actual states / ${modes.length} modes (${assets}${fallback ? ", fallback" : ""})`);
      return;
    }
    await evaluate("chainGen++; transitioning=true; queued=null; pinnedUntil=Infinity; window.__hdWarnings=[]; console.warn=(...args)=>window.__hdWarnings.push(args.join(' '));");
    for (const clip of clips) {
      const file = path.basename(clip.candidate);
      const result = await evaluate(`(async()=>{
        transitionSince=Date.now();const start=drawCount;
        let cycles=0,lastProgress=performance.now(),lastDraw=drawCount,maxGap=0,mediaErrors=0;
        const monitor=setInterval(()=>{
          const now=performance.now();
          if(drawCount!==lastDraw){maxGap=Math.max(maxGap,now-lastProgress);lastProgress=now;lastDraw=drawCount;}
          if(vids[front].error)mediaErrors++;
        },50);
        try {
          await new Promise((resolve,reject)=>{
            const timer=setTimeout(()=>reject(Error('두 사이클 완료 시간 초과')),${Math.ceil(clip.duration / clip.rate * 2000 + 10000)});
            const fail=error=>{clearTimeout(timer);reject(error);};
            playClip(${JSON.stringify(file)},{rate:${clip.rate},onEnded:()=>{
              const video=vids[front];
              if(!video.ended||video.error||Math.abs(video.currentTime-video.duration)>.05)return fail(Error('실제 ended 없이 완료됨'));
              if(++cycles===2){clearTimeout(timer);resolve();return;}
              transitionSince=Date.now();video.currentTime=0;video.play().catch(fail);
            }}).catch(fail);
          });
        } finally {clearInterval(monitor);}
        const video=vids[front], pixels=sctx.getImageData(0,0,screen.width,screen.height).data;
        let opaque=0;for(let i=3;i<pixels.length;i+=4)if(pixels[i]>240)opaque++;
        const corners=[3,(screen.width-1)*4+3,(screen.height-1)*screen.width*4+3,pixels.length-1];
        if(video.videoWidth!==${size}||video.videoHeight!==${size}||opaque===0||corners.some(i=>pixels[i]!==0)||drawCount===start||mediaErrors)throw Error('디코딩/알파/합성 오류');
        if(video.playbackRate!==${clip.rate}||maxGap>1500)throw Error('재생 배율/그리기 지연 오류 '+maxGap);
        if(cacheBytes>CACHE_LIMIT)throw Error('캐시 상한 초과');
        return {width:video.videoWidth,height:video.videoHeight,draws:drawCount-start,duration:video.duration,cycles,maxGap:Math.round(maxGap)};
      })()`);
      if (Math.abs(result.duration - clip.duration) > .002) throw new Error(`재생 길이 변경 ${file}`);
      console.log(`PASS ${clip.clip} ${result.width}² ${result.cycles} cycles ${result.draws} draws maxGap=${result.maxGap}ms`);
    }
    const warnings = await evaluate("window.__hdWarnings");
    if (warnings.length) throw new Error(warnings.join("\n"));
    console.log(`PASS all ${clips.length} runtime clips / ${clips.length * 2} ended (${assets}${fallback ? ", fallback" : ""})${prefix ? ` (${prefix})` : ""}`);
  } finally {
    ws?.close(); chrome.kill(); server.close(); await sleep(500);
    if (profile.startsWith(path.join(os.tmpdir(), "widget-hd720-"))) { try { fs.rmSync(profile, { recursive: true, force: true }); } catch (_) {} }
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
