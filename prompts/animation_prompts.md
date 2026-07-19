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

## 2) 기본 상태 (basic) — 3종

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

## 4) 신남 상태 (excited) — 1종

### excited1 (점프 환호)
- **start (3)**: `3 animation frames of anticipation crouch: knees bending, fists clenched at sides, sparkling excited eyes, big grin.`
- **loop (9)**: `9 animation frames of an excited jump cycle: leaping into the air with both arms thrown up, hair and lab coat flying, star-sparkle effects, landing softly and bouncing again. Seamless loop.`
- **end (3)**: `3 animation frames landing and catching breath, settling back to neutral standing pose with a leftover grin.`

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

## 4-e) 특수: 포케댄스 (pokedance) — 1종

### pokedance1 (포케댄스 '부기부기 뱀뱀') — Lite 모델 검증용
포켓몬 데이 2024 바이럴 댄스(POKÉDANCE)의 시그니처 동작. 양손을 **강아지 앞발
모양 주먹**(손목 툭 떨군 느슨한 주먹, 손등이 화면 쪽)으로 어깨 앞에 들고,
상체+양 앞발이 한쪽으로 스웨이할 때 **힙은 반대쪽으로** 빠지는 바나나 커브
(부기부기), 마지막에 정면 보며 **양 앞발을 화면 쪽으로 두 번 내밀기**(뱀뱀).
16프레임 seamless 루프 @12FPS (0-5 왼쪽 스웨이 2바운스 → 6-11 오른쪽 미러 →
12-15 앞발 푸시 x2).
- **모델: `gemini-3.1-flash-lite-image`** — config에 `"model"` 키로 지정
  (`gen_frames.py`가 `--model`/config `"model"` 오버라이드 지원). Lite 모델도
  베이스 ref 1장 기준 캐릭터/의상/화풍 일관성 양호. 단 **몸통 기울기 지시가
  잘 안 먹는 편** — "clearly LEANING like a banana curve", "NOT standing
  straight"처럼 과장해서 써야 하고, 팔이 가슴을 가로지르는 오생성이 나오면
  "her arms NEVER cross in front of her chest / BOTH paws SIDE BY SIDE as a
  pair on the RIGHT side"로 재생성(`--only N`).
- 정의: `anims/pokedance1_loop.json` (frames 16개, model 키 포함)
- WebM(12FPS, 16프레임=1.33초): `ffmpeg -y -framerate 12 -i sprites/pokedance1_loop/pokedance1_loop_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_pokedance1_loop.webm`
- 위젯 등록: `rate: 0.7, minCycles: 2, maxCycles: 4` (사이클 약 1.9초)

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
