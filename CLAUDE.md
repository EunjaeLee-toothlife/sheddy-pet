# CLAUDE.md

Sheddy Pet — 레몬 치비 캐릭터 위젯. 사용법·구조·모션 추가 절차는 [README.md](README.md) 참고. 여기에는 작업할 때 지켜야 할 것만 적는다.

## 범위

- 살아 있는 것은 **`widget.html`(OBS 브라우저 소스 / GitHub Pages)** 과 **모션 생성 파이프라인**(`tools/`, `anims/`, `sprites/`)이다.
- Electron 데스크톱 앱(`main.js`, `preload.js`, `package.json`, `dialogues/`, `tools/dialogue_hashes.js`,
  `.github/workflows/release.yml`, `widget.html`의 `IS_DESKTOP` 분기)은 유지보수하지 않는다. 요청이 없으면 건드리지 말고,
  검토·제안 대상에서도 뺀다.

## 반드시 지킬 것

- **`docs/`는 생성물이다.** 직접 고치지 않는다. `widget.html`이나 `sprites/anim_*.webm`을 바꿨으면
  `python tools/deploy_pages.py`로 다시 만들어 같은 커밋에 넣는다. Pages는 `master` / `docs`에서 서빙된다.
- **위젯 로직을 고쳤으면 `node tools/widget_check.js`를 돌린다.** (헤드리스 Chrome, 의존성 없음, 약 1분)
- 모션을 추가하면 `widget.html`의 `ANIMS`(+ 새 분류면 `CATEGORY_WEIGHTS`)와 `preview.html`의 `ANIMATIONS` 양쪽에 등록한다.
- 코드 주석과 커밋 메시지는 한국어. 커밋은 `feat:` / `fix:` / `chore:` 접두어. 변경은 브랜치 → PR로 `master`에 넣는다.

## widget.html의 불변식

`playClip` / `setState` / 워치독은 서로 맞물려 있어 한쪽만 고치면 조용히 깨진다. 실제로 있었던 회귀들이다.

- **`ended` 핸들러는 일회성이면 안 된다.** loop 클립은 같은 버퍼를 `currentTime = 0`으로 되감아 다시 재생하므로
  사이클마다 `ended`가 온다. 한 번만 받으면 두 번째 사이클부터 1초 주기 워치독이 루프를 대신 굴려 매 사이클 끝에서 멈칫한다.
  콘솔에 `watchdog: ended clip left on screen`이 반복되면 이 증상이다. 워치독은 안전망이지 정상 경로가 아니다.
- **버퍼는 두 개뿐이고 계속 재사용된다.** `playClip`의 콜백·타이머는 실행 전에 `live()`로 자기 호출이 아직 그 버퍼의
  주인인지 확인한다. 새로 추가하는 콜백도 같은 검사를 거쳐야 한다.
- **크로스 디졸브 중인 버퍼를 다시 쓸 때는 디졸브를 먼저 끝낸다**(`fade = null`). 그러지 않으면 바탕이 비어 알파가 꺼지고,
  디졸브 종료 시의 `pause()`가 새로 로드한 클립을 멈춘다. 전환 직후 큐에 있던 요청(말하는 도중 전환이 끝난 경우)에서 난다.
- **`setState`는 `await` 뒤마다 세대(`chainGen`)를 확인한다.** 워치독이 버린 체인이 뒤늦게 풀려 상태를 덮어쓰지 않게 한다.
  `await`를 추가하면 그 뒤에도 확인을 넣는다.
- **큐에 넣는 요청은 `{ name, pin }`을 함께 보관한다.** pin은 `pinNow()`로만 건다 — '계속 유지'의 `Infinity`를 줄이지 않는다.

## 검증할 때

- Claude 데스크톱 앱의 Browser 패널이 **숨겨져 있으면**(`document.hidden === true`) Chromium이 음소거 영상을 스스로
  일시정지하고 rAF / rVFC도 돌지 않는다. 그 상태에서는 재생·전환을 검증할 수 없고, 영상이 멈춘 것도 위젯 버그가 아니다.
  `tools/widget_check.js`처럼 `--headless=new` Chrome을 CDP로 구동하면 페이지가 visible로 취급되어 실제 경로를 탄다.
- `widget.html`의 최상위 `let` / `const`(`current`, `transitioning`, `vids`, `front`, `CLIP_URL`, …)는 콘솔이나
  `Runtime.evaluate`에서 이름으로 바로 읽고 쓸 수 있다. `?dice=0`을 붙이면 주사위가 꺼져 상태가 결정적으로 유지된다.
- 로컬 서버는 `python -m http.server 8474`. `.claude/`는 git에 올라가지 않으므로, 미리보기용 `.claude/launch.json`이
  없으면 이 명령을 `pet-server`라는 이름으로 등록해서 쓴다.

## 모션 생성 메모

자세한 기록은 [prompts/animation_prompts.md](prompts/animation_prompts.md). 자주 걸리는 것만:

- 기본 모델은 `gemini-3.1-flash-lite-image`. 문제 프레임만 `--only N`(필요하면 `--model`, `--prev`)으로 다시 뽑는다.
- 여러 클립을 병렬 생성할 때는 **동시 5개 이하**. chain 모드는 요청마다 레퍼런스 2장을 보내므로 그 이상이면 분당 입력
  토큰 쿼터(429)에 걸리고 내장 백오프로는 회복되지 않는다.
- 기본 복장(가운)이 아닌 모션은 클립 후반의 정적인 프레임에서 모자·장식이 빠지기 쉽다. 생성 후 프레임을 나열해 확인한다.
- 머리 위 `Zzz`, `!`처럼 본체와 떨어진 기호는 매트 정리(`slice_and_key.py`의 최대 연결 성분 유지)에서 지워진다.
  표정과 동작으로 표현한다.
- `gen_frames.py`의 비-chain 경로는 로컬 lite-image 스킬 스크립트(`~/.claude/skills/lite-image/scripts/generate_image_v2.py`)를
  호출한다. chain 경로는 Gemini API를 직접 호출한다.
