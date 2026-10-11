"use strict";
// 방송 영역만 기록한다. 실제 선택 흐름에서 바보 카드가 있는 덱을 골라 비교 시안을 남긴다.
const fs = require("node:fs"), path = require("node:path"), { chromium } = require("playwright");
const OUT = path.resolve(__dirname, "../output/tarot-widget/qa"), SESSION = "sheddy-lemon-tarot-session-v1";
const BASE = "http://127.0.0.1:8474/" + (process.argv.includes("--pages") ? "docs/" : "") + "tarot-widget/";
async function idle(page) { await page.waitForFunction(() => document.querySelector("#stage").getAttribute("aria-busy") !== "true"); }
async function tap(page, selector) {
  const box = await page.locator(selector).boundingBox(); await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2); await idle(page);
}
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 800, height: 450 }, reducedMotion: "no-preference", recordVideo: { dir: path.join(OUT, "motion-demo"), size: { width: 800, height: 450 } } });
    const page = await context.newPage(), errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(BASE); await page.locator("[data-start='1']").waitFor();
    await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.querySelectorAll("#stage img")].map(img => img.decode())); });
    await page.waitForTimeout(600); await tap(page, "[data-start='1']"); await page.mouse.move(790, 440);
    await page.waitForTimeout(550);
    const position = await page.evaluate(key => {
      const state = JSON.parse(localStorage.getItem(key));
      const pile = state.piles.findIndex(cards => cards.includes("major-00"));
      return { pile, card: state.piles[pile].indexOf("major-00") };
    }, SESSION);
    await tap(page, `[data-pile='${position.pile}']`); await page.mouse.move(790, 440); await page.waitForTimeout(600);
    await tap(page, `[data-draw='${position.card}']`); await page.mouse.move(790, 440); await page.waitForTimeout(550);
    await page.keyboard.press("1"); await page.locator(".show-turn").waitFor(); await idle(page);
    await page.mouse.move(790, 440); await page.waitForTimeout(900); await tap(page, "[data-focus='0']");
    await page.mouse.move(790, 440); await page.waitForTimeout(1400);
    await page.locator("#stage").screenshot({ path: path.join(OUT, "motion-2-focus.png") });
    const video = page.video(); await context.close();
    const destination = path.join(OUT, "motion-2-demo.webm"); await video.saveAs(destination);
    if (errors.length) throw Error(errors.join("\n"));
    console.log(JSON.stringify({ video: destination, source: BASE, viewport: [800, 450], browserErrors: errors }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
