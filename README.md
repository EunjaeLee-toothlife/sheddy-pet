# Sheddy Pet

레몬 치비 캐릭터 위젯. 투명 배경 위에서 혼자 숨 쉬고, 두리번거리고, 가끔 춤추고, 마이크에 말하면 입을 움직인다.
OBS 브라우저 소스나 웹페이지에 그대로 올려 쓴다.

- 위젯: <https://eunjaelee-toothlife.github.io/sheddy-pet/>
- 본체는 [`widget.html`](widget.html) 파일 하나 + [`sprites/anim_*.webm`](sprites/) (VP9 + 알파) 클립들

## OBS에서 쓰기

1. 소스 추가 → **브라우저** → URL에 위 주소 입력. 크기는 정사각형 권장(예: 512×512). 배경은 투명.
2. 설정을 바꾸려면 소스 우클릭 → **상호작용**. 마우스를 움직이면 버튼 두 개가 나타난다.
   - ⚙️ (F2) 마이크 설정 — 입력 장치와 감도 임계값. 임계값을 넘는 동안 `talk` 모션이 재생된다.
   - 🎭 (F3) 모션 선택 — 원하는 모션을 바로 재생. "계속 유지"를 켜면 주사위를 멈추고 그 모션만 반복.

### URL 옵션

| 옵션 | 뜻 |
| --- | --- |
| `?state=happy1` | 시작 상태 |
| `?hold=8` | 외부 명령으로 바꾼 상태를 주사위로부터 보호할 시간(초) |
| `?dice=0` | 주사위 끄기 (외부 제어 전용) |
| `?flip=1` | 좌우 반전 |

### 외부에서 상태 바꾸기

```js
window.setPetState("happy1");                                        // 콘솔 / OBS 커스텀 스크립트
window.postMessage({ type: "pet-state", state: "happy1" }, "*");     // iframe 부모
new BroadcastChannel("sheddy-pet").postMessage("happy1");            // 같은 출처의 컨트롤 페이지
```

## 동작 방식

- **상태 머신 + 2중 가중치 주사위.** loop 한 사이클이 끝날 때마다 주사위를 굴린다. 먼저 분류(`CATEGORY_WEIGHTS`:
  idle / basic / happy / excited / special / sad)를 뽑고, 그 안에서 `weight`로 모션을 뽑는다. 감정 → 감정 직행은 없고
  항상 idle을 거친다.
- **전환 순서.** 현재 상태의 `end`(→ `outro`) → 다음 상태의 `start` → `loop`. `end`가 배열이면 그중 하나를 랜덤 재생(멀티 엔딩).
- **렌더링.** `<video>` 두 개를 더블 버퍼로 쓰고, 화면에는 캔버스 하나만 보인다. 전환은 70ms 크로스 디졸브라 깜박임이 없다.
- **견고성.** 시작 직후 전 클립(약 6MB)을 받아 blob URL로 보관하고, 로드 실패·타임아웃은 건너뛰며, 1초 주기 워치독이
  멈춘 전환을 idle로 되돌린다.

모션 등록 항목(`widget.html`의 `ANIMS`):

| 필드 | 뜻 |
| --- | --- |
| `loop` | 필수. 반복 클립 |
| `start` / `end` / `outro` | 진입 / 이탈(단일 또는 배열) / 모든 `end` 뒤에 이어지는 공용 마무리 |
| `category`, `weight` | 주사위 분류와 분류 내 비율 (`weight: 0`이면 주사위 제외) |
| `minCycles` / `maxCycles` | 최소 유지 사이클 / 이만큼 돌면 idle로 강제 복귀 |
| `rate` | 재생 배속 (start·loop·end 공통) |

## 개발

```bash
python -m http.server 8474
```

- <http://localhost:8474/widget.html> — 위젯
- <http://localhost:8474/preview.html> — PNG 시퀀스와 WebM을 나란히 놓고 보는 검수 페이지

