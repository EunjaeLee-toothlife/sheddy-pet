# Sheddy Pet — Chibi 애니메이션 스프라이트 프롬프트 초안

> **⚡ 파이프라인 변경 (검증 완료):** 그리드 스프라이트 시트 방식은 셀 크기·배치가 매번 흔들려서 폐기.
> 현재 방식: **베이스 이미지 1장(`refs/chibi_base.png`, 잘 나온 idle 프레임)을 --ref로 고정하고
> 각 프레임을 512px 1:1 이미지로 한 장씩 생성.**
> - 프레임별 포즈 설명: `anims/<이름>.json` (frames 배열)
> - 생성: `python tools/gen_frames.py anims/idle1_loop.json --outdir sprites/raw`
> - 후처리: `python tools/slice_and_key.py --frames "sprites/raw/idle1_loop_*.jpg" --outdir sprites/idle1_loop --prefix idle1_loop --erode 1`
> - WebM: `ffmpeg -y -framerate 5 -i sprites/idle1_loop/idle1_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_idle1_loop.webm`
> - 실패 프레임 재시도: `gen_frames.py ... --only <인덱스>`
> - 프레임 공통 프리앰블/캐릭터 블록/스타일은 `tools/gen_frames.py`에 내장.
> 결과: 전 프레임 bbox 높이 동일(456px), 중심 ±0.7px — 그리드 방식보다 훨씬 안정적.
> 아래 그리드 시트 방식 설명은 참고용으로 유지.

## 공통 스펙
- 캐릭터 레퍼런스: `refs/chibi_lemon_turnaround.jpg` (생성 시 `--ref`로 항상 첨부)
- 길이: 3초 @ 5FPS = **총 15프레임**
- **프레임 크기: 512×512px, 1:1** (각 장면 개별 프레임 기준)
- 구조: 예시 에셋(anim_happy1_start/loop/end)처럼 **start / loop / end** 3단 분할 권장
  - start: 3프레임 (진입 동작)
  - loop: 9프레임 (**첫 프레임과 마지막 프레임이 자연스럽게 이어지는 seamless loop**)
  - end: 3프레임 (기본 자세 복귀)
- 시트 레이아웃 (512px 프레임으로 정확히 슬라이스되도록 그리드 생성 → 분할):
  - **loop: 3×3 그리드**, 1:1 aspect로 생성 후 1536×1536으로 리사이즈 → 512px 타일 9개
  - **start+end: 3×2 그리드** (윗줄 start 1→3, 아랫줄 end 1→3), 3:2 aspect로 생성 후 1536×1024로 리사이즈 → 512px 타일 6개
  - 프레임 순서: 왼쪽→오른쪽, 위→아래
- 슬라이스 정합성을 위해 **모든 프레임에서 캐릭터 위치/스케일 고정** (셀 중앙, 세로 약 75% 차지) — 프리앰블에 포함됨

## 공통 프리앰블 (모든 프롬프트 앞에 붙임 — 그리드 형태에 맞게 첫 구절 교체)
```
Sprite sheet of animation frames arranged in a {3x3 | 3 columns x 2 rows} grid with equal square cells, frames ordered left-to-right then top-to-bottom. CRITICAL: every cell shows the ENTIRE character from the top of the head down to the soles of her shoes — head, body, legs, socks and shoes all fully inside the cell, never cropped by any cell edge, with generous empty margin on all four sides; the character is small within the cell, occupying only about 60% of cell height. Same character in every cell, identical proportions and outfit, centered at identical position and scale, front-facing, standing on an invisible floor, solid pure green chroma-key background (#00FF00), no text, no numbers, no borders.
```
> 테스트 검증 완료 버전. 부드러운 조건("about 70%", "feet never touching edges")은 무시됨 — CRITICAL + "from the top of the head down to the soles of her shoes" + 60%처럼 강하게 써야 전신이 보장됨. 동작이 너무 미묘하면 동작 프롬프트에 `clearly visible pose difference between frames, slightly exaggerated motion` 추가.

## 캐릭터 블록 (모든 프롬프트에 포함)
```
a cute chibi girl (2.5-head proportion), long blonde hair, big yellow-gold eyes, small lemon-slice hair clip, oversized white lab coat with rolled sleeves over a white button-up shirt, pastel yellow pleated mini skirt with a lemon print, white crew socks, brown penny loafers
```

## 공통 스타일 접미사 (모든 프롬프트 뒤에 붙임)
```
[STYLE] high-quality anime, clean vector linework, bold thick dark-brown outline around the entire character silhouette (3-4px), consistent heavy line weight, soft bloom. soft pastel lemon palette, cozy desktop-pet mascot design, sticker-like thick contour.
```
> 크로마키 키잉 시 얇은 외곽선이 손상되지 않도록 두꺼운 실루엣 외곽선을 명시 (sticker-like contour가 잘 먹힘)

---

## 1) 대기 상태 (idle) — 1종

### idle1 (숨쉬기 대기)
- **loop (9 frames)**: `9 animation frames of a gentle idle breathing cycle: standing relaxed, subtle up-down body bob, hair swaying slightly, slow blink on middle frames, soft neutral smile. First and last frames match for seamless looping.`
- start/end 생략 가능 (기본 자세 자체가 idle이므로 loop만으로 충분)

