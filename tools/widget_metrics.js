"use strict";
// OBS 위젯의 반복 비교 측정. 런타임 수정 없이 CDP에서 동일한 계측을 주입한다.
const { spawn, execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const crypto = require("node:crypto");
const { findChrome, serve } = require("./widget_check");
const ROOT = path.resolve(__dirname, "..");
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const hash = data => crypto.createHash("sha256").update(data).digest("hex");
const git = (...args) => execFileSync("git", args, { cwd: ROOT, encoding: "utf8" }).trim();

function percentile(values, fraction) {
  if (!values.length || values.some(v => !Number.isFinite(v))) throw new Error("유한한 표본이 필요하다");
  if (!(fraction > 0 && fraction <= 1)) throw new Error("백분위 범위: 0 < p <= 1");
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.ceil(sorted.length * fraction) - 1];
}
function median(values) {
  percentile(values, 0.5);
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}
function reduction(before, after) {
  return before === 0 ? null : (before - after) / before * 100;
}
function summarize(trials) {
  if (!trials.length) throw new Error("측정 결과가 없다");
  const metrics = ["firstFrameMs", "clearsPerSecond", "drawsPerSecond", "drawMegapixelsPerSecond",
    "mainThreadBusyPercent", "videoFramesPerSecond", "droppedFrames", "initialVideoBytes",
    "initialVideoRequests", "initialBlobBytes", "heapUsedBytes", "hiddenDrawsPerSecond"];
  const groups = [];
  for (const scenario of [...new Set(trials.map(t => t.scenario))]) {
    const rows = {};
    for (const variant of ["baseline", "current"]) {
      const samples = trials.filter(t => t.scenario === scenario && t.variant === variant);
      if (!samples.length) throw new Error(`${scenario}: ${variant} 표본 누락`);
      rows[variant] = Object.fromEntries(metrics.map(key => [key, {
        median: median(samples.map(t => t[key])),
        min: Math.min(...samples.map(t => t[key])), max: Math.max(...samples.map(t => t[key])),
      }]));
      for (const sweep of ["first", "repeat"]) {
        const latencies = samples.flatMap(t => t.transitions.filter(x => x.sweep === sweep).map(x => x.ms));
        rows[variant][sweep + "TransitionMs"] = {
          count: latencies.length, median: median(latencies), p95: percentile(latencies, 0.95), max: Math.max(...latencies),
        };
      }
    }
    groups.push({ scenario, ...rows, reductionPercent: Object.fromEntries(metrics.map(key =>
      [key, reduction(rows.baseline[key].median, rows.current[key].median)])) });
  }
  return groups;
}

// clear 횟수는 합성 프레임 수, draw 면적 합계는 디졸브의 두 번 그리기까지 포함한다.
function instrument() {
  window.__wm = { clears: 0, draws: 0, pixels: 0, firstFrameMs: null, lastDrawSrc: null, blobBytes: 0 };
  const clear = CanvasRenderingContext2D.prototype.clearRect;
  const draw = CanvasRenderingContext2D.prototype.drawImage;
  CanvasRenderingContext2D.prototype.clearRect = function (...args) {
    if (this.canvas.id === "screen") window.__wm.clears++;
    return clear.apply(this, args);
  };
  CanvasRenderingContext2D.prototype.drawImage = function (...args) {
    const result = draw.apply(this, args);
    if (this.canvas.id === "screen" && args[0] instanceof HTMLVideoElement && args[0].readyState >= 2) {
      const m = window.__wm;
      m.draws++;
      m.pixels += args.length === 9 ? args[7] * args[8] : args.length === 5 ? args[3] * args[4] : args[0].videoWidth * args[0].videoHeight;
      m.firstFrameMs ??= performance.now();
      m.lastDrawSrc = args[0].src;
    }
    return result;
  };
  const blobs = new Map();
  const create = URL.createObjectURL.bind(URL), revoke = URL.revokeObjectURL.bind(URL);
  URL.createObjectURL = value => {
    const url = create(value);
    if (value instanceof Blob) { blobs.set(url, value.size); window.__wm.blobBytes += value.size; }
    return url;
  };
  URL.revokeObjectURL = url => {
    window.__wm.blobBytes -= blobs.get(url) || 0;
    blobs.delete(url);
    return revoke(url);
  };
  window.__wmPendingFetches = 0;
  const fetchOriginal = window.fetch;
  window.fetch = async (...args) => {
    window.__wmPendingFetches++;
    try { return await fetchOriginal(...args); }
    finally { window.__wmPendingFetches--; }
  };
}

