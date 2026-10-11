"use strict";
// 카드를 테이블 위에서 다루는 연출이다. 추첨 결과는 시작 전에 이미 저장된다.
(function () {
  const EASE = "cubic-bezier(.22,1,.36,1)";
  function create({ stage, back, onBusy, enabled }) {
    const layer = document.querySelector("#presentation"), active = new Set(), held = [];
    let generation = 0, busy = false, audio = null, soundOn = false;
    const live = token => token === generation;
    function cue(kind) {
      if (!soundOn || !audio || audio.state !== "running") return;
      // 얇은 종이 마찰음. 선율 대신 테이블 위 동작의 질감을 더한다.
      const duration = kind === "shuffle" ? .18 : .1, start = audio.currentTime;
      const buffer = audio.createBuffer(1, Math.ceil(audio.sampleRate * duration), audio.sampleRate);
      const samples = buffer.getChannelData(0);
      for (let index = 0; index < samples.length; index++) samples[index] = Math.random() * 2 - 1;
      const noise = audio.createBufferSource(), filter = audio.createBiquadFilter(), gain = audio.createGain();
      noise.buffer = buffer; filter.type = "bandpass"; filter.frequency.value = 1500; filter.Q.value = .65;
      gain.gain.setValueAtTime(0, start); gain.gain.linearRampToValueAtTime(.035, start + .012);
      gain.gain.exponentialRampToValueAtTime(.0001, start + duration);
      noise.connect(filter); filter.connect(gain); gain.connect(audio.destination); noise.start(start);
      noise.onended = () => { noise.disconnect(); filter.disconnect(); gain.disconnect(); };
    }
    function setSound(value) {
      soundOn = value;
      if (value) {
        try { audio ||= new (window.AudioContext || window.webkitAudioContext)(); audio.resume().catch(() => {}); }
        catch { soundOn = false; }
      }
      return soundOn;
    }
    async function animate(node, frames, options, token) {
      if (!live(token) || !enabled()) return;
      const animation = node.animate(frames, { easing: EASE, ...options }); active.add(animation);
      try { await animation.finished; } catch {}
      finally { animation.cancel(); active.delete(animation); }
    }
    function hold(node, property, value) {
      held.push({ node, property, value: node.style[property] }); node.style[property] = value;
    }
    function clean() {
      active.forEach(animation => animation.cancel()); active.clear();
      for (const item of held.splice(0)) item.node.style[item.property] = item.value;
      layer.replaceChildren(); stage.classList.remove("is-shuffling", "is-presenting");
    }
    function cancel(notify = true) {
      generation++; clean(); busy = false; if (notify) onBusy(false);
    }
    async function run(task) {
      cancel(false); const token = generation; busy = true; stage.classList.add("is-presenting"); onBusy(true);
      try { await task(token); }
      finally { if (live(token)) { clean(); busy = false; onBusy(false); } }
    }
    function tokenCard(width, x, y, packet = false) {
      const node = document.createElement("div"); node.className = `show-card${packet ? " show-packet" : ""}`;
      node.style.cssText = `width:${width}px;left:${x}px;top:${y}px`;
      const card = window.LemonTarotCards.makeBack(back, "");
      const button = card.querySelector("button"), shell = document.createElement("div"); shell.className = "card-button";
      shell.append(...button.childNodes); button.replaceWith(shell); node.append(card); layer.append(node); return node;
    }
    async function shuffle(token) {
      if (!live(token) || !enabled()) return;
      layer.replaceChildren(); stage.classList.add("is-shuffling"); cue("shuffle");
      const scale = stage.clientWidth / 800, x = 353 * scale, y = 153 * scale;
      const label = document.createElement("div"); label.className = "shuffle-caption";
      label.innerHTML = '<span>카드를 고르게 섞고 있어요</span><small>LEMON TAROT</small>'; layer.append(label);
      const packets = [0, 1, 2].map(index => {
        const node = tokenCard(94 * scale, x, y, true); node.style.zIndex = index + 1; return node;
      });
      // 세 더미를 짧게 벌린 뒤 순서를 바꾸어 포갠다. 회전·바운스·크기 변화는 쓰지 않는다.
      const frames = [
        [[0, 4], [0, 4], [0, 4], [0, 0], [0, 0]],
        [[2, 2], [-99, 2], [-99, 2], [2, -3], [2, -3]],
        [[4, 0], [4, -4], [101, -4], [101, -4], [4, -6]]
      ];
      await Promise.all(packets.map((node, index) => animate(node, frames[index].map(([dx, dy], frame) => ({
        transform: `translate(${dx * scale}px,${dy * scale}px)`, offset: [0, .28, .48, .73, 1][frame]
      })), { duration: 780, fill: "both", easing: "cubic-bezier(.45,0,.2,1)" }, token)));
      if (!live(token)) return;
      // 끝난 셔플의 더미가 다음 분할 장면의 출발점으로 남는다.
      packets.forEach((node, index) => node.style.transform = `translate(${index * 2 * scale}px,${-index * 3 * scale}px)`);
      label.remove(); stage.classList.remove("is-shuffling");
    }
    async function enter(selector, token, kind = "deal", origin) {
      if (!live(token) || !enabled()) return;
      const area = stage.getBoundingClientRect(), nodes = [...stage.querySelectorAll(selector)];
      const scale = area.width / 800;
      const anchor = origin || { left: area.left + 353 * scale, top: area.top + 153 * scale, width: 94 * scale };
      // 도착 지점의 실제 카드가 출발 더미를 이어받아 복제 카드가 겹치지 않는다.
      layer.replaceChildren();
      await Promise.all(nodes.map((node, index) => {
        const card = node.querySelector(".slot-card,.widget-card") || node;
        const box = card.getBoundingClientRect(), outer = node.getBoundingClientRect();
        const delay = kind === "reading" ? index * 45 : index * (nodes.length > 6 ? 20 : 28);
        const dx = kind === "reading" ? 0 : anchor.left - box.left;
        const dy = kind === "reading" ? 9 * scale : anchor.top - box.top;
        const ratio = kind === "reading" ? 1 : anchor.width / box.width;
        node.style.transformOrigin = `${box.left - outer.left}px ${box.top - outer.top}px`;
        const move = animate(node, [
          { transform: `translate(${dx}px,${dy}px) scale(${ratio})`, opacity: kind === "reading" ? 0 : 1 },
          { transform: "none", opacity: 1 }
        ], { duration: kind === "reading" ? 300 : 420, delay, fill: "backwards" }, token);
        const label = node.querySelector(".deck-label,.pick-number,.slot-label");
        const caption = label ? animate(label, [{ opacity: 0 }, { opacity: 1 }], { duration: 140, delay: delay + 260, fill: "backwards" }, token) : null;
        return Promise.all([move, caption]);
      }));
    }
    async function fly(rect, destination, token, kind, source) {
      if (!rect || !live(token) || !enabled()) return null;
      layer.replaceChildren(); cue(kind);
      const area = stage.getBoundingClientRect(), scale = area.width / 800, to = destination?.getBoundingClientRect();
      const targetWidth = to ? to.width : 94 * scale;
      const targetX = to ? to.left - area.left : 353 * scale;
      const targetY = to ? to.top - area.top : 153 * scale;
      const startX = rect.left - area.left, startY = rect.top - area.top;
      const node = tokenCard(rect.width, startX, startY, kind === "pile");
      const selected = source?.closest(".pick-slot,.deck-button") || source;
      if (selected) hold(selected, "visibility", "hidden");
      const others = [...stage.querySelectorAll(".deck-button,.pick-slot")].filter(item => item !== selected);
      const soften = others.map(item => {
        hold(item, "opacity", ".3");
        return animate(item, [{ opacity: 1 }, { opacity: .3 }], { duration: 170 }, token);
      });
      const ratio = targetWidth / rect.width;
      // 작은 들림 후 한 번에 착지한다. 선택한 원본은 숨겨 복제처럼 보이지 않게 한다.
      const frames = [
        { transform: "translate(0,0) scale(1)" },
        { transform: `translate(0,${-3 * scale}px) scale(1)`, offset: .2 },
        { transform: `translate(${targetX - startX + (targetWidth - rect.width) / 2}px,${targetY - startY + (targetWidth * 12 / 7 - rect.height) / 2}px) scale(${ratio})` }
      ];
      await Promise.all([animate(node, frames, { duration: kind === "pile" ? 360 : 440, fill: "forwards" }, token), ...soften]);
      if (!live(token)) return null;
      node.style.transform = frames[2].transform;
      return { left: area.left + targetX, top: area.top + targetY, width: targetWidth };
    }
    async function focus(previous, token) {
      if (!live(token) || !enabled()) return;
      const cards = [...stage.querySelectorAll(".reading-slot")].map(node => {
        const card = node.querySelector(".slot-card"), old = previous.get(node.dataset.slot), now = card.getBoundingClientRect();
        if (!old || !now.width) return;
        return animate(card, [{ transform: `translate(${old.left - now.left}px,${old.top - now.top}px) scale(${old.width / now.width})` }, { transform: "none" }], { duration: 420 }, token);
      });
      const caption = stage.querySelector(stage.classList.contains("is-focused") ? ".focus-caption" : ".stage-heading");
      cards.push(animate(caption, [{ opacity: 0, transform: "translateY(4px)" }, { opacity: 1, transform: "none" }], { duration: 240, delay: 120, fill: "backwards" }, token));
      await Promise.all(cards);
    }
    async function reveal(rect, slot, card, blink, token) {
      if (!rect || !slot || !live(token) || !enabled()) return;
      cue("reveal"); const area = stage.getBoundingClientRect();
      const turn = document.createElement("div"); turn.className = "show-turn";
      turn.style.cssText = `width:${rect.width}px;left:${rect.left - area.left}px;top:${rect.top - area.top}px`;
      const rotor = document.createElement("div"); rotor.className = "turn-rotor";
      for (const [side, artwork] of [["back", window.LemonTarotCards.makeBack(back, "")], ["front", window.LemonTarotCards.makeFront(card, blink, 0)]]) {
        const face = document.createElement("div"); face.className = `turn-face turn-${side}`;
        const button = artwork.querySelector("button"), shell = document.createElement("div"); shell.className = "card-button";
        shell.append(...button.childNodes); button.replaceWith(shell); face.append(artwork); rotor.append(face);
      }
      turn.append(rotor); layer.append(turn); hold(slot, "visibility", "hidden");
      // 앞면 전체를 한 면으로 뒤집는다. 원화 속 소품과 별도 레이어도 함께 유지된다.
      await Promise.all([
        animate(rotor, [{ transform: "rotateY(0deg)" }, { transform: "rotateY(180deg)" }], { duration: 560, easing: "cubic-bezier(.4,0,.2,1)", fill: "forwards" }, token),
        animate(turn, [{ transform: "translateY(0)" }, { transform: "translateY(-3px)", offset: .45 }, { transform: "translateY(0)" }], { duration: 560, easing: "ease-in-out" }, token)
      ]);
    }
    return Object.freeze({ run, cancel, live, shuffle, enter, fly, focus, reveal, setSound, get busy() { return busy; } });
  }
  window.LemonTarotShow = Object.freeze({ create });
})();
