# Sheddy Pet

레몬 치비 캐릭터 위젯. 투명 배경 위에서 혼자 숨 쉬고, 두리번거리고, 가끔 춤추고, 마이크에 말하면 입을 움직인다.
OBS 브라우저 소스나 웹페이지에 그대로 올려 쓴다.

- 위젯: <https://eunjaelee-toothlife.github.io/sheddy-pet/>
- 본체는 [`widget.html`](widget.html) 파일 하나 + [`sprites/anim_*.webm`](sprites/) (VP9 + 알파) 클립들

## OBS에서 쓰기

1. 소스 추가 → **브라우저** → URL에 위 주소 입력. 크기는 정사각형 권장(예: 720×720). 배경은 투명.
2. 설정을 바꾸려면 소스 우클릭 → **상호작용**. 마우스를 움직이면 조작 버튼이 나타난다.
   - ⚙️ (F2) 마이크 설정 — 입력 장치와 감도 임계값. 임계값을 넘는 동안 `talk` 모션이 재생된다.
   - 🎭 (F3) 모션 선택 — 원하는 모션을 바로 재생. "계속 유지"를 켜면 주사위를 멈추고 그 모션만 반복.
   - **모드 (F4)** — 일반·할로윈·한국 설·크리스마스·어린이날·여름휴가 선택. 현재 복장으로 힘을 모아 레몬빛으로 사라진 뒤 새 복장으로 등장한다(약 2.7초). 페이지와 마이크 연결·URL 옵션을 유지하며, 이전 `state`·`ending` 지정은 지운다. 변신 중 연속 선택은 무시한다. 현재 모드를 다시 누르면 닫기만 한다. OBS 소스의 저장된 URL은 바뀌지 않으므로 재시작 후에도 유지하려면 소스 URL의 `mode`도 맞춰 둔다.

### URL 옵션

| 옵션 | 뜻 |
| --- | --- |
| `?mode=halloween` | 마녀 복장을 유지하며 할로윈 전용 동작만 자동 재생·선택 |
| `?state=happy1` | 시작 상태 |
| `?hold=8` | 외부 명령으로 바꾼 상태를 주사위로부터 보호할 시간(초) |
| `?dice=0` | 주사위 끄기 (외부 제어 전용) |
| `?flip=1` | 좌우 반전 |
| `?resolution=720` | 정사각형 합성 캔버스의 한 변 상한(px). 기본 720, 범위 128~2048. 화면의 짧은 변×DPR보다 크게 만들지 않음 |
| `?assets=rebuilt` | 이전 512 리소스로 비교. 기본은 `hd720`, 최초 리소스는 `original` |

### 할로윈 모드

`https://eunjaelee-toothlife.github.io/sheddy-pet/?mode=halloween`

처음부터 소품 없는 마녀 대기로 시작한다. 전용 24종과 기존 연금술 4종, 총 28개 동작을 F3에서 선택하거나 자동 추첨으로 재생한다.
일반 모드에서는 전용 24종이 선택·추첨되지 않는다. 가운 변신·원복 영상도 할로윈 모드에서는 재생하지 않는다.

| 상태 | 동작 |
| --- | --- |
| `witchidle1` | 마녀 대기 |
| `broom1` | 빗자루 비행 |
| `lantern1` | 호박 랜턴 |
| `ghost1` | 꼬마 유령 |
| `bat1` | 박쥐 친구 |
| `candy1` | 사탕 나눔 |
| `spellbook1` | 마법책 낭독 |
| `starspell1` | 별빛 마법봉 |
| `crystal1` | 수정구 점술 |
| `blackcat1` | 검은 고양이 |
| `raven1` | 장난꾸러기 까마귀 |
| `spider1` | 거미 구조 |
| `potion1` | 딸꾹 물약 |
| `moon1` | 초승달 그네 |
| `tarot1` | 호박 타로 |
| `umbrella1` | 유령비 우산 |
| `witchdance1` | 마녀 스텝 댄스 |
| `peekaboo1` | 망토 까꿍 |
| `candles1` | 떠다니는 촛불 |
| `gift1` | 할로윈 선물상자 |
| `witchbreathe1` | 마녀 — 편안한 숨쉬기 |
| `witchlook1` | 마녀 — 주변 둘러보기 |
| `witchtidy1` | 마녀 — 모자와 망토 정돈 |
| `witchtalk1` | 마녀 — 말하기 (자동 추첨 제외) |