// 식은 해당 페이지의 전역 lexical binding(current, vids 등)에서 평가한다.
async function ready() {
  const start = performance.now();
  while (typeof current === "undefined" || !current || transitioning || window.__wm.firstFrameMs === null) {
    if (performance.now() - start > 15000) throw new Error("초기 프레임 타임아웃");
    await new Promise(r => setTimeout(r, 20));
  }
  await new Promise(r => setTimeout(r, 3000));
  while (window.__wmPendingFetches > 0) {
    if (performance.now() - start > 20000) throw new Error("초기 로딩 타임아웃");
    await new Promise(r => setTimeout(r, 20));
  }
}
function snapshot() {
  const video = vids[front];
  const quality = video.getVideoPlaybackQuality();
  return {
    time: performance.now(), ...window.__wm, canvas: [screen.width, screen.height],
    frames: quality.totalVideoFrames, dropped: quality.droppedVideoFrames,
    videoIndex: front, current, transitioning, paused: video.paused, hidden: document.hidden,
    initialVideoBytes: performance.getEntriesByType("resource").filter(r => r.name.endsWith(".webm")).reduce((n, r) => n + r.encodedBodySize, 0),
    initialVideoRequests: performance.getEntriesByType("resource").filter(r => r.name.endsWith(".webm")).length,
  };
}
async function transitions() {
  const result = [];
  for (const sweep of ["first", "repeat"]) {
    for (const name of ["happy2", "idle1", "excited1", "idle1", "basic2", "idle1"]) {
      const t = performance.now();
      setPetState(name);
      while (current !== name || transitioning || window.__wm.lastDrawSrc !== vids[front].src) {
        if (performance.now() - t > 15000) throw new Error("전환 타임아웃: " + name);
        await new Promise(r => setTimeout(r, 5));
      }
      result.push({ sweep, state: name, ms: performance.now() - t });
      await new Promise(r => setTimeout(r, 150));
    }
  }
  return result;
}

async function launch(chromePath) {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "widget-metrics-"));
  const chrome = spawn(chromePath, ["--headless=new", "--remote-debugging-port=0", `--user-data-dir=${profile}`,
    "--autoplay-policy=no-user-gesture-required", "--no-first-run", "--no-default-browser-check", "--mute-audio", "about:blank"], { stdio: "ignore" });
  let ws;
  const close = async () => {
    ws?.close();
    if (chrome.exitCode === null && chrome.signalCode === null) {
      const exited = new Promise(resolve => chrome.once("exit", resolve));
      chrome.kill();
      await Promise.race([exited, sleep(3000)]);
      if (chrome.exitCode === null && chrome.signalCode === null) { chrome.kill("SIGKILL"); await exited; }
    }
    fs.rmSync(profile, { recursive: true, force: true });
  };
  try {
    let port;
    for (let i = 0; i < 80 && !port; i++) {
      await sleep(100);
      try { port = Number(fs.readFileSync(path.join(profile, "DevToolsActivePort"), "utf8").split("\n")[0]); } catch (_) {}
    }
    if (!port) throw new Error("Chrome이 기동하지 않았다");
    const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
    ws = new WebSocket(targets.find(t => t.type === "page").webSocketDebuggerUrl);
    await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
    const pending = new Map();
    let id = 0;
    ws.onmessage = event => {
      const message = JSON.parse(event.data);
      if (!pending.has(message.id)) return;
      const { resolve, reject, timer } = pending.get(message.id);
      pending.delete(message.id); clearTimeout(timer);
      if (message.error) reject(new Error(JSON.stringify(message.error))); else resolve(message.result);
    };
    const send = (method, params = {}) => new Promise((resolve, reject) => {
      const key = ++id;
      const timer = setTimeout(() => { pending.delete(key); reject(new Error(`CDP 타임아웃: ${method}`)); }, 45000);
      pending.set(key, { resolve, reject, timer });
      ws.send(JSON.stringify({ id: key, method, params }));
    });
    const evaluate = async expression => {
      const result = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
      if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
      return result.result.value;
    };
    return { send, evaluate, close };
  } catch (error) { await close(); throw error; }
}

