# 파워 챌린지

Codex 내장 ImageGen으로 생성. `refs/chibi_base.png`는 정체성·화풍 참조다.
원본: `sprites/raw/power1_imagegen_sheet_v2.png`. 4×4 투명 시트, 16프레임, 15fps·60틱·4초. 중간 14포즈를 두 번 재생한다.

like JENNIE풍에서 착안한 캐릭터용 재구성 동작이며 원곡 안무의 정확한 복제나 음악 동기화가 아니다.
참고: https://ssl.sme.co.jp/artist/JENNIE/info/573668

생성 알파를 사용하며 극저알파 배경 잡점만 제거한다. 발 정렬은 생략하고 전체 포즈에 동일한 배율·이동을 적용해 좌우 이동과 점프를 보존한다.
첫/마지막 프레임은 동일하다.

재현: `python3 tools/build_reactions.py power1` (Pillow·NumPy·libvpx-vp9 ffmpeg).

## 생성 프롬프트

Use case: stylized-concept. Asset: production 2D OBS character dance sprite sheet. Reference image is character identity/style only; ignore its green background. Match this same pale blonde long-haired golden-eyed girl, lemon wedge hairclip, white lab coat, white shirt, yellow lemon-print skirt, white knee socks, brown shoes. Pastel anime line art. EXACTLY 4 columns x 4 rows = 16 equal square cells, chronological reading order. Genuine transparent background. No text, cell borders, shadows, props, symbols or effects. Fixed camera, identical scale and head size throughout. Each complete figure must fit within its own cell with generous margins. Hair and coat follow motion, face remains recognizable. This must be a lively FULL BODY dance animation, with visibly different leg positions, knee bends, shoulder angles and rhythmic weight shifts, not a series of hand gestures. Ground line remains at 86% of each cell, neutral head at 20%, neutral body centered; keep all motion inside central 80% cell. Intentional horizontal travel and jump heights must remain visible relative to this fixed imaginary floor. DO NOT align every pose by feet or recenter independently. Arms not above head, to leave jump clearance. First and last frames show the same relaxed neutral pose. The 14 middle poses form one smooth repeating dance phrase. Handcrafted original adaptation inspired by viral challenge movement vocabulary, not an exact choreography copy. Powerful K-pop challenge-inspired original dance phrase: wide grounded stance, sharp chest hits, diagonal arm punches, quarter-body turns, squat rebound and compact hop. 1 neutral. 2 step LEFT into wide stance, knees bent, forearms cross chest. 3 strong diagonal punch to LEFT at shoulder height, torso and hips twist left, right heel lifts. 4 retract arms sharply, chest pop front. 5 shift RIGHT, diagonal punch right, left heel lifts. 6 pull fists to waist and deep knee dip. 7 spring tall, elbows flare at shoulder height, head confident. 8 quarter-turn left torso only, left forearm blocks in front, right foot taps behind. 9 square front, low squat, arms crossed. 10 explode to wide stance, arms sweep wide at shoulder height. 11 compact airborne hop, knees bent beneath skirt, arms tuck to torso; head rises visibly above its neutral height but stays within cell. 12 land on wide bent knees, coat and hair settle. 13 chest hit and double forearm push forward. 14 pull elbows back, body lean right and left heel lifts. 15 bring feet toward center with knee dip, arms crossing ready to repeat pose2. 16 neutral identical1. Athletic and playful, with facial determination, expressive body mechanics, modest unchanged outfit. No sexy posing, no floorwork, no camera movement.

## 칸 경계 보정

ImageGen 편집으로 여백을 넓힌 v2를 사용한다. 시트의 발 기준선이 균등 행 경계보다 아래에 있어 `row_offset: 16`으로 각 행을 16px 내려 자른다. 윗행 신발 혼입과 현재 행 신발 잘림을 함께 막는다.

Edit this existing 4-by-4 transparent dance sprite sheet. Keep EXACTLY the same 16 poses, character identity, outfit, facial expressions and chronological order. Correct sprite-cell contamination only: every figure must be fully isolated inside its own equal square cell. REDUCE each figure uniformly to about 75% of its current size, keeping the original relative dance offsets; ensure at least 30 pixels completely transparent margin on ALL FOUR SIDES of EVERY cell. In particular no shoe or hair from the row above may intrude at the top of the next cell. Remove all isolated floating specks and stray detached marks from the transparent background. Do not redraw choreography or add symbols. Fixed clean alpha, truly transparent empty space. Four columns, four rows, 16 frames, same poses at consistent scale, no visible grid.

