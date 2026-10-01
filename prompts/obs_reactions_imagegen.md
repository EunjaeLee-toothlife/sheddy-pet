# OBS 방송 반응 모션

Codex 내장 ImageGen으로 생성했다. `refs/chibi_base.png`는 캐릭터 정체성과 화풍 참조다.
박수의 첫 RGBA 결과에 배경 잡티가 있어 ImageGen으로 크로마키 배경을 다시 만들었다.
채택한 원본은 `sprites/raw/{clap1,heart1,surprise1}_imagegen_sheet.png`에 보관한다.
4열 × 2행의 시트를 기존 키잉 함수로 분리하고 원본 비율을 유지해 512px로 조립한다.
재생 타이밍·반복·원본 해시는 `anims/obs_reactions.json`, 재현 명령은 `python3 tools/build_reactions.py`다.

## clap1

Create a production animation sprite sheet for Sheddy, the EXACT girl character in the reference: long pale blonde hair, lemon wedge hair clip, golden eyes, white laboratory coat, white button shirt, yellow lemon-pattern skirt, white knee socks, brown shoes. Match reference muted pastel anime line art, facial proportions and full-body proportions. Reference is identity/style only; remove the green background. Output genuinely transparent RGBA. Layout exactly 4 columns x 2 rows of EIGHT equally sized square cells, no gutters, no text or grid lines. Each cell contains one centered full-body girl at identical scale and ground baseline, comfortably inside its cell. Action: happy APPLAUSE. Read left to right top to bottom: 1 neutral arms relaxed; 2 both forearms lift in front of chest; 3 palms separated 15cm ready to clap cheerful smile; 4 palms contacting at chest closed eyes smiling; 5 hands separate slightly; 6 palms contacting again delighted closed eyes; 7 hands lower smiling; 8 return to neutral like frame 1. Hands must visibly move, not just expressions. Feet planted, preserve hair, clothing and head size between frames. No extra fingers, props, particles, backgrounds, cast shadows or duplicate people in any cell. High-quality crisp consistent animation keyframes, not a collage.

### 배경 정리

Edit this applause animation sheet. Keep all eight character poses and details unchanged. Replace ONLY the transparent background and all detached colored speckles with a perfectly uniform solid chroma-key green #00ff00 background. No transparency in this intermediate production sheet. Remove every detached speck, glow and shadow around the characters. Keep white coat and skin completely opaque and clean, dark clean outlines. Exactly same 4 columns x 2 rows grid, full bodies, no cropping, no text.

## heart1

Production animation sprite sheet, exactly FOUR columns by TWO rows, 8 full body keyframes of the same girl in reference. Identity/style reference: long pale blonde hair, lemon wedge hair clip, golden eyes, white laboratory coat and shirt, yellow lemon-pattern skirt, knee socks and brown shoes. Keep muted pastel anime line art and same full-body proportions. SOLID UNIFORM pure green #00ff00 chroma-key background throughout, no transparency, no shadows, particles, speckles, text, lines or gutters. One girl per cell, fixed scale and ground line, centered with generous clearance. Animation: TWO-HAND HEART thank-you gesture. Reading order: 1 arms relaxed neutral; 2 both hands rise near chest; 3 hands approach chest fingers curved; 4 BOTH HANDS form one clearly readable heart shape at upper chest, fingers on top thumbs below, happy smile; 5 hold heart with eyes closed and gentle head tilt; 6 hold heart eyes open; 7 hands separate and lower; 8 neutral identical to first. Show genuinely different arm poses. No floating heart symbols. Hands anatomically clear. White coat fully opaque. Preserve consistent outfit and character across all eight frames.

## surprise1

Production animation sprite sheet, exactly FOUR columns by TWO rows, 8 full-body keyframes of the same girl in reference. Identity and style: pale blonde long hair, lemon wedge hair clip, golden eyes, white lab coat over white shirt, yellow lemon skirt, knee socks, brown shoes. Match reference muted pastel anime line art and full-body proportions. Uniform solid chroma key green #00ff00 background, no transparency, shadows, particles, speckles, text, punctuation, grid lines or gutters. One full body girl per cell with generous margin. All cells fixed character scale and baseline. Action: startled DOUBLE TAKE then relieved smile. Left to right top to bottom: 1 neutral relaxed; 2 eyes open wide small O mouth shoulders lift; 3 both hands raised with open palms beside cheeks leaning back slightly surprised; 4 peak startle hands beside cheeks eyes wide; 5 hands pull inward to upper chest, eyebrows softening; 6 eyes close relieved smile one hand over chest; 7 hand lowering smiling; 8 same neutral as first. No symbols over head. No props. Feet stay on ground, body anatomy and proportions consistent. Clean readable hands. White coat fully opaque.