async function measure(chromePath, html, viewport, dpr) {
  const server = await serve(html);
  let browser;
  try {
    browser = await launch(chromePath);
    const { send, evaluate } = browser;
    const version = await send("Browser.getVersion");
    await send("Page.enable");
    await send("Network.enable");
    await send("Network.setCacheDisabled", { cacheDisabled: true });
    await send("Performance.enable");
    await send("Emulation.setDeviceMetricsOverride", { width: viewport, height: viewport, deviceScaleFactor: dpr, mobile: false });
    await send("Page.addScriptToEvaluateOnNewDocument", { source: `(${instrument})()` });
    await send("Page.navigate", { url: `http://127.0.0.1:${server.address().port}/widget.html?dice=0` });
    // 초기 문서 교체가 끝난 뒤에 위젯 전역을 읽는다.
    for (let i = 0; ; i++) {
      if (await evaluate("typeof window.__wm === 'object'")) break;
      if (i >= 100) throw new Error("페이지 로딩 타임아웃");
      await sleep(50);
    }
    await evaluate(`(${ready})()`);
    const before = await evaluate(`(${snapshot})()`);
    const beforeMetrics = await send("Performance.getMetrics");
    await sleep(5000);
    const afterMetrics = await send("Performance.getMetrics");
    const after = await evaluate(`(${snapshot})()`);
    if (before.hidden || after.hidden || before.paused || after.paused || before.videoIndex !== after.videoIndex || after.frames <= before.frames || after.current !== "idle1" || after.transitioning) {
      throw new Error("유효하지 않은 대기 측정: 숨김/정지/프레임 미진행/상태 변경");
    }
    if (before.initialVideoBytes !== after.initialVideoBytes || before.blobBytes !== after.blobBytes) {
      throw new Error("준비 시간 이후에도 초기 로딩이 진행됐다. 대기 측정에서 제외한다.");
    }
    const metric = (result, name) => {
      const value = result.metrics.find(m => m.name === name)?.value;
      if (!Number.isFinite(value)) throw new Error(`CDP 지표 누락: ${name}`);
      return value;
    };
    const seconds = (after.time - before.time) / 1000;
    const taskSeconds = metric(afterMetrics, "TaskDuration") - metric(beforeMetrics, "TaskDuration");
    const metricSeconds = metric(afterMetrics, "Timestamp") - metric(beforeMetrics, "Timestamp");
    const transitionSamples = await evaluate(`(${transitions})()`);
    await evaluate("window.dispatchEvent(new CustomEvent('obsSourceVisibleChanged', {detail:{visible:false}}))");
    const hiddenBefore = await evaluate(`(${snapshot})()`);
    await sleep(1000);
    const hiddenAfter = await evaluate(`(${snapshot})()`);
    await evaluate("window.dispatchEvent(new CustomEvent('obsSourceVisibleChanged', {detail:{visible:true}}))");
    return {
      browser: version.product, viewport, dpr, canvas: after.canvas, sampleSeconds: seconds,
      firstFrameMs: before.firstFrameMs,
      clearsPerSecond: (after.clears - before.clears) / seconds,
      drawsPerSecond: (after.draws - before.draws) / seconds,
      drawMegapixelsPerSecond: (after.pixels - before.pixels) / seconds / 1e6,
      taskSeconds, metricSeconds, mainThreadBusyPercent: taskSeconds / metricSeconds * 100,
      videoFramesPerSecond: (after.frames - before.frames) / seconds,
      droppedFrames: after.dropped - before.dropped,
      initialVideoBytes: before.initialVideoBytes, initialVideoRequests: before.initialVideoRequests,
      initialBlobBytes: before.blobBytes, heapUsedBytes: metric(afterMetrics, "JSHeapUsedSize"),
      hiddenDrawsPerSecond: (hiddenAfter.draws - hiddenBefore.draws) / ((hiddenAfter.time - hiddenBefore.time) / 1000),
      transitions: transitionSamples,
      raw: { before, after, hiddenBefore, hiddenAfter, beforeMetrics: beforeMetrics.metrics, afterMetrics: afterMetrics.metrics },
    };
  } finally { if (browser) await browser.close(); await new Promise(resolve => server.close(resolve)); }
}

