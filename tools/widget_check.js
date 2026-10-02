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
const HALLOWEEN = argv.includes("--halloween");
const baselineHTML = require.main === module && BASELINE ? execFileSync("git", ["show", "HEAD:widget.html"], { cwd: ROOT }) : null;
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
function serve(html = baselineHTML) {
  const TYPES = { ".html": "text/html; charset=utf-8", ".webm": "video/webm", ".png": "image/png", ".jpg": "image/jpeg", ".json": "application/json" };
  const server = http.createServer((req, res) => {
    const file = path.normalize(path.join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname)));
    if (html && file === path.join(ROOT, "widget.html")) {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Content-Length": html.length });
      res.end(html); return;
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
  expect(window.__halloweenStates.every(n => !ACTIVE_ANIMS[n] && !motionList.querySelector(`[data-name="${n}"]`)), "일반 모드에 할로윈 모션 노출");
  setPetState("broom1");
  expect(idle() && !queued, "일반 모드에서 할로윈 외부 명령 허용");
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
    const reactions = Object.keys(ACTIVE_ANIMS).filter(name => ACTIVE_ANIMS[name].once);
    for (const name of reactions) {
      setPetState(name);
      await waitFor(() => current === name && !transitioning, 10000, name);
      await sleep(750);
      const corner = sctx.getImageData(0, 0, 1, 1).data[3];
      const body = sctx.getImageData(Math.floor(screen.width / 2), Math.floor(screen.height * 0.55), 1, 1).data[3];
      // 생성 PNG의 알파와 VP9 양자화로 생기는 거의 불투명한 값도 허용한다.
      expect(corner === 0 && body >= 250, `${name} 배경/몸통 알파 이상: ${corner}/${body}`);
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
    return `${reactions.length}개 모션 단발 복귀 + 박수 계속 유지`;
  });

  const dances = ["bounce1", "shuffle1", "power1"].filter(name => ACTIVE_ANIMS[name]);
  if (dances.length) await check("danceLoops", async w0 => {
    motionHold.checked = true;
    try {
      for (const name of dances) {
        pickMotion(name);
        await waitFor(() => current === name && !transitioning, 10000, name + " 유지");
        let loops = 0, lastTime = vids[front].currentTime;
        await waitFor(() => {
          const time = vids[front].currentTime;
          if (time < lastTime - 0.5) loops++;
          lastTime = time;
          return loops >= 2;
        }, 12000, name + " 두 사이클");
        expect(current === name && pinnedUntil === Infinity, name + " 반복 유지 실패");
      }
      expect(!warns.slice(w0).some(w => w.includes("watchdog:")), "춤 반복 중 워치독 개입");
    } finally { motionHold.checked = false; pinnedUntil = 0; }
    return `${dances.length}개 춤 각각 두 사이클, 무기한 유지, 워치독 개입 없음`;
  });

  if (window.__reactionsOnly) {
    await toIdle();
    console.warn = ow;
    return results;
  }

  await check("alchemyEndings", async w0 => {
    const random = Math.random;
    const seq = [], got = [];
    const onPlaying = e => {
      const n = nameOf(e.target.src);
      if (seq[seq.length - 1] !== n) seq.push(n);
    };
    for (const v of vids) v.addEventListener("playing", onPlaying);
    try {
      for (let ending = 1; ending <= 3; ending++) {
        seq.length = 0;
        Math.random = () => (ending - 0.5) / 3;
        setPetState("alchemy1");
        await waitFor(() => current === "alchemy1" && !transitioning, 10000, "연금술 loop");
        await sleep(300);
        setPetState("idle1");
        await waitFor(() => nameOf(vids[front].src) === `alchemy1_end${ending}`, 5000, "결과 시작");
        await sleep(1500);
        if (window.__captureReactions) window.__captureReactions.push({ name: `alchemy1_end${ending}`, png: screen.toDataURL() });
        const corner = sctx.getImageData(0, 0, 1, 1).data[3];
        expect(corner === 0, "연금술 배경이 불투명함");
        await waitFor(idle, 15000, "연금술 원복");
        await sleep(150);
        const expected = `alchemy1_start → alchemy1_loop → alchemy1_end${ending} → alchemy1_outro → idle1_loop`;
        expect(seq.join(" → ") === expected, "연금술 순서 이상: " + seq.join(" → "));
        got.push(expected);
      }
      expect(!warns.slice(w0).some(w => w.includes("watchdog")), "연금술 전환 중 워치독 개입");
    } finally {
      Math.random = random;
      for (const v of vids) v.removeEventListener("playing", onPlaying);
    }
    return got.join(" | ");
  });

  await check("alchemyHold", async w0 => {
    const visibility = visible => window.dispatchEvent(new CustomEvent("obsSourceVisibleChanged", { detail: { visible } }));
    motionHold.checked = true;
    try {
      pickMotion("alchemy1");
      await waitFor(() => current === "alchemy1" && !transitioning, 10000, "연금술 유지");
      let loops = 0, lastTime = vids[front].currentTime;
      await waitFor(() => {
        const time = vids[front].currentTime;
        if (time < lastTime - 0.5) loops++;
        lastTime = time;
        return loops >= 2;
      }, 10000, "연금술 두 사이클");
      expect(pinnedUntil === Infinity, "연금술 무기한 유지 유실");
      visibility(false);
      const draws = drawCount, time = vids[front].currentTime;
      setPetState("idle1");
      await sleep(1200);
      expect(suspended && vids.every(v => v.paused), "연금술 숨김 중 재생");
      expect(drawCount === draws && Math.abs(vids[front].currentTime - time) < 0.05, "연금술 숨김 중 렌더/시간 진행");
      expect(queued?.name === "idle1", "연금술 숨김 중 요청 유실");
      visibility(true);
      await waitFor(idle, 15000, "연금술 숨김 복귀 후 원복");
      expect(!warns.slice(w0).some(w => w.includes("watchdog")), "연금술 유지 중 워치독 개입");
    } finally {
      motionHold.checked = false;
      pinnedUntil = 0;
      visibility(true);
    }
    return "두 사이클 무기한 유지, 숨김 중 draw/재생 0, 큐 실행과 원복 정상";
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
    const file = ACTIVE_ANIMS.chem1.loop;
    const cached = CLIP_URL.has(file);
    const a = loadClip(file), b = loadClip(file);
    if (!cached) expect(a === b, "진행 중인 같은 클립의 fetch가 합쳐지지 않음");
    expect(await a === await b, "같은 클립 중복 URL");
    const files = [...new Set(Object.values(ACTIVE_ANIMS).flatMap(a => [a.start, a.loop, a.outro, ...(Array.isArray(a.end) ? a.end : [a.end])]).filter(Boolean))];
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

// node tools/widget_check.js --halloween [--fallback] [--page docs/index.html]
const IN_HALLOWEEN = async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const expect = (ok, message) => { if (!ok) throw Error(message); };
  const wait = async (test, label, ms = 15000) => {
    const until = Date.now() + ms;
    while (!test()) { if (Date.now() > until) throw Error(label + " 시간 초과"); await sleep(20); }
  };
  const at = name => current === name && !transitioning;
  const names = [...window.__halloweenStates, "alchemy1", "alchemygold1", "alchemyboom1", "alchemyslime1"];
  const files = [...window.__halloweenStates.map(n => `anim_${n}_loop.webm`), "anim_alchemy1_loop.webm", ...[1, 2, 3].map(i => `anim_alchemy1_end${i}.webm`)];
  const warnings = [], warn = console.warn, random = Math.random;
  console.warn = (...args) => { warnings.push(args.join(" ") + ` [state=${current}, time=${vids[front].currentTime}, paused=${vids[front].paused}]`); warn.apply(console, args); };
  const visibility = visible => window.dispatchEvent(new CustomEvent("obsSourceVisibleChanged", { detail: { visible } }));
  const result = [];
  try {
    await wait(() => at("witchidle1"), "일반 시작 상태의 마녀 대체");
    pinnedUntil = Infinity;
    expect(DEFAULT_STATE === "witchidle1", "기본 복장이 마녀가 아님");
    expect(JSON.stringify([...motionList.querySelectorAll("[data-name]")].map(el => el.dataset.name)) === JSON.stringify(names), "선택기에 일반 모션 노출");
    setPetState("happy1"); setPetState("talk");
    expect(at("witchidle1") && !queued, "일반 외부 명령 허용");
    expect(CLIP_URL.size === 1 && CLIP_URL.has(files[0]), "불필요한 초기 영상 로딩");
    result.push({ name: "modeScope", ok: true, detail: "일반 시작 상태 대체, 선택기 24종, 외부 일반 모션 차단, 초기 영상 1개" });

    let idleLoops = 0, idleTime = vids[front].currentTime;
    await wait(() => {
      const time = vids[front].currentTime;
      if (time < idleTime - 0.5) idleLoops++;
      idleTime = time;
      return idleLoops >= 2;
    }, "마녀 대기 두 사이클");
    result.push({ name: "witchIdle", ok: true, detail: "대기 루프 두 사이클 연속 재생" });

    for (const name of names.slice(1)) {
      pinnedUntil = 0;
      setPetState(name);
      await wait(() => at(name), name);
      await sleep(1200);
      expect(sctx.getImageData(0, 0, 1, 1).data[3] === 0, "배경 알파 오류");
      expect(vids[front].videoWidth === 720 && !vids[front].paused, "720 영상 재생 오류");
      if (window.__captureReactions) window.__captureReactions.push({ name, png: screen.toDataURL() });
      await wait(() => at("witchidle1"), name + " 마녀 복귀");
    }
    result.push({ name: "witchResults", ok: true, detail: "동작 23종 실제 재생 후 마녀 복장으로 복귀, 투명 720 영상" });

    motionHold.checked = true;
    pickMotion("alchemygold1");
    await wait(() => at("alchemygold1"), "결과 유지");
    talkActive = true; // 마이크 게이트가 열려도 일반 talk로 전환하지 않는다.
    let loops = 0, lastTime = vids[front].currentTime;
    await wait(() => {
      const time = vids[front].currentTime;
      if (time < lastTime - 0.5) loops++;
      lastTime = time;
      return loops >= 2;
    }, "결과 두 사이클");
    expect(pinnedUntil === Infinity && at("alchemygold1"), "유지/마이크 격리 실패");
    visibility(false);
    const draws = drawCount, time = vids[front].currentTime;
    setState("alchemyslime1", { pin: false });
    setPetState("idle1");
    await sleep(1200);
    expect(drawCount === draws && vids.every(v => v.paused) && Math.abs(vids[front].currentTime - time) < 0.05, "숨김 중 재생/그리기");
    expect(queued?.name === "alchemyslime1", "일반 명령이 유효한 대기 요청을 덮어씀");
    visibility(true);
    await wait(() => at("alchemyslime1"), "숨김 복귀 후 요청 실행");
    expect(pinnedUntil === Infinity, "큐를 거치며 무기한 유지 유실");
    motionHold.checked = false; pinnedUntil = 0; talkActive = false;
    await wait(() => at("witchidle1"), "유지 해제 후 마녀 복귀");
    result.push({ name: "witchHold", ok: true, detail: "두 사이클 유지, 마이크 격리, 숨김 중 작업 0, 유효한 큐와 Infinity 보존" });

    // 실제 ended 이벤트와 주사위를 거쳐 결과가 선택되고 다시 마녀 대기로 돌아오는지 확인한다.
    idleStreak = 0;
    Math.random = () => 0.3;
    await wait(() => current !== DEFAULT_STATE && !transitioning, "할로윈 자동 추첨");
    await wait(() => at("witchidle1"), "자동 결과 복귀");
    const requests = performance.getEntriesByType("resource").filter(r => r.name.endsWith(".webm"));
    expect(requests.every(r => files.includes(r.name.split("/").pop())), "일반/변신/원복 영상 요청 발생");
    expect(cacheBytes <= CACHE_LIMIT, "캐시 상한 초과");
    expect(!warnings.some(w => w.includes("watchdog")), "할로윈 워치독 개입: " + warnings.filter(w => w.includes("watchdog")).join(" | "));
    result.push({ name: "witchAutomatic", ok: true, detail: `실제 자동 추첨·복귀, 전용 클립만 요청, 캐시 ${cacheBytes}B` });
  } finally {
    Math.random = random; console.warn = warn; talkActive = false;
    motionHold.checked = false; pinnedUntil = 0; visibility(true);
  }
  return result;
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

async function main() {
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
    const halloweenStates = JSON.parse(fs.readFileSync(path.join(ROOT, "anims/halloween/motions.json"), "utf8")).map(m => m.id);
    await send("Page.addScriptToEvaluateOnNewDocument", { source: `window.__halloweenStates=${JSON.stringify(halloweenStates)};` });
    if (argv.includes("--reactions-only")) await send("Page.addScriptToEvaluateOnNewDocument", { source: "window.__reactionsOnly=true;" });
    if (argv.includes("--capture")) await send("Page.addScriptToEvaluateOnNewDocument", { source: "window.__captureReactions=[];" });
    if (FALLBACK) await send("Page.addScriptToEvaluateOnNewDocument", { source: "delete HTMLVideoElement.prototype.requestVideoFrameCallback; delete HTMLVideoElement.prototype.cancelVideoFrameCallback;" });
    if (BENCHMARK) {
      await send("Page.addScriptToEvaluateOnNewDocument", { source: "window.__canvasDraws=0; const clear=CanvasRenderingContext2D.prototype.clearRect; CanvasRenderingContext2D.prototype.clearRect=function(...args){window.__canvasDraws++; return clear.apply(this,args)};" });
      await send("Emulation.setDeviceMetricsOverride", { width: 512, height: 512, deviceScaleFactor: 1, mobile: false });
      await send("Performance.enable");
    }
    await send("Page.navigate", { url: `http://127.0.0.1:${server.address().port}/${PAGE}?${HALLOWEEN ? "mode=halloween&state=happy1&hold=0" : "dice=0"}` });
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
    const r = await send("Runtime.evaluate", { expression: `(${HALLOWEEN ? IN_HALLOWEEN : IN_PAGE})()`, awaitPromise: true, returnByValue: true });
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
    if (HALLOWEEN) {
      for (const [query, expected] of [["mode=halloween&state=alchemyslime1&dice=0", "alchemyslime1"], ["mode=unknown&dice=0", "idle1"]]) {
        await send("Page.navigate", { url: `http://127.0.0.1:${server.address().port}/${PAGE}?${query}` });
        await sleep(1000);
        const check = await send("Runtime.evaluate", { expression: `(async()=>{const until=Date.now()+15000;while((!current||transitioning)&&Date.now()<until)await new Promise(r=>setTimeout(r,20));return current===${JSON.stringify(expected)}&&!transitioning;})()`, awaitPromise: true, returnByValue: true });
        const ok = check.result.result?.value === true;
        results.push({ name: query, ok });
        console.log(`${ok ? "PASS" : "FAIL"}  ${query} → ${expected}`);
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
}

module.exports = { findChrome, serve };
if (require.main === module) main().catch(e => { console.error("ERROR:", e.message); process.exit(2); });