## 2) 기본 상태 (basic) — 4종

### basic1 (두리번거리기)
- **start (3)**: `3 animation frames easing from neutral standing pose into a curious look-around: head begins turning to the left.`
- **loop (9)**: `9 animation frames of looking around curiously: head turns left, pauses, turns right, eyes following, tiny body lean each way. Seamless loop.`
- **end (3)**: `3 animation frames returning from look-around back to neutral front-facing standing pose.`

### basic2 (기지개)
- **start (3)**: `3 animation frames easing from neutral pose: arms slowly rising overhead into a stretch.`
- **loop (9)**: `9 animation frames of a sleepy stretch: arms overhead, body arching slightly, eyes squeezed, small yawn, then relaxing shoulders. Seamless loop.`
- **end (3)**: `3 animation frames lowering arms and settling back to neutral standing pose.`

### basic3 (좌우 흔들기)
- **start (3)**: `3 animation frames easing from neutral pose into a gentle side-to-side sway, hands clasped behind back.`
- **loop (9)**: `9 animation frames of relaxed side-to-side swaying, weight shifting foot to foot, skirt and lab coat swinging softly, content expression. Seamless loop.`
- **end (3)**: `3 animation frames settling from the sway back to neutral standing pose.`

### basic4 / doze1 (꾸벅꾸벅 졸기)
제자리에 서서 눈이 감기며 고개가 점점 떨어지다 앞으로 넘어질 듯 → 놀라서 고개 번쩍 →
눈 비비고 작게 하품 → 다시 눈이 감기기 시작. 14프레임 seamless 루프 @10FPS, 위젯 `rate 0.7`
(사이클 약 2초), `minCycles 2 / maxCycles 3`. 몸 위치 고정, 머리·눈·한 팔만 움직임.
- 정의: `anims/doze1_loop.json`
- **머리 위 'Zzz'·'!' 같은 떠 있는 기호는 넣지 않음** — 매트 정리에서 본체와 분리된 조각은
  지워지므로 표정과 고개 움직임만으로 표현.
- 생성 메모: chain 모드의 "motion must be small and smooth" 지시가 고개 떨어지는 폭을 눌러
  1차 결과가 너무 미묘했음. 3~5번 프레임에 "clearly visible pose difference, exaggerated
  nodding motion / chin pressed on her chest so the viewer mostly sees the top of her head"를
  추가해 재생성(`--only 3 4 5` 순차)하자 확실한 꾸벅 동작이 나옴.
- WebM: `ffmpeg -y -framerate 10 -i sprites/doze1_loop/doze1_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_doze1_loop.webm`

## 3) 행복 상태 (happy) — 2종

### happy1 (미소 + 몸 흔들기)
- **start (3)**: `3 animation frames of face lighting up: eyes widening into happy arcs, smile growing, hands coming together in front of chest.`
- **loop (9)**: `9 animation frames of happy wiggle: closed-eye smile, cheeks blushing, body swaying rhythmically with hands clasped, small sparkles around head. Seamless loop.`
- **end (3)**: `3 animation frames of the smile softening and hands lowering back to neutral standing pose.`

### happy2 (팔 흔들며 인사)
- **start (3)**: `3 animation frames raising one hand up into a wave, face brightening into an open-mouth smile.`
- **loop (9)**: `9 animation frames of cheerful waving: hand waving side to side overhead, other hand at chest, bouncing lightly on toes, beaming smile. Seamless loop.`
- **end (3)**: `3 animation frames lowering the waving hand and settling into neutral standing pose.`

### happy3 (공주님 턴 + 커트시)
샤랄라 우아하게 한 바퀴 돌고(온팁토, 발레리나처럼 양팔 벌림, 스커트/코트/머리카락 플레어)
공주님 인사(커트시: 양손으로 치맛단 잡고 한 발 뒤로 빼며 깊이 숙임)로 마무리하는
완결형 시퀀스. `gen_frames.py` 방식 20프레임 루프 (스핀 0-10, 커트시 11-19).
- 회전은 8방향 뷰 서술로 표현: front → 3/4 left → LEFT PROFILE → 3/4 back →
  FULL BACK(얼굴 없음, 뒷머리+등) → 3/4 back right → RIGHT PROFILE → 3/4 right → front.
  "몇 도 회전" 같은 수치는 모델이 못 알아듣고, "FULL BACK view, her face NOT visible"처럼
  **뷰 자체를 명시**해야 안정적으로 나온다.
- 정의: `anims/happy3_loop.json` (frames 20개)
- WebM(10FPS, 20프레임=2초): `ffmpeg -y -framerate 10 -i sprites/happy3_loop/happy3_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_happy3_loop.webm`
- 위젯에서 `rate: 0.8` + `minCycles 1 / maxCycles 2`로 등록 (완결형 동작이라 1~2회만)
- **의상/소품 일관성 팁**:
  - "skirt flared wide like a spinning bell" 같은 표현은 치마를 드레스처럼 길게
    늘린다. 매 프레임에 "SHORT pleated mini skirt, hem well above her knees,
    white crew socks clearly visible"을 명시할 것.
  - 연속 프레임에서 손 그립(치맛단 잡기 등)이 흔들리면 **체인 모드** 사용:
    `python tools/gen_frames.py <cfg> --chain --only N` (또는 config에 `"chain": true`).
    직전 프레임을 IMAGE 2로 함께 첨부해 "change ONLY the specific pose difference"로
    지시한다 — 그립·의상 디테일이 프레임 간 고정됨. (happy3 커트시 12-17이 이 방식)
  - 회전 각도는 수치("30도")가 아니라 뷰 명칭(3/4 view, FULL BACK view 등)으로 지시.

