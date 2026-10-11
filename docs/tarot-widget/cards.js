"use strict";
// 승인된 스터디의 배치·눈 마스크·고정 전경·상징 레이어를 그대로 조립한다.
(function () {
  const base = new URL("../tarot-study/", location.href);
  function asset(file) { return new URL(file, base).href; }
  function image(file, className = "", description = "") {
    const node = document.createElement("img");
    node.src = asset(file); node.className = className; node.alt = description;
    node.draggable = false;
    node.addEventListener("error", () => window.dispatchEvent(new CustomEvent("tarot-image-error")));
    return node;
  }
  function makeBack(back, label) {
    const article = document.createElement("article");
    article.className = "sample classic-gilt widget-card";
    article.innerHTML = `<button class="card-button" type="button"><div class="card-rotor"><div class="card-face card-back">${window.LEMON_GILT.back(asset(back))}</div></div></button>`;
    article.querySelector("button").setAttribute("aria-label", label);
    article.querySelectorAll("img").forEach(node => node.addEventListener("error", () => window.dispatchEvent(new CustomEvent("tarot-image-error"))));
    return article;
  }
  function makeFront(sample, blinkSpec, index) {
    const article = document.createElement("article");
    article.className = "sample classic-gilt widget-card revealed";
    article.dataset.id = sample.id;
    const vars = { "--foreground-clip": sample.foreground_clip, "--figure-scale-y": sample.foreground_scale_y,
      "--figure-offset-x": sample.foreground_offset_x ? `${sample.foreground_offset_x}%` : undefined,
      "--figure-offset-y": sample.foreground_offset_y ? `${sample.foreground_offset_y}%` : undefined,
      "--figure-scale": sample.foreground_scale, "--figure-origin": sample.foreground_origin,
      "--phase": `${-(index % 7) * .63}s` };
    for (const [key, value] of Object.entries(vars)) if (value !== undefined) article.style.setProperty(key, value);
    article.innerHTML = `<button class="card-button" type="button"><div class="card-rotor"><div class="card-face card-front">${window.LEMON_GILT.margins()}<div class="card-numeral"></div><div class="art-window"><div class="scene"></div><div class="character"></div><div class="effect"></div>${window.LEMON_GILT.overlay()}</div><div class="card-title-block"><div class="card-title-ko"></div><div class="card-title"></div></div></div></div></button>`;
    article.querySelector("button").setAttribute("aria-label", `${sample.korean} · 공개됨 · 정방향`);
    article.querySelector(".card-numeral").textContent = sample.numeral;
    article.querySelector(".card-title-ko").textContent = sample.korean;
    article.querySelector(".card-title").textContent = window.LEMON_GILT.title(sample.title);
    const art = article.querySelector(".art-window"), moving = article.querySelector(".character"), scene = article.querySelector(".scene");
    scene.append(image(sample.scene_file || sample.scene_atlas || sample.atlas, sample.scene_file ? "scenery-image" : "atlas"));
    moving.append(image(sample.atlas, "atlas"));
    const effect = article.querySelector(".effect"); effect.className = `effect ${sample.effect}`;
    if (blinkSpec) {
      const blink = document.createElement("div"); blink.className = "blink-layer";
      const [width, height] = blinkSpec.panel || [724, 1086];
      blink.style.maskImage = blinkSpec.eyes.map(([x, y, rx, ry]) => `radial-gradient(ellipse ${rx / width * 100}% ${ry / height * 100}% at ${x / width * 100}% ${y / height * 100}%, black 75%, transparent 100%)`).join(",");
      blink.append(image(blinkSpec.file, "atlas")); moving.append(blink);
    }
    if (sample.fixed_foreground) {
      const split = sample.fixed_foreground.split;
      moving.style.clipPath = `inset(0 0 ${100 - split}% 0)`; moving.style.transformOrigin = `50% ${split}%`;
      const fixed = document.createElement("div"); fixed.className = "fixed-foreground";
      fixed.style.clipPath = `inset(${split}% 0 0 0)`; fixed.append(image(sample.atlas, "atlas")); art.append(fixed);
    }
    for (const layer of sample.overlays || []) {
      const overlay = document.createElement("div"); overlay.className = "symbol-layer";
      if (layer.clip) overlay.style.clipPath = layer.clip;
      if (layer.mask) overlay.style.maskImage = layer.mask;
      if (layer.offset_x || layer.offset_y) overlay.style.translate = `${layer.offset_x || 0}% ${layer.offset_y || 0}%`;
      if (layer.scale) { overlay.style.transform = `scale(${layer.scale})`; overlay.style.transformOrigin = layer.origin; }
      overlay.append(image(layer.file, layer.atlas_scene ? "atlas" : "", layer.description)); art.append(overlay);
    }
    if (["water", "water-shine"].includes(sample.effect)) scene.append(effect);
    else if (sample.effect !== "none") for (let i = 0; i < 10; i++) {
      const particle = document.createElement("span");
      particle.className = sample.effect === "petal" || sample.id === "major-00" ? "effect particle petal" : "effect particle";
      particle.style.cssText = `left:${25 + (i * 17) % 55}%;top:${18 + (i * 13) % 50}%;animation-delay:-${i * .7}s`;
      art.append(particle);
    }
    return article;
  }
  async function preload(sample, blinkSpec) {
    const files = new Set([sample.atlas, sample.scene_file, sample.scene_atlas, blinkSpec?.file,
      ...(sample.overlays || []).map(layer => layer.file)].filter(Boolean));
    await Promise.all([...files].map(async file => { const node = new Image(); node.src = asset(file); await node.decode(); }));
  }
  window.LemonTarotCards = Object.freeze({ makeBack, makeFront, preload });
})();
