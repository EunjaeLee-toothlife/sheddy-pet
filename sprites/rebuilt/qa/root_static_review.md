# 초기 13개 클립 정적 그림·동작 검토

검토자: special_motion / 2026-09-30. 기준은 현재 `anims/rebuild_manifest.json`의 후보 PNG와 원본 PNG/구성 계획이다. 0부터 시작하는 PNG 인덱스를 사용한다. 원본 204장과 후보 204장을 모두 원본/후보 비교 시트로 확인하고, 기존 및 새 key-pose donor, 주요 포즈의 512px 확대, 흰 배경 합성, 얼굴/입 확대를 추가 확인했다. 브라우저 영상 재생과 상태 전환은 이 검토에 포함하지 않았다.

## 관측 결과와 범위

흰 가운·얼굴 안쪽에서 랜덤 얼룩, 잔상처럼 겹쳐 붙은 다른 캐릭터 조각, 뚜렷한 녹색 배경 구멍, 캔버스 경계에서 잘린 손/머리/신발을 발견하지 않았다. 얼굴 볼의 의도된 홍조, 가운 접힘의 옅은 보라색 음영, sad2 눈물, boxing 입김과 펀치 속도선은 얼룩으로 분류하지 않았다. 기본 의상, 레몬 머리핀, 주요 동작 순서도 보존되어 있다. 이 관측은 전체 원본/후보 contact 및 별도 donor 확대에 근거한다. 코드 audit 통과로 그림/전체 재생을 합격 판정한 것이 아니다.

정적 검토에서 반드시 재생성해야 할 심한 얼룩/클리핑/행동 누락은 확인되지 않았다. 다만 아래 3가지 연결/발 움직임은 브라우저에서 우선 확인해야 한다. 정적 관측만으로 런타임 전환을 합격 처리하면 안 된다.

## 우선 재생 확인 / 개선 후보

### R1. boxing1 04→05→06 발 위치 변화

- 근거: [전체 원본/후보 비교](root_static/boxing1_loop_compare.png), [512px 흰 배경 확대](root_static/boxing1_loop_details_white.png), [색상 기반 신발 bbox 참고값](root_static/shoe_boxes.json).
- 후보 04의 화면 왼쪽 갈색 신발 x범위는 146–193, 05는 135–174, 06는 139–179이다. 신발 가시 범위 중심이 04→05에서 약 15px 왼쪽으로 바뀐다. 화면 오른쪽 신발은 폭/방향이 함께 달라진다. 전체 발 중심을 맞춘 등록으로는 양쪽 발 각각의 고정점을 보장하지 않는다.
- 원본도 발의 방향/폭 변화가 있어 후보 회전만을 동작 누락으로 판단하지 않았다. metadata는 발을 같은 바닥 지점에 두고 발끝으로 pivot하라고 명시한다. 회전할 때 신발 실루엣 변화는 정상일 수 있으므로, 여기서는 **바닥에서 미끄러져 보이는지 재생 확인할 항목**으로 남긴다.
- 02↔03과 05↔06은 각각 반복되는 펀치 구간이다. 0.8 배속에서도 발이 옆으로 왕복하면 각 신발의 발끝/접지점을 기준으로 donor 등록을 보완한다. 폭 자체를 강제로 같게 만드는 수정은 회전을 훼손할 수 있다.
- 사용자 승인한 07/08 upright/puffed-cheek breathing은 적용되어 있다. 해당 두 프레임의 duck/weave 제거는 결함이 아니다.

### R2. happy1 루프 종료→end 시작은 실제 마지막 프레임과 동일하지 않음

- 근거: [happy1 loop 전체](root_static/happy1_loop_compare.png), [마지막/첫 프레임 512px](root_static/happy1_loop_details_white.png), [앵커 픽셀 비교](root_static/happy_anchors.json).
- start05→loop00 및 loop00→end00는 가시 픽셀이 정확히 같다. 그러나 실제 loop17은 원본 sine sway의 약 −0.82° 기울기/약 −0.41px bob 상태이고 end00는 중립 clasped pose다. loop17→end00는 기울기가 돌아오는 한 단계 움직임이다.
- 이 차이는 원본 구성과 같은 연속 sway 샘플링에서 오는 것으로, 마지막=첫 프레임 조건을 무조건 강제할 결함은 아니다. 하지만 중앙 ledger의 loop00→end00 앵커 검증을 **실제 loop17→end00 재생 검증**과 혼동하면 안 된다.
- 70ms 크로스 디졸브 중 얼굴/가운이 잠깐 이중으로 보이는지 확인한다. 자연스럽게 돌아오면 유지한다. 뚜렷한 snap이 보이면 실행 중 종료 phase에 맞춰 end 첫 프레임을 등록하거나 다음 중립 loop anchor에서 종료하도록 검토한다.