## 4) 신남 상태 (excited) — 2종

### excited1 (점프 환호)
- **start (3)**: `3 animation frames of anticipation crouch: knees bending, fists clenched at sides, sparkling excited eyes, big grin.`
- **loop (9)**: `9 animation frames of an excited jump cycle: leaping into the air with both arms thrown up, hair and lab coat flying, star-sparkle effects, landing softly and bouncing again. Seamless loop.`
- **end (3)**: `3 animation frames landing and catching breath, settling back to neutral standing pose with a leftover grin.`

### excited2 / boxing1 (뚜쉬뚜쉬 쉐도우 복싱) — v2 몸 돌리기
어깨너비 스탠스(발 고정, 발끝으로만 피벗), 양 주먹 턱 앞 가드, 볼 빵빵 + 입 오므려
"뚜쉬뚜쉬" 숨 내뱉는 표정. **왼쪽 3/4 뷰로 몸을 틀어** 잽 → 가드 → **오른쪽 3/4 뷰로 틀어**
크로스 → 가드 → 정면으로 돌아와 낮게 덕킹 좌·우 → 일어나 바운스.
12프레임 seamless 루프 @10FPS, 위젯 `rate 0.8`, `minCycles 2 / maxCycles 4`.
- 정의: `anims/boxing1_loop.json`
- 몸 회전은 happy3처럼 각도가 아니라 **뷰 이름**으로 지시: "3/4 VIEW FACING THE LEFT SIDE OF
  THE IMAGE (one shoulder closer to the viewer, NOT a full profile)". lite 모델에서도 1발에
  좌·우 3/4 뷰가 안정적으로 나옴 (v1은 정면 고정 + 대각선 펀치였음, 스크래치 백업만 유지).
- **되돌리는 회전은 chain이 거부함**: 3/4 뷰 → 정면 복귀 프레임(7~10)이 1차에서 전부 3/4 뷰에
  머물렀음. "her body has ROTATED BACK to a FRONT VIEW, square to the viewer: both shoulders
  equally visible, chest facing the camera (NOT a 3/4 view anymore)"처럼 **결과 상태를 묘사 +
  이전 상태를 부정형으로 명시**해야 돌아옴. 덕킹→기립(v1)도 같은 패턴("NOT crouching").
  루프 클로저(11)는 chain 결과 대신 **0번 프레임을 그대로 복사**해 완전 seamless로 처리.
- 펀치는 몸을 튼 방향으로 **화면 좌/우를 향해 직선**으로 (정면 펀치는 단축 원근이 깨짐).
  dance2에서 검증된 "arms never cross in front of her chest" 문구 포함.
- **구간 반복 인코딩 (`encode_holds.py` `repeats`)**: 잽(2-3)과 크로스(5-6)를 각 4회 반복해
  뚜쉬뚜쉬 연타로 만듦 — 12프레임 → 24틱(2.4초, rate 0.8로 약 3초). 프레임 생성 없이 JSON에
  `"repeats": [{"frames": [2, 3], "times": 4}, {"frames": [5, 6], "times": 4}]`만 추가.
  ```bash
  python tools/encode_holds.py anims/boxing1_loop.json
  ```
- 정면 복귀(7)는 chain 앵커를 직전 프레임(6, 3/4 뷰)이 아니라 **0번 정면 프레임**으로 바꿔
  생성: `gen_frames.py ... --only 7 --prev sprites/raw/boxing1_loop_00.jpg` (`--prev` 신규 옵션).
  텍스트로 "ROTATED BACK to FRONT VIEW"를 강조해도 3/4 뷰 앵커에서는 두 번 연속 실패했음.
- WebM: `ffmpeg -y -framerate 10 -i sprites/boxing1_loop/boxing1_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_boxing1_loop.webm`

## 4-b) 특수: 댄스 (dance) — 1종

### dance1 (오버맨 킹 게이너 춤 — 팔 흔들기)
작품 「OVERMAN 킹 게이너」 OP의 상징적인 춤. 반쯤 앉은 자세로 무릎 바운스하며,
**팔꿈치를 항상 90도로 굽힌 채** 두 주먹을 몸 앞에서 위아래 **반대 위상**으로 펌핑
(한쪽이 뺨 높이일 때 반대쪽은 허리 높이 — 마라카스 흔들듯). 주먹은 절대 머리 위로
올라가지 않고 팔도 절대 쭉 펴지 않는다. 발은 모든 프레임에서 엉덩이 바로 아래에
모음(벌리면 기마자세가 됨). `gen_frames.py` 방식 16프레임 seamless 루프
(짝수 = 키 포즈, 홀수 = 중간 프레임).
- 프레임 구조: `0 최저점(양주먹 가슴) → 1-4 화면왼쪽 주먹이 가슴→어깨→뺨으로 상승,
  반대 주먹은 허리→엉덩이로 하강 (몸은 바운스 업) → 5-7 주먹 교차하며 하강 →
  8 최저점 → 9-12 화면오른쪽 주먹 상승 (미러) → 13-15 교차·하강 → 루프`