기존 연금술: `alchemy1` 솥 젓기, `alchemygold1` 황금 레몬, `alchemyboom1` 실험 폭발, `alchemyslime1` 레몬 슬라임.

- `&state=broom1`: 빗자루 비행부터 시작한다.
- 기본 대기는 16프레임/4초, 테마 동작은 핵심 포즈를 충분히 보여주는 4.33~5.33초의 투명 VP9 영상이다. 기본 720px, 이전 자산 모드에는 512px를 제공한다.
- `&dice=0`: 자동 추첨을 끈다. 단발 동작은 한 번 재생 후 마녀 대기로 돌아온다.
- F3의 “계속 유지”: 선택한 동작을 반복한다.
- 일반 모션을 `state`로 지정하면 마녀 대기로 시작하며, `setPetState`의 일반 모션 요청은 무시한다.
- 숨쉬기는 발을 고정하고 최대 2px의 미세 호흡과 눈 깜빡임만 반복한다. 둘러보기·모자 정돈은 대기 분류에서 제외하고 한 번 실행 후 기본 대기로 복귀한다. F3의 “계속 유지”로는 반복할 수 있다.
- F2에서 마이크를 선택하면 음량 임계값을 넘을 때 `witchtalk1`(16포즈/1.33초)이 반복된다. 임계값 아래로 450ms가 지나면 말하기 사이클을 마치고 기본 마녀 대기로 돌아온다. 저장된 마이크 설정도 일반 모드와 동일하게 복원한다.
- 말하기는 자동 추첨에서 제외되며 마이크 신호가 있는 동안 반복한다. 가운 복장의 일반 말하기로 전환하지 않는다.
- 모든 영상을 선로딩하지 않는다. 최초에는 대기 영상 하나만 받고, 이후 필요한 영상만 가져오며 기존 4MiB 캐시 상한을 유지한다.

[20종 모아보기 영상](output/halloween/motions-preview.mp4)과 [말하기·대기 3종 영상](output/halloween/mic-idle-preview.mp4)에서 동작을 확인할 수 있다.

제작 프롬프트와 포즈 순서는 `anims/halloween/motions.json`, ImageGen 원본은 `sprites/raw/halloween/`에 보관한다.
`python tools/build_halloween.py`로 조립하고 `python tools/verify_halloween.py --register`로 신규 자산을 검증·등록한 뒤 Pages를 생성한다.

### 마녀 연금술

F3에서 **마녀 연금술(`alchemy1`)**을 선택하면 가운에서 클래식 마녀 복장으로 변신하고 솥을 젓는다.
주사위 자동 재생에서는 2~3사이클 뒤 **황금 레몬 · 실험 실패 · 레몬 슬라임** 중 하나를 보여 주고,
솥을 정리한 뒤 가운으로 돌아온다. “계속 유지”를 켜면 솥 젓기를 반복하며, 다른 모션을 선택하면 결과와 원복을 거쳐 전환한다.
`?dice=0`에서는 자동 전환이 꺼지므로 다른 모션을 선택해야 결과를 볼 수 있다.

원본은 내장 ImageGen으로 제작했다. 프롬프트는 `prompts/alchemy1_imagegen.json`, 검수한 셀 경계와 타이밍은
`anims/alchemy1_*.json`에 보관한다. Pillow와 libvpx-vp9를 지원하는 ffmpeg 환경에서 재현한다.

```bash
python tools/build_alchemy.py
python tools/verify_alchemy.py
python tools/deploy_pages.py
```

### 기념일 모드

