# 셔플 스텝

Codex 내장 ImageGen으로 생성. `refs/chibi_base.png`는 정체성·화풍 참조다.
원본: `sprites/raw/shuffle1_imagegen_sheet.png`. 4×4 투명 시트, 16프레임, 15fps·60틱·4초. 중간 14포즈를 두 번 재생한다.

러닝맨·셔플 챌린지풍에서 착안한 캐릭터용 재구성 동작이며 원곡 안무의 정확한 복제나 음악 동기화가 아니다.
참고: https://www.snapchat.com/%40kyleexum/spotlight/W7_EDlXWTBiXAEEniNoMPwAAYaXhkbHZhaWp6AZQ7eB3VAZQ7eBGkAAAAAQ

생성 알파를 사용하며 극저알파 배경 잡점만 제거한다. 발 정렬은 생략하고 전체 포즈에 동일한 배율·이동을 적용해 좌우 이동과 점프를 보존한다.
첫/마지막 프레임은 동일하다.

재현: `python3 tools/build_reactions.py shuffle1` (Pillow·NumPy·libvpx-vp9 ffmpeg).

## 생성 프롬프트

Use case: stylized-concept. Asset: production 2D OBS character dance sprite sheet. Reference image is character identity/style only; ignore its green background. Match this same pale blonde long-haired golden-eyed girl, lemon wedge hairclip, white lab coat, white shirt, yellow lemon-print skirt, white knee socks, brown shoes. Pastel anime line art. EXACTLY 4 columns x 4 rows = 16 equal square cells, chronological reading order. Genuine transparent background. No text, cell borders, shadows, props, symbols or effects. Fixed camera, identical scale and head size throughout. Each complete figure must fit within its own cell with generous margins. Hair and coat follow motion, face remains recognizable. This must be a lively FULL BODY dance animation, with visibly different leg positions, knee bends, shoulder angles and rhythmic weight shifts, not a series of hand gestures. Ground line remains at 86% of each cell, neutral head at 20%, neutral body centered; keep all motion inside central 80% cell. Intentional horizontal travel and jump heights must remain visible relative to this fixed imaginary floor. DO NOT align every pose by feet or recenter independently. Arms not above head, to leave jump clearance. First and last frames show the same relaxed neutral pose. The 14 middle poses form one smooth repeating dance phrase. Handcrafted original adaptation inspired by viral challenge movement vocabulary, not an exact choreography copy. Bouncy RUNNING MAN and T-STEP shuffle, strong footwork in place, opposite arms pumping. 1 neutral. 2 lift LEFT knee sharply to waist, right leg supports, right forearm forward. 3 extend left foot forward heel, right foot slides back. 4 land staggered, both knees compress. 5 lift RIGHT knee to waist, left foot slides back, left forearm forward. 6 extend right heel forward. 7 compress springy staggered stance. 8 swivel both toes toward LEFT, left heel out, arms counterbalance. 9 close feet briefly on toes, knees bent. 10 swivel toes toward RIGHT, right heel out, arms counterbalance. 11 scissor-hop with left foot forward and right back, visibly airborne a little. 12 land, compress, arms pump. 13 scissor-hop switching feet, right forward left back. 14 land with knees bent. 15 gather feet near neutral with weight on right foot, ready to raise left knee again. 16 neutral identical1. Shoes and bent legs must be clearly readable in every cell, hair and skirt bounce subtly. NO leg duplicates or frozen lower body. No spin or camera rotation.
