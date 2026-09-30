# Sheddy doze1 ImageGen experiment

Provider: Codex built-in ImageGen. First two attempts used transparent
background; final accepted sheet uses opaque green plus chroma-key cleanup.
No API key or model override was used. The original animation is retained.

## Color cleanup after user review (final accepted source)

The user noticed stains inside the white coat and face. This fourth pass
edits the green-screen sheet with the original frame as a color reference.

Use case: precise-object-edit.
Edit target image 1: eight-frame 4x2 animation sprite sheet. Supporting image 2: original clean sleepy character sprite, used only as the exact color and shading reference.
Primary request: REMOVE the blotchy, mottled shading added to the hair, white lab coat and face. The sprite-sheet character currently has irregular white blobs in the blonde bangs, pink patches across the white sleeves and coat, and too much reddish glow at the outlines. Match the original image 2's restrained clean anime cel coloring.
Keep all eight poses, anatomy, expressions, grid coordinates, scale, shoe positions and lemon skirt pattern exactly unchanged. Do not add or remove intentional lemon patterns on the skirt.
Hair: even pale blonde base, simple coherent darker blonde shadow shapes, only the original understated highlight treatment, NO scattered white highlight spots, no dappled lighting.
Lab coat and shirt: clean neutral ivory/white surfaces, subtle consistent pale gray-lavender shadows only at folds, NO pink stains, NO patchy shading, no textures.
Face and legs: smooth original pale skin with only a subtle cheek blush, no white splotches, no mottled lighting.
Outlines: original uniform warm brown, no saturated red glow or fringes.
Background: completely flat opaque RGB #00FF00 green including between legs, with no gradients, noise, speckles, cast shadows or texture. No transparency in this output.
Output the same 4 columns by 2 rows, overall 2:1 sprite sheet. This is color cleanup only. The character must look like the clean original drawing, without a new rendering style.

## Green-screen cleanup alternative

The transparent-sheet attempts retained colored speckles. A third built-in
ImageGen edit uses an opaque chroma-key background instead:

Edit the supplied 4-column 2-row eight-frame Sheddy sprite sheet. Preserve all eight poses and the exact character design, grid, placement and scale. Replace transparency with a perfectly uniform solid RGB green #00FF00 background across every empty pixel including between legs, around hair and cell gaps. Clean away all stray red/yellow/white speckled background residue and ragged halos outside the character silhouette. Crisp clean brown outline, no extra white border. Preserve yellow hair, yellow skirt lemon pattern, white lab coat, white socks, brown shoes, lemon hairclip on viewer right. Maintain the 2:1 overall canvas and 4x2 square-cell layout. No text, labels, shadows or borders. Output one opaque green-screen sprite sheet for chroma-keying. Do NOT alter poses or redraw anatomy. This is background replacement and matte cleanup only.

## Initial generation

Edit the supplied existing Sheddy desktop-pet sprite into ONE production animation sprite-sheet asset.
Input image 1 is the edit target and exact identity/style anchor: existing sleepy standing sprite. Input image 2 is supporting design reference only (ignore its green background).
Create a 4-column by 2-row contact sheet, exactly eight equally sized square cells, reading left-to-right then top-to-bottom. Desired overall canvas 2048x1024 with each cell 512x512. Transparent RGBA background throughout; no cell borders, no text, no numbers, no checkerboard drawn into the pixels.
Each cell contains the SAME single full-body character at the SAME scale and placement as image 1: hair top around y=50, soles y=498 relative to its cell, center x=256. Keep generous side margins. Shoes and legs MUST stay at identical coordinates in all cells. Preserve source outfit, skirt lemon shapes, lemon hairclip on viewer RIGHT, hairstyle, white socks, brown loafers, exact warm brown line weight and soft pastel rendering. Preserve original silhouette outline thickness. Do not add sticker white borders.
Animation is a small gentle sleepy head nod and startled recovery, not a dance. Arms remain resting at sides in every cell, body below shoulders remains identical. Only eyes, brows, mouth, head angle and very small hair motion change.
Cell 1: original relaxed sleepy half-open eyes, head upright, faint smile.
Cell 2: eyes almost closed, head nodding down only slightly, shoulders still.
Cell 3: eyes closed, head tilted forward about 10 degrees, chin lower, face remains visible.
Cell 4: deepest gentle nod 15 degrees, closed eyes, head and bangs slightly lower, not huge bobble-head, no bending knees.
Cell 5: same deep nod as cell 4, sleepy paused beat.
Cell 6: head back upright, surprised open eyes and tiny o-mouth, subtle raised brows, hair remains near same silhouette (no flying strands or symbols).
Cell 7: head upright, recovering half-open sleepy eyes, soft relieved small smile, match baseline hair.
Cell 8: EXACT duplicate of cell 1 for seamless loop closure.
No glow, no shadow, no symbols, no props, no extra body parts, no perspective or camera changes. The central priority is stable sprite geometry and character consistency across all eight cells.

## Matte cleanup

undefined
