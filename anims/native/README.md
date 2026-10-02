# 기념일 모션 원본 재작업

기준 커밋: `4710b3a619877f74e8ad8ffc7a1bab13d58babef`. `jobs.json`의 poseReferences는 이 커밋의 프레임이다. 런타임 프레임 교체 전에 별도 디렉터리로 추출해서 사용한다.

생성: ImageGen 내장 도구, 투명 배경. 입력 순서는 왼쪽 포즈, 오른쪽 포즈, 복장 세부 참고 이미지다. 각 작업의 실제 프롬프트 파일은 `jobs.json`의 `promptFile`에 기록한다. 일반 모션은 `guided.prompt.txt`, 변신은 `transform.prompt.txt`, 경계에 걸린 포즈의 재생성은 `wide.prompt.txt` 또는 `transform-wide.prompt.txt`를 사용했다. 16포즈 시트는 실제 셀 해상도가 부족하므로 두 포즈씩 생성한다.

`geometry.json`은 기존 모션의 크기·바닥선을 고정한다. 정상 복장 변신의 축소는 기본 대기 모션 높이 기준으로 보정한다. 새 원본은 셀당 최소 720px이며 실제 캐릭터 영역을 확대하지 않는다. `build_native_motion.py`가 원본 크기, 잘림, 확대를 검사하고 `nativeSources`에 실제 사용한 원본·접합 프레임의 해시를 기록한다. `verify_native_sources.py`는 이 증빙으로 720 프레임을 다시 계산해 픽셀 단위로 비교한다.

완료: 기념일 40종과 6개 복장의 이탈/등장 12클립, 총 52클립. 원본 368장 중 367장은 1774×887, 1장은 1773×887이며 실제 포즈 칸은 최소 886×887이다. 사용한 원본의 최대 축소 비율은 0.843138이고 확대는 없다. 출력은 기존과 같은 720×720/512×512, 16프레임, 기존 fps/holds다.

눈사람·로봇·모래성처럼 바닥의 소품이 발보다 아래에 있는 모션은 전체 실루엣 중심으로 정렬한다. 화면 여백을 벗어나면 크기를 바꾸지 않고 필요한 만큼만 이동하며, 이동으로도 들어가지 않으면 빌드를 거부한다. 일반/할로윈 변신의 중립 접합점은 기존 대기 프레임을 재사용한다. 기념일 접합점은 새 대기 프레임, 모든 변신의 빛 접합점은 새 일반 변신의 마지막 프레임을 공유한다. 이러한 재사용도 `nativeSources`의 `anchor`와 해시로 기록한다.

재조립은 `tools/build_native_motion.py STATE...`, 검사는 `tools/verify_native_motion.py STATE... --register`로 실행한다. 모드별 대기 모션을 먼저 만들고, 변신은 `transform_normal`을 먼저 만든다. 기존 `build_seasonal.py`와 `build_transform.py`도 교체된 모션은 이 파이프라인으로 연결한다. 배포본은 `tools/deploy_pages.py --require-reviewed`로 생성한다. 전체 검수 증빙은 `review.md`와 `anims/hd720_manifest.json`에 기록한다.
