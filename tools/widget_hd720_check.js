"use strict";
// 720 기본 경로·반응형 합성·등록된 모든 영상의 실제 위젯 재생을 검사한다.
const { spawn } = require("child_process");
const fs = require("fs"), os = require("os"), path = require("path");
const { findChrome, serve } = require("./widget_check");
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const ROOT = path.join(__dirname, "..");
async function main() {
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "anims/hd720_manifest.json"), "utf8"));
  const prefixIndex = process.argv.indexOf("--prefix");
  const prefix = prefixIndex < 0 ? "" : process.argv[prefixIndex + 1];
  const clips = manifest.clips.filter(clip => clip.clip.startsWith(prefix));
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
    await send("Page.navigate", { url: `http://127.0.0.1:${server.address().port}/widget.html?dice=0` });
    await evaluate(`(async()=>{const until=Date.now()+30000;while((!current||transitioning)&&Date.now()<until)await new Promise(r=>setTimeout(r,20));if(ASSET_SET!=='hd720'||RESOLUTION!==720||vids[front].videoWidth!==720)throw Error('720 기본값 오류');return ASSET_SET;})()`);
    for (const [width, height, dpr, expected] of [[1280,720,1,720], [720,1280,1,720], [320,640,1,320], [1280,720,2,720]]) {
      await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: dpr, mobile: false });
      const value = await evaluate(`fitCanvas();({canvas:[screen.width,screen.height],fit:getComputedStyle(screen).objectFit})`);
      if (value.canvas[0] !== expected || value.canvas[1] !== expected || value.fit !== "contain") throw new Error(`합성 해상도 오류 ${JSON.stringify(value)}`);
      console.log(`PASS canvas ${width}×${height} DPR${dpr} → ${expected}²`);
    }
    const filenames = await evaluate(`Object.values(ANIMS).flatMap(a=>['start','loop','end','outro'].flatMap(p=>a[p]||[])).sort()`);
    if (JSON.stringify(filenames) !== JSON.stringify(manifest.clips.map(c=>path.basename(c.candidate)).sort())) throw new Error("전체 등록 경로 불일치");
    await evaluate("chainGen++; transitioning=true; queued=null; pinnedUntil=Infinity; window.__hdWarnings=[]; console.warn=(...args)=>window.__hdWarnings.push(args.join(' '));");
    for (const clip of clips) {
      const file = path.basename(clip.candidate);
      const result = await evaluate(`(async()=>{
        transitionSince=Date.now();const start=drawCount;
        await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('재생 완료 시간 초과')),20000);
          playClip(${JSON.stringify(file)},{rate:${clip.rate},onEnded:()=>{clearTimeout(timer);resolve();}}).catch(reject);});
        const video=vids[front], pixels=sctx.getImageData(0,0,screen.width,screen.height).data;
        let opaque=0;for(let i=3;i<pixels.length;i+=4)if(pixels[i]>240)opaque++;
        if(video.videoWidth!==720||video.videoHeight!==720||opaque===0||pixels[3]!==0||drawCount===start)throw Error('디코딩/알파/합성 오류');
        return {width:video.videoWidth,height:video.videoHeight,draws:drawCount-start,duration:video.duration};
      })()`);
      if (Math.abs(result.duration - clip.duration) > .002) throw new Error(`재생 길이 변경 ${file}`);
      console.log(`PASS ${clip.clip} ${result.width}² ${result.draws} draws`);
    }
    const warnings = await evaluate("window.__hdWarnings");
    if (warnings.length) throw new Error(warnings.join("\n"));
    console.log(`PASS all ${clips.length} runtime clips${prefix ? ` (${prefix})` : ""}`);
  } finally {
    ws?.close(); chrome.kill(); server.close(); await sleep(500);
    if (profile.startsWith(path.join(os.tmpdir(), "widget-hd720-"))) { try { fs.rmSync(profile, { recursive: true, force: true }); } catch (_) {} }
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