### R3. boxing/sad 상태의 idle 연결은 포즈가 바뀌므로 정확 앵커만으로 해결되지 않음

- 근거: [boxing](root_static/boxing1_loop_compare.png), [sad1](root_static/sad1_loop_compare.png), [sad2](root_static/sad2_loop_compare.png), [가시 픽셀 seam 비교](root_static/seam_stats.json).
- boxing00/11은 넓은 발 간격·주먹 guard이고 canonical idle은 좁은 발 간격·내린 팔이다. sad1은 축 처진 팔과 슬픈 얼굴, sad2는 바닥에 앉아 무릎을 끌어안은 포즈다. 각 clip의 내부 끝→처음은 정확히 닫히지만 시작/끝이 idle과 같은 포즈는 아니다.
- `widget.html`의 상태 전환은 기존 end가 있을 때만 재생한 뒤 다음 clip으로 넘어가며 `FADE_MS=70` 디졸브를 사용한다. 이 세 상태에는 전용 end/start가 없다. sad2→idle은 특히 몸 높이가 크게 바뀌어 순간적인 겹침/팝업이 생길 가능성이 있다. 원본에도 같은 구조였으므로 **후보 그림 손상으로 확정하지 않는다**.
- 일반 표시 크기와 확대 표시에서 idle↔sad2를 우선 확인한다. 이중 몸/갑작스러운 일어남이 불편하면 별도 일어나는 bridge/outro를 만드는 개선이 필요하다. sad2를 억지로 서 있는 높이로 확대하는 수정은 금지: 현재 0.83 donor 스케일은 머리 크기를 standing 기준에 맞추려는 의도적 정규화이고 실제 crouch를 유지한다.

## 클립별 전체 프레임 관측

