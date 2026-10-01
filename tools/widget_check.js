"use strict";
/* 위젯 상태 머신 회귀 검사 — 헤드리스 Chrome을 CDP로 직접 구동한다 (의존성 없음, Node 22+).

   usage: node tools/widget_check.js [--page widget.html]
   Chrome/Edge를 자동으로 찾는다. 다른 경로는 CHROME_PATH 환경변수로 지정.

   왜 헤드리스인가: 가려진 탭(document.hidden)에서는 Chromium이 음소거 영상을 스스로
   일시정지하고 rAF/rVFC도 돌지 않아 재생·전환을 검증할 수 없다. --headless=new 는
   페이지를 visible로 취급하므로 실제 OBS/브라우저와 같은 경로를 탄다.

   검사 항목
     cycles      loop 사이클이 ended 이벤트로 즉시 이어지는가 (워치독이 대신 굴리지 않는가)
     transitions start → loop → end(→ outro) → idle 순서가 지켜지는가
     queuedTalk  전환 중 큐에 들어간 talk가 pin을 걸지 않고, 깜박임·지연 없이 시작하는가
     holdQueue   '계속 유지' 중 큐를 거친 모션이 무기한 pin을 잃지 않는가
     staleChain  워치독 리셋 뒤 버려진 전환 체인이 되살아나 상태를 덮어쓰지 않는가 */
const { spawn, execFileSync } = require("child_process");
const fs = require("fs");
const http = require("http");
const os = require("os");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const argv = process.argv.slice(2);
const PAGE = argv.includes("--page") ? argv[argv.indexOf("--page") + 1] : "widget.html";
const BENCHMARK = argv.includes("--benchmark");
const BASELINE = argv.includes("--baseline");
const FALLBACK = argv.includes("--fallback");
const baselineHTML = BASELINE ? execFileSync("git", ["show", "HEAD:widget.html"], { cwd: ROOT }) : null;
const sleep = ms => new Promise(r => setTimeout(r, ms));

function findChrome() {
  const pf = process.env.ProgramFiles || "", pf86 = process.env["ProgramFiles(x86)"] || "";
  const local = process.env.LOCALAPPDATA || "";
  return [
    process.env.CHROME_PATH,
    path.join(pf, "Google/Chrome/Application/chrome.exe"),
    path.join(pf86, "Google/Chrome/Application/chrome.exe"),
    path.join(local, "Google/Chrome/Application/chrome.exe"),
    path.join(pf86, "Microsoft/Edge/Application/msedge.exe"),
    path.join(pf, "Microsoft/Edge/Application/msedge.exe"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
  ].find(p => p && fs.existsSync(p));
}

// 저장소 루트를 서빙하는 최소 정적 서버 (webm 탐색 재생을 위해 Range 지원)
function serve() {
  const TYPES = { ".html": "text/html; charset=utf-8", ".webm": "video/webm", ".png": "image/png", ".jpg": "image/jpeg", ".json": "application/json" };
  const server = http.createServer((req, res) => {
    const file = path.normalize(path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname)));
    if (baselineHTML && file === path.join(ROOT, "widget.html")) {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Content-Length": baselineHTML.length });
      res.end(baselineHTML); return;
    }
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
    const size = fs.statSync(file).size;
    const head = { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream", "Accept-Ranges": "bytes" };
    const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || "");
    if (m) {
      const start = m[1] ? Number(m[1]) : 0, end = m[2] ? Math.min(Number(m[2]), size - 1) : size - 1;
      res.writeHead(206, { ...head, "Content-Range": `bytes ${start}-${end}/${size}`, "Content-Length": end - start + 1 });
      fs.createReadStream(file, { start, end }).pipe(res);
    } else {
      res.writeHead(200, { ...head, "Content-Length": size });
      fs.createReadStream(file).pipe(res);
    }
  });
  return new Promise(res => server.listen(0, "127.0.0.1", () => res(server)));
}

