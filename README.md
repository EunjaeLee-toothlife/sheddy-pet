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
| `?resolution=512` | 합성 캔버스의 긴 변 상한(px). 기본 512, 범위 128~2048. 큰 소스에서 더 높은 해상도가 필요하면 1024 사용 |

### 방송 반응 모션

F3 모션 선택기에서 **박수(`clap1`) · 손하트(`heart1`) · 깜짝 놀람(`surprise1`)**을 고를 수 있다.
각각 3.2초 / 2초 / 2초 재생 뒤 기본 자세로 돌아온다. `dice=0`이나 일반 `hold` 시간에도 단발 복귀하며,
**계속 유지**를 켜면 반복한다. 기존 `setPetState`, `postMessage`, BroadcastChannel로도 실행할 수 있다.
자동 주사위에서는 박수·손하트가 happy, 놀람이 excited 분류에 포함된다.

```js
window.setPetState("clap1");
window.postMessage({ type: "pet-state", state: "heart1" }, "*");
```

추가 모션도 F3 또는 `setPetState`로 실행한다. 모두 2.4초 단발 재생이며 계속 유지로 반복할 수 있다.

| 상태 | 동작 |
| --- | --- |
| `thumbsup1` | 엄지척 |
| `salute1` | 경례 |
| `shrug1` | 어깨 으쓱 |
| `think1` | 고민 |
| `listen1` | 귀 기울이기 |
| `facepalm1` | 이마 짚기 |
| `shush1` | 쉿 |
| `cheer1` | 주먹 응원 |
| `pout1` | 삐짐 |
| `kiss1` | 손키스 |
<!-- 추가 반응 모션 -->

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
- **렌더링.** `<video>` 두 개와 캔버스 하나를 사용한다. 실제 영상 프레임이 도착할 때만 합성하고,
  70ms 크로스 디졸브 중에만 화면 주사율로 그린다. 영상 프레임 콜백이 없는 구형 브라우저는 최대 30Hz로 동작한다.
  OBS 합성 캔버스의 긴 변은 기본 512px이며 CSS가 출력 크기를 맞춘다.
- **로딩.** 필요한 영상만 받아 최대 4MiB의 LRU blob 캐시에 보관한다. 중복 요청을 합치고 동시 fetch를 2개로 제한한다.
  다음 상태의 loop는 진입·이탈 영상 재생 중 미리 받는다. 캐시에서 빠진 클립은 다시 필요할 때 로드하므로
  모든 모션을 미리 받은 방식에 비해 첫 전환에서 네트워크 대기가 생길 수 있다.
- **숨김·복귀.** 탭 또는 OBS 소스가 숨겨지면 영상 디코딩과 캔버스 합성을 멈춘다. 마지막 그림은 보존하고,
  복귀하면 재생과 대기 명령을 이어 간다. 숨김 시간은 워치독 타임아웃에서 제외한다.
  OBS 연결은 공식 [소스 가시성 이벤트](https://github.com/obsproject/obs-browser/blob/master/README.md#register-for-event-callbacks)를 사용한다.
- **견고성.** 로드 실패·타임아웃은 건너뛰며, 1초 주기 워치독이 멈춘 전환을 idle로 되돌린다.

모션 등록 항목(`widget.html`의 `ANIMS`):

| 필드 | 뜻 |
| --- | --- |
| `loop` | 필수. 반복 클립 |
| `start` / `end` / `outro` | 진입 / 이탈(단일 또는 배열) / 모든 `end` 뒤에 이어지는 공용 마무리 |
| `category`, `weight` | 주사위 분류와 분류 내 비율 (`weight: 0`이면 주사위 제외) |
| `minCycles` / `maxCycles` | 최소 유지 사이클 / 이만큼 돌면 idle로 강제 복귀 |
| `rate` | 재생 배속 (start·loop·end 공통) |
| `once` / `label` | 한 사이클 뒤 기본 자세 복귀(무기한 유지 제외) / 모션 선택기에 표시할 이름 |

## 개발

```bash
python -m http.server 8474
```

- <http://localhost:8474/widget.html> — 위젯
- <http://localhost:8474/preview.html> — PNG 시퀀스와 WebM을 나란히 놓고 보는 검수 페이지

위젯 로직을 고쳤으면 회귀 검사를 돌린다. 헤드리스 Chrome을 직접 구동하며 의존성은 없다(Node 22+, 약 1분).

```bash
node tools/widget_check.js
node tools/widget_check.js --fallback       # 영상 프레임 콜백 없는 OBS/CEF 경로
node tools/widget_check.js --page docs/index.html
```

성능 지표와 반복 비교 보고서는 다음 명령으로 만든다. 기준 커밋을 명시하므로 커밋 이후에도 같은 버전과 비교할 수 있다.
각 해상도에서 기준/현재를 3회씩, 총 12번 측정한다. 새 Chrome 프로필을 사용하고 실행 순서는 AB/BA로 교대한다.

```bash
node tools/widget_metrics.js --baseline d909552 --runs 3
node --test tools/widget_metrics.test.js
```

원시 표본·브라우저 버전·파일 해시는 `reports/obs-performance.json`, 계산 결과는
[`reports/obs-performance.md`](reports/obs-performance.md)에 저장한다. 첫 그림 지연, 초당 합성 횟수,
그리기 픽셀량, 메인 스레드 점유율, 초기 전송량·Blob 보유량, 전환 지연 P95, 숨김 중 작업량을 측정한다.
중앙값·최소/최대·감소율을 계산하며, 실제 OBS 전체 CPU/GPU 사용률은 포함하지 않는다.
`--output <경로.json>`으로 별도 결과를 남길 수 있다. 중단된 JSON에는 완료된 표본만 있으며 `summary`가 없으면 미완료다.

간단한 미커밋 변경 비교는 다음 명령을 순서대로 실행한다. 이때 `--baseline`은 Git HEAD의 위젯을 서빙한다.
대기 상태(`dice=0`), 5초간 그리기 횟수, 캐시 수, 초기 영상 전송량을 출력한다.
512px/DPR 1과 1024px/DPR 2를 각각 측정한다. `TaskDuration`은 렌더러 메인 스레드 작업 시간이며 OBS 전체 CPU/GPU 사용률이 아니다.

```bash
node tools/widget_check.js --benchmark --baseline
node tools/widget_check.js --benchmark
```

로컬 Chrome 측정(2026-10-01): 512px에서 5초당 그리기 **300 → 50회**, 초기 영상 **8,901,737 → 67,280바이트**.
1024px/DPR 2에서 캔버스 **2048² → 512²**, 그리기 **300 → 49회**. 실제 부하는 OBS 버전·장면·해상도에 따라 달라진다.

신규 반응 모션은 내장 ImageGen으로 제작했다. [원본 프롬프트](prompts/obs_reactions_imagegen.md),
[시트·타이밍 정의](anims/obs_reactions.json), `sprites/raw/*_imagegen_sheet.png`를 보관한다.
Pillow·NumPy와 `libvpx-vp9` 인코더가 포함된 ffmpeg 환경에서 `python3 tools/build_reactions.py`로 재현할 수 있다.
재인코딩했다면 `anims/rebuild_manifest.json`의 해당 영상 해시를 검수 후 갱신하고 배포본을 다시 만든다.

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

   생성기가 달라 캐릭터 크기가 기존 클립과 조금 다르게 나왔다면 `--match sprites/idle1_loop/idle1_loop_00.png`를 붙여
   클립 전체를 idle 첫 프레임의 키·발 위치에 맞춘다(전환할 때 크기가 튀지 않게).

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