| 클립 | 확인한 동작/그림 | 내부 끝→처음 및 idle 연결 | 증거 |
|---|---|---|---|
| idle1_loop 18장 | open/closed eye donor, 07/08 깜박임, 나머지 호흡 bob. 얼굴/가운 깨끗함. metadata의 9개 설명보다 실제 18장 compose plan을 기준으로 확인. | 17→00은 원본 +0.1px→0px bob 복귀. 가시 픽셀 차이는 있지만 눈/포즈 교체가 아님. 17 신발 바닥 및 중심도 거의 동일. | [비교](root_static/idle1_loop_compare.png), [donor](root_static/idle1_loop_donors.png) |
| basic1_loop 18장 | 정면→왼쪽 3/4→정면→오른쪽 near-profile→정면, 좌우 머리핀/옷 유지. 세 donor는 선명. | 00/17 및 idle00 정확히 동일. | [비교](root_static/basic1_loop_compare.png), [donor](root_static/basic1_loop_donors.png) |
| basic2_loop 18장 | neutral00/01→mid02/03 열린 손바닥·졸린 눈·작은 하품→full04–14 주먹·감은 눈·큰 하품→mid15/16→neutral17. 양팔 wide V 보존. | 00/17/idle 정확히 동일. donor 머리/신발 크기를 512px로 비교한 결과 뚜렷한 비의도 크기 점프는 확인하지 못함. 포즈 전환은 원본과 같은 3단계. | [비교](root_static/basic2_loop_compare.png), [흰 배경](root_static/basic2_loop_details_white.png), [donor](root_static/basic2_loop_donors.png) |
| basic3_loop 18장 | canonical 단일 donor를 양방향 기울임. 얼굴/옷은 동일 픽셀 재사용. 원본 ±2.4°와 dy 계획 유지. | 17 약 −0.8°→00 중립으로 돌아오는 연속 단계. 정확한 복사 seam은 아니며 이 자체는 결함 아님. 발을 축으로 기울일 때 화면 바닥 bob은 재생에서 확인. | [비교](root_static/basic3_loop_compare.png) |
| happy1_start 6장 | neutral00/01→가슴 앞 주먹02/03→손 clasped04/05, 웃는 눈·금색 sparkles. 가운/손에 파편 없음. | start00 idle 동일, start05 loop00 동일. | [비교](root_static/happy1_start_compare.png), [donor](root_static/happy1_start_donors.png) |
| happy1_loop 18장 | clasped happy donor로 좌우 sway/bob. 금색 sparkles가 분리된 효과로 유지. | R2 참조. | [비교](root_static/happy1_loop_compare.png) |
| happy1_end 6장 | clasped00/01→가슴 앞 주먹02/03→neutral04/05. 효과 사라짐은 포즈 복귀 단계에 맞음. | end05 idle00 동일. end00은 loop00 동일이며 실제 loop17 연결은 R2. | [비교](root_static/happy1_end_compare.png) |
| happy2_loop 18장 | 화면 왼쪽 열린 손 인사·활짝 웃는 얼굴, sway 후 neutral 복귀. 머리핀/의상 유지. | 00/17/idle 동일. | [비교](root_static/happy2_loop_compare.png), [donor](root_static/happy2_loop_donors.png) |
| excited1_loop 18장 | 무릎 굽히기·가슴 앞 주먹02–05, 양손 들고 다리 접은 airborne06–11, 착지12/13, neutral 복귀14–17. 머리 위 ahoge 및 손끝이 잘리지 않음. | 00/17/idle 동일. jump 높이 변화는 의도적. | [비교](root_static/excited1_loop_compare.png), [donor](root_static/excited1_loop_donors.png), [흰 배경](root_static/excited1_loop_details_white.png) |
| boxing1_loop 12장 | LEFT jab02, LEFT guard03, RIGHT pivot04, RIGHT cross05, guard06, 승인 upright07/08, 마지막 front guard. 속도선/입김 유지. 가운 깨끗함. | 11=00 정확. 발 재생 R1, idle R3. | [비교](root_static/boxing1_loop_compare.png) |
| sad1_loop 18장 | 처진 팔·눈썹·슬픈 작은 입, 미세 호흡. action 추가 누락은 원본 plan 기준 없고 원본도 단일 donor 호흡. | 17=00 정확, idle R3. | [비교](root_static/sad1_loop_compare.png), [donor](root_static/sad1_loop_donors.png) |
| sad2_loop 18장 | 무릎 끌어안기·눈물·축 처진 표정, 미세 sway/bob. 원본처럼 큰 머리로 늘리지 않고 standing 머리에 맞게 축소/발 정렬. | 17=00 정확, idle R3. 낮은 머리 높이는 crouch 의도. | [비교](root_static/sad2_loop_compare.png), [donor](root_static/sad2_loop_donors.png) |
| talk_loop 18장 | 원본 불규칙 base/half/open mouth 순서 보존. 입 밖 얼굴·옷 고정은 승인된 의도. 확대에서 뚜렷한 rectangular patch/턱 선 중복/가운 얼룩 없음. | 17 half→00 base는 정상 입 닫기. 차이 bbox [234,162,276,194]로 feather 포함 입 근처에 한정. 00 idle 동일. | [비교](root_static/talk_loop_compare.png), [donor](root_static/talk_loop_donors.png), [입 확대](root_static/edge_mouth_zoom.png) |

## 정적 보조 자료

- [원본 및 후보 파일 경로·각 frame bbox](root_static/geometry.json).
- [visible-alpha seam / idle 비교](root_static/seam_stats.json): 완전 투명 픽셀의 숨은 RGB를 제외하고 premultiplied RGB+alpha를 비교했다. 변경 픽셀 수는 미세 보간에도 커질 수 있으므로 시각적 결함의 크기로 해석하지 않는다.
- 관련 원본 204장의 SHA-256은 중앙 ledger `sourceFrameHashes`와 모두 일치한다. 원본과 후보/중앙/tools를 편집하지 않았다.
- [happy1 실제 연결 앵커](root_static/happy_anchors.json).
- `*_original_donors.png`는 구성에 사용된 원본 donor 전부를 별도로 펼친 자료이고, `*_donors.png`는 새 donor 확대다. boxing 원본은 독립 frame 자체가 donor 역할을 하므로 전체 비교 시트에서 12장 모두 확인했다.
- 보고서 및 contact 생성에 사용한 전용 QA 스크립트: [build_details.py](root_static/build_details.py). 이는 기존 tool이나 candidate 생성 pipeline에 연결하지 않았다.

브라우저 담당자는 R1–R3와 basic3 발축 sway를 일반 표시 크기/확대에서 확인한 뒤 재생 및 cross-state review 플래그를 판단하면 된다. 이 정적 리뷰는 중앙 review 플래그를 변경하지 않았다.