OBS 브라우저 소스 URL에 아래 `mode`를 붙이면 해당 복장의 모션만 재생한다.
각 모드는 **미세 호흡 대기 1종 + 가끔 나오는 잔동작 2종 + 마이크 말하기 1종 + 테마 동작 6종**으로 구성된다.
F3 선택기·자동 추첨·외부 상태 명령도 같은 모드 안에서만 동작한다.
잘못된 모드 이름은 일반 모드로 돌아간다.

| URL 옵션 | 복장 | 테마 동작 |
| --- | --- | --- |
| `?mode=seollal` | 색동저고리·청록 치마·레몬 노리개 | 세배, 복주머니, 윷놀이, 떡국, 방패연, 제기차기 |
| `?mode=christmas` | 빨간 숏패딩·체크 목도리·귀달이 방한모 | 보자기 선물, 붕어빵, 눈사람, 캐럴 율동, 스노볼, 첫눈 |
| `?mode=childrensday` | 노란 모자·멜빵바지·작은 배낭 | 비눗방울, 풍선, 로봇, 종이비행기, 솜사탕, 바람개비 |
| `?mode=summer` | 밀짚모자·레몬 셔츠·반바지 | 튜브, 모래성, 수박, 물총, 파도, 부채 |

테마 동작은 한 번 재생한 뒤 해당 복장의 대기로 돌아간다. F3의 **계속 유지**로 반복할 수 있다.
마이크 입력 시 해당 복장의 말하기로 전환하고 무음이 되면 같은 복장의 대기로 복귀한다.
대기는 발을 고정한 4초 주기이며, 말하기는 몸체를 고정하고 입 모양만 바꾼다. 테마 동작은 4.58~5.67초로, 등장·행동·감상 포즈에 서로 다른 유지 시간을 둔다.

대기·말하기의 얼굴 원본은 내장 ImageGen으로 생성했다. 프롬프트는 `prompts/calm/`, 원본 시트와 기준 몸체는 `sprites/raw/calm/`, 합성 좌표·원본 해시는 `anims/calm_faces.json`에 보관한다. `python tools/compose_calm_motion.py witchidle1 witchbreathe1 witchtalk1`처럼 해당 상태를 지정하면 720/512 PNG와 영상을 재생성한다. Python에는 NumPy·Pillow, FFmpeg에는 `libvpx-vp9` 인코더와 디코더가 필요하다.

`python tools/test_calm_motion.py`는 얼굴 밖 픽셀·발 고정·루프 연결을, `node --test tools/motion_policy.test.js`는 자동 반복 상한과 수동 유지 동작을 검사한다. `preview.html`은 위젯과 같은 프레임 유지 시간·구간 반복·재생 배율을 반영한다.
예: `?mode=seollal&state=seollal_bow1`, `setPetState("christmas_fishbread1")`.
기존 4MiB LRU 캐시·영상 버퍼 2개·숨김 시 정지 정책을 그대로 사용하며 다른 모드 영상을 미리 받지 않는다.

확정 복장은 `output/imagegen/seasonal-costume-concepts/`, 모션별 내장 ImageGen 프롬프트와 타이밍은
`anims/seasonal/motions.json`, 생성 원본은 `sprites/raw/seasonal/`에 보관한다.
크리스마스는 한국 겨울 감성의 `02-christmas-korean-v2.png`를 기준으로 한다.
재생성·수정 프롬프트는 `anims/seasonal/*-repair.prompt.txt`, 검증 결과는 `reports/seasonal-modes.json`에 보관한다.

```bash
python tools/build_seasonal.py
python tools/verify_seasonal.py --register
python tools/deploy_pages.py
node tools/widget_check.js --mode seollal --page docs/index.html
node tools/widget_check.js --mode christmas --fallback --page docs/index.html
```

위젯 검사는 `--mode childrensday`, `--mode summer`에도 동일하게 실행한다.
변신 원본은 `sprites/raw/transform/`, 내장 ImageGen 프롬프트는 `anims/transform/motions.json`에 보관한다. `python tools/build_transform.py`로 6복장 × 이탈/등장 12클립을 조립·검증한다. 변신은 자동 추첨이나 F3 목록에 나오지 않고 모드 선택 시에만 재생한다.

