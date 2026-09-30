# Pastry restored-scale static review — 2026-09-30

Read-only review of the latest13 pastry clips /158 PNG slots after normal chef camera0.96, lowered presentation04/07 camera0.87 and overhead05/06 camera0.9594. All13 current contact sheets were generated from final PNGs and actually viewed. Production PNGs/videos, originals, central ledger and shared tools were not edited.

## Scope and hash binding

[Exact158-frame /13-video inventory](pastry_scale_final/hash_inventory.json) fixes the assets reviewed here. Contacts in `pastry_scale_final/` cover start14, loop14, outro10 and all10 endings12 each. Every contact shows every frame on a dark background at256px per512px sprite. Native512 checks additionally covered end9_03, end3_06 and end8_04. Original normal end9_03/loop00 and the original/current raw presentation sources were also viewed during the preceding geometry investigation.

This is static asset review, not approval of temporal camera easing,70ms runtime dissolves or every frame at native resolution. Root separately completed scoped ending coverage and actual widget canvas inspection; the follow-up evidence below is distinct from this agent's static review.

## Observed improvements and preserved content

- Normal chef size is restored. End9_03 now fills essentially the original normal height instead of the earlier0.78-wide camera: the prior geometry check measured original472px/96px face and proposed0.96 result464.6px/95px face. Loop00 is approximately471px tall versus original472px. The shown normal character no longer appears uniformly reduced to78percent.
- Start preserves labcoat idea/anticipation/spin, spiral/flash transformation, chef arrival, bowl/whisk reveal and mixing entry. Outro preserves chef anticipation/bounce/spin/spiral/flash and canonical labcoat return. No extra labcoat/chef costume replacement or prop swap appeared in contacts.
- Loop14 slots retain whisk rotation, bowl, batter motion, hair movement, facial effort and whisk lift/reset. Normal scale/body identity stays consistent through these repeated poses.
- Endings1–8 preserve strawberry cake, lemon tart, three pastel macarons, cupcake, ring donut, pudding, croissant and soft serve. Their shared flash/reveal, starry-eyed lowered presentation, overhead plate, lowered food, puffed-cheek chewing, empty plate/hearts, cheek touch and hands-behind return remain present.
- Overhead05/06 retain readable chef toque below the plate, full supporting arms, whole food and contained sparkle effects. Neither plate nor hands are cropped; the face retains the approved identity.04→05→06→07 now stages the apparent zoom through the0.87 lowered poses. The camera change remains visible in stills; root's actual playback subsequently accepted this intentional staged change, with no continuous pose interpolation claimed.
- Green macaron is visibly opaque in all03–07 presentations. Native end3_06 shows its restored pastel-green bottom macaron on dark background, without the prior transparent hole.
- End9 retains burnt heap, surprise/disappointment, tentative taste, grimace/tongue-out blue-face reaction, recovery and hidden props. End10 retains whole-lemon surprise, inspection/ellipsis, reassurance/heart and hidden props. Their normal poses match the enlarged normal camera rather than the overhead camera.
- White chef jacket/face interiors are clean in the viewed contacts. Intended magic highlights, blush, nausea blue-face and food details are distinguished from accidental stains.

## Required static repair found and resolved

**`pastry1_end8_04.png` contains a small detached red fragment below its shoes.** Native inspection confirms it is not part of the character/food. The raw2x2 sheet has the bottom-left soft-serve cherry stem crossing above its horizontal quadrant boundary; that stem fragment survives in top-left frame04.

The final character's actual opaque shoe bottom is y484, while the detached fragment has9 alpha>100 pixels at y496–497. Camera registration therefore used the fragment as baseline and placed the whole character about13px too high. This can produce foot movement at04→05/07. An automatic check comparing the largest opaque component bottom with all opaque pixels across all158 PNGs found only this frame with a difference greater than3px; the other157 did not have this bottom-fragment pattern.

Root was notified immediately and completed the scoped repair. [Repair evidence](../configs/pastry1_end8_cell_spill_repair.json) records removal of25 source spill-alpha pixels,13 opaque, from an immutable before input; every non-spill source pixel remains exact. Root re-registered the clean source with the existing camera, refreshed exact anchors, re-encoded and audited end8.

Independent post-repair verification actually viewed native512 frame04 and the refreshed full12-frame end8 contact. The fragment is absent and the real shoe bottom is now y497. Repeating the largest-component/all-opaque-bottom comparison across all158 current PNGs found **zero** bottom-fragment issues above the3px threshold. All158 are512 RGBA with zero alpha on every canvas edge; no canvas-boundary contact remains.

The exact inventory was refreshed only after comparing all158 PNG and13 video hashes against the initial review. **Only end8 frame04 and the end8 video changed**; the other157 PNGs and12 videos remain byte-identical. Updated frame04 SHA-256: `ed678d7554636f212dfa8d6cc37c535febe6c595e853aefb1474da3d1efd1530`; updated end8 video SHA-256: `720b289614514237be0addeb3e5682eba1a7a6ed08eed0c26bde0c7e53ef7efb`.

**All13 clips now pass this stated static review scope.** No remaining required static image repair was observed. This conclusion is bound to the refreshed inventory and retains the runtime limits below.

## Review limits

All13 contacts/158 slots were actually viewed, with selected native512 checks and source comparisons as stated. Tiny edge signals may not be visible at contact resolution; this report does not substitute for the technical alpha/hash audit. Normal0.96, presentation0.87 and overhead0.9594 are uniform image transforms, so this review found no new independent head/body squash or gesture deletion. Temporal camera behavior, playback, central approval and local docs integration were reviewed by root, not by this static reviewer.

Root's completed follow-up: [actual scoped DOM proof](pastry_scale_runtime_dom_20260930.json) finished at2026-09-30T11:28:09.721Z with11 cases passed,0 failed,14 videos covered and no missing clips, including explicit idle completion plus all10 endings. Actual14 runtime hashes and current13 video/158 PNG hashes were verified; original assets and unchanged26 prior-runtime hashes remain exact. [Actual-canvas evidence](pastry_scale_canvas_review_20260930.json) records ending3 with146 snapshots/8 boundaries/9300ms: normal→lowered→overhead→lowered→normal at0.361–1.600, end/outro at0.097–0.189 and idle return. Root directly observed clean whole-hand/plate/food headroom in [the overhead screenshot](pastry_scale_actual_overhead.png), without cropping. The camera adjustment remains intentionally visible and discrete between preserved poses rather than continuously interpolated. Root approved current13 central review/status/finalReview hash bindings and completed the reviewed-only docs dry-run/actual recopy of39 videos/8307KB. These scoped actual observations complement all13 static contacts and all10 ending runtime coverage; they do not claim dense actual-canvas inspection of every ending. No remote publication was performed.

Root subsequently verified all39 docs video hashes, byte-identical widget/docs HTML and all39 reviewed flags, with UTF-8 runtime JavaScript syntax and git diff check passing. The runtime proof now records finalApprovedManifestSha256, localDocs and finalChecks; [actual browser comparison](pastry_scale_browser_comparison.png) preserves ending9 frame03. This is root integration evidence, separate from the static review above.