function reportMarkdown(report) {
  const f = n => n === null ? "계산 불가(기준 0)" : n.toLocaleString("en-US", { maximumFractionDigits: 3 });
  let text = `# OBS 위젯 성능 측정\n\n측정 시각: ${report.createdAt}\n\n기준: \`${report.baseline.commit}\` → 현재: \`${report.current.commit}\` (파일 SHA-256은 JSON에 기록).\n\n`;
  text += `${report.environment.platform}/${report.environment.arch}, ${report.environment.cpu}, ${report.trials[0].browser}, Node ${report.environment.node}. 각 조건 ${report.runs}회, 순서 AB/BA 교대. 새 Chrome 프로필·HTTP 캐시 비활성·로컬 서버·dice=0. 3초 준비 후 5초 대기 측정.\n\n`;
  text += "## 지표 정의\n\n- 감소율 = (기준 중앙값 − 현재 중앙값) / 기준 중앙값 × 100. 음수는 증가, 기준 0은 계산하지 않는다.\n- 합성 횟수 = 캔버스 clearRect 횟수 / 실제 측정 초. 영상 FPS와 구분한다.\n- 영상 그리기량(Mpixel/s) = drawImage 목적지 픽셀 면적의 합 / 측정 초 / 1,000,000. 디졸브 중 중복 그리기를 포함하며 GPU 사용률·대역폭이 아니다.\n- 메인 스레드 점유율 = CDP TaskDuration 증가 / CDP Timestamp 증가 × 100. 프로세스 전체 CPU, 영상 디코더, GPU 부하를 포함하지 않는다.\n- 초기 영상 바이트 = 준비 완료까지 ResourceTiming encodedBodySize 합. HTTP 헤더·HTML은 제외한다. 초기 Blob 보유량은 생성/해제된 Blob URL 크기의 차이다.\n- JS heap은 별도 메모리 스냅샷이며 Blob·디코더·GPU 메모리나 프로세스 RSS가 아니다.\n- 전환 지연 = 상태 명령부터 대상 영상의 첫 캔버스 그리기까지. 첫 순회·반복 순회를 구분한다. happy2/idle1/excited1/idle1/basic2/idle1 순서이며 start/end 연출이 있는 모션은 포함하지 않는다. 5ms 폴링 오차가 있다. 기본 자세 복귀도 포함하며, 기준 버전은 전체 선로딩하므로 첫 순회가 양쪽 모두 cold cache라는 뜻은 아니다.\n- P95는 오름차순 ceil(0.95×표본수) 번째 값. 반복 측정의 통계는 기술 통계이며 유의성이나 모든 OBS 장면의 성능을 증명하지 않는다.\n- 숨김은 OBS 가시성 이벤트(false)를 보내 1초 측정한다. 실제 OBS나 OS의 백그라운드 처리 결과를 대신하지 않는다.\n\n";
  const labels = { firstFrameMs: "첫 그림(ms)", clearsPerSecond: "합성 횟수(/s)", drawsPerSecond: "영상 그리기(/s)", drawMegapixelsPerSecond: "영상 그리기량(Mpixel/s)", mainThreadBusyPercent: "메인 스레드 점유율(%)", videoFramesPerSecond: "영상 프레임(/s)", droppedFrames: "드롭 프레임(5초)", initialVideoBytes: "초기 영상 바이트", initialVideoRequests: "초기 영상 요청 수", initialBlobBytes: "초기 Blob 보유 바이트", heapUsedBytes: "JS heap 바이트", hiddenDrawsPerSecond: "숨김 중 그리기(/s)" };
  for (const group of report.summary) {
    text += `## ${group.scenario}\n\n중앙값 [최소, 최대]. 영상 FPS 감소는 개선으로 해석하지 않는다.\n\n| 지표 | 기준 | 현재 | 감소율 |\n| --- | ---: | ---: | ---: |\n`;
    for (const [key, label] of Object.entries(labels)) {
      const cell = v => `${f(v.median)} [${f(v.min)}, ${f(v.max)}]`;
      text += `| ${label} | ${cell(group.baseline[key])} | ${cell(group.current[key])} | ${key === "videoFramesPerSecond" ? "—" : f(group.reductionPercent[key]) + (group.reductionPercent[key] === null ? "" : "%")} |\n`;
    }
    text += "\n| 전환 | 기준 중앙값 / P95 / 최대(ms) | 현재 중앙값 / P95 / 최대(ms) | 표본 수(각 버전) |\n| --- | ---: | ---: | ---: |\n";
    for (const [key, label] of [["firstTransitionMs", "첫 순회"], ["repeatTransitionMs", "반복 순회"]]) {
      const cell = v => `${f(v.median)} / ${f(v.p95)} / ${f(v.max)}`;
      text += `| ${label} | ${cell(group.baseline[key])} | ${cell(group.current[key])} | ${group.baseline[key].count} / ${group.current[key].count} |\n`;
    }
    text += "\n";
  }
  return text + "## 해석 범위\n\n계측 코드 비용은 양쪽에 포함된다. 같은 로컬 자산을 사용하는 HTML 런타임 비교이며, 인터넷 지연·실제 OBS CPU/GPU/RSS·마이크 입력은 측정하지 않았다. 캐시 상한 4MiB는 별도의 widget_check 회귀 검사가 검증하며 이 보고서의 초기 보유량과 다르다.\n";
}

