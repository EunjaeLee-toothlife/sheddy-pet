# 최종 39클립 경계 정적 시각 검토

2026-09-30 / special_motion. 현재 실제 candidate PNG/WebM의 hash를 고정한 정적 검토다. 중앙 ledger와 후보를 편집하지 않았다.

**정적 경계 비교에서 새로 확인한 blocking 그림 결함은 없다.** 원본 동작에 필요한 점프·회전·웅크림·표정·소품 변화는 유지되어 있고, 경계 frame에 다른 셀의 캐릭터 파편, 뚜렷한 얼굴/흰 가운 얼룩, 갑자기 다른 복장/손 소품으로 바뀌는 문제를 발견하지 못했다. 이는 아래 경계 contact와 주요 native frame 관측 범위에 대한 결론이다. 70ms 디졸브 런타임을 시각적으로 합격 판정한 것은 아니다.

## Hash에 묶인 검토 범위

- 39클립의 실제 후보 PNG **579장 모두**와 후보 WebM 39개를 SHA-256 inventory에 기록했다. 여기서 모든579장의 내부 행동을 다시 native로 재검토했다는 의미는 아니다: 이번 검토는 전체 inventory에 묶인 **경계 검토**다. 전체 행동의 기존 정적 검토는 `root_static_review.md`, `special_final_review.md` 및 다른 담당자의 결과를 함께 사용한다.
- 21개 loop의 실제 마지막3장→첫3장, 원본/후보 나란히 전부 확인했다.
- 실제 상태 연결 69개를 원본과 후보로 전부 확인했다. 각 연결의 마지막2장→첫2장을 표시했다.
- happy start→loop→end→idle, pastry start→loop→각end1…10→공용outro→idle, chem start→loop→각end1…3→idle, 17개 single-loop의 idle 양방향 경계를 포함한다.
- 원본579장의 hash는 중앙 ledger에 기록된 원본 hash와 모두 일치했다. 처음 contact/inventory 이후 root가 pastry1_end3의 내부03–07 음식 matte만 교정한 것을 실제hash차이로 확인했다. 경계00/01/10/11은 변경되지 않았고 시각검수한 경계도 그대로다. 해당교정/encode후 최신중앙 및 후보PNG/WebM 전체를 다시 hashinventory로 발행했다. 내부03–07 교정결과의 전체행동시각판정은 root 검수범위다.
- 최신 Manifest SHA-256: `ce7a461127d4386bbb1590e85fa9a667434f755a53a3380be8d1c4054e1a6b6b`.
- [후보 PNG별/WebM별 실제 hash binding](seam_final/hash_binding.json). 이 JSON 자체의 SHA-256: `6e910c5219fe16c44decf43938ed9bfec1873fe134e55ff83d868e03754dc113`.

파일이 바뀌면 이 판정을 그대로 새 자산에 적용하면 안 된다. 중앙 reviewNotes/플래그가 바뀌기만 한 경우에도 manifest hash는 달라질 수 있으므로 실제 candidateFrames hash를 우선 대조한다.

## Loop 마지막3장→첫3장

| 증거 페이지 | 해당 loop | 눈으로 확인한 경계 관측 |
|---|---|---|
| [loops00](seam_final/loops_00.png) | idle1/basic1/basic2/basic3/doze1 | idle 호흡의 subpixel 귀환, basic1 정면 복귀, basic2 raisedpalms→neutral→raisedpalms, basic3 기울기복귀, doze 마지막sleepyface→초기sleepyface→눈감기. 의도된 팔/눈/기울기 변화가 있음. 다른 캐릭터로 바뀌는 head/body 오류는 보이지 않음. |
| [loops01](seam_final/loops_01.png) | happy1/happy2/happy3/excited1/boxing1 | happy1 sway의 한단계귀환, happy2 인사→neutral, happy3 neutral/감은눈→회전용팔펼치기, excited1 착지이후neutral→준비crouch, boxing frontguard 귀환. boxing 승인된07/08upright는 이 seam검토에서 duck누락으로 취급하지 않음. |
| [loops02](seam_final/loops_02.png) | dance1/yaho1/parapara1/dance2/dance3 | dance1 가슴앞손loopclose, yaho 최종neutral→가슴앞주먹/볼손, parapara 가슴앞손loopclose, dance2 양주먹loopclose, dance3 양주먹/발벌림loopclose. 손/눈/발폭 차이는 source-action에 따른 동작이며 얼룩이나 실루엣 조각으로 보이지 않음. |
| [loops03](seam_final/loops_03.png) | pastry1/lemon1/sad1/sad2/talk | pastry13 mixing→00mixing에 props/chef복장 일치, lemonneutral뒤하품/소품준비, sad1 standingbreath, sad2 실제crouchbreath, talk 입모양half→base→half. sad2의 낮은 전체높이는 crouch이고, source의 oversizedhead를 그대로 키운 것이 아님. |
| [loops04](seam_final/loops_04.png) | chem1 | inspect16→propreset17→sharedmix18→sharedmix00→beakertilt01→droplet02. magentaflaskLEFT/cyanbeakerRIGHT 유지, 액체가 엉뚱한 소품으로 바뀌거나 없어지는 경계 없음. |

마지막=첫 복사가 모든 loop의 요구조건은 아니다. idle/breathing/basic3/happy1 등은 원본의 연속 사이클 샘플을 유지하므로 작은 bob/rotation 변화가 있다. 큰 pixel-diff 수는 보간 때문일 수 있고 시각 결함 크기를 의미하지 않는다.

## 실제 복합 상태 연결

### Happy