위젯 로직을 고쳤으면 회귀 검사를 돌린다. 헤드리스 Chrome을 직접 구동하며 의존성은 없다(Node 22+, 약 1분).

```bash
node tools/widget_check.js
```

`widget.html`이나 `sprites/anim_*.webm`을 바꿨으면 Pages 배포본을 다시 만든다. `docs/`는 생성물이므로 직접 고치지 않는다.
`master`에 들어가면 GitHub Pages(`master` / `docs`)에 반영된다.

```bash
python tools/deploy_pages.py
```

## 모션 추가하기

필요한 것: Python 3(`numpy`, `Pillow`, 선택 `scipy`), `ffmpeg`(libvpx-vp9), 환경변수 `GEMINI_API_KEY`.

1. **프레임 정의** — `anims/<name>.json`에 프레임별 포즈 설명을 적는다.

   | 키 | 뜻 |
   | --- | --- |
   | `name`, `ref`, `frames[]` | 클립 이름, 베이스 레퍼런스(`refs/chibi_base.png`), 프레임별 포즈 |
   | `chain` | 직전 프레임을 두 번째 레퍼런스로 붙여 소품·손 모양을 프레임 간에 고정 |
   | `chain_from` | 0번 프레임도 다른 클립의 이미지에 이어 붙임 (start → loop → end 복장 유지) |
   | `character` | 기본 복장(가운) 대신 쓸 캐릭터 설명 |
   | `holds`, `repeats` | 인코딩 시 특정 프레임을 오래 보여주거나 구간을 반복 (`encode_holds.py`) |

2. **생성** — 프레임을 한 장씩 1:1로 만든다. 마음에 안 드는 프레임만 `--only N`으로 다시 뽑는다.

   ```bash
   python tools/gen_frames.py anims/<name>.json --outdir sprites/raw
   ```

3. **키잉·정합** — 크로마키 제거, 크기 정규화, 서브픽셀 위치 정합. 결과는 512px PNG 시퀀스.
   (원본 확장자는 응답에 따라 `.jpg`일 수 있다.)

   ```bash
   python tools/slice_and_key.py --frames "sprites/raw/<name>_*.png" --outdir sprites/<name> --prefix <name>
   ```

4. **인코딩**

   ```bash
   ffmpeg -y -framerate 10 -i sprites/<name>/<name>_%02d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 24 -an sprites/anim_<name>.webm
   ```

   `holds` / `repeats`를 썼다면 대신 `python tools/encode_holds.py anims/<name>.json --fps 10`.

5. **등록** — `widget.html`의 `ANIMS`에 추가(새 분류면 `CATEGORY_WEIGHTS`에도), `preview.html`의 `ANIMATIONS`에 한 줄 추가.
6. **배포본 갱신** — `python tools/deploy_pages.py`

모션별 프롬프트와 시행착오 기록은 [`prompts/animation_prompts.md`](prompts/animation_prompts.md)에 있다.

## 디렉터리

| 경로 | 내용 |
| --- | --- |
| `widget.html` | 위젯 본체 |
| `preview.html` | 프레임 검수 페이지 |
| `sprites/anim_*.webm` | 위젯이 재생하는 클립 |
| `sprites/raw/`, `sprites/<name>/` | 생성 원본과 키잉된 PNG 시퀀스 (재인코딩용으로 함께 보관) |
| `anims/` | 프레임 정의(JSON) |
| `refs/` | 캐릭터 레퍼런스 이미지 |
| `tools/` | 생성 · 키잉 · 인코딩 · 배포 · 검사 스크립트 |
| `docs/` | GitHub Pages 배포본 (`deploy_pages.py`가 생성) |

`main.js`, `preload.js`, `package.json`, `dialogues/`, `.github/workflows/release.yml`은 같은 위젯을 감싼
Electron 데스크톱 앱(Desk Toy)용이며, 현재는 유지보수하지 않는다.
