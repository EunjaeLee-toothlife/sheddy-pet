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

## 4) 신남 상태 (excited) — 1종

### excited1 (점프 환호)
- **start (3)**: `3 animation frames of anticipation crouch: knees bending, fists clenched at sides, sparkling excited eyes, big grin.`
- **loop (9)**: `9 animation frames of an excited jump cycle: leaping into the air with both arms thrown up, hair and lab coat flying, star-sparkle effects, landing softly and bouncing again. Seamless loop.`
- **end (3)**: `3 animation frames landing and catching breath, settling back to neutral standing pose with a leftover grin.`

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
