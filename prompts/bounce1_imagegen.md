# 챌린지 바운스

Codex 내장 ImageGen으로 생성. `refs/chibi_base.png`는 정체성·화풍 참조다.
원본: `sprites/raw/bounce1_imagegen_sheet.png`. 4×4 투명 시트, 16프레임, 15fps·60틱·4초. 중간 14포즈를 두 번 재생한다.

삐끼삐끼풍에서 착안한 캐릭터용 재구성 동작이며 원곡 안무의 정확한 복제나 음악 동기화가 아니다.
참고: https://www.yna.co.kr/view/AKR20240915020200007

생성 알파를 사용하며 극저알파 배경 잡점만 제거한다. 발 정렬은 생략하고 전체 포즈에 동일한 배율·이동을 적용해 좌우 이동과 점프를 보존한다.
첫/마지막 프레임은 동일하다.

재현: `python3 tools/build_reactions.py bounce1` (Pillow·NumPy·libvpx-vp9 ffmpeg).

## 생성 프롬프트

Use case: stylized-concept. Asset: production 2D OBS character dance sprite sheet. Reference image is character identity/style only; ignore its green background. Match this same pale blonde long-haired golden-eyed girl, lemon wedge hairclip, white lab coat, white shirt, yellow lemon-print skirt, white knee socks, brown shoes. Pastel anime line art. EXACTLY 4 columns x 4 rows = 16 equal square cells, chronological reading order. Genuine transparent background. No text, cell borders, shadows, props, symbols or effects. Fixed camera, identical scale and head size throughout. Each complete figure must fit within its own cell with generous margins. Hair and coat follow motion, face remains recognizable. This must be a lively FULL BODY dance animation, with visibly different leg positions, knee bends, shoulder angles and rhythmic weight shifts, not a series of hand gestures. Ground line remains at 86% of each cell, neutral head at 20%, neutral body centered; keep all motion inside central 80% cell. Intentional horizontal travel and jump heights must remain visible relative to this fixed imaginary floor. DO NOT align every pose by feet or recenter independently. Arms not above head, to leave jump clearance. First and last frames show the same relaxed neutral pose. The 14 middle poses form one smooth repeating dance phrase. Handcrafted original adaptation inspired by viral challenge movement vocabulary, not an exact choreography copy. Cute upbeat cheer bounce, double thumbs-up accents but the legs and torso do most of the animation. 1 neutral. 2 sink knees, elbows flex. 3 step LEFT, torso leans left, thumbs beside shoulders. 4 left weight, right heel lifts, right shoulder pops high. 5 rebound upright, both knees spring. 6 tap RIGHT foot outward, arms sweep low across front. 7 step RIGHT, left knee flexes, thumbs up beside shoulders. 8 right weight, left heel lifts, left shoulder pops. 9 bounce through center with deep knees and both elbows out. 10 lift LEFT knee, opposite shoulder forward. 11 plant left, rotate torso a little left. 12 lift RIGHT knee, opposite shoulder forward. 13 plant right, torso rotates right. 14 rebound to center, heels raised with a small airborne hop and elbows close. 15 land with flexed knees and arms lowering, ready to repeat pose2. 16 neutral identical pose1. Make left-right whole-body travel and springing knees obvious, cheerful deadpan face then small smile.
