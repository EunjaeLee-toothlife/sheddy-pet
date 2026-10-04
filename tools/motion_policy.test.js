"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const html = fs.readFileSync(path.join(__dirname, "../widget.html"), "utf8");
const registry = "const ANIMS =" + html.split("const ANIMS =")[1].split("const THEME_STATES")[0];
const functions = "function pickWeighted" + html.split("function pickWeighted")[1].split("// 외부 명령 보호 시간을")[0];
function player(name, pin = 0) {
  const context = vm.createContext({ current: name, pinnedUntil: pin, emotionCycles: 0,
    idleStreak: 0, DEFAULT_STATE: "idle1", TALK_STATE: "talk", modeSwitching: false,
    transitioning: false, isDragging: false, talkActive: false, DICE_ON: true,
    MIN_EMOTION_CYCLES: 3, MIN_IDLE_CYCLES: 2, REROLL_CHANCE: .35,
    front: 0, vids: [{ currentTime: 1, play: () => Promise.resolve() }],
    setState(next) { context.current = next; } });
  vm.runInContext(registry + "; const ACTIVE_ANIMS = ANIMS; Math.random=()=>.999;" + functions, context);
  return context;
}
test("자동 몸짓은 재추첨이 계속 빗나가도 정해진 사이클 안에 대기로 돌아온다", () => {
  for (const name of ["basic1", "basic2", "basic3", "happy1", "happy2", "excited1", "sad1", "sad2"]) {
    const p = player(name);
    for (let i = 0; i < 3 && p.current !== "idle1"; i++) vm.runInContext("onCycleEnd()", p);
    assert.equal(p.current, "idle1", name);
  }
});
test("계속 유지로 선택한 모션은 자동 반복 상한을 적용하지 않는다", () => {
  for (const name of ["basic2", "happy2", "witchlook1", "seollal_tidy1"]) {
    const p = player(name, Infinity);
    for (let i = 0; i < 5; i++) vm.runInContext("onCycleEnd()", p);
    assert.equal(p.current, name);
    assert.equal(p.pinnedUntil, Infinity);
  }
});
test("모든 테마의 둘러보기·옷 정돈은 한 번만 실행되고 대기 추첨에 섞이지 않는다", () => {
  for (const prefix of ["witch", "seollal_", "christmas_", "childrensday_", "summer_"]) {
    for (const suffix of ["look1", "tidy1"]) {
      const name = prefix + suffix, p = player(name);
      assert.equal(vm.runInContext(`ANIMS['${name}'].category`, p), "basic");
      vm.runInContext("onCycleEnd()", p);
      assert.equal(p.current, "idle1", name);
    }
  }
});
