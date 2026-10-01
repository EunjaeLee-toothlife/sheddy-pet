# 주먹 응원 모션

Codex 내장 ImageGen으로 생성. `refs/chibi_base.png`는 캐릭터 정체성과 화풍 참조다.
원본: `sprites/raw/cheer1_imagegen_sheet.png`. 4열 × 2행 8포즈, 512px 투명 PNG/VP9, 2.4초 단발 모션.
발 위치를 맞추고 마지막 프레임을 첫 프레임과 동일하게 만들어 반복 경계를 고정한다.

재현: `python3 tools/build_reactions.py cheer1` (Pillow·NumPy·libvpx-vp9 ffmpeg 필요).

## 생성 프롬프트

Use case: stylized-concept. Production OBS character animation sprite sheet. Reference is IDENTITY AND STYLE ONLY. Match precisely the reference girl: long pale blonde hair, lemon wedge hair clip, golden eyes, white laboratory coat over white shirt, yellow lemon-pattern skirt, white knee socks, brown shoes; muted pastel anime line art and same full-body proportions. Exactly FOUR columns by TWO rows, eight evenly spaced full-body poses, reading order left to right top to bottom. Uniform solid pure green #00ff00 background for existing chroma-key pipeline. No transparency, no gradients, shadows, speckles, text, grid lines or gutters. One girl per cell. Keep SAME SCALE, SAME feet baseline and centered root position throughout. Generous empty margins all around each figure. No cropped fingers or shoes. Legs planted and unchanged, only specified upper-body motion. Keep outfit, hair volume, head size, drawing style consistent between frames. Each pose must visibly differ in the specified hand/arm placement; no identical copies except neutral first/last. FIST-PUMP CHEER: 1 neutral; 2 both hands curl into fists at waist; 3 raise both fists to shoulder level with elbows bent; 4 pump both fists upward beside head, delighted open smile; 5 fists dip to shoulders; 6 pump fists up beside head again cheerful eyes closed; 7 fists lower; 8 identical neutral first. Keep BOTH FEET ON GROUND, no jumping. Hands always below highest point of head and entirely inside cell.