- 정의: `anims/dance1_loop.json` (frames 16개)
- 생성: `python tools/gen_frames.py anims/dance1_loop.json --outdir sprites/raw`
- 후처리: `python tools/slice_and_key.py --frames "sprites/raw/dance1_loop_*.jpg" --outdir sprites/dance1_loop --prefix dance1_loop`
- WebM(16FPS, 16프레임=1초): `ffmpeg -y -framerate 16 -i sprites/dance1_loop/dance1_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_dance1_loop.webm`
- **프롬프트 팁 (검증됨)**:
  - "monkey dance" 같은 별칭 단어를 쓰면 만세/점프 동작으로 새어나간다.
    별칭 대신 **동작의 기하학을 직접 서술**할 것 (팔꿈치 각도, 주먹 높이 한계, 반대 위상).
  - 좌우 팔 교대: 모델이 한쪽 팔(주로 화면 왼쪽)만 계속 올리는 경향이 있다.
    거울 프레임은 **캐릭터 기준 + 화면 기준 이중 표기**("HER LEFT fist (the fist near
    the RIGHT edge of the image) is pumping UP")로 지시해야 확실히 반대 팔이 올라간다.
    (`--only N`으로 해당 프레임만 재생성)
  - 한 주먹 위 + 한 주먹 아래 비대칭이 자꾸 양주먹 동시 올림으로 나오면:
    "IMPORTANT: the two fists are FAR APART vertically / NOT together, NOT at the
    same height"를 명시하고, **내려간 팔을 문장 맨 앞에** 먼저 서술할 것.

## 4-c) 특수: 거제 야호 (yaho) — 1종

### yaho1 (리센느 '거제 야호' 밈 포즈)
걸그룹 리센느 미나미의 '거제 야호' 밈 재현. 양손을 입가에 메가폰처럼 모아
"야호~!" 하고 외친 뒤, 갸루 시그니처 포즈로 마무리: **한쪽 눈 윙크 +
거꾸로 브이(검지·중지를 아래로 향하게, 손등이 화면 쪽) 를 뺨 옆에** 대고
반대 손은 허리에, 골반은 반대쪽으로 쭉. `gen_frames.py` 방식 14프레임
완결형 시퀀스 (0-2 숨 들이쉬기 → 3-5 외침 → 6-8 포즈 전환 → 9-11 포즈
유지(미세 바운스) → 12-13 복귀).
- 정의: `anims/yaho1_loop.json` (frames 14개)
- WebM(10FPS, 14프레임=1.4초): `ffmpeg -y -framerate 10 -i sprites/yaho1_loop/yaho1_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_yaho1_loop.webm`
- 위젯 등록: `rate: 0.53, minCycles: 1, maxCycles: 2` (완결형 동작. 0.8도 빨라서 그 2/3로 조정, 사이클 약 2.6초)
- 포즈 팁: "V sign"만 쓰면 평범한 브이가 나온다. **"UPSIDE-DOWN V peace
  sign, fingers pointing DOWN, back of her hand toward the viewer, held
  next to her cheekbone under the winking eye"처럼 손 방향을 기하학적으로
  명시**해야 갸루 피스가 나온다.

## 4-d) 특수: 파라파라 댄스 (parapara) — 1종

### parapara1 (파라파라) — v2
'거제 야호' 밈에서 미나미가 춘 그 춤. **하체는 거의 고정**(어깨너비로 발을
심고 무릎 바운스 + 힐 리프트만), 파라파라의 시그니처인 **곧게 뻗은 팔의
교차 대각 찌르기**가 핵심. 부드러운 움직임을 위해 **24프레임 @12FPS**
(사이클 2초, 3프레임 × 8비트) seamless 루프.
- 비트맵: 화면왼쪽 팔 좌상단 45° 찌르기(반대 손은 가슴에) → 스왑, 오른팔
  우상단 찌르기 → 왼팔 반복 → 오른팔 반복 → 양팔 T자 → 가슴 앞 손목
  X크로스 → 양팔 하이 V → 내리며 가슴 복귀.
- 정의: `anims/parapara1_loop.json` (frames 24개)
- WebM(12FPS): `ffmpeg -y -framerate 12 -i sprites/parapara1_loop/parapara1_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_parapara1_loop.webm`
- 위젯 등록: `rate: 0.6, minCycles: 2, maxCycles: 3` (원속 2초/사이클은 너무 빨라 0.6배속 ≈ 3.3초/사이클)
- **프롬프트 팁 (v1 실패에서 배운 것)**:
  - "양손으로 큰 호를 그린다" 같은 **연속 궤적 서술은 실패한다** — 프레임마다
    팔꿈치 각도·팔 위치가 제각각으로 나와 팔이 널뛴다. 킹게이너 댄스처럼
    **매 프레임 양팔의 기하학(각도·높이·곧음)을 전부 명시**할 것:
    "FULLY extended, PERFECTLY STRAIGHT with no elbow bend, toward the
    upper-LEFT corner at about 45 degrees" + 활성 팔은 이중 라벨
    ("HER RIGHT arm (the arm on the LEFT side of the image)").
  - 쉬는 손 위치도 고정: "the other hand pulled in, lying flat against
    her upper chest, elbow tucked down".
  - "her arms NEVER cross in front of her face"를 매 프레임 반복 — 머리
    위에서 팔이 꼬이는 프레임 방지. X크로스는 "at CHEST height, well
    below her face"로 높이를 못박는다.
  - 매 프레임에 "open flat hands, fingers together and extended (never
    fists)" + "feet planted shoulder-width, no jump, no squat" 반복.

