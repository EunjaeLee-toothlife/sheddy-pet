"""Slice a grid sprite sheet into 512px tiles, chroma-key green to alpha,
and optionally align frames by alpha centroid to remove positional jitter."""
import argparse
import numpy as np
from PIL import Image


def bbox_height(img: Image.Image):
    a = np.asarray(img)[..., 3]
    ys = np.nonzero(a > 10)[0]
    return int(ys.max() - ys.min()) if len(ys) else 0


def normalize_scale(frames, tol=0.12):
    """Resize frames so alpha-bbox heights match the median height.
    Deviations beyond tol are treated as intentional pose changes and skipped."""
    heights = [bbox_height(f) for f in frames]
    valid = [h for h in heights if h > 0]
    if not valid:
        return frames
    target = float(np.median(valid))
    out = []
    for f, h in zip(frames, heights):
        s = target / h if h else 1.0
        if h == 0 or abs(s - 1.0) > tol or abs(s - 1.0) < 0.002:
            out.append(f)
            continue
        w, ht = f.size
        scaled = f.resize((round(w * s), round(ht * s)), Image.LANCZOS)
        canvas = Image.new("RGBA", f.size, (0, 0, 0, 0))
        canvas.paste(scaled, ((w - scaled.width) // 2, (ht - scaled.height) // 2), scaled)
        out.append(canvas)
    return out


def phase_offset(ref_a: np.ndarray, img_a: np.ndarray):
    """Sub-pixel (dx, dy) that moves img to best overlap ref (phase correlation)."""
    F = np.fft.fft2(ref_a)
    G = np.fft.fft2(img_a)
    R = F * np.conj(G)
    R /= np.abs(R) + 1e-9
    c = np.fft.ifft2(R).real
    py, px = np.unravel_index(np.argmax(c), c.shape)
    h, w = c.shape

    def parabola(vm, v0, vp):
        d = vm - 2 * v0 + vp
        return 0.0 if d == 0 else 0.5 * (vm - vp) / d

    sub_y = parabola(c[(py - 1) % h, px], c[py, px], c[(py + 1) % h, px])
    sub_x = parabola(c[py, (px - 1) % w], c[py, px], c[py, (px + 1) % w])
    dy = py + sub_y
    dx = px + sub_x
    if dy > h / 2:
        dy -= h
    if dx > w / 2:
        dx -= w
    return dx, dy


def subpixel_shift(img: Image.Image, dx: float, dy: float) -> Image.Image:
    return img.transform(img.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy),
                         resample=Image.BILINEAR)


# 의도적인 큰 동작(점프 등)은 정합 대상이 아님 — 이보다 큰 오프셋은 무시
MAX_REG_SHIFT = 12.0


def align_frames(frames):
    """Register every frame to the first frame with sub-pixel accuracy
    using phase correlation on the alpha channel."""
    ref_a = np.asarray(frames[0])[..., 3].astype(np.float64)
    out = [frames[0]]
    for f in frames[1:]:
        a = np.asarray(f)[..., 3].astype(np.float64)
        dx, dy = phase_offset(ref_a, a)
        if abs(dx) > MAX_REG_SHIFT or abs(dy) > MAX_REG_SHIFT:
            out.append(f)  # intentional large motion — leave as-is
            continue
        out.append(subpixel_shift(f, dx, dy))
    return out


def estimate_bg(arr: np.ndarray) -> np.ndarray:
    """Median color of border pixels (assumed chroma background)."""
    border = np.concatenate([
        arr[:8].reshape(-1, 3), arr[-8:].reshape(-1, 3),
        arr[:, :8].reshape(-1, 3), arr[:, -8:].reshape(-1, 3),
    ])
    return np.median(border, axis=0)


def erode_alpha(alpha: np.ndarray, px: int = 1) -> np.ndarray:
    """Min-filter the alpha map to pull the matte edge inward."""
    out = alpha
    for _ in range(px):
        p = np.pad(out, 1, mode="edge")
        stack = [p[dy:dy + out.shape[0], dx:dx + out.shape[1]]
                 for dy in range(3) for dx in range(3)]
        out = np.min(stack, axis=0)
    return out


def flood(mask: np.ndarray, seeds: np.ndarray) -> np.ndarray:
    """Binary flood fill: grow seeds through mask (4-connectivity)."""
    reach = seeds & mask
    while True:
        p = np.pad(reach, 1)
        grown = (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
                 | reach) & mask
        if (grown == reach).all():
            return reach
        reach = grown


def cleanup_matte(alpha: np.ndarray, rel_green: np.ndarray) -> np.ndarray:
    """Post-key matte cleanup:
    1. kill leftover green streaks/haze connected to the border
    2. remove floating debris not connected to the character body
    3. harden mushy semi-transparent alpha"""
    h, w = alpha.shape
    # 1) definite-background flood: from the border, through pixels that are
    #    mostly transparent or still green-tinted
    passable = (alpha < 0.5) | (rel_green > 0.04)
    border = np.zeros_like(passable)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    bg = flood(passable, border)
    alpha = np.where(bg, 0.0, alpha)
    # 2) keep only the component connected to the character (seed = the
    #    largest-alpha pixel, always on the body)
    body_mask = alpha > 0.05
    if body_mask.any():
        sy, sx = np.unravel_index(np.argmax(alpha), alpha.shape)
        seeds = np.zeros_like(body_mask)
        seeds[sy, sx] = True
        body = flood(body_mask, seeds)
        alpha = np.where(body_mask & ~body, 0.0, alpha)
    # 3) hard cutout: binarize the matte so soft bloom/glow halos are cut off
    #    at the contour, then re-antialias with a 1px feather
    hard = (alpha > 0.55).astype(np.float64)
    p = np.pad(hard, 1, mode="edge")
    alpha = sum(p[dy:dy + h, dx:dx + w]
                for dy in range(3) for dx in range(3)) / 9.0
    return alpha


def chroma_key(img: Image.Image, erode_px: int = 0) -> Image.Image:
    arr = np.asarray(img.convert("RGB")).astype(np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    bg = estimate_bg(arr)

    # greenness: how much G exceeds the max of R/B (absolute), plus a
    # brightness-relative version applied ONLY to dark pixels — catches
    # olive outline+green mixtures without eating the bright sticker contour
    greenness = g - np.maximum(r, b)
    brightness = np.maximum(r, np.maximum(g, b))
    lo, hi = 10.0, 80.0
    k_abs = np.clip((greenness - lo) / (hi - lo), 0.0, 1.0)
    rel = greenness / (brightness + 1.0)
    k_rel = np.clip((rel - 0.08) / (0.22 - 0.08), 0.0, 1.0)
    k_rel = np.where(brightness < 130, k_rel, 0.0)
    alpha = 1.0 - np.maximum(k_abs, k_rel)
    alpha = cleanup_matte(alpha, rel)
    # optional: pull the matte edge inward (eats thin outlines — off by default)
    if erode_px > 0:
        alpha = erode_alpha(alpha, px=erode_px)

    # un-mix: edge pixels are fg*a + bg*(1-a); recover fg = (px - (1-a)*bg) / a.
    # Only where alpha >= 0.5 (true-alpha division is stable there); lower-alpha
    # pixels keep their color — they are nearly invisible and over-division
    # produces purple fringes.
    a3 = alpha[..., None]
    unmixed = (arr - (1.0 - a3) * bg) / np.maximum(a3, 0.5)
    fg = np.where((a3 >= 0.5) & (a3 < 1.0), unmixed, arr).clip(0, 255)

    # despill: clamp excess green toward max(R,B) — on semi pixels AND on a
    # band within a few px of the matte edge, where the source art itself has
    # baked-in green spill (e.g. greenish tint on the white sticker contour)
    edge_band = erode_alpha(alpha, px=3) < 1.0
    fr, fgc, fb = fg[..., 0], fg[..., 1], fg[..., 2]
    limit = np.maximum(fr, fb)
    spill = (fgc > limit) & ((alpha < 1.0) | edge_band)
    fg[..., 1] = np.where(spill, limit, fgc)
    # green spill also depresses B, leaving a khaki tint after the G clamp —
    # partially restore B toward min(R, G) on the same pixels
    fg[..., 2] = np.where(spill, np.maximum(fb, np.minimum(fr, fg[..., 1]) - 12),
                          fb)

    out = np.concatenate([fg, alpha[..., None] * 255.0], axis=-1)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def main():
    p = argparse.ArgumentParser()
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--sheet", help="grid sprite sheet to slice")
    src.add_argument("--frames", help="glob of individual frame images "
                                      "(e.g. 'sprites/raw/idle1_*.png')")
    p.add_argument("--cols", type=int)
    p.add_argument("--rows", type=int)
    p.add_argument("--tile", type=int, default=512)
    p.add_argument("--outdir", required=True)
    p.add_argument("--prefix", default="frame")
    p.add_argument("--no-align", action="store_true",
                   help="skip centroid alignment across frames")
    p.add_argument("--no-scale-norm", action="store_true",
                   help="skip bbox-height scale normalization across frames")
    p.add_argument("--erode", type=int, default=0,
                   help="pull matte edge N px inward (may eat thin outlines)")
    a = p.parse_args()

    import glob
    import os
    os.makedirs(a.outdir, exist_ok=True)
    frames = []
    if a.frames:
        paths = sorted(glob.glob(a.frames))
        if not paths:
            raise SystemExit(f"no files match {a.frames}")
        for path in paths:
            im = Image.open(path).convert("RGB")
            if im.size != (a.tile, a.tile):
                im = im.resize((a.tile, a.tile), Image.LANCZOS)
            frames.append(chroma_key(im, erode_px=a.erode))
    else:
        if not a.cols or not a.rows:
            raise SystemExit("--sheet requires --cols and --rows")
        sheet = Image.open(a.sheet).convert("RGB")
        target = (a.cols * a.tile, a.rows * a.tile)
        if sheet.size != target:
            sheet = sheet.resize(target, Image.LANCZOS)
        for row in range(a.rows):
            for col in range(a.cols):
                tile = sheet.crop((col * a.tile, row * a.tile,
                                   (col + 1) * a.tile, (row + 1) * a.tile))
                frames.append(chroma_key(tile, erode_px=a.erode))
    if not a.no_scale_norm:
        frames = normalize_scale(frames)
    if not a.no_align:
        frames = align_frames(frames)
    for n, f in enumerate(frames):
        f.save(os.path.join(a.outdir, f"{a.prefix}_{n:02d}.png"))
    print(f"saved {len(frames)} tiles -> {a.outdir}"
          + ("" if a.no_align else " (centroid-aligned)"))


if __name__ == "__main__":
    main()
