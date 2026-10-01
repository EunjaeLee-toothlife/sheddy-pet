# 마녀 연금술 검증 — 2026-10-01

2번 클래식 연금술사 복장을 선택한 뒤, ImageGen으로 변신·솥 젓기·결과 3종·원복을 제작했다.
각 클립은 16개 포즈다. 황금 레몬 결과의 9번 프레임에서 사라진 솥은 ImageGen으로 보정했다.
원본과 수정본, 프롬프트, 셀 경계 및 타이밍을 저장소에 보관했다.

## 시각 검수

- 생성 시트 6종 및 조립한 96개 프레임: 모자·신발 잘림 없음, 마녀 복장과 솥 유지.
- 실제 위젯 캔버스: 투명 배경, 결과 소품과 복장 정상. 아래 이미지는 실행 중 캔버스 캡처다.
- start→loop, loop 반복, end→outro 및 idle 원복의 PNG 접합점은 동일 픽셀이다.
- 클립 내부에는 생성 포즈 사이의 작은 형태 차이가 남아 있다. 부드러운 보간 애니메이션이 아닌 포즈 단위 애니메이션이다.

| 황금 레몬 | 실험 실패 | 레몬 슬라임 |
| --- | --- | --- |
| ![황금 레몬](end1-runtime.png) | ![실험 실패](end2-runtime.png) | ![슬라임](end3-runtime.png) |

## 검증 결과

- `tools/verify_alchemy.py`: 96 PNG, 219 VP9 프레임의 디코딩 알파, 재생 시간, 여백, 원본 해시 및 접합점 통과.
- 클립 길이: start 3.400초 / loop 2.666초 / end 각 3.333초 / outro 2.750초.
- `node tools/widget_check.js --page docs/index.html --capture`: 13/13 통과.
- `node tools/widget_check.js --fallback --page docs/index.html`: 13/13 통과.
- 세 엔딩의 start→loop→end→outro→idle, 무기한 유지, 두 사이클 반복, OBS 숨김 중 재생·그리기 중단과 큐 복귀 확인.
- 기존 반응 16종·춤 3종, 전환·마이크 큐·워치독 회귀 검사 통과.
- 전체 62개 영상 순회: 캐시 4,150,525B < 4MiB, 동시 요청 2개.
- `tools/test_build_reactions.py`: 4개 통과. `node --test tools/widget_metrics.test.js`: 7개 통과.
- Pages 원본/재구성 dry-run 해시 정합 통과. 재구성 검수 요건도 통과하고 `docs` 재생성 완료.
- 위젯과 생성된 `docs/index.html` 내용 일치. 공개 Pages 갱신은 PR 병합 이후다.

[상태 머신 기록](runtime-checks.json) · [성능 표본](benchmark.json)

단독 Chrome idle 측정에서 5초 합성 50/49회, 초기 영상 1개·67,280B를 유지했다.
512px/DPR1 및 1024px/DPR2 모두 실제 캔버스는 512×512이며, 8초 메인 스레드 작업은 각각 105/99ms였다.
단일 표본이며 OBS 프로세스 전체 CPU/GPU 수치나 모든 장면의 성능 보장은 아니다.
