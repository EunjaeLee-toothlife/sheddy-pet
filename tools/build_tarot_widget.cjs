"use strict";
// 승인된 78장 데이터와 필요한 파일만 묶어 정적 Pages 위젯을 만든다.
const fs = require("node:fs"), path = require("node:path"), vm = require("node:vm"), crypto = require("node:crypto");
const ROOT = path.resolve(__dirname, "..");
function collect() {
  const deck = { version: 1, back: "frame-study/art/a-classic-back-v1.png", cards: [], blinks: {
    "major-00": { file: "art/fool-blink.png", eyes: [[264, 290, 38, 43], [350, 311, 40, 43]] },
    "major-01": { file: "art/magician-blink.png", eyes: [[283, 334, 38, 44], [374, 351, 40, 44]] },
    "cups-13": { file: "art/queen-cups-blink.png", eyes: [[294, 356, 34, 43], [374, 381, 39, 43]] }
  } };
  for (const name of ["major", "wands", "cups", "swords", "pentacles"]) {
    const context = { window: {} };
    vm.runInNewContext(fs.readFileSync(path.join(ROOT, "tarot-study", `${name}-data.js`), "utf8"), context, { timeout: 1000 });
    deck.cards.push(...context.window.TAROT_SAMPLES); Object.assign(deck.blinks, context.window.TAROT_BLINKS);
  }
  if (deck.cards.length !== 78 || new Set(deck.cards.map(card => card.id)).size !== 78) throw Error("78장 구성을 확인해 주세요.");
  return deck;
}
function assets(deck) {
  return [...new Set([deck.back, ...deck.cards.flatMap(card => [card.atlas, card.scene_file, card.scene_atlas, ...(card.overlays || []).map(layer => layer.file)]), ...Object.values(deck.blinks).map(blink => blink.file)].filter(Boolean))].sort();
}
function write(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.tmp`; fs.writeFileSync(temporary, value); fs.renameSync(temporary, file);
}
async function main() {
  const deck = collect(), files = assets(deck);
  for (const file of files) if (!fs.existsSync(path.join(ROOT, "tarot-study", file))) throw Error(`파일 누락: ${file}`);
  write(path.join(ROOT, "tarot-widget/deck.json"), JSON.stringify(deck, null, 2) + "\n");
  console.log(`78장 목록 저장 · 원화 ${files.length}개`);
  if (!process.argv.includes("--pages")) return;
  const sharp = require("sharp");
  const docs = path.join(ROOT, "docs"), manifest = { version: 1, encoding: "lossless-webp", cards: 78, assets: [] };
  const rewrite = new Map();
  for (const [index, file] of files.entries()) {
    const source = path.join(ROOT, "tarot-study", file), relative = file.replace(/\.png$/i, ".webp");
    const target = path.join(docs, "tarot-study", relative), hash = crypto.createHash("sha256").update(fs.readFileSync(source)).digest("hex");
    const marker = `${target}.source-sha256`;
    if (!fs.existsSync(target) || !fs.existsSync(marker) || fs.readFileSync(marker, "utf8") !== hash) {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      const temporary = `${target}.tmp`;
      // 무손실 압축으로 보이는 색상·알파·상징을 유지한다.
      await sharp(source).webp({ lossless: true, effort: 4 }).toFile(temporary);
      fs.renameSync(temporary, target); fs.writeFileSync(marker, hash);
    }
    rewrite.set(file, relative); manifest.assets.push({ file: relative, source_sha256: hash, bytes: fs.statSync(target).size });
    if ((index + 1) % 10 === 0 || index + 1 === files.length) console.log(`무손실 이미지 ${index + 1}/${files.length}`);
  }
  for (const card of deck.cards) {
    for (const key of ["atlas", "scene_file", "scene_atlas"]) if (card[key]) card[key] = rewrite.get(card[key]);
    for (const layer of card.overlays || []) layer.file = rewrite.get(layer.file);
  }
  for (const blink of Object.values(deck.blinks)) blink.file = rewrite.get(blink.file);
  deck.back = rewrite.get(deck.back);
  for (const file of ["study.css", "major.css", "minor.css", "classic-gilt.css", "classic-gilt.js", "fonts/PirataOne-Regular.ttf", "fonts/NanumMyeongjo-ExtraBold.ttf", "fonts/CinzelDecorative-Regular.ttf", "fonts/pirataone-OFL.txt", "fonts/nanummyeongjo-OFL.txt", "fonts/cinzeldecorative-OFL.txt"]) {
    const source = path.join(ROOT, "tarot-study", file), target = path.join(docs, "tarot-study", file);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    if (file.endsWith("-OFL.txt")) write(target, fs.readFileSync(source, "utf8").replace(/[ \t]+(?=\r?$)/gm, ""));
    else fs.copyFileSync(source, target);
  }
  for (const file of ["index.html", "widget.css", "salon.css", "cards.js", "game.js", "show.js", "widget.js"]) {
    const target = path.join(docs, "tarot-widget", file); fs.mkdirSync(path.dirname(target), { recursive: true }); fs.copyFileSync(path.join(ROOT, "tarot-widget", file), target);
  }
  write(path.join(docs, "tarot-widget/deck.json"), JSON.stringify(deck, null, 2) + "\n");
  write(path.join(docs, "tarot-widget/build-manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
  write(path.join(docs, ".nojekyll"), "");
  console.log(`Pages 정적 배포본 생성 완료 · ${(manifest.assets.reduce((sum, asset) => sum + asset.bytes, 0) / 1024 / 1024).toFixed(1)} MiB`);
}
if (require.main === module) main().catch(error => { console.error(error); process.exitCode = 1; });
module.exports = { collect, assets };