## 4-e) 특수: 화학 실험 (chem) — 1종, 멀티 엔딩 ⭐신규 구조

### chem1 (플라스크 실험 — start + loop + 랜덤 end 3종)
등 뒤에서 삼각 플라스크(마젠타-핑크 액체)와 비커(시안-블루 액체)를 꺼내
'짜잔!' → 비커를 플라스크에 붓고 얼굴 앞에서 흔들어 섞기(loop) →
loop 2~5회 뒤 **3가지 엔딩 중 하나가 랜덤 재생**되는 첫 멀티 엔딩 모션.
- **클립 구성 (모두 @10FPS, `gen_frames.py` + chain 모드)**:
  프레임 수를 동작 대비 1.25배로 잡아 실시간 재생이 체감 0.8배속이 되게 함
  (프레임 밀도로 느리게 해 부드러움 확보. 0.95(정확히 0.8배속)도 체감상 빨라서
  위젯 `rate: 0.7`로 최종 조정 — loop 사이클 약 2.7초, 원안 대비 약 0.6배속)
  - `chem1_start` 12프레임 (1.2초): 등 뒤에서 꺼내 짜잔 → 믹싱 준비 자세
  - `chem1_loop` 20프레임 (2.0초): 붓기 → 플라스크 얼굴 앞으로 → 흔들어 섞기 → 복귀 (seamless)
  - `chem1_end1` 20프레임 (2.0초): 실패 — 검은 연기 펑! → 그을음 벙찐 콩알눈 → 켈록 기침
    → 도구 숨기고 노란 프릴 손수건으로 얼굴 닦기 (마지막 프레임은 그을음 완전 제거)
  - `chem1_end2` 12프레임 (1.2초): 애매 — 살짝 빛나다 사그라듦 → 머리 위 '?' → 도구 숨김
  - `chem1_end3` 18프레임 (1.8초): 성공 — 화려한 빛 + 내용물 무지개색 변화 → 과장된
    반짝이 눈 → 짜잔! 플라스크 치켜들기 → 도구 숨김
- 정의: `anims/chem1_start.json`, `chem1_loop.json`, `chem1_end1.json`, `chem1_end2.json`, `chem1_end3.json`
- 생성/후처리 (클립별 반복):
  ```bash
  python tools/gen_frames.py anims/chem1_loop.json --outdir sprites/raw
  python tools/slice_and_key.py --frames "sprites/raw/chem1_loop_*.jpg" --outdir sprites/chem1_loop --prefix chem1_loop
  ffmpeg -y -framerate 10 -i sprites/chem1_loop/chem1_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_chem1_loop.webm
  ```
- 위젯 등록: `end`를 **배열**로 주면 상태 전환 시 랜덤으로 하나 재생.
  `minCycles: 2, maxCycles: 5` → 최소 2사이클 보장, 이후 매 사이클 35% 확률로 종료,
  5사이클 도달 시 강제 종료.
- **연속성 규칙 (프레임 정의에 반영됨)**:
  - start 마지막 프레임 = loop 프레임 0 = end 3종의 프레임 0 (플라스크 가슴 높이
    화면왼쪽 손, 비커 어깨 높이 화면오른쪽 손)
  - end 3종의 마지막 프레임 = 빈손 기본 idle 자세 (도구는 등 뒤로 숨김)
