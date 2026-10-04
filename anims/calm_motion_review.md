# 대기·동작 템포 및 고해상도 재제작 검수 — 2026-10-05

동작 개선 기준은 `b10ff20`, 고해상도 교정 직전 기준은 `0e41b2d`다. 기본 모드 외 대기의 과한 전신 움직임, 빠른 포즈 전환과 자동 반복을 줄이고, 작은 원본을 확대한 자산까지 고해상도로 교체했다. 상태 머신의 전환·마이크·워치독 구현은 유지한다.

## 최종 동작

- 대기 6개: 4초 주기, 최대 2px 미세 호흡과 짧은 눈깜박임. 하단 560~719행은 모든 프레임에서 동일하다.
- 테마 말하기 5개: 1.33초 길이와 마이크 응답을 유지하고 입 영역 밖 RGBA를 고정한다. 어린이날은 열린 기본 입을 닫는 패치를 별도로 사용한다.
- 테마 잔동작 10개: `idle`에서 `basic`으로 이동해 한 번 실행 후 대기로 돌아간다. 사용자가 지정한 “계속 유지”는 반복한다.
- 테마 특수 동작 43개: 3초에서 5.42~6.67초로 연장했다. 이동 포즈는 최소 0.25초, 시작·복귀는 0.5초, 주요 행동·감상 포즈는 더 오래 유지한다.
- 바운스·셔플·파워: 기존 안무를 다시 그리고 중간 포즈를 2개씩 사용한다. 18포즈·70틱·15fps, 한 사이클 4.67초다. 키 포즈는 약 0.267초, 중간 포즈는 0.2초다. 내부 2회 반복은 제거했다.
- 레몬 한입: 16틱에서 40틱으로 연장했다. 10fps 영상 4초를 실제 0.7배속으로 약 5.71초 재생한다.
- 기본 몸짓·감정·기존 춤 9개: 재생 배율과 자동 반복 상한을 낮췄다. 이미지 재제작 범위에는 포함하지 않았다.
- PNG 미리보기에도 실제 holds/repeats/rate를 적용해 영상과 같은 템포로 표시한다.

## 고해상도 교정 범위

대기·속도 개선으로 영상이 바뀐 60클립 전체를 조사했다. 고해상도 원본이 확인된 기념일 32클립은 유지했고, 작은 원본을 확대했던 28클립은 다시 제작했다. 재제작 대상은 할로윈 24종, 춤 3종, 레몬 한입이다. 마녀 기준 포즈와 연결되는 변신 2클립의 앵커도 갱신했다.

새 포즈 원본은 내장 ImageGen으로 생성했다. 3포즈 시트는 2172×724, 2포즈 시트는 1774×887, 마녀 몸체와 재사용 가능한 단독 중간 포즈는 1254×1254다. 실제 사용하는 셀은 최소 720px이고, 조립 시 축소 비율은 1 이하로 제한한다. 최종 출력은 720×720이며 512×512 호환본은 이 결과에서 축소한다. 기존 720 내보내기 파일이 있었다는 사실만으로 원본 해상도가 충분하다고 판단했던 오류를 바로잡았다.

원본 셀 크기·해시·축소율·정렬 위치로 최종 PNG 전체를 다시 재현하고 픽셀 단위로 비교한다. 시트 셀 경계를 넘은 포즈는 인접 포즈가 섞이지 않는 실제 경계를 기록했다. 원본 외곽에서 잘린 프레임, 잘못된 포즈는 다시 생성했다. 춤의 전체 안무와 삽입 위치는 유지하지만 새로 그린 키 포즈가 이전 파일과 픽셀까지 동일하다고 주장하지 않는다.

- 생성 원본: `sprites/raw/native-correction/`
- 프롬프트: `prompts/native-correction/`; 기존 기념일 표정과 단독 중간 포즈는 `prompts/calm/`, `prompts/inbetweens/`
- 원본 셀·정렬 설정: `anims/native/geometry.json`, 각 `anims/*_loop.json`의 `nativeSources`
- 대기 몸체·표정 좌표와 해시: `anims/calm_faces.json`
- 60클립 및 변신 2클립의 원본 증빙: `anims/native/resolution-correction.json`

## 비교 자료와 재현

[마녀 대기 720px 원본 크기 비교](../output/native-correction/witchidle-before-after.png)

[마녀 대기 영상](../output/native-correction/witchidle1-before-after.mp4) · [바운스 영상](../output/native-correction/bounce1-before-after.mp4) · [레몬 한입 영상](../output/native-correction/lemon1-before-after.mp4)