// ── 페이지 안에서 실행되는 검사 본문 ───────────────────────────
// widget.html의 최상위 let/const(current, transitioning, vids, …)는 같은 realm의 평가 코드에서 보인다.
const IN_PAGE = async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const waitFor = async (pred, ms, what) => {
    const t0 = performance.now();
    while (!pred()) { if (performance.now() - t0 > ms) throw new Error("timeout: " + what); await sleep(10); }
  };
  const idle = () => current === "idle1" && !transitioning;
  const toIdle = async () => { if (!idle()) { talkActive = false; pinnedUntil = 0; setState("idle1", { pin: false }); } await waitFor(idle, 30000, "idle"); };
  const nameOf = src => { for (const [f, u] of CLIP_URL) if (u === src) return f.replace(/^anim_|\.webm$/g, ""); return src.split("/").pop(); };
  const warns = []; const ow = console.warn;
  console.warn = (...a) => { warns.push(a.map(String).join(" ")); ow.apply(console, a); };
  const results = [];
  const check = async (name, fn) => {
    const w0 = warns.length;
    try { await toIdle(); const detail = await fn(w0); results.push({ name, ok: true, detail }); }
    catch (e) { results.push({ name, ok: false, detail: e.message }); }
  };
  const expect = (cond, msg) => { if (!cond) throw new Error(msg); };

  await waitFor(idle, 30000, "initial idle");
  await waitFor(() => CLIP_URL.size > 0 && !document.hidden, 30000, "preload / visible page");
  await sleep(1500); // 선로딩 마무리

  await check("renderBudget", async () => {
    const before = drawCount;
    await sleep(3000);
    const draws = drawCount - before;
    expect(draws > 5 && draws < 110, `3초 그리기 횟수 이상: ${draws}`);
    expect(Math.max(screen.width, screen.height) <= RESOLUTION, "캔버스 해상도 상한 초과");
    return `3초 ${draws}회, ${screen.width}×${screen.height}`;
  });

  await check("newReactions", async () => {
    for (const name of ["clap1", "heart1", "surprise1"]) {
      setPetState(name);
      await waitFor(() => current === name && !transitioning, 10000, name);
      await sleep(750);
      const corner = sctx.getImageData(0, 0, 1, 1).data[3];
      const body = sctx.getImageData(Math.floor(screen.width / 2), Math.floor(screen.height * 0.55), 1, 1).data[3];
      expect(corner === 0 && body === 255, `${name} 배경/몸통 알파 이상: ${corner}/${body}`);
      if (window.__captureReactions) window.__captureReactions.push({ name, png: screen.toDataURL() });
      await waitFor(idle, 10000, name + " 단발 복귀");
    }
    motionHold.checked = true;
    try {
      pickMotion("clap1");
      await waitFor(() => current === "clap1" && !transitioning, 10000, "clap1 유지");
      await sleep(4000);
      expect(current === "clap1" && pinnedUntil === Infinity, "반응 모션 유지 실패");
    } finally { motionHold.checked = false; pinnedUntil = 0; }
    return "3개 모션 단발 복귀 + 박수 계속 유지";
  });

  await check("visibility", async w0 => {
    const visibility = visible => window.dispatchEvent(new CustomEvent("obsSourceVisibleChanged", { detail: { visible } }));
    setPetState("happy1");
    await waitFor(() => transitioning && nameOf(vids[front].src) === "happy1_start" && vids[front].currentTime > 0.1, 5000, "전환 시작");
    const v = vids[front];
    visibility(false);
    const time = v.currentTime, draws = drawCount;
    const oldSince = transitionSince;
    transitionSince = Date.now() - 60000;
    try {
      setPetState("heart1");
      await sleep(1300);
      expect(suspended && vids.every(v => v.paused), "숨김 상태 비디오 재생");
      expect(drawCount === draws && Math.abs(v.currentTime - time) < 0.05, "숨김 상태 렌더/시간 진행");
      expect(!warns.slice(w0).some(w => w.includes("watchdog")), "숨김 중 워치독 오작동");
      expect(queued?.name === "heart1", "숨김 중 명령 유실");
    } finally { transitionSince = oldSince; visibility(true); }
    await waitFor(() => current === "heart1" && !transitioning, 15000, "숨김 복귀 후 큐 실행");
    await waitFor(idle, 10000, "반응 후 idle");
    return "숨김 중 draw/재생 0, 전환과 큐 복구";
  });

  await check("cacheBudget", async () => {
    const file = ANIMS.chem1.loop;
    const cached = CLIP_URL.has(file);
    const a = loadClip(file), b = loadClip(file);
    if (!cached) expect(a === b, "진행 중인 같은 클립의 fetch가 합쳐지지 않음");
    expect(await a === await b, "같은 클립 중복 URL");
    const files = [...new Set(Object.values(ANIMS).flatMap(a => [a.start, a.loop, a.outro, ...(Array.isArray(a.end) ? a.end : [a.end])]).filter(Boolean))];
    let maxLoads = 0;
    const timer = setInterval(() => { maxLoads = Math.max(maxLoads, activeLoads); }, 1);
    try { await Promise.all(files.map(loadClip)); } finally { clearInterval(timer); }
    expect(maxLoads <= 2 && cacheBytes <= CACHE_LIMIT, `캐시/동시 요청 상한 초과: ${cacheBytes}/${maxLoads}`);
    expect(CLIP_URL.size < files.length && cacheBytes > 0, "LRU 퇴출이 동작하지 않음");
    return `${CLIP_URL.size}/${files.length}클립, ${cacheBytes}바이트, 동시 요청 ${maxLoads}`;
  });

  await check("pausePendingPlay", async w0 => {
    const visibility = visible => window.dispatchEvent(new CustomEvent("obsSourceVisibleChanged", { detail: { visible } }));
    const v = backVid();
    const hideOnPlay = () => visibility(false);
    v.addEventListener("play", hideOnPlay, { once: true });
    try {
      setPetState("happy2");
      await waitFor(() => suspended, 10000, "play 직후 숨김");
      await sleep(400);
      expect(!warns.slice(w0).some(w => w.includes("play failed")), "숨김의 정상 재생 취소를 클립 실패로 처리");
    } finally {
      v.removeEventListener("play", hideOnPlay);
      visibility(true);
    }
    await waitFor(() => current === "happy2" && !transitioning && !vids[front].paused && vids[front].currentTime > 0.1, 10000, "미완료 play 복구");
    return "play 완료 전 숨김/복귀 정상";
  });

  await check("cycles", async w0 => {
    const gaps = []; let endedAt = null;
    const onEnded = () => { endedAt = performance.now(); };
    const onPlaying = () => { if (endedAt !== null) { gaps.push(Math.round(performance.now() - endedAt)); endedAt = null; } };
    for (const v of vids) { v.addEventListener("ended", onEnded); v.addEventListener("playing", onPlaying); }
    await sleep(7500);
    for (const v of vids) { v.removeEventListener("ended", onEnded); v.removeEventListener("playing", onPlaying); }
    expect(gaps.length >= 3, `사이클이 돌지 않음 (재시작 ${gaps.length}회)`);
    expect(Math.max(...gaps) < 80, `사이클 재시작 지연 ${JSON.stringify(gaps)}ms — ended 이벤트가 아니라 워치독이 굴리는 중`);
    expect(!warns.slice(w0).some(w => w.includes("watchdog")), "워치독 경고 발생: " + warns.slice(w0)[0]);
    return `재시작 지연 ${JSON.stringify(gaps)}ms`;
  });

  await check("transitions", async () => {
    const seq = [];
    const onPlaying = e => { const n = nameOf(e.target.src); if (seq[seq.length - 1] !== n) seq.push(n); };
    for (const v of vids) v.addEventListener("playing", onPlaying);
    const got = [];
    for (const [st, pattern] of [["pastry1", /^pastry1_start → pastry1_loop → pastry1_end\d+ → pastry1_outro → idle1_loop$/],
                                 ["happy1", /^happy1_start → happy1_loop → happy1_end → idle1_loop$/]]) {
      seq.length = 0;
      setPetState(st);
      await waitFor(() => current === st && !transitioning, 30000, st + " loop");
      await sleep(1200);
      setPetState("idle1");
      await waitFor(idle, 30000, st + " → idle");
      await sleep(200);
      expect(pattern.test(seq.join(" → ")), `${st} 순서 이상: ${seq.join(" → ")}`);
      got.push(seq.join(" → "));
    }
    for (const v of vids) v.removeEventListener("playing", onPlaying);
    return got.join(" | ");
  });

  await check("queuedTalk", async () => {
    let on = false, dips = 0, minAlpha = 255, stop = false;
    const tick = () => { // 몸통 부근 9x9 블록의 최대 알파 — 온전히 그려졌다면 255
      if (on) {
        const d = sctx.getImageData(Math.floor(screen.width / 2) - 4, Math.floor(screen.height * 0.55) - 4, 9, 9).data;
        let a = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > a) a = d[i];
        if (a < minAlpha) minAlpha = a; if (a < 250) dips++;
      }
      if (!stop) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    const delays = [];
    for (let i = 0; i < 4; i++) {
      await toIdle(); await sleep(350); pinnedUntil = 0;
      on = true;
      setState("happy2", { pin: false });
      talkActive = true; setState("talk", { pin: false }); // 전환 중이라 큐로 들어간다
      await waitFor(() => current === "talk" && !transitioning, 30000, "talk");
      const t0 = performance.now();
      await waitFor(() => !vids[front].paused && vids[front].currentTime > 0.1, 5000, "talk playing");
      delays.push(Math.round(performance.now() - t0));
      expect(pinnedUntil === 0, "큐를 거친 talk 요청이 pin을 새로 걸었다");
      await sleep(250);
      on = false; talkActive = false;
    }
    stop = true;
    expect(dips === 0, `전환 중 캔버스 알파가 꺼짐 (${dips}프레임, 최소 알파 ${minAlpha})`);
    expect(Math.max(...delays) < 200, `talk 재생 시작 지연 ${JSON.stringify(delays)}ms`);
    return `알파 최소 ${minAlpha}, talk 시작 지연 ${JSON.stringify(delays)}ms`;
  });

  await check("holdQueue", async () => {
    try {
      motionHold.checked = true;
      setState("happy2", { pin: false });
      pickMotion("excited1");
      await waitFor(() => current === "excited1" && !transitioning, 30000, "excited1");
      expect(pinnedUntil === Infinity, "'계속 유지' pin이 큐를 거치며 풀렸다");
      return "pinnedUntil = Infinity 유지";
    } finally { motionHold.checked = false; pinnedUntil = 0; }
  });

  await check("staleChain", async () => {
    const IDLE = "anim_idle1_loop.webm";
    const realIdle = CLIP_URL.get(IDLE);
    try {
      setPetState("chem1");
      await waitFor(() => transitioning && nameOf(vids[front].src) === "chem1_start" && vids[front].currentTime > 0.2, 15000, "chem1_start on screen");
      const staleVid = vids[front];
      staleVid.pause(); // start 클립이 재생 도중 멎은 상황 → 전환이 끝나지 않는다
      CLIP_URL.set(IDLE, URL.createObjectURL(new MediaSource())); // 새 체인의 idle 로드도 지연시킨다
      transitionSince = Date.now() - 60000; // 워치독이 다음 틱에 리셋하도록
      await waitFor(() => warns.some(w => w.includes("transition stuck")), 5000, "watchdog reset");
      await sleep(200);
      const endedP = new Promise(r => staleVid.addEventListener("ended", r, { once: true }));
      staleVid.play(); // 멎었던 이전 클립이 뒤늦게 끝까지 흘러가 ended 발생
      await endedP;
      await sleep(1200);
      expect(current === "idle1", `버려진 체인이 되살아나 상태를 ${current}(으)로 덮어썼다`);
      return "리셋 뒤에도 current = idle1 유지";
    } finally {
      CLIP_URL.set(IDLE, realIdle);
      if (transitioning) transitionSince = Date.now() - 60000; // 지연시킨 idle 로드를 버리고 다시 리셋
    }
  });

  await toIdle().catch(() => {});
  console.warn = ow;
  return results;
};

