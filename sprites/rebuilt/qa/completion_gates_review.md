# 최종 완료 조건 읽기 전용 검토

검토 범위: `ANIMATION_REBUILD.md`, 중앙 `anims/rebuild_manifest.json`, 실제 위젯과 Pages 생성 코드, 저장된 브라우저 DOM 요약 및 정적 QA 기록. 중앙 flags, 후보 프레임, 영상, 위젯은 수정하지 않았다. 이 문서는 그림 전체를 새로 육안 합격 판정한 결과가 아니라 현재 증거와 남은 완료 조건을 대조한 기록이다.

## 현재 확인된 범위

- 중앙 계약은 **39개 클립 / 21개 상태 / 579개 원본 PNG 슬롯**이다. 후보 폴더에 실제 579 PNG가 있으며 모두 512×512 RGBA다. 원본 579 PNG 및 39 WebM의 SHA-256은 중앙 원본 계약과 일치했다.
- 검토 중 root가 `chem1_end3`를 재등록하여 중앙 상태가 **38 generated / 1 staged**로 바뀌었다. 현재 staged chem1_end3에는 candidate/evidence 및 완료 flags가 없다. 나머지 38개의 현 후보 PNG·영상 해시는 기록된 audit와 일치하고, source/timing/decodedAlpha 증거가 존재하며 canvas 접촉 기록이 비어 있다. staged clip의 예전 영상이 디스크에 존재하는 것만으로 최신 18 PNG가 인코딩되었다고 볼 수 없다.
- 해당 기술 점검에서 읽은 중앙 manifest SHA-256: `314fb1941563e76e9c596bbc4f42b01181e87d618c97de351b1272571225d3fb`. 통합 작업 중인 시점의 스냅샷이며 이후 변경은 다시 확인해야 한다.
- `runtime_dom_summary_20260930.json`은 실제 브라우저 **32/32 케이스 성공, 39/39 영상 완주, 미디어 오류 0, 누락 없음, talk 자동 idle 복귀**를 기록한다. 빠른 상태 진입에서 이전 dissolve가 재사용 버퍼를 pause하던 회귀도 수정 후 통과했다. 이는 단순 ready/ended 추정이 아닌 관측 playing/ended 커버리지다.
- 브라우저 통과 시점의 widget/harness 해시는 현재 파일과 일치한다. 현재 manifest는 그 이후 바뀌었다. 저장된 `runtime_manifest_20260930.json`과 현재 중앙의 영상 해시를 대조했을 때 바뀐 클립은 chem1_end3 하나다.
- 브라우저 요약의 chem1_end3 해시는 `a599ac4c2da7c7e9ce3f2c8872ab4e1ce316135c08b20c5c7c5532cf22d47b5e`다. 이 결과는 **교체 전 그림**에 대한 재생 증거이며 현재 anatomy/rainbow 수정을 자동 승인하지 않는다. 전체 이벤트 JSON export는 당시 timeout으로 보존되지 않았고 실제 DOM 요약과 관련 runtime snapshot이 남아 있다. 전체 export 부재가 관측 32/39 통과를 무효화하지는 않지만 증거의 한계로 명시해야 한다.

## 남은 구체 gate

| Gate | 현재 상태와 필요한 완료 증거 |
|---|---|
| G1. chem1_end3 최신 후보 등록·audit | 수정된 18 PNG 전체를 인코딩하고 source hashes, 1.8초/원래 rate0.7, 실제 VP9 decoded alpha, rainbow green 보존 및 canvas 여백을 재검증한다. 중앙 staged→generated와 최신 영상 해시는 root가 증거에 따라 등록한다. |
| G2. 원본 행동·의상·소품 보존 최종 판정 | 현재 `motion=false`: pastry1_start, pastry1_loop, pastry1_end1–5, pastry1_outro, chem1_end3의 **9클립**. 단순 flags 누락을 행동 누락으로 단정하지 않는다. 기존 contact/원본 pose/최종 실제 재생을 대조하고, 최종 그림에 대한 구체 관측을 적은 뒤 flags를 판단한다. |
| G3. chem1_end3 최신 그림 품질 | 현 `style=false`, `alpha=false`도 staged 수정 중에 초기화되었다. 04–07 및 08–11, 12–15 리페어를 함께 최종 18프레임으로 확인한다. 플라스크 밴드는 위에서 red→orange→yellow→green→blue→violet, 모든 가시 플라스크 동일 순서여야 한다. 액체 green이 투명 구멍이 되거나, 12/13 overhead에서 몸통/다리가 짧아지거나, 15 이후 숨길 소품이 남지 않는지 확인한다. 의도된 rainbow/flare를 피부·가운 얼룩과 구분한다. |
| G4. 최종 교체 영상 실제 재생 | G1 뒤 chem1의 start→loop→ending3→idle을 원래 rate로 다시 관측한다. 최신 hash를 붙인 추가 재생 증거로 기존 32케이스/39영상 증거와 연결할 수 있다. 다른 영상/위젯까지 다시 바뀌면 해당 변경 범위도 재생한다. 전체 검사를 무조건 반복하기보다 실제 변경 범위와 hashes를 기준으로 판단한다. |
| G5. 시각적 loop·상태 연결 | **39개 전부 `seams=false`**다. 커버리지 통과는 재생 안정성을 증명하지만 얼굴/가운 이중상, 갑작스러운 카메라 크기 변화, 발 미끄러짐과 포즈 snap의 자연스러움을 증명하지 않는다. 내부 loop 경계와 idle↔각 상태, happy start/loop/end, pastry start/loop/10 endings/outro, chem start/loop/3 endings/idle을 실제 크기와 필요시 확대에서 보고 관측 결과를 남긴다. 정확 픽셀 앵커가 없는 정상 동작을 강제로 동일화하지 않는다. |
| G6. 중앙 최종 review 승인 | 검증한 항목만 style/motion/alpha/seams=true로 남기고, 문서 workflow의 reviewed 단계로 완료 상태를 기록한다. 현재 모든 clip이 fully reviewed는 아니다. `--require-reviewed`는 모든 flags와 status=reviewed를 요구하므로 현재 배포 gate가 막히는 것이 정상이다. |
| G7. 런타임·Pages 자산 통합 | 현재 `widget.html` 기본 `DEFAULT_ASSET_SET="original"`; rebuilt는 query로만 선택된다. `docs/index.html`은 `BASE="sprites/"`인 이전 payload이며 rebuilt 영상 폴더에는 0개, 기존 영상은39개다. 검토 완료 후 기본 런타임 경로와 Pages payload를 reviewed 후보로 정합하게 만들고 registry39개/현재영상hash/no-missing-reference를 검증한다. Electron build.files에는 rebuilt 영상 경로가 이미 포함되어 있지만 기본 자산 선택 완료 증거와는 다르다. |
| G8. 문서와 결과 기록 정리 | ANIMATION_REBUILD.md의 현재 수치15/39,29/39,doze draft,24 pending,브라우저 timeout,원본 기본,ending10 staged,전체 transition pending 등은 최신 결과와 함께 읽으면 혼동된다. 최종 39/579, 실제32케이스/39영상, 최종 chem3 추가검수, 기본자산·Pages 경로, 주요 repair·회귀 수정, 증거파일과 남은 한계를 일관된 최종 상태로 갱신한다. |