비교 영상은 왼쪽 `0e41b2d`, 오른쪽 최종 결과이며 각 칸을 실제 720px로 표시한다. 이전 `output/calm/`의 비교 이미지와 영상은 속도 개선 단계의 기록이다.

```sh
python tools/compose_calm_motion.py witchidle1 witchbreathe1 witchtalk1
python tools/build_native_motion.py broom1 bounce1 shuffle1 power1 lemon1
python tools/build_hd720_dance.py --reference sprites/hd720/frames/idle1_loop/idle1_loop_00.png --clip bounce1_loop shuffle1_loop power1_loop
python tools/build_hd720_special.py --clips lemon1_loop
python tools/verify_halloween.py --register
python tools/verify_native_motion.py transform_halloween --register
```

기존 할로윈·반응 생성 진입점에서도 각 항목의 고해상도 조립 경로를 사용한다. 실제 타이밍은 `anims/*_loop.json`의 fps/holds/repeats로 유지한다. 단순 조립에는 Python NumPy/Pillow, 특수·춤 장부에는 SciPy도 필요하다. FFmpeg/ffprobe는 libvpx-vp9 인코더·디코더를 지원해야 한다.

검증 환경은 macOS와 headless Chrome이다. 시스템 FFmpeg에 libvpx가 없어 임시 imageio-ffmpeg 0.6.0 번들의 FFmpeg 7.1을 사용했다. 프로젝트 의존성이나 시스템 설치는 바꾸지 않았다. 생성은 내장 ImageGen으로 수행했으며 이미지 생성 CLI와 API 키는 사용하지 않았다.

## 검증 결과

- 회귀 테스트 16개 통과: 원본 검사 7개, 대기 합성 3개, 반응 타이밍 6개. 512px 원본·확대·잘린 포즈를 거부하고 18포즈 픽셀 변조도 검출한다.
- 60클립과 연결 변신 2클립의 원본→최종 PNG 재현 검사 통과. 실제 최소 원본 셀은 724px, 최대 확대율은 0.968563이다. 기존 고해상도 32클립은 `0e41b2d`와 영상·PNG 해시가 같다.
- 전체 60클립의 fps/holds/repeats/rate가 고해상도 교정 전과 같다. 새로 바뀐 30클립의 512px PNG는 720px 결과의 정확한 축소본이다.
- 할로윈 24클립 384포즈, 변신 2클립 32포즈의 알파·경계·연결·타이밍 검사 통과.
- 전체 자산 감사: 영상 315개, PNG 4,715포즈, 디코딩 12,275틱, Pages 복사본 315개 검사. HD720 전체 138개와 이번에 변경한 런타임 영상 61개는 해시·크기·시간·포즈 순서·알파 검사를 통과했다.
- 감사 명령은 기존 512px `chem1_end1`의 4번 틱과 `chem1_end3`의 16번 틱에서 불투명도 경고를 내므로 종료 코드 1이다. 두 영상은 교정 전과 SHA256이 같으며 이번 변경 대상이 아니다. 경고를 숨기거나 검사 기준을 낮추지 않았다.
- Chrome에서 할로윈 단발 복귀·대기/마이크 반복·유지·숨김·큐, 춤 3종 두 사이클, 레몬 완료와 4개 뷰포트, Pages rVFC 미지원 폴백, 6개 모드 전환·실패 복구를 통과했다. OBS 앱에서 직접 재생한 결과는 아니다.
- 비교 영상 3개를 끝까지 디코딩했고, 원본 크기의 전후 이미지와 전체 포즈 모아보기 시트를 시각 검수했다. AI로 다시 그린 포즈는 이전 그림과 세부 선·표정이 다를 수 있다.
- original/rebuilt/hd720 세 경로의 Pages 배포 계획을 `--require-reviewed --dry-run`으로 검사했다. 각 138클립이 검수 완료 상태이며 해시가 일치한다.

검사 원문: [원본·회귀 검사](../output/native-correction/validation-checks.txt), [런타임 검사](../output/native-correction/runtime-checks.txt), [전체 자산 감사](../output/native-correction/asset-audit.json). 최종 검수는 `anims/native/resolution-correction.json`의 영상·PNG SHA256에 연결한다.

이번 범위 밖의 기존 일반 동작 일부에는 작은 원본을 확대한 720px 파일이 남아 있다. 프로젝트 전체 138클립이 모두 네이티브 고해상도라는 뜻은 아니다.
