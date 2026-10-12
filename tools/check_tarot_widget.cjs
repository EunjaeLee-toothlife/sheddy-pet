"use strict";
// 추첨 불변식, 실제 UI, 복원, 78장 레이어와 Pages 상대 경로를 함께 검사한다.
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const { chromium } = require("playwright");
const { collect } = require("./build_tarot_widget.cjs");
const game = require("../tarot-widget/game.js");
const ROOT = path.resolve(__dirname, ".."), OUT = path.join(ROOT, "output/tarot-widget/qa");
const deck = collect(), ids = deck.cards.map(card => card.id);
function rules() {
  let seed = 271828;
  const rng = limit => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed % limit; };
  for (let trial = 0; trial < 600; trial++) {
    const target = trial % 2 ? 1 : 3;
    let state = game.apply(game.create(), { type: "start", count: target }, ids, rng);
    for (let draw = 0; draw < target; draw++) {
      const available = state.piles.flat();
      assert.equal(available.length, 78 - draw);
      assert.equal(new Set(available).size, available.length);
      assert(state.piles.every(pile => pile.length >= 11 && pile.length <= 13));
      assert(state.selected.every(id => !available.includes(id)));
      state = game.apply(state, { type: "pile", index: rng(6) }, ids, rng);
      const before = structuredClone(state);
      const restored = JSON.parse(JSON.stringify(state));
      assert(game.valid(restored, ids));
      state = game.apply(restored, { type: "draw", index: rng(state.piles[state.pile].length) }, ids, rng);
      assert.deepEqual(restored, before);
    }
    assert.equal(state.phase, "reveal"); assert.equal(new Set(state.selected).size, target);
    assert(state.revealed.every(value => !value));
    assert.throws(() => game.apply(state, { type: "draw", index: 0 }, ids, rng));
    for (let index = target - 1; index >= 0; index--) state = game.apply(state, { type: "reveal", index }, ids, rng);
    assert.equal(state.phase, "complete"); assert(state.revealed.every(Boolean));
    assert.throws(() => game.apply(state, { type: "reveal", index: 0 }, ids, rng));
  }
  const duplicate = game.apply(game.create(), { type: "start", count: 3 }, ids, rng);
  duplicate.piles[0][0] = duplicate.piles[0][1]; assert(!game.valid(duplicate, ids));
  const badTarget = { ...game.create(), target: 3 }; assert(!game.valid(badTarget, ids));
  console.log("추첨·중복 제외·한 장씩 공개·복원 규칙 600회 통과");
}
async function loaded(page) {
  await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.querySelectorAll("#stage img")].map(img => img.decode())); });
}
async function idle(page) { await page.waitForFunction(() => document.querySelector("#stage").getAttribute("aria-busy") !== "true"); }
async function click(page, selector) { await page.locator(selector).click(); await idle(page); }
async function snapshot(page, name) { await idle(page); await loaded(page); await page.locator("#stage").screenshot({ path: path.join(OUT, `${name}.png`) }); }
async function main() {
  rules(); fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true });
  const issues = [];
  const context = await browser.newContext({ viewport: { width: 800, height: 600 }, reducedMotion: "no-preference" });
  const page = await context.newPage();
  page.on("pageerror", error => issues.push(error.message));
  page.on("response", response => { if (response.status() >= 400) issues.push(`${response.status()} ${response.url()}`); });
  const base = process.argv.includes("--pages") ? "http://127.0.0.1:8474/docs/tarot-widget/" : "http://127.0.0.1:8474/tarot-widget/";
  const read = () => page.evaluate(() => JSON.parse(localStorage.getItem("sheddy-lemon-tarot-session-v1")));
  try {
    await page.goto(base + "?preview=1"); await page.locator("[data-start='3']").waitFor();
    await snapshot(page, "01-ready");
    assert.equal(await page.locator("#stage").evaluate(node => node.getBoundingClientRect().height), 450);
    assert.equal(await page.locator(".controller").evaluate(node => node.getBoundingClientRect().top), 450);
    assert(await page.evaluate(() => document.documentElement.scrollHeight === innerHeight));
    await click(page, "[data-start='1']");
    assert.equal(await page.locator("[data-pile]").count(), 6);
    await click(page, "[data-pile='2']"); assert.equal(await page.locator("[data-draw]").count(), 13);
    await snapshot(page, "02-pick");
    const original = (await read()).piles;
    await click(page, "#back"); assert.deepEqual((await read()).piles, original);
    await click(page, "[data-pile='2']"); await click(page, "[data-draw='5']");
    assert.equal(await page.locator("#stage [data-id]").count(), 0);
    assert.equal(await page.locator("#stage .card-front").count(), 0);
    const one = await read(); await page.reload(); await page.locator("[data-slot='0']").waitFor();
    assert.deepEqual(await read(), one);
    await page.locator("#reveal-controls [data-reveal='0']").click(); await page.locator("#stage .card-front").first().waitFor({ state: "attached" }); await idle(page);
    await snapshot(page, "03-one"); assert.equal((await read()).phase, "complete");
    assert.equal(await page.locator(".card-front").evaluate(node => getComputedStyle(node).transform), "none");
    assert.equal(await page.locator(".reading-slot .card-rotor").evaluate(node => getComputedStyle(node).transitionDuration), "0s");
    await click(page, "#reset"); await click(page, "[data-start='3']");
    await page.locator("#title").fill("레몬의 오늘"); await page.locator("#set-title").click();
    await snapshot(page, "04-piles");
    for (let i = 0; i < 3; i++) {
      const state = await read(); assert.equal(state.piles.flat().length, 78 - i);
      assert(state.selected.every(id => !state.piles.flat().includes(id)));
      await click(page, "[data-pile='5']");
      assert.equal(await page.locator("[data-draw]").count(), i ? 12 : 13);
      await click(page, "[data-draw='0']");
      if (i === 0) { const saved = await read(); await page.reload(); await page.locator("[data-pile]").first().waitFor(); assert.deepEqual(await read(), saved); }
    }
    assert.equal(new Set((await read()).selected).size, 3);
    await snapshot(page, "05-unrevealed");
    const movingCard = await page.locator("#stage [data-reveal='2']").boundingBox();
    await page.mouse.click(movingCard.x + movingCard.width / 2, movingCard.y + movingCard.height / 2); await page.locator("#stage .card-front").first().waitFor({ state: "attached" }); await idle(page);
    assert.deepEqual((await read()).revealed, [false, false, true]);
    await page.locator("#reveal-controls [data-reveal='0']").click(); await idle(page); assert.equal(await page.locator("#stage .card-front").count(), 2);
    await page.locator("#reveal-controls [data-reveal='1']").click(); await idle(page); assert.equal(await page.locator("#stage .card-front").count(), 3);
    await snapshot(page, "06-three");
    const motionBefore = await page.locator(".character").first().evaluate(node => getComputedStyle(node).transform);
    await page.waitForTimeout(950);
    const motionAfter = await page.locator(".character").first().evaluate(node => getComputedStyle(node).transform);
    assert.notEqual(motionBefore, motionAfter);
    await page.locator("#motion").click();
    assert.equal(await page.locator(".character").first().evaluate(node => getComputedStyle(node).animationPlayState), "paused");
    await page.locator("#visibility").click(); assert.equal(await page.locator("#stage").evaluate(node => getComputedStyle(node).visibility), "hidden");
    assert(await page.locator("#visibility").isVisible());
    await page.reload(); await page.locator("#visibility").waitFor(); assert.equal((await read()).visible, false);
    await page.locator("#visibility").click(); await page.locator("#motion").click();
    await click(page, "#reset"); await click(page, "[data-start='3']");
    await page.locator("#reset").click(); assert.equal((await read()).phase, "pile");
    await page.locator("#reset").click(); assert.equal((await read()).phase, "ready");
    // 전체 카드에서 원본과 동일한 상징 레이어 수, 올바른 이미지 경로를 확인한다.
    await page.evaluate(() => document.body.classList.add("motion-paused"));
    for (const card of deck.cards) {
      await page.evaluate(async id => {
        const data = await (await fetch("deck.json")).json(), item = data.cards.find(card => card.id === id);
        const node = LemonTarotCards.makeFront(item, data.blinks[id], 0); document.querySelector("#table").replaceChildren(node);
        node.style.width = "350px"; await Promise.all([...node.querySelectorAll("img")].map(img => img.decode()));
      }, card.id);
      assert.equal(await page.locator(".symbol-layer").count(), (card.overlays || []).length);
      assert.equal(await page.locator(".fixed-foreground").count(), card.fixed_foreground ? 1 : 0);
      assert.equal(await page.locator(".gilt-art-overlay").count(), 1);
      assert.equal(await page.locator("#stage .card-title-ko").textContent(), card.korean);
      assert.equal(await page.locator("#table .card-button").evaluate(node => getComputedStyle(node).opacity), "1");
    }
    await page.setViewportSize({ width: 390, height: 800 }); await page.reload(); await page.locator("[data-start='3']").waitFor();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await click(page, "[data-start='1']"); await click(page, "[data-pile='0']"); assert.equal(await page.locator("[data-draw]").count(), 13);
    await page.screenshot({ path: path.join(OUT, "07-small.png"), fullPage: true });
    // 저장소가 제한돼도 추첨은 가능하고 저장 제한을 분명히 알린다.
    const limited = await browser.newContext({ viewport: { width: 1280, height: 1000 } });
    await limited.addInitScript(() => { Storage.prototype.setItem = () => { throw Error("저장 제한"); }; });
    const limitedPage = await limited.newPage(); await limitedPage.goto(base);
    assert.equal(await limitedPage.locator("#stage").evaluate(node => getComputedStyle(node).backgroundColor), "rgba(0, 0, 0, 0)");
    assert.equal(await limitedPage.locator("body").evaluate(node => getComputedStyle(node).backgroundColor), "rgba(0, 0, 0, 0)");
    await click(limitedPage, "[data-start='1']"); assert.equal(await limitedPage.locator("[data-pile]").count(), 6);
    assert.match(await limitedPage.locator("#error").textContent(), /자동 저장이 제한/); await limited.close();
    // 지연된 그림 준비를 초기화한 뒤 옛 콜백이 새 추첨을 덮지 않아야 한다.
    const slow = await browser.newContext({ viewport: { width: 1920, height: 1360 } });
    let release; const gate = new Promise(resolve => { release = resolve; });
    await slow.route(/atlas/, async route => { await gate; await route.abort(); });
    const slowPage = await slow.newPage(); await slowPage.goto(base);
    await click(slowPage, "[data-start='1']"); await click(slowPage, "[data-pile='0']");
    await click(slowPage, "[data-draw='0']"); await slowPage.locator("#reveal-controls [data-reveal='0']").click();
    assert.match(await slowPage.locator("#status").textContent(), /준비하고/);
    await slowPage.locator("#reset").click(); await slowPage.locator("#reset").click();
    await slowPage.locator("[data-start='3']").click(); assert.equal(await slowPage.locator("[data-pile]").count(), 6);
    release(); await slowPage.waitForTimeout(100); assert.equal(await slowPage.locator("[data-pile]").count(), 6); await slow.close();
    await page.evaluate(() => localStorage.setItem("sheddy-lemon-tarot-session-v1", "잘못된 저장값"));
    await page.reload(); await page.locator("[data-start='1']").waitFor(); assert.match(await page.locator("#error").textContent(), /복원하지 못/);
    assert.deepEqual(issues, []);
    fs.writeFileSync(path.join(OUT, "result.json"), JSON.stringify({ passed: true, pages: process.argv.includes("--pages"), cards: 78, ruleTrials: 600, browserErrors: issues, checkedAt: new Date().toISOString() }, null, 2));
    console.log("브라우저 추첨·복원·공개·실제 움직임·78장 레이어·투명 송출 크기 검증 통과");
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