async function main() {
  const args = process.argv.slice(2);
  const option = (key, fallback) => args.includes(key) ? args[args.indexOf(key) + 1] : fallback;
  const ref = option("--baseline");
  if (!ref || ref.startsWith("-")) throw new Error("사용법: node tools/widget_metrics.js --baseline <commit> [--runs 3] [--output reports/obs-performance.json]");
  const runs = Number(option("--runs", "3"));
  if (!Number.isInteger(runs) || runs < 1 || runs > 20) throw new Error("runs 범위: 1~20 정수");
  const output = path.resolve(ROOT, option("--output", "reports/obs-performance.json"));
  if (!output.endsWith(".json")) throw new Error("출력은 .json 경로여야 한다");
  const baselineCommit = git("rev-parse", "--verify", `${ref}^{commit}`);
  const baseline = execFileSync("git", ["show", `${baselineCommit}:widget.html`], { cwd: ROOT });
  const current = fs.readFileSync(path.join(ROOT, "widget.html"));
  const chromePath = findChrome();
  if (!chromePath) throw new Error("Chrome/Edge가 필요하다. CHROME_PATH를 지정한다.");
  const assetFiles = fs.readdirSync(path.join(ROOT, "sprites/rebuilt/videos")).filter(f => f.endsWith(".webm")).map(f => "sprites/rebuilt/videos/" + f);
  assetFiles.push(...["note1", "clap1", "heart1", "surprise1"].map(n => `sprites/anim_${n}_loop.webm`));
  const report = {
    schemaVersion: 1, createdAt: new Date().toISOString(), runs,
    baseline: { commit: baselineCommit, htmlSha256: hash(baseline) },
    current: { commit: git("rev-parse", "HEAD"), htmlSha256: hash(current), dirty: Boolean(git("status", "--porcelain")) },
    environment: { platform: os.platform(), arch: os.arch(), cpu: os.cpus()[0]?.model, node: process.version },
    assets: Object.fromEntries(assetFiles.sort().map(file => [file, hash(fs.readFileSync(path.join(ROOT, file)))])), trials: [],
  };
  fs.mkdirSync(path.dirname(output), { recursive: true });
  for (let run = 1; run <= runs; run++) {
    for (const [viewport, dpr] of [[512, 1], [1024, 2]]) {
      for (const variant of run % 2 ? ["baseline", "current"] : ["current", "baseline"]) {
        console.log(`측정 ${run}/${runs} ${viewport}px DPR${dpr} ${variant}`);
        const result = await measure(chromePath, variant === "baseline" ? baseline : current, viewport, dpr);
        report.trials.push({ run, variant, scenario: `${viewport}px / DPR ${dpr}`, ...result });
        // 중단된 실행도 완료된 표본은 보존한다. summary 없는 파일은 미완료다.
        fs.writeFileSync(output, JSON.stringify(report, null, 2) + "\n");
        console.log(`  합성 ${result.clearsPerSecond.toFixed(2)}/s, 메인 스레드 ${result.mainThreadBusyPercent.toFixed(3)}%, 영상 ${result.initialVideoBytes}B`);
      }
    }
  }
  report.summary = summarize(report.trials);
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + "\n");
  fs.writeFileSync(output.replace(/\.json$/, ".md"), reportMarkdown(report));
  console.log(`완료: ${output}`);
}

module.exports = { percentile, median, reduction, summarize, reportMarkdown };
if (require.main === module) main().catch(error => { console.error(error); process.exitCode = 1; });
