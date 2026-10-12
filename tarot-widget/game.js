"use strict";
// 추첨 규칙은 화면과 분리해 새로고침 복원과 검증에서도 같은 규칙을 쓴다.
(function (root) {
  const VERSION = 1;
  function integer(limit) {
    const ceiling = Math.floor(0x100000000 / limit) * limit;
    const buffer = new Uint32Array(1);
    do { root.crypto.getRandomValues(buffer); } while (buffer[0] >= ceiling);
    return buffer[0] % limit;
  }
  function shuffle(cards, random = integer) {
    const result = [...cards];
    for (let i = result.length - 1; i > 0; i--) {
      const j = random(i + 1);
      if (!Number.isInteger(j) || j < 0 || j > i) throw Error("잘못된 난수입니다.");
      [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
  }
  function partition(cards) {
    const piles = [];
    let offset = 0;
    for (let i = 0; i < 6; i++) {
      const size = Math.floor(cards.length / 6) + (i < cards.length % 6 ? 1 : 0);
      piles.push(cards.slice(offset, offset + size));
      offset += size;
    }
    return piles;
  }
  function create() {
    return { version: VERSION, phase: "ready", target: 0, piles: [], pile: null,
      selected: [], revealed: [], visible: true, title: "", motion: true, revision: 0 };
  }
  function valid(state, ids) {
    if (!state || state.version !== VERSION || ids.length !== 78 || new Set(ids).size !== 78) return false;
    if (!["ready", "pile", "pick", "reveal", "complete"].includes(state.phase)) return false;
    if (!Number.isInteger(state.revision) || state.revision < 0 || typeof state.visible !== "boolean" || typeof state.motion !== "boolean") return false;
    if (typeof state.title !== "string" || state.title.length > 60) return false;
    if (!Array.isArray(state.selected) || !Array.isArray(state.revealed) || !Array.isArray(state.piles)) return false;
    if (state.selected.length !== state.revealed.length || state.revealed.some(value => typeof value !== "boolean")) return false;
    const active = state.phase === "pile" || state.phase === "pick";
    const cards = [...state.selected];
    if (state.piles.some(pile => !Array.isArray(pile))) return false;
    cards.push(...state.piles.flat());
    if (new Set(cards).size !== cards.length || cards.some(id => !ids.includes(id))) return false;
    if (state.phase === "ready") return state.target === 0 && cards.length === 0 && state.pile === null;
    if (![1, 3].includes(state.target) || state.selected.length > state.target) return false;
    if (active) {
      if (state.selected.length >= state.target || state.revealed.some(Boolean)) return false;
      if (cards.length !== 78 || state.piles.length !== 6 || state.piles.some(pile => pile.length < 11 || pile.length > 13)) return false;
      return state.phase === "pile" ? state.pile === null : Number.isInteger(state.pile) && state.pile >= 0 && state.pile < 6;
    }
    if (state.piles.length || state.pile !== null || state.selected.length !== state.target) return false;
    return state.phase === "complete" ? state.revealed.every(Boolean) : !state.revealed.every(Boolean);
  }
  function apply(state, action, ids, random = integer) {
    if (!valid(state, ids)) throw Error("저장된 추첨 상태를 확인할 수 없습니다.");
    const next = JSON.parse(JSON.stringify(state));
    const index = action.index;
    switch (action.type) {
      case "start":
        if (state.phase !== "ready" || ![1, 3].includes(action.count)) throw Error("먼저 새 점보기를 시작해 주세요.");
        next.target = action.count; next.phase = "pile";
        next.piles = partition(shuffle(ids, random));
        break;
      case "pile":
        if (state.phase !== "pile" || !Number.isInteger(index) || index < 0 || index >= 6) throw Error("덱을 선택해 주세요.");
        next.pile = index; next.phase = "pick";
        break;
      case "back":
        if (state.phase !== "pick") throw Error("카드 선택 중에만 덱으로 돌아갈 수 있습니다.");
        next.pile = null; next.phase = "pile";
        break;
      case "draw":
        if (state.phase !== "pick" || !Number.isInteger(index) || index < 0 || index >= state.piles[state.pile].length) throw Error("카드를 선택해 주세요.");
        next.selected.push(state.piles[state.pile][index]); next.revealed.push(false); next.pile = null;
        if (next.selected.length === next.target) { next.piles = []; next.phase = "reveal"; }
        else {
          next.piles = partition(shuffle(ids.filter(id => !next.selected.includes(id)), random));
          next.phase = "pile";
        }
        break;
      case "reveal":
        if (state.phase !== "reveal" || !Number.isInteger(index) || index < 0 || index >= state.selected.length || state.revealed[index]) throw Error("아직 공개하지 않은 카드를 골라 주세요.");
        next.revealed[index] = true;
        if (next.revealed.every(Boolean)) next.phase = "complete";
        break;
      case "reset":
        Object.assign(next, create(), { visible: state.visible, motion: state.motion, title: "", revision: state.revision });
        break;
      case "visibility": next.visible = !state.visible; break;
      case "motion": next.motion = !state.motion; break;
      case "title": next.title = String(action.value || "").trim().slice(0, 60); break;
      default: throw Error("알 수 없는 조작입니다.");
    }
    next.revision++;
    if (!valid(next, ids)) throw Error("추첨 규칙을 벗어난 상태입니다.");
    return next;
  }
  const api = Object.freeze({ create, valid, apply, shuffle, partition });
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.LemonTarotGame = api;
})(typeof globalThis !== "undefined" ? globalThis : window);