// 동일 브라우저/영상/시간으로 현재 파일과 HEAD의 캔버스 작업량을 비교한다.
// node tools/widget_check.js --benchmark [--baseline] [--fallback]
const IN_BENCHMARK = async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const until = Date.now() + 30000;
  while ((!current || transitioning) && Date.now() < until) await sleep(20);
  if (!current || transitioning) throw new Error("벤치마크 초기 재생 실패");
  await sleep(3000);
  const before = window.__canvasDraws || 0;
  const beforeTime = vids[front].currentTime;
  await sleep(5000);
  return {
    canvas: [screen.width, screen.height],
    drawsIn5s: (window.__canvasDraws || 0) - before,
    videoTime: [beforeTime, vids[front].currentTime],
    cachedClips: CLIP_URL.size,
    fetchedBytes: performance.getEntriesByType("resource").filter(r => r.name.endsWith(".webm")).reduce((n, r) => n + r.encodedBodySize, 0),
  };
};

(async () => {
  const chromePath = findChrome();
  if (!chromePath) throw new Error("Chrome/Edge를 찾지 못했습니다. CHROME_PATH를 지정하세요.");
  const server = await serve();
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "widget-check-"));
  const chrome = spawn(chromePath, [
    "--headless=new", "--remote-debugging-port=0", `--user-data-dir=${profile}`,
    "--autoplay-policy=no-user-gesture-required", "--window-size=420,520",
    "--no-first-run", "--no-default-browser-check", "--mute-audio", "about:blank",
  ], { stdio: "ignore" });
  let failed = true;
  try {
    // --remote-debugging-port=0 → 실제 포트는 프로필의 DevToolsActivePort 파일에 기록된다
    let port = null;
    for (let i = 0; i < 80 && !port; i++) {
      await sleep(250);
      try { port = Number(fs.readFileSync(path.join(profile, "DevToolsActivePort"), "utf8").split("\n")[0]); } catch (_) {}
    }
    if (!port) throw new Error("Chrome이 기동하지 않았습니다.");
    const target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === "page");
    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
    let seq = 0; const pending = new Map();
    ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
    const send = (method, params = {}) => new Promise(res => { const id = ++seq; pending.set(id, res); ws.send(JSON.stringify({ id, method, params })); });

    await send("Page.enable");
    if (argv.includes("--capture")) await send("Page.addScriptToEvaluateOnNewDocument", { source: "window.__captureReactions=[];" });
    if (FALLBACK) await send("Page.addScriptToEvaluateOnNewDocument", { source: "delete HTMLVideoElement.prototype.requestVideoFrameCallback; delete HTMLVideoElement.prototype.cancelVideoFrameCallback;" });
    if (BENCHMARK) {
      await send("Page.addScriptToEvaluateOnNewDocument", { source: "window.__canvasDraws=0; const clear=CanvasRenderingContext2D.prototype.clearRect; CanvasRenderingContext2D.prototype.clearRect=function(...args){window.__canvasDraws++; return clear.apply(this,args)};" });
      await send("Emulation.setDeviceMetricsOverride", { width: 512, height: 512, deviceScaleFactor: 1, mobile: false });
      await send("Performance.enable");
    }
    await send("Page.navigate", { url: `http://127.0.0.1:${server.address().port}/${PAGE}?dice=0` });
    await sleep(1000);
    console.log(`checking ${PAGE}${BASELINE ? " (HEAD 기준)" : ""}${FALLBACK ? " (rVFC 미지원)" : ""}…`);
    if (BENCHMARK) {
      for (const [size, dpr] of [[512, 1], [1024, 2]]) {
        await send("Emulation.setDeviceMetricsOverride", { width: size, height: size, deviceScaleFactor: dpr, mobile: false });
        const before = await send("Performance.getMetrics");
        const r = await send("Runtime.evaluate", { expression: `(${IN_BENCHMARK})()`, awaitPromise: true, returnByValue: true });
        if (r.result.exceptionDetails) throw new Error(r.result.exceptionDetails.text);
        const after = await send("Performance.getMetrics");
        const taskTime = result => result.result.metrics.find(m => m.name === "TaskDuration").value;
        console.log(JSON.stringify({ viewport: size, dpr, ...r.result.result.value, taskMsIn8s: Math.round((taskTime(after) - taskTime(before)) * 1000) }));
      }
      failed = false;
      ws.close();
      return;
    }
    const r = await send("Runtime.evaluate", { expression: `(${IN_PAGE})()`, awaitPromise: true, returnByValue: true });
    if (r.result.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text);
    const results = r.result.result.value;
    for (const c of results) console.log(`${c.ok ? "PASS" : "FAIL"}  ${c.name.padEnd(12)} ${c.detail}`);
    if (argv.includes("--capture")) {
      const captured = await send("Runtime.evaluate", { expression: "window.__captureReactions", returnByValue: true });
      for (const { name, png } of captured.result.result.value || []) {
        const file = path.join(os.tmpdir(), `sheddy-${name}-runtime.png`);
        fs.writeFileSync(file, Buffer.from(png.split(",")[1], "base64"));
        console.log("QA", file);
      }
    }
    failed = results.some(c => !c.ok);
    ws.close();
  } finally {
    chrome.kill();
    server.close();
    await sleep(500);
    try { fs.rmSync(profile, { recursive: true, force: true }); } catch (_) {}
  }
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error("ERROR:", e.message); process.exit(2); });
