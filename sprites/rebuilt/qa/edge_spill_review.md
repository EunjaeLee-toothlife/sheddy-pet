# 반투명 가장자리 green spill 읽기 전용 검토

## 결과

chem1_end3를 제외한 **38클립/561PNG**를 정량 검사했다. **32클립/437PNG**에 `0 < alpha < 100` 및 `G - max(R,B) > 20` 조건의 픽셀이 있으며 합계181,528픽셀이다. 픽셀 수는 프레임별 저알파 RGB 신호의 수이지 불투명 얼룩 면적이 아니다. 원래 alpha0에 남은 숨은RGB는 제외했다. 실제 합성의 녹색 기여 근사값은 `excess × alpha /255`로 따로 기록했다.

신호가 강한 12개 클립의 worst frame을 실제512px 흰색/어두운 배경에서 확인했고, 신호가 있는32개 클립 모두 최대기여 위치의24px native crop 및4배 nearest 확대를 확인했다. 대부분은 가운·머리·별·연기 외곽의 아주 얇은 저알파 회색/연한 색 테두리다. native 크기에서 넓고 뚜렷한 녹색 halo가 보이는 사례는 이 표본에서 확인하지 못했다. 확대에서는 Lanczos 재샘플링에 의한 일부 녹색 성분 재도입을 측정할 수 있다. 얼굴·흰 가운 내부의 랜덤 얼룩으로 해석하면 안 된다.

**별도로 명확한 중요 결함이 발견되었다:** `pastry1_end3_06`의 하단 green macaron이 투명하다. [원래 생성 시트](../sheets/pastry1_end3_04-05-06-07.png)는 pink/yellow/green 3개가 모두 불투명하게 그려져 있으나, 후보의 하단 층은 흰 배경에서 white처럼 보이고 dark에서 배경색으로 뚫린다. `(250,70)`, `(254,70)`, `(260,70)`의 RGBA는 모두 `[0,0,0,0]`, `(255,67)`은 alpha9다. 이는 미세 외곽rim보다 큰 음식 내부 alpha hole이며 의도된 green을 살리는 bounded keying/원 donor 재등록이 필요하다. 같은 food가 보이는 end3 slots03–07 전체를 repair 때 확인해야 한다. 현재 직접 native 비교로 확정한 프레임은06이며 다른 슬롯까지 동일 결함으로 확정하지 않는다.

## 높은 외곽 신호와 관측

- chem1_end1: 프레임별0–971픽셀, worst 강도 프레임04에서932픽셀/alpha가중excess>8은278픽셀. 많은 신호가 smoke 외곽에 있다. smoke 및 얼굴 soot는 의도된 효과이며 가운 얼룩이 아니다.
- happy3_loop:241–1011픽셀, frame08에서824픽셀/가중>8은158. 회전 포즈의 가운/머리·별 가장자리로, native 흰/어두운 배경에서는 매우 얇고 확대에서만 구분이 쉬웠다.
- pastry1_outro:0–1159픽셀, frame02에서1159픽셀/가중>8은144. 머리/회전 ribbon/별 외곽 신호. 수치가 크다는 이유로 의도된 회전효과나 분리된 별을 제거해서는 안 된다.
- boxing1_loop:270–757픽셀, frame06에서757픽셀/가중>8은134. outline과 입김의 주변 저알파 신호다.
- pastry1_end1–8: 각 프레임 약295–849픽셀 범위, 최대 가중>8은54–125. overhead outline 및 별이 측정량에 기여한다. green macaron은 외곽 수정과 분리하여 반드시 보호해야 한다.
- doze1_loop:467–883픽셀, frame09의 가중>8은111. 가운·양말 외곽에서 신호를 측정했다. native 크기에서 큰 green halo는 관측하지 못했다.

## 보존 조건과 한계

`G>R/B` 전체를 blindly clamp하면 leaf/food/rainbow 같은 유효 녹색이 소실되거나, 피부·가운의 antialias색이 변한다. 이 검토는 후보나 ledger를 수정하지 않았으며 post-resize 처리를 직접 적용하지 않았다. Root가 선택적으로 처리한다면 외곽 low-alpha와 의도된 enclosed green의 마스크를 분리하고, macaron/rainbow 같은 내부 녹색 alpha 보존을 먼저 확인해야 한다. RGBA edge count 감소만으로 그림 품질 또는 state seam을 합격 판정하지 않는다.

