# doze1 ImageGen experiment

Branch: `codex/imagegen-doze-improvement`.

Existing `doze1` remains the default. Open `doze-comparison.html` through a
local HTTP server to compare the old and candidate clips at playback rate 0.7.
The candidate is also listed in `preview.html`.

## Assets and provenance

- Source: `sprites/raw/doze1_imagegen_sheet.png`, 4 columns by 2 rows.
- Keyed frames: `sprites/doze1_imagegen_loop/doze1_imagegen_loop_00.png` through `_07.png`.
- Video: `sprites/anim_doze1_imagegen_loop.webm`, 512x512 VP9 with alpha.
- Timing: 8 unique frame slots expanded to 14 ticks at 10 FPS, 1.4 seconds;
  2 seconds per cycle at the widget's 0.7 playback rate.
- Exact prompts: `prompts/doze1_imagegen.md`; timing: `anims/doze1_imagegen_loop.json`.
- ImageGen was invoked in Codex, not through a Python API adapter. No API key
  or explicit image-model choice was used.

The first transparent sheet and its cleanup retained colored speckles. A
third ImageGen edit replaced the background with green. User review then
identified blotchy coloring inside the coat and face. A fourth ImageGen edit
used the original sprite as a color reference to remove irregular highlights
and pink patches. This final sheet uses the existing chroma-key routine. Raw rejected attempts
remain in the Codex generated-images folder and are not project inputs.

## Rebuild from the accepted sheet (PowerShell, repository root)

```powershell
python tools/slice_and_key.py --sheet sprites/raw/doze1_imagegen_sheet.png --cols 4 --rows 2 --outdir sprites/doze1_imagegen_loop --prefix doze1_imagegen_loop --no-align --no-scale-norm
Copy-Item -LiteralPath sprites/doze1_imagegen_loop/doze1_imagegen_loop_00.png -Destination sprites/doze1_imagegen_loop/doze1_imagegen_loop_07.png
python tools/encode_holds.py anims/doze1_imagegen_loop.json
python -m http.server 8475 --bind 127.0.0.1
```

Frame 7 is copied from frame 0 so loop endpoints match exactly. The common
sheet resize preserves relative character size; per-frame bounding-box scale
normalization and whole-silhouette phase alignment are disabled because they
can compensate away intentional nodding.

`slice_and_key.py --preserve-alpha` also supports future clean RGBA inputs,
without re-keying or discarding their existing transparency. It is not used
for the accepted green-screen source.

## Verification and limits

- Exact RGBA round trip checked with partially transparent synthetic pixels.
- Legacy green-screen removal checked with opaque foreground and transparent background.
- PNG frames are 512x512 RGBA; first and last PNGs match exactly.
- FFprobe confirms VP9, alpha_mode=1 and 1.4-second duration.
- Comparison and preview JavaScript pass syntax checking.
- Browser confirms candidate video loads and plays with transparent background.

The candidate reduces outline/style changes visible in the old frames but
simplifies the action: eye rubbing and yawning are removed. The generated
head nod is weaker than requested; this is a comparison candidate, not a
validated improvement in every aspect. No widget default, Pages payload or
release version has been changed.