## 시각적 seam 우선 확인 항목

`root_static_review.md`의 우선 항목은 재생 오류가 아닌 시각적 검수 항목으로 아직 남아 있다.

- Boxing 04→05→06 및 반복 펀치 구간: 각각의 신발 접지점이 미끄러져 보이는지. 전체 shoe-center 정렬만으로 개별 발이 고정되었다고 가정하지 않는다.
- Happy1 실제 loop17→end00: loop00→end00의 정확한 anchor 검사와 구분한다. 원래 sway의 마지막 기울기에서 돌아오는 한 단계 자체는 결함이 아니다. 70ms dissolve 중 얼굴/가운 이중상이나 snap이 보이는지 확인한다.
- idle↔boxing/sad1/sad2와 basic3 발축 sway: 전용 bridge가 없는 원래 상태 구조와 의도된 crouch/jump를 보존하며 전환이 자연스러운지. sad2를 standing 높이로 확대하여 차이를 없애면 원래 행동을 훼손한다.
- Pastry 공통 camera: `pastry_camera_comparison.json`은 chef 얼굴 폭 약0.842×, 턱~신발 거리 약0.777× idle인 deliberate zoom 차이를 설명한다. flash 중 의상 변환과 함께 허용 가능한 카메라인지 실제 재생에서 판단한다. 무조건 동일 bbox로 보정하면 hat/overhead food가 잘리거나 의도된 포즈가 축소된다.
- Pastry end1–8 공통 display 04→05/06→07 및 eating08/09: overhead 머리·몸 비율, lowered plate 이후 크기 변화, 명확한 chipmunk cheeks/빈접시/heart/cheek-touch를 최종 프레임에서 확인한다. end6–8 정적 관측 notes의 slot7 크기 차이 항목도 재생 판단 후 최종 notes를 갱신한다.
- Happy3 full-turn/back/profile/curtsy, doze eye-rub/yawn, chemistry soot/wipe/clean recovery와 fizzle 결과는 원래 행동 보존의 핵심이다. 정적 motion 승인 기록은 이미 있지만, 최종 전체 재생에서 의도된 움직임을 지우는 정규화가 없다는 점과 안정된 전환을 함께 확인한다.

## 읽기 전용 dry-run 결과

검토 시 실행한 `python tools/deploy_pages.py --assets rebuilt --dry-run`은 수정 중 chem1_end3 때문에 `Missing reconstructed clip: chem1_end3`으로 중단했다. `--assets rebuilt --require-reviewed --dry-run`은 `Review incomplete: basic1_loop`으로 중단했다. 두 호출은 payload를 쓰지 않았다. 최종 승인 및 G1 완료 후 같은 검사를 통과시키고, 로컬 docs payload의 실제 후보 연결을 확인해야 한다. 문서에 적힌 deployed Pages 기준까지 완료로 주장하려면 배포된 결과의 해당 경로/현재 hash 검증 증거도 필요하다. 로컬 생성과 원격 게시를 같은 결과로 취급하지 않는다.

**완료 판정:** 579 PNG 생성과 이전32/39 런타임 통과는 확인된 큰 진척이다. 현재 chem3 최신 등록·재생,9 motion 승인,39 visual seam 승인,기본 런타임/Pages 자산 통합 및 최종 문서 정리가 남으므로 전체 목표 완료로 판정할 수 없다. 위 gate는 실제 작업 변경으로 해소되는 항목이며, 이 보고서 작성 자체로 review flags를 올리지 않았다.