[edges00](seam_final/edges_00.png)의 happy4개 연결에서 의상/머리/손 포즈가 자연스럽게 이어지는 경계 표본을 확인했다. start05→loop00는 동일 가시픽셀, end05→idle00도 동일하다. **loop17→end00**은 동일하지 않으며, 원본과 같은 sway에서 중립 clasped 위치로 돌아오는 한 단계다. 이전의 loop00=end00 검증을 실제 종료 검증과 혼동하지 않았다. 70ms dissolve 중 얼굴/가운이 불편하게 겹치는지 실제 재생에서 확인해야 한다.

### Pastry 10가지 결말

[edges00](seam_final/edges_00.png), [edges01](seam_final/edges_01.png), [edges02](seam_final/edges_02.png), [edges03](seam_final/edges_03.png)의 모든 ending 연결을 확인했다.

- start13→loop00, loop13→각end00, 각end11→outro00, outro09→idle00가 모두 동일 가시픽셀로 연결된다. 따라서 한쪽 경계에서 모자/셰프재킷/분홍앞치마/그릇 등이 갑자기 다른 donor로 바뀌는 문제는 이 표본에서 없다.
- end10에는 레몬/plate가 남는 hiding 직전포즈가 있고 end11에는 공용chefreset으로 돌아온다. 이 **동작 자체의 전환**은 원본도 동일구조다. plate가 달린 손이 갑자기 반대편으로 순간이동하는 경계는 관측되지 않았다.
- commoncamera가 chef장면을작게보이게 하는 것은 의도된 여백 확보다. 실제 start/ending 내부 camera이동의 부드러움은 별도 재생검수 대상이다.
- native outro07/08/09 확인: 07 closedface + tiny effect 이후08/09canonicalidle로 돌아오며 얼굴·가운에 패치/잔여셰프조각은 보이지 않았다.

### Chemistry 3가지 결말

[edges00](seam_final/edges_00.png), [edges01](seam_final/edges_01.png), [edges03](seam_final/edges_03.png), [edges04](seam_final/edges_04.png)의 모든 branch를 확인했다.

- start11→loop00, loop18→각end00, 각end마지막→idle00는 모두 동일 가시픽셀이다. entry의flaskLEFT/cyanbeakerRIGHT 및 의상 일치, exit props/smoke/soot 제거를 확인했다.
- **chem1_end2 최신04를512px native로 다시 확인했다.** 이전 보고서의 blink누락은 root수정으로 해결되어 두눈이완전히감겼고 flatmouth/원래glass/몸이 유지된다. 현재판정에 이전open-eye04를 사용하지 않았다.
- chem1_end3 native15/16/17 확인: 15작은endingcamera→16중간높이→17canonical로 단계적scale복귀가 들어가 있다. 작은body에서17만갑자기커진 것으로 분리해 bodyidentity결함 판정하지 않았다. 얼굴/가운은 깨끗하고17은exactcanonical이다. zoom이 실제속도에서부드러운지는 runtime확인 필요하다.
- end1의 얼굴/앞머리soot는 의도된 실패장면이고, idle경계까지남는 랜덤얼룩은없다. smokealpha가밝은테두리처럼보이는지는 검정/흰/실제OBS배경 재생에서 확인한다.

## Idle ↔ single-loop: 재생 판정이 필요한 연결

[edges04](seam_final/edges_04.png), [edges05](seam_final/edges_05.png), [edges06](seam_final/edges_06.png), [edges07](seam_final/edges_07.png), [edges08](seam_final/edges_08.png)에서 17개loop의 양방향연결을 확인했다.

neutralreset이 있는 basic1/basic2/happy2/excited1/yaho1/lemon1의 loop마지막→idle00는 가시픽셀exact다. 실제 idle마지막17은0.1pxbob라 모든incomingedge가exactzero가 되는 것은 아니다. 작은호흡위치차이를 새결함으로 분류하지 않았다.

다음은 source에도 다른포즈로 연결되는 상태다. 정적뷰만으로70ms디졸브의 불편함을 판단할 수 없으며, 재생결과없이새프레임을무조건 생성할 이유는 없다.

| Runtime 우선순위 | 구체적인 포즈차이 | 필요한 판정 |
|---|---|---|
| sad2 ↔ idle | 무릎끌어안은낮은crouch ↔ standing, 머리의수직위치가크게다름. 새sad2머리크기는standing과일관하게정규화되어있음. | 디졸브 중 두몸이 보이거나순간일어남이불편한지. 불편할때만일어나는bridge 검토, crouch를standing높이로키우지않기. |
| boxing ↔ idle, dance3 ↔ idle | 넓은발 stance/주먹 ↔ 좁은발/내린팔 | 발/팔의겹침이그냥짧은전환인지눈에띄는이중상인지. 원래stance유지. |
| happy3 ↔ idle | 팔펼친turn 준비 또는closed-facefinish ↔neutral | 원래spin을줄이지않고팔포즈전환이읽히는지. |
| dance1/dance2/parapara ↔ idle | 가슴앞손/주먹 ↔내린팔 | 얼굴/몸identity는같고팔만다른상태에가까움. 70ms중첩의가독성. |
| doze/sad1/talk ↔ idle | sleepy/slump/mouthclosed 차이, body같거나근접 | 눈·입바뀜과가운이중상없는지. talk입밖고정은의도이며해제할필요없음. |

## 결론의 한계와 root의 남은 판정

정적source/candidate경계는 확인했고, 이전chemblink누락도최신프레임에서해결되었다. 추가필수이미지재생성결함을관측하지못했다. root는 실제70ms디졸브 재생,branch완주후idle,각loop반복을확인한후 runtime/seam review플래그를판정하면된다. 이 보고서는 정적검수범위만증명하고중앙review플래그를변경하지않았다.

전용 생성스크립트: [build_seam_final.py](build_seam_final.py). 원본/중앙/후보/공용tools를편집하지않고 QAcontact와hashinventory만생성한다.