검사 manifest snapshot SHA-256: `e10ca92e75400d92b098a3c244dc1049dee347f1210dc34210e0433c95a6afee`. 모든 프레임 SHA-256은 아래 측정JSON에 함께 보존했다. 이후 자산 변경은 해당 frame hash와 비교해야 한다.

## 증거

- [전체38클립/561프레임 측정](edge_spill/measurements.json): raw count, alpha-weighted>3/>8, exterior-adjacent count, bbox, 파일hash. exterior count는 alpha0 외부와2px 이내인 수치적 분류이고 실제green의 유효 여부를 자동 확정하지 않는다.
- [native white/dark 1](edge_spill/native_white_dark_1.png), [2 — green macaron hole](edge_spill/native_white_dark_2.png), [3](edge_spill/native_white_dark_3.png).
- [32개 클립 native/확대 edge crop 1](edge_spill/native_edge_patches_1.png), [2](edge_spill/native_edge_patches_2.png), [3](edge_spill/native_edge_patches_3.png), [4](edge_spill/native_edge_patches_4.png). 왼쪽 작은 두24px 이미지는native, 중앙 두96px 이미지는nearest4배 확대다.
- [읽기 전용 검사 스크립트](inspect_edge_spill.py). 최종자산 폴더에는 쓰지 않으며 별도QA measurements/composites만 만든다.

## 클립별 정량 범위

아래 표의 최대 raw count와 최대 가중>8은 서로 다른 프레임일 수 있다. 둘을 동일 프레임 결함으로 합산하지 않는다.

| Clip | affected/frames | raw/frame min–max | max alpha-weighted>8 |
|---|---|---|---|
| idle1_loop | 0/18 | 0–0 | 0 |
| basic1_loop | 12/18 | 0–360 | 2 |
| basic2_loop | 15/18 | 0–377 | 2 |
| basic3_loop | 16/18 | 0–219 | 1 |
| doze1_loop | 14/14 | 467–883 | 111 |
| happy1_start | 0/6 | 0–0 | 0 |
| happy1_loop | 16/18 | 0–182 | 1 |
| happy1_end | 0/6 | 0–0 | 0 |
| happy2_loop | 10/18 | 0–251 | 11 |
| happy3_loop | 20/20 | 241–1011 | 158 |
| excited1_loop | 0/18 | 0–0 | 0 |
| boxing1_loop | 12/12 | 270–757 | 134 |
| dance1_loop | 16/16 | 269–547 | 30 |
| yaho1_loop | 13/14 | 0–583 | 10 |
| parapara1_loop | 24/24 | 262–607 | 74 |
| dance2_loop | 16/16 | 379–672 | 71 |
| dance3_loop | 16/16 | 252–658 | 54 |
| pastry1_start | 8/14 | 0–818 | 11 |
| pastry1_loop | 14/14 | 321–636 | 5 |
| pastry1_end1 | 12/12 | 295–843 | 97 |
| pastry1_end2 | 12/12 | 295–843 | 125 |
| pastry1_end3 | 12/12 | 295–843 | 116 |
| pastry1_end4 | 12/12 | 295–849 | 105 |
| pastry1_end5 | 12/12 | 295–843 | 108 |
| pastry1_end6 | 12/12 | 295–843 | 91 |
| pastry1_end7 | 12/12 | 295–843 | 112 |
| pastry1_end8 | 12/12 | 295–843 | 54 |
| pastry1_end9 | 12/12 | 349–843 | 9 |
| pastry1_end10 | 12/12 | 362–843 | 22 |
| pastry1_outro | 4/10 | 0–1159 | 144 |
| lemon1_loop | 14/16 | 0–476 | 24 |
| sad1_loop | 0/18 | 0–0 | 0 |
| sad2_loop | 18/18 | 166–300 | 1 |
| talk_loop | 0/18 | 0–0 | 0 |
| chem1_start | 11/12 | 0–559 | 35 |
| chem1_loop | 18/19 | 0–510 | 41 |
| chem1_end1 | 19/20 | 0–971 | 278 |
| chem1_end2 | 11/12 | 0–610 | 103 |
