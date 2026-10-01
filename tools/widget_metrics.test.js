"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { median, percentile, reduction, summarize, reportMarkdown } = require("./widget_metrics");

test("중앙값은 홀짝 표본을 처리하고 입력 순서를 보존한다", () => {
  const values = [100, 3, 2, 1];
  assert.equal(median(values), 2.5);
  assert.equal(median([100, 1, 3]), 3);
  assert.deepEqual(values, [100, 3, 2, 1]);
});
test("P95는 nearest-rank를 쓰고 작은 표본의 최대 지연을 숨기지 않는다", () => {
  assert.equal(percentile(Array.from({ length: 20 }, (_, i) => i + 1), 0.95), 19);
  assert.equal(percentile([1, 2, 100], 0.95), 100);
});
test("빈 표본과 비유한 값은 성공한 측정으로 처리하지 않는다", () => {
  for (const values of [[], [1, NaN], [Infinity]]) assert.throws(() => median(values));
  assert.throws(() => percentile([1], 0));
});
test("감소율은 악화와 0 기준을 구분한다", () => {
  assert.equal(reduction(300, 50), 83.33333333333334);
  assert.equal(reduction(50, 100), -100);
  assert.equal(reduction(0, 0), null);
  assert.equal(reduction(0, 10), null);
});
const metricKeys = ["firstFrameMs", "clearsPerSecond", "drawsPerSecond", "drawMegapixelsPerSecond",
  "mainThreadBusyPercent", "videoFramesPerSecond", "droppedFrames", "initialVideoBytes",
  "initialVideoRequests", "initialBlobBytes", "heapUsedBytes", "hiddenDrawsPerSecond"];
function sample(variant, value) {
  return { scenario: "512px / DPR 1", variant, ...Object.fromEntries(metricKeys.map(k => [k, value])),
    transitions: [{ sweep: "first", ms: value * 2 }, { sweep: "repeat", ms: value }] };
}
test("반복 측정의 중앙값·범위·순회별 P95와 감소율을 계산한다", () => {
  const [group] = summarize([sample("baseline", 60), sample("baseline", 100), sample("baseline", 60),
    sample("current", 10), sample("current", 10), sample("current", 20)]);
  assert.deepEqual(group.baseline.clearsPerSecond, { median: 60, min: 60, max: 100 });
  assert.equal(group.current.firstTransitionMs.p95, 40);
  assert.equal(group.current.repeatTransitionMs.count, 3);
  assert.equal(group.reductionPercent.clearsPerSecond, reduction(60, 10));
});
test("짝이 없는 비교와 누락된 지표는 보고서 생성에 실패한다", () => {
  assert.throws(() => summarize([]));
  assert.throws(() => summarize([sample("baseline", 1)]));
  const broken = sample("current", 1); delete broken.drawsPerSecond;
  assert.throws(() => summarize([sample("baseline", 1), broken]));
});
test("보고서에는 지표 단위·계산식·측정 한계를 함께 기록한다", () => {
  const report = { createdAt: "2026-10-01", baseline: { commit: "abc" }, current: { commit: "def" },
    environment: { platform: "test", arch: "test", cpu: "test", node: "test" },
    trials: [{ browser: "test" }], runs: 3, summary: summarize([sample("baseline", 60), sample("current", 10)]) };
  const text = reportMarkdown(report);
  for (const expected of ["83.333%", "Mpixel/s", "TaskDuration", "P95", "프로세스 RSS", "5ms", "실제 OBS"]) assert.ok(text.includes(expected));
});
