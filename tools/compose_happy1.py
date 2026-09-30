"""Compose happy1 start/loop/end from 2 generated key poses + the idle base.

start: base -> hands rising -> hands clasped   (6 frames)
loop : clasped pose swaying by rotation about the feet, 18 frames
end  : clasped -> hands rising -> base          (6 frames)
"""
import argparse
from pathlib import Path
from PIL import Image
from compose_anim import bbox, match_to_base

BASE = "sprites/idle1_loop/idle1_loop_00.png"
POSE_MID = "sprites/happy1_poses/happy1_pose_00.png"
POSE_FULL = "sprites/happy1_poses/happy1_pose_01.png"
OUTDIR = "sprites/happy1"

import math
N_LOOP = 18  # @10fps = 1.8s, seamless sine sway
SWAY = [2.4 * math.sin(2 * math.pi * i / N_LOOP) for i in range(N_LOOP)]
BOUNCE = [-1.2 * abs(math.sin(2 * math.pi * i / N_LOOP)) for i in range(N_LOOP)]


def sway_frame(img: Image.Image, deg: float, dy: float,
               pivot_y: int) -> Image.Image:
    f = img.rotate(deg, resample=Image.BICUBIC, center=(img.width / 2, pivot_y)) if deg else img
    if dy:
        f = f.transform(f.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy),
                        resample=Image.BILINEAR)
    return f


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=BASE)
    parser.add_argument("--mid", default=POSE_MID)
    parser.add_argument("--full", default=POSE_FULL)
    parser.add_argument("--outdir", type=Path, default=Path(OUTDIR))
    parser.add_argument("--split-parts", action="store_true")
    args = parser.parse_args()
    def save(frame, part, index):
        outdir = args.outdir / f"happy1_{part}" if args.split_parts else args.outdir
        outdir.mkdir(parents=True, exist_ok=True)
        frame.save(outdir / f"happy1_{part}_{index:02d}.png")
    base = Image.open(args.base).convert("RGBA")
    mid = match_to_base(Image.open(args.mid).convert("RGBA"), base)
    full = match_to_base(Image.open(args.full).convert("RGBA"), base)
    _, _, _, foot_y = bbox(base)

    # start/end: 6 frames @10fps = 0.6s (동일 타이밍, 프레임 2배)
    for i, f in enumerate([base, base, mid, mid, full, full]):
        save(f, "start", i)
    for i, (deg, dy) in enumerate(zip(SWAY, BOUNCE)):
        save(sway_frame(full, deg, dy, foot_y), "loop", i)
    for i, f in enumerate([full, full, mid, mid, base, base]):
        save(f, "end", i)
    print("composed happy1: 6 start + 18 loop + 6 end")


if __name__ == "__main__":
    main()
