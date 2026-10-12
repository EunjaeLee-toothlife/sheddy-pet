"use strict";
// 무손실 배포본이 원화의 보이는 RGB·알파와 실제로 같은지 전 파일에서 검사한다.
const fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto"), assert = require("node:assert/strict");
const sharp = require("sharp");
const ROOT = path.resolve(__dirname, "..");
(async function () {
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "docs/tarot-widget/build-manifest.json"), "utf8"));
  for (const [index, item] of manifest.assets.entries()) {
    const original = path.join(ROOT, "tarot-study", item.file.replace(/\.webp$/, ".png"));
    const output = path.join(ROOT, "docs/tarot-study", item.file);
    assert.equal(crypto.createHash("sha256").update(fs.readFileSync(original)).digest("hex"), item.source_sha256);
    assert.equal(fs.statSync(output).size, item.bytes);
    const [a, b] = await Promise.all([original, output].map(file => sharp(file).ensureAlpha().raw().toBuffer({ resolveWithObject: true })));
    assert.deepEqual(a.info, b.info);
    for (let pixel = 0; pixel < a.data.length; pixel += 4) {
      if (a.data[pixel + 3] !== b.data[pixel + 3]) throw Error(`${item.file} 알파 차이: ${pixel / 4}`);
      // 완전 투명한 픽셀의 숨은 RGB는 WebP 압축에서 정리될 수 있다.
      if (a.data[pixel + 3]) for (let channel = 0; channel < 3; channel++) {
        if (a.data[pixel + channel] !== b.data[pixel + channel]) throw Error(`${item.file} 색상 차이: ${pixel / 4}`);
      }
    }
    if ((index + 1) % 25 === 0 || index + 1 === manifest.assets.length) console.log(`원화·배포본 보이는 픽셀/알파 동일: ${index + 1}/${manifest.assets.length}`);
  }
  console.log("78장 전체 원화·깜빡임·상징·뒷면의 무손실 압축 검증 통과");
})().catch(error => { console.error(error); process.exitCode = 1; });