조립에는 Pillow·NumPy와 `libvpx-vp9` 인코더/디코더를 지원하는 ffmpeg가 필요하다.

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

### 챌린지풍 전신 댄스

F3에서 선택하거나 `setPetState`로 실행한다. 16포즈·4초 단발 재생 뒤 복귀하며 **계속 유지**로 반복한다.
챌린지에서 착안해 캐릭터용으로 재구성한 춤이다. 좌우 이동·무릎 반동·발동작을 포함한다.

| 상태 | 춤 | 동작 방향 |
| --- | --- | --- |
| `bounce1` | 챌린지 바운스 | 삐끼삐끼풍 |
| `shuffle1` | 셔플 스텝 | 러닝맨·셔플 챌린지풍 |
| `power1` | 파워 챌린지 | like JENNIE풍 |
<!-- 추가 챌린지 댄스 -->

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
  합성 캔버스는 기본 최대 720×720이며 CSS `object-fit: contain`으로 중앙에 배치한다.
  가로로 긴 창에서도 영상을 작은 직사각형 캔버스 안으로 먼저 축소하지 않는다.
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
node tools/widget_check.js --halloween --page docs/index.html
node tools/widget_check.js --halloween --fallback --page docs/index.html
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

현재 위젯의 기본 리소스는 전체 **62클립 / 846 PNG / 720×720 VP9 알파**다.
기존 동작·FPS·holds·repeats·상태 재생 속도를 유지하며, 원시 이미지에서 직접 720으로 키잉·정합했다.
영상 총용량은 기존 14.2MiB에서 21.7MiB로 약 53% 증가했다. 실제로 필요한 영상만 받는 4MiB 캐시는 유지한다.
1254px 개별 원본과 1024px 필기 원본은 세부 선이 개선되지만, 627px/약314px 시트 셀은 원본 해상도 한계가 남는다.

전체 재현·검증:

720 재현 도구는 `numpy`, `Pillow`, `scipy`와 `ffmpeg`/`ffprobe`가 필요하다.

```bash
python tools/build_hd720_root.py
python tools/build_hd720_dance.py
python tools/build_hd720_special.py
python tools/build_hd720_pastry.py
python tools/audit_hd720.py
node tools/widget_check.js
node tools/widget_hd720_check.js
node tools/widget_hd720_check.js --endings
python tools/deploy_pages.py
```

`anims/hd720_manifest.json`이 62개 영상의 프레임·해시·원본·타이밍을 기록한다.
재생성 후에는 720 PNG를 육안 검수하고 런타임 검사를 다시 진행한다.
이전 512 PNG/WebM은 비교와 원본 보존을 위해 유지하며, 기존 생성 절차는 아래와 같다.

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
| `sprites/hd720/videos/`, `sprites/hd720/frames/` | 기본 720 영상과 PNG 시퀀스 |
| `anims/hd720_manifest.json` | 전체 720 리소스 검증 목록 |
| `sprites/anim_*.webm`, `sprites/rebuilt/` | 최초·이전 512 클립과 원시 이미지 |
| `sprites/raw/`, `sprites/<name>/` | 생성 원본과 키잉된 PNG 시퀀스 (재인코딩용으로 함께 보관) |
| `anims/` | 프레임 정의(JSON) |
| `refs/` | 캐릭터 레퍼런스 이미지 |
| `tools/` | 생성 · 키잉 · 인코딩 · 배포 · 검사 스크립트 |
| `docs/` | GitHub Pages 배포본 (`deploy_pages.py`가 생성) |

`main.js`, `preload.js`, `package.json`, `dialogues/`, `.github/workflows/release.yml`은 같은 위젯을 감싼
Electron 데스크톱 앱(Desk Toy)용이며, 현재는 유지보수하지 않는다.
