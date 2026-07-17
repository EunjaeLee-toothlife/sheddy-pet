"""Compose happy1 start/loop/end from 2 generated key poses + the idle base.

start: base -> hands rising -> hands clasped   (3 frames)
loop : clasped pose swaying by rotation about the feet, 9 frames, seamless
end  : clasped -> hands rising -> base          (3 frames)
"""
import os
import numpy as np
from PIL import Image

BASE = "sprites/idle1_loop/idle1_loop_00.png"
POSE_MID = "sprites/happy1_poses/happy1_pose_00.png"
POSE_FULL = "sprites/happy1_poses/happy1_pose_01.png"
OUTDIR = "sprites/happy1"

import math
N_LOOP = 18  # @10fps = 1.8s, seamless sine sway
SWAY = [2.4 * math.sin(2 * math.pi * i / N_LOOP) for i in range(N_LOOP)]
BOUNCE = [-1.2 * abs(math.sin(2 * math.pi * i / N_LOOP)) for i in range(N_LOOP)]


def bbox(img):
    a = np.asarray(img)[..., 3]
    ys, xs = np.nonzero(a > 10)
    return xs.min(), ys.min(), xs.max(), ys.max()


def match_to_base(img: Image.Image, base: Image.Image) -> Image.Image:
    """Scale/translate img so its bbox height, foot line and horizontal
    center match the base sprite (keeps feet planted)."""
    bx0, by0, bx1, by1 = bbox(base)
    x0, y0, x1, y1 = bbox(img)
    s = (by1 - by0) / (y1 - y0)
    w, h = img.size
    scaled = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    sx0, sy0, sx1, sy1 = bbox(scaled)
    dx = round((bx0 + bx1) / 2 - (sx0 + sx1) / 2)
    dy = round(by1 - sy1)
    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    out.paste(scaled, (dx, dy), scaled)
    return out


def sway_frame(img: Image.Image, deg: float, dy: float,
               pivot_y: int) -> Image.Image:
    f = img.rotate(deg, resample=Image.BICUBIC, center=(256, pivot_y))
    if dy:
        f = f.transform(f.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy),
                        resample=Image.BILINEAR)
    return f


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    base = Image.open(BASE).convert("RGBA")
    mid = match_to_base(Image.open(POSE_MID).convert("RGBA"), base)
    full = match_to_base(Image.open(POSE_FULL).convert("RGBA"), base)
    _, _, _, foot_y = bbox(base)

    # start/end: 6 frames @10fps = 0.6s (동일 타이밍, 프레임 2배)
    for i, f in enumerate([base, base, mid, mid, full, full]):
        f.save(f"{OUTDIR}/happy1_start_{i:02d}.png")
    for i, (deg, dy) in enumerate(zip(SWAY, BOUNCE)):
        sway_frame(full, deg, dy, foot_y).save(
            f"{OUTDIR}/happy1_loop_{i:02d}.png")
    for i, f in enumerate([full, full, mid, mid, base, base]):
        f.save(f"{OUTDIR}/happy1_end_{i:02d}.png")
    print("composed happy1: 6 start + 18 loop + 6 end")


if __name__ == "__main__":
    main()
