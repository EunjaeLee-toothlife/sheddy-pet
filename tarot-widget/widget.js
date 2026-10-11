"use strict";
(async function () {
  const $ = selector => document.querySelector(selector);
  const game = window.LemonTarotGame, cards = window.LemonTarotCards;
  const STORAGE = "sheddy-lemon-tarot-session-v1";
  const UI_STORAGE = "sheddy-lemon-tarot-salon-v1";
  const messages = { ready: ["오늘, 어떤 이야기를\n들어볼까요?", "마음속에 질문 하나를 떠올려보세요.\n레몬이 당신의 카드를 기다리고 있어요."],
    pile: ["마음이 머무는 덱을 골라주세요", "여섯 개의 작은 가능성. 끌리는 덱 하나를 선택하세요."],
    pick: ["당신을 기다리는 한 장", "서두르지 않아도 괜찮아요. 마음이 가는 카드를 골라주세요."],
    reveal: ["이제, 당신의 이야기를 펼칠 시간", "원하는 순서로 한 장씩 공개해 주세요."],
    complete: ["오늘의 이야기가 모였어요", "공개된 카드를 누르면 그림을 더 크게 볼 수 있어요."] };
  let deck, ids, lookup, state, pending = false, revealToken = 0, resetTimer = 0, restored = false;
  const loading = new Map();
  function warning(text) { $("#error").textContent = text; $("#error").hidden = false; }
  window.addEventListener("tarot-image-error", () => warning("카드 그림을 불러오지 못했습니다. 인터넷 연결을 확인하고 새로고침해 주세요."));
  if (new URLSearchParams(location.search).get("preview") === "1") document.body.classList.add("preview");
  try {
    const response = await fetch("deck.json");
    if (!response.ok) throw Error("카드 목록을 불러오지 못했습니다.");
    deck = await response.json();
    ids = deck.cards.map(card => card.id); lookup = new Map(deck.cards.map(card => [card.id, card]));
    state = game.create();
    state.motion = !matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!game.valid(state, ids)) throw Error("78장 카드 목록에 문제가 있습니다.");
    try {
      const saved = localStorage.getItem(STORAGE);
      if (saved) {
        const previous = JSON.parse(saved);
        if (!game.valid(previous, ids)) throw Error("저장 상태 오류");
        state = previous; restored = previous.phase !== "ready";
      }
    } catch { warning("이전 상태를 복원하지 못했습니다. 새 점보기로 시작합니다. 저장이 제한된 환경에서는 새로고침하면 진행이 사라질 수 있습니다."); }
  } catch (error) {
    warning(error.message); $("#status").textContent = "준비 실패"; $("#instruction").textContent = "카드 목록을 불러오지 못했습니다.";
    document.querySelectorAll(".controller button, .controller input").forEach(node => node.disabled = true);
    return;
  }
  let ui = { sound: false, focus: -1 };
  try {
    const saved = JSON.parse(localStorage.getItem(UI_STORAGE) || "null");
    if (saved) { ui.sound = saved.sound === true; ui.focus = Number.isInteger(saved.focus) ? saved.focus : -1; }
  } catch {}
  if (!state.revealed[ui.focus]) ui.focus = -1;
  const show = window.LemonTarotShow.create({ stage: $("#stage"), back: deck.back,
    enabled: () => state.motion && state.visible && !document.hidden,
    onBusy: value => { if (value) updateDesk(); else render(); } });
  function saveUI() { try { localStorage.setItem(UI_STORAGE, JSON.stringify(ui)); } catch {} }
  function preload(id) {
    if (!loading.has(id)) {
      const promise = cards.preload(lookup.get(id), deck.blinks[id]).catch(error => {
        if (loading.get(id) === promise) loading.delete(id);
        throw error;
      });
      loading.set(id, promise);
    }
    return loading.get(id);
  }
  function disarm() { clearTimeout(resetTimer); resetTimer = 0; $("#reset").textContent = "새 점보기"; $("#reset").classList.remove("armed"); }
  function dispatch(action, source) {
    try {
      const before = state;
      const picture = source?.matches(".card-button") ? source : source?.querySelector(".card-button");
      const sourceRect = picture?.getBoundingClientRect();
      const next = game.apply(state, action, ids);
      // UI를 갱신하기 전에 동기 저장해 선택 직후의 종료에도 최대한 보존한다.
      try { localStorage.setItem(STORAGE, JSON.stringify(next)); }
      catch { warning("자동 저장이 제한되어 있습니다. 이 창을 새로고침하거나 닫으면 진행이 사라질 수 있습니다."); }
      if (action.type === "reset") { revealToken++; pending = false; ui.focus = -1; saveUI(); }
      state = next; restored = false; disarm();
      for (const id of state.selected) if (!state.revealed[state.selected.indexOf(id)]) preload(id).catch(() => {});
      if (["reset", "motion", "visibility"].includes(action.type)) { show.cancel(); render(); return; }
      if (action.type === "reveal" && state.motion && state.visible) {
        render();
        const slot = $("#table").querySelector(`[data-slot="${action.index}"] .slot-card`);
        const card = lookup.get(state.selected[action.index]);
        if (ui.sound) show.setSound(true);
        show.run(token => show.reveal(sourceRect, slot, card, deck.blinks[card.id], token)).catch(() => show.cancel());
        return;
      }
      if (!["start", "pile", "draw", "back"].includes(action.type) || !state.motion || !state.visible) { render(); return; }
      if (ui.sound) show.setSound(true);
      show.run(async token => {
        if (action.type === "start") {
          render(); await show.shuffle(token);
          if (show.live(token)) await show.enter(".deck-button", token);
        } else if (action.type === "pile") {
          const origin = await show.fly(sourceRect, null, token, "pile", source);
          if (!show.live(token)) return;
          render(); await show.enter(".pick-slot", token, "deal", origin);
        } else if (action.type === "draw") {
          const destination = $("#selection-rail").querySelector(`[data-rail="${before.selected.length}"]`);
          await show.fly(sourceRect, destination, token, "draw", source);
          if (!show.live(token)) return;
          render();
          if (state.phase === "pile") {
            await show.shuffle(token);
            if (show.live(token)) await show.enter(".deck-button", token);
          } else await show.enter(".reading-slot", token, "reading");
        } else {
          render(); await show.enter(".deck-button", token);
        }
      }).catch(error => { warning("연출을 마무리하지 못했습니다. 저장된 카드로 계속 진행합니다."); show.cancel(); });
    } catch (error) { warning(error.message); }
  }
  function click(action) { return event => { if (event.detail > 1 || pending || show.busy) return; dispatch(action, event.currentTarget); }; }
  async function reveal(index) {
    if (pending || show.busy || state.revealed[index] || state.phase !== "reveal") return;
    pending = true; const revision = state.revision, token = ++revealToken, id = state.selected[index];
    let timeout;
    updateDesk();
    try {
      await Promise.race([preload(id), new Promise((resolve, reject) => {
        timeout = setTimeout(() => reject(Error("이미지 준비 시간 초과")), 20000);
      })]);
      if (revision === state.revision) dispatch({ type: "reveal", index }, $("#table").querySelector(`[data-slot="${index}"] .card-button`));
    } catch {
      if (token === revealToken) {
        loading.delete(id);
        warning("카드 그림을 불러오지 못했습니다. 연결을 확인한 뒤 공개 버튼을 다시 눌러 주세요.");
      }
    } finally {
      clearTimeout(timeout);
      if (token === revealToken) { pending = false; render(); }
    }
  }
  function element(tag, className, text) { const node = document.createElement(tag); node.className = className; if (text) node.textContent = text; return node; }
  function decorativeBack() {
    const back = cards.makeBack(deck.back, "");
    const button = back.querySelector("button"), shell = element("div", "card-button");
    shell.append(...button.childNodes); button.replaceWith(shell); return back;
  }
  function focus(index) {
    if (pending || show.busy || (index >= 0 && !state.revealed[index])) return;
    const previous = new Map([...document.querySelectorAll(".reading-slot")].map(node => [node.dataset.slot, node.querySelector(".slot-card").getBoundingClientRect()]));
    ui.focus = ui.focus === index ? -1 : index; saveUI(); render();
    show.run(token => show.focus(previous, token)).catch(() => show.cancel());
  }
  function renderTable() {
    const table = $("#table");
    const view = ["reveal", "complete"].includes(state.phase) ? "reading" : state.phase;
    const key = view === "reading" ? `${view}:${state.selected.join(",")}` : `${view}:${state.pile}:${state.piles.flat().join(",")}`;
    if (table.dataset.key !== key) {
      table.replaceChildren(); table.dataset.key = key;
      if (view === "ready") {
        const row = element("div", "mode-options");
        for (const count of [1, 3]) {
          const button = element("button", "mode-option"); button.type = "button"; button.dataset.start = count;
          const art = element("div", "mode-art"); art.setAttribute("aria-hidden", "true");
          for (let index = 0; index < count; index++) {
            const miniature = element("div", "mode-mini"); miniature.style.setProperty("--fan-angle", `${count === 1 ? -6 : (index - 1) * 18}deg`);
            miniature.append(decorativeBack()); art.append(miniature);
          }
          button.append(element("span", "mode-kicker", count === 1 ? "ONE MOMENT" : "A LITTLE JOURNEY"), art,
            element("strong", "", count === 1 ? "한 장의 메시지" : "세 장의 이야기"),
            element("span", "mode-english", count === 1 ? "One Card Spread" : "Three Card Spread"),
            element("small", "", count === 1 ? "지금 마음에 필요한\n작은 한마디" : "하나의 질문을 따라\n이어지는 세 장의 카드"), element("span", "mode-arrow", "↗"));
          button.addEventListener("click", click({ type: "start", count })); row.append(button);
        }
        table.append(row);
      } else if (view === "pile") {
        const row = element("div", "deck-grid");
        state.piles.forEach((_, index) => {
          const button = element("button", "deck-button"); button.type = "button"; button.dataset.pile = index;
          button.setAttribute("aria-label", `${index + 1}번 덱`);
          const back = decorativeBack();
          const label = element("span", "deck-label", `${index + 1}번 덱`);
          button.append(back, label); button.addEventListener("click", click({ type: "pile", index })); row.append(button);
        });
        table.append(row);
      } else if (view === "pick") {
        const row = element("div", "pick-grid");
        row.dataset.count = state.piles[state.pile].length;
        state.piles[state.pile].forEach((id, index) => {
          const slot = element("div", "pick-slot");
          const back = cards.makeBack(deck.back, `${index + 1}번째 카드 선택`), button = back.querySelector("button");
          button.dataset.draw = index; button.addEventListener("click", click({ type: "draw", index }));
          slot.append(back, element("span", "pick-number", String(index + 1).padStart(2, "0"))); row.append(slot);
        });
        table.append(row);
      } else {
        const row = element("div", `reading-grid ${state.target === 1 ? "single" : ""}`);
        state.selected.forEach((id, index) => {
          const slot = element("div", "reading-slot"); slot.dataset.slot = index;
          slot.style.setProperty("--slot-index", index);
          slot.append(element("p", "slot-label", state.target === 1 ? "당신의 카드" : `${index + 1}번째 카드`), element("div", "slot-card"), element("p", "slot-hint"));
          row.append(slot);
        });
        table.append(row);
      }
    }
    if (view === "reading") state.selected.forEach((id, index) => {
      const slot = table.querySelector(`[data-slot="${index}"]`), face = slot.querySelector(".slot-card");
      if (face.dataset.revealed !== String(state.revealed[index])) {
        const card = state.revealed[index] ? cards.makeFront(lookup.get(id), deck.blinks[id], index) : cards.makeBack(deck.back, `${index + 1}번째 카드 공개`);
        const button = card.querySelector("button");
        if (!state.revealed[index]) { button.dataset.reveal = index; button.addEventListener("click", event => { if (event.detail <= 1) reveal(index); }); }
        else { button.dataset.focus = index; button.addEventListener("click", event => { if (event.detail <= 1) focus(index); }); }
        face.replaceChildren(card); face.dataset.revealed = String(state.revealed[index]);
      }
      slot.classList.toggle("is-open", state.revealed[index]);
      slot.querySelector(".slot-hint").textContent = state.revealed[index] ? "정방향 · 눌러서 크게 보기" : "눌러서 공개";
      const button = face.querySelector("button"); button.disabled = pending || show.busy;
    });
    if (view === "reading") {
      const row = table.querySelector(".reading-grid"); row.classList.toggle("focus-mode", ui.focus >= 0);
      let mini = 0;
      for (const slot of row.children) {
        const focused = Number(slot.dataset.slot) === ui.focus;
        slot.classList.toggle("focused", focused); if (!focused) slot.style.setProperty("--mini-index", mini++);
      }
    }
  }
  function updateDesk() {
    const busy = pending || show.busy;
    $("#stage").setAttribute("aria-busy", String(busy));
    $("#skip").hidden = !show.busy;
    $("#overview").hidden = ui.focus < 0;
    $("#back").hidden = state.phase !== "pick";
    $("#back").disabled = busy;
    $("#overview").disabled = busy;
    $("#sound").textContent = ui.sound ? "효과음 켜짐" : "효과음 끔";
    $("#sound").setAttribute("aria-pressed", String(ui.sound));
    const summary = state.phase === "pick" ? `${state.pile + 1}번 덱 · ${state.piles[state.pile].length}장 중 선택` : state.phase === "pile" ? `${state.selected.length + 1}번째 카드 · 덱을 선택해 주세요` : state.phase === "ready" ? "카드 수를 선택해 주세요" : `${state.revealed.filter(Boolean).length} / ${state.target}장 공개`;
    $("#status").textContent = pending ? "카드 그림을 준비하고 있습니다…" : show.busy ? "이야기를 준비하는 중 · Space로 건너뛰기" : `${restored ? "이전 점보기 복원 · " : ""}${summary}`;
    document.querySelectorAll("#stage button").forEach(button => button.disabled = busy);
    $("#set-title").disabled = busy;
    document.querySelectorAll("#reveal-controls button").forEach(button => button.disabled = busy || button.dataset.opened === "true");
  }
  function render() {
    const view = ["reveal", "complete"].includes(state.phase) ? "reading" : state.phase;
    if (view !== "reading") ui.focus = -1;
    $("#stage").dataset.view = view;
    $("#stage").classList.toggle("is-focused", ui.focus >= 0);
    const steps = ["ready", "pile", "pick", "reading"], step = steps.indexOf(view);
    document.querySelectorAll(".stage-steps li").forEach((node, index) => {
      node.classList.toggle("current", index === step); node.classList.toggle("done", index < step);
      if (index === step) node.setAttribute("aria-current", "step"); else node.removeAttribute("aria-current");
    });
    document.body.classList.toggle("motion-paused", !state.motion || !state.visible);
    document.body.classList.toggle("motion-enabled", state.motion);
    document.body.classList.toggle("stage-hidden", !state.visible);
    $("#stage").setAttribute("aria-hidden", String(!state.visible));
    const [heading, instruction] = messages[state.phase];
    $("#heading").textContent = heading; $("#instruction").textContent = instruction;
    $("#reading-title").hidden = !state.title; $("#reading-title").textContent = state.title;
    $("#eyebrow").textContent = view === "ready" ? "A LITTLE MAGIC, A LITTLE LEMON" : view === "pile" ? "FOLLOW YOUR INTUITION" : view === "pick" ? `DECK ${String(state.pile + 1).padStart(2, "0")} · YOUR CHOICE` : "LET THE STORY BEGIN";
    $("#progress").textContent = state.target ? `${state.target === 1 ? "한 장" : "세 장"} · ${view === "reading" ? `${state.revealed.filter(Boolean).length} / ${state.target} 공개` : `${state.selected.length} / ${state.target} 선택`}` : "78장의 작은 가능성";
    const rail = $("#selection-rail"); rail.replaceChildren();
    for (let index = 0; index < state.target; index++) {
      const token = element("span", "rail-slot", String(index + 1)); token.dataset.rail = index;
      token.classList.toggle("chosen", index < state.selected.length); token.classList.toggle("opened", state.revealed[index] === true);
      if (index < state.selected.length) { token.textContent = ""; const miniature = decorativeBack(); miniature.setAttribute("aria-hidden", "true"); token.append(miniature); }
      token.setAttribute("aria-label", `${index + 1}번째 카드 ${state.revealed[index] ? "공개됨" : index < state.selected.length ? "선택됨" : "대기"}`); rail.append(token);
    }
    $("#back").hidden = state.phase !== "pick";
    $("#motion").textContent = state.motion ? "움직임 켜짐" : "움직임 멈춤"; $("#motion").setAttribute("aria-pressed", String(state.motion));
    $("#visibility").textContent = state.visible ? "화면 숨기기" : "화면 보이기"; $("#visibility").setAttribute("aria-pressed", String(state.visible));
    if (document.activeElement !== $("#title")) $("#title").value = state.title;
    const controls = $("#reveal-controls"); controls.replaceChildren();
    if (["reveal", "complete"].includes(state.phase)) state.selected.forEach((id, index) => {
      const button = element("button", "", `${index + 1}번째 ${state.revealed[index] ? "공개됨" : "공개"}`);
      button.dataset.reveal = index; button.dataset.opened = String(state.revealed[index]); button.disabled = state.revealed[index] || pending || show.busy;
      button.addEventListener("click", () => reveal(index)); controls.append(button);
    });
    if (!state.visible && state.phase === "ready") for (const count of [1, 3]) {
      const button = element("button", "", count === 1 ? "한 장 시작" : "세 장 시작");
      button.addEventListener("click", click({ type: "start", count })); controls.append(button);
    }
    renderTable();
    $("#focus-caption").hidden = ui.focus < 0;
    if (ui.focus >= 0) {
      const card = lookup.get(state.selected[ui.focus]);
      $("#focus-topic").textContent = state.title || "YOUR CARD, YOUR STORY";
      $("#focus-name").textContent = card.korean; $("#focus-english").textContent = window.LEMON_GILT.title(card.title);
    }
    updateDesk();
  }
  $("#back").addEventListener("click", click({ type: "back" }));
  // 연출 중에도 정지·숨김은 언제든 사용할 수 있다.
  $("#motion").addEventListener("click", () => dispatch({ type: "motion" }));
  $("#visibility").addEventListener("click", () => dispatch({ type: "visibility" }));
  $("#sound").addEventListener("click", () => { ui.sound = show.setSound(!ui.sound); saveUI(); updateDesk(); });
  $("#skip").addEventListener("click", () => show.cancel());
  $("#overview").addEventListener("click", () => focus(-1));
  $("#set-title").addEventListener("click", () => dispatch({ type: "title", value: $("#title").value }));
  $("#title").addEventListener("keydown", event => { if (event.key === "Enter") { event.preventDefault(); dispatch({ type: "title", value: event.target.value }); } });
  $("#reset").addEventListener("click", () => {
    if (state.phase === "ready") return;
    if (state.phase === "complete" || resetTimer) dispatch({ type: "reset" });
    else { $("#reset").textContent = "한 번 더 누르면 초기화"; $("#reset").classList.add("armed"); resetTimer = setTimeout(disarm, 5000); }
  });
  document.addEventListener("visibilitychange", () => { document.body.classList.toggle("page-hidden", document.hidden); if (document.hidden) show.cancel(); });
  document.addEventListener("keydown", event => {
    if (event.target.matches("input,textarea,select") || event.altKey || event.ctrlKey || event.metaKey) return;
    if ((event.code === "Space" || event.key === "Escape") && show.busy) { event.preventDefault(); show.cancel(); return; }
    if (event.key === "Escape" && ui.focus >= 0) { event.preventDefault(); focus(-1); return; }
    if (show.busy || pending) return;
    const number = Number(event.key);
    if (state.phase === "pile" && number >= 1 && number <= 6) { event.preventDefault(); $(`[data-pile="${number - 1}"]`).click(); }
    else if (state.phase === "reveal" && number >= 1 && number <= state.target && !state.revealed[number - 1]) { event.preventDefault(); reveal(number - 1); }
    else if (state.phase === "pick" && ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"].includes(event.key)) {
      const buttons = [...document.querySelectorAll("[data-draw]")], columns = buttons.length === 13 ? 7 : 6;
      const current = Math.max(0, buttons.indexOf(document.activeElement));
      const offset = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -columns, ArrowDown: columns, Home: -current, End: buttons.length - current - 1 }[event.key];
      event.preventDefault(); buttons[Math.max(0, Math.min(buttons.length - 1, current + offset))].focus();
    }
  });
  render();
  for (const id of state.selected) preload(id).catch(() => {});
})();