- **소품 프롬프트 팁**:
  - 손 배정 고정: 플라스크는 항상 화면 **왼쪽** 손, 비커는 항상 화면 **오른쪽** 손.
    chain 모드 필수 — 소품 디테일(액체 색·유리 형태)이 텍스트만으로는 프레임 간 고정 안 됨.
  - **액체 양은 모든 프레임에서 동일** ("liquid levels never change, cartoon logic").
    붓는 동작이 loop라서 양이 변하면 seamless가 깨짐.
  - 유리는 **불투명 페일 틴트로 지시** ("opaque pale blue-white glass tint, NEVER
    transparent") — 투명 유리로 나오면 그린 배경이 비쳐 크로마키 때 유리에 구멍이 뚫림.
  - end1의 그을음은 마지막 3프레임에 걸쳐 단계적으로 지우고, 최종 프레임에
    "face COMPLETELY CLEAN"을 명시해야 idle 복귀가 자연스러움.

## 4-f) 특수: 앞발 부기 댄스 (dance2) — 1종

### dance2 (앞발 부기 댄스, 포케댄스 '부기부기 뱀뱀' 모티브) — Lite 모델 1호
포켓몬 데이 2024 바이럴 댄스(POKÉDANCE)의 시그니처 동작. 양손을 **강아지 앞발
모양 주먹**(손목 툭 떨군 느슨한 주먹, 손등이 화면 쪽)으로 어깨 앞에 들고,
상체+양 앞발이 한쪽으로 스웨이할 때 **힙은 반대쪽으로** 빠지는 바나나 커브
(부기부기), 마지막에 정면 보며 **양 앞발을 화면 쪽으로 두 번 내밀기**(뱀뱀).
16프레임 seamless 루프 @12FPS (0-5 왼쪽 스웨이 2바운스 → 6-11 오른쪽 미러 →
12-15 앞발 푸시 x2).
- **모델: `gemini-3.1-flash-lite-image`** — 이 모션의 검증 결과가 좋아
  `gen_frames.py`의 기본 모델을 lite로 교체함 (`--model`/config `"model"`로
  다른 모델 오버라이드 가능). Lite 모델도
  베이스 ref 1장 기준 캐릭터/의상/화풍 일관성 양호. 단 **몸통 기울기 지시가
  잘 안 먹는 편** — "clearly LEANING like a banana curve", "NOT standing
  straight"처럼 과장해서 써야 하고, 팔이 가슴을 가로지르는 오생성이 나오면
  "her arms NEVER cross in front of her chest / BOTH paws SIDE BY SIDE as a
  pair on the RIGHT side"로 재생성(`--only N`).
- 정의: `anims/dance2_loop.json` (frames 16개)
- WebM(12FPS, 16프레임=1.33초): `ffmpeg -y -framerate 12 -i sprites/dance2_loop/dance2_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_dance2_loop.webm`
- 위젯 등록: `rate: 0.7, minCycles: 2, maxCycles: 4` (사이클 약 1.9초)

### dance3 (검지 포인팅 부기, 'Hey! Boogie woogie bang bang' 모티브)
포켓몬 데이 팬 애니메이션 GIF(63프레임 @70ms)를 프레임 해체해 인간 여성
캐릭터의 안무를 추출한 모션. 양손을 항상 **검지 포인팅**(핑거건) 모양으로
유지하고, 어깨보다 **넓은 스탠스**로 발 고정. 상체가 한쪽으로 기울며 양손
검지가 같은 쪽(가까운 팔은 어깨 높이로 뻗고, 반대 손은 가슴 앞)을 가리키고
힙은 반대쪽 — 좌우 2바운스씩. 마지막에 정면에서 **양손 검지를 귀 높이로 들어
위-바깥을 두 번 포인트**(hey! hey!). 16프레임 seamless 루프 @12FPS
(0 센터 딥 → 1-4 왼쪽 스웨이 2바운스 → 5-6 센터 → 7-10 오른쪽 미러 →
11 센터 → 12-15 업 포인트 x2).
- 모델: `gemini-3.1-flash-lite-image` (기본). 16프레임 중 2프레임만 재생성
  (`--only 1`: 스윕 방향 반대로 나옴, `--only 14`: 회색 헤일로) — lite 검증 2호.
- 정의: `anims/dance3_loop.json` (frames 16개)
- WebM(12FPS, 16프레임=1.33초): `ffmpeg -y -framerate 12 -i sprites/dance3_loop/dance3_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_dance3_loop.webm`
- 위젯 등록: `rate: 0.5, minCycles: 2, maxCycles: 4` (사이클 약 2.7초)

## 4-g) 특수: 파티시엘 변신 (pastry) — 1종, 10종 멀티 엔딩 + 공용 outro ⭐신규 구조

### pastry1 (회전 변신 → 셰프복 → 휘핑볼 반죽 → 반짝! 10가지 결과)
꿈빛 파티시엘의 딸기처럼 **휘리릭 돌아 셰프복(흰 더블 재킷 + 핑크 프릴 앞치마 +
낮은 토크 모자)으로 변신**, 등 뒤에서 노란 믹싱볼과 휘핑기를 꺼내 휘적휘적 반죽(loop)
→ loop 2~4회 뒤 볼이 반짝! 하며 **10가지 결과 중 하나가 랜덤 재생** → 공용 outro에서
역변신하여 idle 복귀. 가장 긴 모션 (총 약 9~13초).
- **클립 구성 (모두 @10FPS, chain 모드, 위젯 `rate: 0.7`)**:
  - `pastry1_start` 14프레임: idle(가운) → 아이디어! → 회전 + 스파클 리본 → 플래시 →
    셰프복으로 등장 → 짜잔 → 등 뒤에서 볼·휘핑기 꺼내기 → 믹싱 자세
  - `pastry1_loop` 14프레임 (seamless): 느린 한 바퀴 → 빠른 한 바퀴 → 격렬 휘핑 →
    휘핑기 들어 반죽 확인 → 끄덕 → 복귀
  - `pastry1_end1~10` 각 12프레임(홀드 인코딩으로 23틱): 볼 발광 → 플래시(볼·휘핑기 소멸) →
    접시 위 결과 등장 → 반응 → 마무리 (마지막 프레임 = 양손 등 뒤, 셰프복, 만족 미소)
    1 딸기 쇼트케이크 · 2 레몬 타르트 · 3 마카롱 타워 · 4 컵케이크 · 5 도넛 · 6 푸딩 ·
    7 크루아상 · 8 소프트아이스크림 (1~8: 별눈 → 짜잔 → 통째로 냠 → 다람쥐 볼 → 행복)
    · 9 실패: 새까맣게 탄 덩어리 (찔러보기 → 용기내 한 입 → 블렉 → 숨기기)
    · 10 뜬금: 얼굴 그려진 통레몬 (멍 → ? → 눈싸움 → 어깨 으쓱 → 안고 웃음 → 숨기기)
  - `pastry1_outro` 10프레임 (공용): 등 뒤 손 → 바운스 → 회전 + 플래시 → 가운으로 역변신
    → idle 자세
- 정의: `anims/pastry1_start.json`, `pastry1_loop.json`, `pastry1_end1.json`~`end10.json`,
  `pastry1_outro.json`
- **위젯 신규 필드 `outro`**: `end`(랜덤 1개) 뒤에 항상 이어 재생되는 공용 마무리 클립.
  엔딩이 10개라 "정리 → 역변신 → idle 복귀" 구간을 매 엔딩마다 그리지 않고 한 클립으로 공유.
  등록: `end: [...10개], outro: "anim_pastry1_outro.webm", minCycles: 2, maxCycles: 4, rate: 0.7`
- **`gen_frames.py` 신규 옵션 (JSON 키)**:
  - `"chain_from": "<이미지 경로>"` — 프레임 0도 chain 모드로 생성하되 IMAGE 2로 이 이미지를
    사용. 텍스트로만 정의된 디테일(셰프복, 볼 색·형태)이 클립마다 다르게 재해석되는 것을
    막기 위해 **loop는 start_13, end 10종은 loop_00, outro는 end1_11**에 체인시킴.
    → 생성 순서 의존성: start → loop → (end1~10 병렬) → outro
  - `"character": "..."` — 기본 CHARACTER 블록(가운 복장 서술)을 클립별로 교체.
    셰프 클립은 셰프복 서술로, 복장이 바뀌는 start/outro는 "outfit as described in the
    pose text"로 두고 프레임마다 복장을 명시.
  - 429/5xx 응답 시 8·16·24초 백오프 재시도 추가 (엔딩 병렬 생성용).
- **변신 연출 팁**: 회전의 뒷모습/측면 프레임은 모델이 약하므로 실제 회전은 1프레임(쿼터 턴 +
  모션 라인)만 두고, 그 다음 2프레임은 "스파클 리본에 감싸인 실루엣 → 풀 플래시"로 복장을
  완전히 가린 뒤 다음 프레임에서 새 복장으로 등장시킴. 복장 교체 프레임은 텍스트로만 정의됨.
- **엔딩 타이밍 — 홀드 인코딩 (`tools/encode_holds.py`)**: 12프레임 엔딩을 그대로 재생하면
  (rate 0.7 기준 1.7초) 결과가 너무 빨리 지나감. 프레임을 새로 생성하거나 rate를 더 낮추는 대신
  JSON의 `"holds": {"3": 3, "4": 3, ...}`로 **핵심 비트 프레임을 2~3틱 홀드**해 인코딩한다
  (발광·플래시는 1틱으로 빠르게, 결과 등장·별눈·짜잔·냠·블렉은 2~3틱). 12프레임 → 23틱
  (2.3초, 위젯 rate 0.7로 약 3.3초). rate를 낮추면 loop 휘핑과 플래시까지 늘어지므로 홀드 방식이 적합.
  ```bash
  python tools/encode_holds.py anims/pastry1_end1.json   # sprites/pastry1_end1/*.png → anim_pastry1_end1.webm
  ```
  같은 도구의 `"repeats": [{"frames": [a, b], "times": n}]`는 프레임 구간 a~b를 n회 연속 재생
  (연타·떨림·더블테이크용, boxing1 참고). holds는 반복된 각 프레임에도 적용됨.
- **클립 간 스케일 보정**: `slice_and_key.py`는 클립 내부 중앙값으로만 정규화하므로 클립 간 크기는
  맞춰주지 않음. end10만 bbox 높이 461(loop 475)로 3% 작게 나와, 프레임을 1.03배 확대하고
  발끝 y=502·중심 x=254(loop 기준)에 맞춰 재배치함. 새 클립은 `_00` 프레임의 bbox 높이/발끝을
  loop와 비교해 볼 것.
- **후처리 주의**: 모자가 생기는 start와 사라지는 outro는 프레임 간 bbox 높이가 달라지므로
  `slice_and_key.py --no-scale-norm`으로 처리 (정규화하면 모자 프레임의 몸이 작아짐).
  loop/end는 전 프레임 모자 착용이라 기본 정규화 그대로.
- **생성 결과 (lite 모델, 총 158프레임 중 재생성 12프레임)**:
  - 변신 연출(회전 → 리본 → 플래시 → 새 복장)은 1발에 성공. 셰프복도 chain_from 덕에
    12개 클립 전체에서 동일하게 유지됨.
  - **가장 흔한 오생성 = 모자 누락**: 클립 후반 "하품/등 뒤 손/만족 미소"류 정적 프레임에서
    토크 모자가 사라지는 경우가 8회 (loop 13, end3 8, end5 9, end6 10, end7 9, end8 11 등).
    `--only N` 재생성 1회로 대부분 해결. 새 복장에 모자·장식이 있으면 후반 프레임 검수 필수.
  - 그 외: 흰 스티커 테두리(loop 2), 앞치마 누락(loop 2 재생성분) — 각 1회 재생성.
- **레이트 리밋**: 엔딩 10종을 9개 프로세스로 병렬 생성하자 Gemini 유료 티어의
  분당 입력 토큰 쿼터(`generate_content_paid_tier_input_token_count`)에 걸려 4프레임 실패
  (백오프 3회로도 부족). **동시 5개 이하** 권장. 실패 프레임은 `--only`로 순차 재시도.
- **`slice_and_key.py` 버그 수정**: 매트 정리에서 "본체" 시드를 `argmax(alpha)`로 잡던 것을
  **가장 큰 연결 성분**으로 변경. argmax는 행 우선이라 가장 위쪽의 불투명 픽셀 = 머리 위
  전구·스파클·'?'·하트가 시드가 되어 **본체가 통째로 지워지는** 문제가 있었음
  (start 1·4번 프레임이 빈 이미지로 나와 발견). 머리 위 이펙트가 있는 모든 모션에 해당.
- 생성/후처리:
  ```bash
  PYTHONIOENCODING=utf-8 python tools/gen_frames.py anims/pastry1_start.json --outdir sprites/raw
  python tools/slice_and_key.py --frames "sprites/raw/pastry1_start_*.png" --outdir sprites/pastry1_start --prefix pastry1_start --no-scale-norm
  ffmpeg -y -framerate 10 -i sprites/pastry1_start/pastry1_start_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_pastry1_start.webm
  ```

## 4-h) 특수: 레몬 한 입 (lemon) — 1종

### lemon1 (레몬 한 입 — 시큼!)
idle → 등 뒤에서 통레몬 꺼내 자랑 → 크게 베어물기 → 얼굴 쪼그라드는 시큼 표정 + 부르르 →
고개 흔들어 털어내고 큰 한숨 → 엄지척 만족 → 레몬 등 뒤로 숨기고 idle 복귀.
완결형 16프레임 @10FPS, 위젯 `rate 0.7`, `minCycles 1 / maxCycles 1` (1회만 재생).
- 정의: `anims/lemon1_loop.json`
- 레몬은 항상 화면 **오른쪽** 손, 불투명 노란색(크로마키 안전). 베어문 뒤엔 매 프레임
  "big bite taken out of it"으로 상태를 고정.
- WebM: `ffmpeg -y -framerate 10 -i sprites/lemon1_loop/lemon1_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_lemon1_loop.webm`

## 5) 우울 상태 (sad) — 2종

### sad1 (풀 죽음)
- **start (3)**: `3 animation frames of deflating: shoulders dropping, head tilting down, smile fading to a small pout.`
- **loop (9)**: `9 animation frames of gloomy idle: head hung low, shoulders slumped, occasional heavy sigh with a small drooping motion, dark cloud doodle above head, teary downcast eyes. Seamless loop.`
- **end (3)**: `3 animation frames of lifting the head and straightening up back to neutral standing pose.`

### sad2 (쪼그려 앉아 시무룩)
- **start (3)**: `3 animation frames of slowly crouching down into a squat, hugging knees, face turning sad.`
- **loop (9)**: `9 animation frames of sulking in a crouch: hugging knees, chin resting on knees, idly poking the ground with one finger, teary puppy eyes, tiny rain-cloud above. Seamless loop.`
- **end (3)**: `3 animation frames of standing back up from the crouch to neutral standing pose.`

---

## 생성 커맨드 예시
```bash
# loop 시트 (3×3 그리드, 1:1)
PYTHONIOENCODING=utf-8 python ~/.claude/skills/lite-image/scripts/generate_image_v2.py \
  --prompt "<공통 프리앰블(3x3)> <loop 동작 프롬프트> <캐릭터 블록>. <공통 스타일 접미사>" \
  --ref "refs/chibi_lemon_turnaround.jpg" \
  --output "sprites/anim_idle1_loop_sheet.png" \
  --aspect 1:1 --size 2K

# start+end 시트 (3×2 그리드, 3:2)
PYTHONIOENCODING=utf-8 python ~/.claude/skills/lite-image/scripts/generate_image_v2.py \
  --prompt "<공통 프리앰블(3x2)> Top row: <start 동작 프롬프트> Bottom row: <end 동작 프롬프트> <캐릭터 블록>. <공통 스타일 접미사>" \
  --ref "refs/chibi_lemon_turnaround.jpg" \
  --output "sprites/anim_idle1_startend_sheet.png" \
  --aspect 3:2 --size 2K
```

## 후처리 (시트 → 512px 투명 PNG 프레임 → WebM) — 검증된 파이프라인
투명 배경이 최종 산출물이므로 **생성 시 프리앰블의 배경 구문을 `solid pure green chroma-key background (#00FF00)`로 교체**해서 생성한다.

```bash
# 1. 슬라이스 + 그린 키잉 + despill (loop: 3x3 / start+end: --rows 2)
python tools/slice_and_key.py --sheet sprites/anim_idle1_loop_sheet.jpg \
  --cols 3 --rows 3 --outdir sprites/idle1_loop --prefix idle1_loop

# 2. WebM (VP9 + 알파) 조립, 5FPS — loop 9프레임 = 1.8초
ffmpeg -y -framerate 5 -i sprites/idle1_loop/idle1_loop_%02d.png \
  -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_idle1_loop.webm
```
- PNG 시퀀스가 최종 산출물이면 1번까지만 수행
- 생성 모델이 1:1은 1024×1024로 출력하므로 슬라이스 시 1536으로 업스케일됨 (스크립트가 자동 처리, 512px 타일 품질 양호)
