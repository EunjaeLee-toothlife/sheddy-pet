"use strict";
// 실제 프레임·마우스·키보드로 방송 연출, 확대 읽기와 중단 복원을 검수한다.
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const { chromium } = require("playwright"), { PNG } = require("pngjs");
const ROOT = path.resolve(__dirname, ".."), OUT = path.join(ROOT, "output/tarot-widget/qa");
const BASE = "http://127.0.0.1:8474/" + (process.argv.includes("--pages") ? "docs/" : "") + "tarot-widget/";
const SESSION = "sheddy-lemon-tarot-session-v1";
const WIDTH = process.argv.includes("--width=800") ? 800 : 1200, HEIGHT = WIDTH * 3 / 4, STAGE_HEIGHT = WIDTH * 9 / 16, SCALE = WIDTH / 800;
async function idle(page) { await page.waitForFunction(() => document.querySelector("#stage").getAttribute("aria-busy") !== "true"); }
async function tap(page, selector, settle = true) {
  const node = page.locator(selector); await node.waitFor({ state: "visible" });
  assert(!await node.isDisabled(), `클릭 불가: ${selector}`);
  const box = await node.boundingBox(); assert(box?.width > 0 && box?.height > 0);
  // 호흡 중인 카드의 중심을 실제 마우스로 클릭한다.
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  if (settle) await idle(page);
}
async function shot(page, name) {
  await idle(page); await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.querySelectorAll("#stage img")].map(img => img.decode())); });
  await page.locator("#stage").screenshot({ path: path.join(OUT, `salon-${WIDTH}-${name}.png`), omitBackground: true });
}
function difference(first, second) {
  const a = PNG.sync.read(first), b = PNG.sync.read(second); let changed = 0;
  for (let i = 0; i < a.data.length; i += 4) if ([0, 1, 2, 3].some(channel => Math.abs(a.data[i + channel] - b.data[i + channel]) > 22)) changed++;
  return changed;
}
async function fit(page) {
  const layout = await page.evaluate(() => {
    const stage = document.querySelector("#stage").getBoundingClientRect();
    return { width: stage.width, height: stage.height, pageHeight: document.documentElement.scrollHeight,
      panelHeight: document.querySelector(".controller").clientHeight, panelScroll: document.querySelector(".controller").scrollHeight,
      boxes: [...document.querySelectorAll("#stage button")].filter(button => button.getBoundingClientRect().width).map(button => {
        const box = button.getBoundingClientRect(); return { label: button.getAttribute("aria-label") || button.textContent.slice(0, 20), x: box.x - stage.x, y: box.y - stage.y, width: box.width, height: box.height };
      }) };
  });
  assert.equal(layout.width, WIDTH); assert.equal(layout.height, STAGE_HEIGHT); assert.equal(layout.pageHeight, HEIGHT);
  assert(layout.panelScroll <= layout.panelHeight + 1, `조작 패널 잘림: ${JSON.stringify(layout)}`);
  for (const box of layout.boxes) assert(box.x >= 9 * SCALE && box.x + box.width <= 791 * SCALE && box.y >= 55 * SCALE && box.y + box.height <= 415 * SCALE, `카드 잘림: ${JSON.stringify(box)}`);
  const captionGap = await page.evaluate(() => {
    if (!document.querySelector("#stage").classList.contains("is-focused")) return null;
    const guide = document.querySelector(".focus-guide").getBoundingClientRect();
    const labels = [...document.querySelectorAll(".reading-slot:not(.focused) .slot-label")].map(node => node.getBoundingClientRect().top);
    return labels.length ? Math.min(...labels) - guide.bottom : null;
  });
  if (captionGap !== null) assert(captionGap >= 5 * SCALE, `확대 설명과 작은 카드 이름이 겹칩니다: ${captionGap}`);
}
(async function () {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true });
  const context = await browser.newContext({ viewport: { width: WIDTH, height: HEIGHT }, reducedMotion: "no-preference", recordVideo: { dir: path.join(OUT, "salon-video"), size: { width: WIDTH, height: HEIGHT } } });
  await context.addInitScript(() => {
    const NativeAudio = window.AudioContext;
    window.AudioContext = class extends NativeAudio {
      constructor(...args) { super(...args); window.__salonAudio = this; window.__salonSounds = 0; }
      createBufferSource() { window.__salonSounds++; return super.createBufferSource(); }
    };
  });
  let page;
  try { page = await context.newPage(); } catch (error) { await browser.close(); throw error; }
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("response", response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
  const read = () => page.evaluate(key => JSON.parse(localStorage.getItem(key)), SESSION);
  try {
    await page.goto(BASE); await page.locator("[data-start='3']").waitFor();
    await shot(page, "01-salon"); await fit(page);
    const alpha = PNG.sync.read(await page.locator("#stage").screenshot({ omitBackground: true })).data[3];
    assert(alpha <= 5, `테이블 바깥 모서리에 불투명한 배경이 있습니다: ${alpha}`);
    assert.equal(await page.locator("#stage").evaluate(node => node.getAnimations({ subtree: true }).length), 0, "준비 화면에 불필요한 반복 연출이 있습니다");
    await tap(page, "[data-start='3']", false); await page.waitForTimeout(120);
    assert(await page.locator("#stage").evaluate(node => node.classList.contains("is-presenting")));
    assert.equal(await page.locator(".show-packet").count(), 3);
    assert(await page.locator(".show-packet").evaluateAll(nodes => nodes.every(node => {
      const matrix = new DOMMatrix(getComputedStyle(node).transform);
      return Math.abs(matrix.a - 1) < .001 && Math.abs(matrix.d - 1) < .001 && Math.abs(matrix.b) < .001 && Math.abs(matrix.c) < .001;
    })), "셔플 더미가 회전하거나 확대됩니다");
    assert(await page.locator("[data-pile='0']").isDisabled());
    const shuffled = await read(), first = await page.locator("#stage").screenshot({ path: path.join(OUT, "salon-shuffle-a.png"), omitBackground: true });
    await page.waitForTimeout(230);
    const second = await page.locator("#stage").screenshot({ path: path.join(OUT, "salon-shuffle-b.png"), omitBackground: true });
    const shufflePixels = difference(first, second); assert(shufflePixels > 3500, `섞기 움직임 부족: ${shufflePixels}`);
    await page.keyboard.press("Space"); await idle(page); assert.deepEqual(await read(), shuffled);
    assert.equal(await page.locator(".show-card").count(), 0); await fit(page); await shot(page, "02-six-decks");
    assert.deepEqual(await page.locator(".deck-button").evaluateAll(nodes => nodes.map(node => [node.textContent.trim(), node.getAttribute("aria-label")])), Array.from({ length: 6 }, (_, index) => [`${index + 1}번 덱`, `${index + 1}번 덱`]));
    await page.keyboard.press("2"); await page.waitForTimeout(90);
    assert.equal(await page.locator("[data-pile='1']").evaluate(node => getComputedStyle(node).visibility), "hidden", "선택한 덱이 복제되어 남습니다");
    await idle(page); assert.equal((await read()).pile, 1); assert.equal(await page.locator("[data-draw]").count(), 13);
    await fit(page); await shot(page, "03-thirteen");
    await page.keyboard.press("ArrowRight"); await page.keyboard.press("ArrowDown");
    assert.equal(await page.evaluate(() => document.activeElement.dataset.draw), "8");
    await page.keyboard.press("Enter"); await page.waitForTimeout(600);
    const savedDuringShow = await read(); assert.equal(savedDuringShow.selected.length, 1); assert.equal(savedDuringShow.piles.flat().length, 77);
    await page.reload(); await page.locator("[data-pile]").first().waitFor(); assert.deepEqual(await read(), savedDuringShow);
    assert(!await page.locator("#stage").evaluate(node => node.classList.contains("is-presenting")));
    assert.equal(await page.locator("#stage .card-front").count(), 0); assert.equal(await page.locator(".rail-slot.chosen").count(), 1);
    for (let round = 1; round < 3; round++) {
      await tap(page, "[data-pile='5']"); await fit(page); assert.equal(await page.locator("[data-draw]").count(), 12);
      await tap(page, "[data-draw='1']");
    }
    assert.equal(new Set((await read()).selected).size, 3); await fit(page); await shot(page, "04-closed-reading");
    await page.keyboard.press("2"); await page.locator(".show-turn").waitFor();
    assert.equal(await page.locator("[data-slot='1'] .slot-card").evaluate(node => getComputedStyle(node).visibility), "hidden");
    const flipFirst = await page.locator("#stage").screenshot({ path: path.join(OUT, "motion-turn-a.png") });
    await page.waitForTimeout(220);
    const flipSecond = await page.locator("#stage").screenshot({ path: path.join(OUT, "motion-turn-b.png") });
    const flipPixels = difference(flipFirst, flipSecond); assert(flipPixels > 2000, `뒤집기 움직임 부족: ${flipPixels}`);
    await idle(page); assert.equal(await page.locator(".show-turn").count(), 0);
    assert.deepEqual((await read()).revealed, [false, true, false]);
    assert(!await page.locator("#stage").evaluate(node => node.classList.contains("is-presenting")));
    assert.equal(await page.locator(".card-front").evaluate(node => getComputedStyle(node).transform), "none");
    assert.equal(await page.locator(".card-rotor").first().evaluate(node => getComputedStyle(node).transitionDuration), "0s");
    const beforeFocus = await read(); const smallWidth = (await page.locator("[data-focus='1']").boundingBox()).width;
    await tap(page, "[data-focus='1']");
    assert((await page.locator(".focused .card-button").boundingBox()).width > smallWidth * 1.2);
    assert.deepEqual(await read(), beforeFocus); assert.equal(await page.locator("#stage .card-front").count(), 1);
    await fit(page); await shot(page, "05-focus");
    await page.reload(); await page.locator(".focused").waitFor(); assert.deepEqual(await read(), beforeFocus);
    assert.equal(await page.locator("#focus-name").textContent(), await page.locator(".focused .card-title-ko").textContent());
    await tap(page, "#reveal-controls [data-reveal='0']", false); await page.locator(".show-turn").waitFor();
    const savedDuringTurn = await read(); assert.deepEqual(savedDuringTurn.revealed, [true, true, false]);
    await page.reload(); await page.locator(".focused").waitFor(); assert.deepEqual(await read(), savedDuringTurn);
    assert.equal(await page.locator(".show-turn").count(), 0); assert.equal(await page.locator("#stage .card-front").count(), 2);
    await tap(page, "#reveal-controls [data-reveal='2']"); assert.equal(await page.locator("#stage .card-front").count(), 3);
    await page.keyboard.press("Escape"); await idle(page); assert.equal((await read()).phase, "complete"); await fit(page); await shot(page, "06-three-stories");
    // 익숙한 대표 원화로 호흡·눈 마스크와 확대 구성을 함께 기록한다.
    await page.evaluate(key => {
      const state = JSON.parse(localStorage.getItem(key)); state.selected = ["major-00", "major-01", "cups-13"]; state.revealed = [true, true, true];
      localStorage.setItem(key, JSON.stringify(state)); localStorage.setItem("sheddy-lemon-tarot-salon-v1", JSON.stringify({ sound: false, focus: -1 }));
    }, SESSION);
    await page.reload(); await page.locator("[data-focus='0']").waitFor(); await shot(page, "07-approved-art");
    await page.mouse.move(WIDTH - 10, STAGE_HEIGHT - 10);
    const breathing = await page.locator(".character").first().evaluate(node => getComputedStyle(node).transform);
    await page.waitForTimeout(700); assert.notEqual(await page.locator(".character").first().evaluate(node => getComputedStyle(node).transform), breathing);
    await tap(page, "[data-focus='0']"); await fit(page); await shot(page, "08-fool-closeup");
    assert(Math.abs((await page.locator(".focused .card-button").boundingBox()).width - 192 * SCALE) < 1, "확대 카드가 소스 해상도에 맞게 렌더링되지 않습니다");
    assert.equal(await page.locator(".focused .blink-layer").count(), 1);
    await tap(page, "#overview"); await tap(page, "#sound"); assert.equal(await page.locator("#sound").getAttribute("aria-pressed"), "true");
    await tap(page, "#reset"); await tap(page, "[data-start='3']", false); await page.waitForTimeout(160);
    assert(await page.evaluate(() => window.__salonSounds >= 1 && window.__salonAudio.state === "running"));
    const stoppedAt = await read(); await tap(page, "#motion"); assert.deepEqual((await read()).piles, stoppedAt.piles);
    assert(!await page.locator("#stage").evaluate(node => node.classList.contains("is-presenting")));
    assert.equal(await page.locator(".show-card").count(), 0);
    assert(await page.evaluate(() => [...document.querySelector("#stage").getAnimations({ subtree: true })].every(animation => animation.playState !== "running")));
    await tap(page, "#sound"); await tap(page, "[data-pile='0']"); await fit(page);
    assert(!await page.locator("#stage").evaluate(node => node.classList.contains("is-presenting")));
    await tap(page, "#motion"); await tap(page, "[data-draw='0']", false); await page.waitForTimeout(90);
    assert(await page.locator("#stage").evaluate(node => node.classList.contains("is-presenting")));
    await tap(page, "#visibility"); assert.equal(await page.locator("#stage").evaluate(node => getComputedStyle(node).visibility), "hidden");
    assert.equal(await page.locator(".show-card").count(), 0); await tap(page, "#visibility");
    assert.equal(await page.locator("[data-pile]").count(), 6);
    const reduced = await browser.newContext({ viewport: { width: WIDTH, height: HEIGHT }, reducedMotion: "reduce" });
    const reducedPage = await reduced.newPage(); await reducedPage.goto(BASE); await reducedPage.locator("[data-start='1']").waitFor();
    assert.equal(await reducedPage.locator("#motion").getAttribute("aria-pressed"), "false");
    await tap(reducedPage, "[data-start='1']"); assert(!await reducedPage.locator("#stage").evaluate(node => node.classList.contains("is-presenting")));
    await tap(reducedPage, "#motion"); assert.equal(await reducedPage.locator("#motion").getAttribute("aria-pressed"), "true");
    await tap(reducedPage, "[data-pile='0']"); await tap(reducedPage, "[data-draw='0']");
    await tap(reducedPage, "#reveal-controls [data-reveal='0']", false); await reducedPage.locator(".show-turn").waitFor();
    await tap(reducedPage, "#motion"); assert.equal(await reducedPage.locator(".show-turn").count(), 0);
    assert.equal(await reducedPage.locator("[data-slot='0'] .slot-card").evaluate(node => getComputedStyle(node).visibility), "visible");
    assert.equal(await reducedPage.evaluate(key => JSON.parse(localStorage.getItem(key)).phase, SESSION), "complete");
    await tap(reducedPage, "#reset"); await tap(reducedPage, "[data-start='1']");
    await tap(reducedPage, "[data-pile='0']"); await tap(reducedPage, "[data-draw='0']");
    await tap(reducedPage, "#reveal-controls [data-reveal='0']"); assert.equal(await reducedPage.locator(".show-turn").count(), 0);
    assert.equal(await reducedPage.locator("#stage .card-front").count(), 1); await reduced.close();
    assert.deepEqual(errors, []);
    const video = page.video(); await context.close(); const videoPath = await video.path();
    const result = { passed: true, source: BASE, size: [WIDTH, HEIGHT], stage: [WIDTH, STAGE_HEIGHT], shuffleChangedPixels: shufflePixels,
      flipChangedPixels: flipPixels,
      verified: ["세 더미 셔플 실제 프레임", "카드 나누기", "서브덱 수량 숨김", "선택한 원본 숨김", "키보드 선택", "연출 중 복원", "공개 전 정보 숨김", "정방향 뒤집기", "뒤집기 중 복원", "뒤집기 중 정지", "모션 끈 상태에서 즉시 공개", "확대와 복원", "호흡과 눈 마스크", "종이 효과음", "모션 끄기와 건너뛰기", "숨김 중 취소", "동작 줄이기", "투명 모서리", "모든 장면 크기"], video: videoPath, browserErrors: errors };
    fs.writeFileSync(path.join(OUT, `salon-${WIDTH}-result.json`), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
