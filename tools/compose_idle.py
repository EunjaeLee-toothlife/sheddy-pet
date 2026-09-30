"""Compose a perfectly stable idle loop from ONE base frame.

Blink: the closed-eye donor frame (same raw batch, keyed+registered to the
base) contributes ONLY two tight per-eye rectangles — the inter-eye gap and
bangs are untouched, so hair mismatch cannot break the face.
Breathing bob is a procedural sub-pixel vertical shift.
"""
import numpy as np
from PIL import Image
import argparse
from pathlib import Path

BASE = "sprites/idle1_donor/donor_00.png"    # open eyes (keyed raw 00)
CLOSED = "sprites/idle1_donor/donor_01.png"  # closed eyes (keyed raw 04)
OUT = "sprites/idle1_loop/idle1_loop_{:02d}.png"

EYE_RECTS = [(198, 120, 250, 184), (258, 120, 312, 184)]  # left, right
FEATHER = 4

# frame i -> (eyes, vertical bob px); 18 frames @10fps = 1.8s,
# one 0.2s blink mid-cycle
PLAN = [
    ("open", 0.0),
    ("open", -0.4),
    ("open", -0.8),
    ("open", -1.2),
    ("open", -1.6),
    ("open", -1.8),
    ("open", -1.8),
    ("closed", -1.6),
    ("closed", -1.4),
    ("open", -1.2),
    ("open", -0.9),
    ("open", -0.6),
    ("open", -0.3),
    ("open", 0.0),
    ("open", 0.3),
    ("open", 0.4),
    ("open", 0.3),
    ("open", 0.1),
]


def rect_mask(size, rects, feather):
    m = np.zeros(size, dtype=np.float64)
    for x0, y0, x1, y1 in rects:
        m[y0:y1, x0:x1] = 1.0
    for _ in range(feather):
        p = np.pad(m, 1, mode="edge")
        m = sum(p[dy:dy + size[0], dx:dx + size[1]]
                for dy in range(3) for dx in range(3)) / 9.0
    return m[..., None]


def vshift(img: Image.Image, dy: float) -> Image.Image:
    return img.transform(img.size, Image.AFFINE, (1, 0, 0, 0, 1, -dy),
                         resample=Image.BILINEAR)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=BASE)
    parser.add_argument("--closed", default=CLOSED)
    parser.add_argument("--outdir", default="sprites/idle1_loop")
    parser.add_argument("--prefix", default="idle1_loop")
    parser.add_argument("--register-closed", action="store_true",
                        help="align the donor silhouette before transplanting its eyelids")
    args = parser.parse_args()
    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    base = np.asarray(Image.open(args.base).convert("RGBA")).astype(np.float64)
    closed = np.asarray(Image.open(args.closed).convert("RGBA")).astype(np.float64)
    if args.register_closed:
        from slice_and_key import phase_offset
        dx, dy = phase_offset(base[..., 3], closed[..., 3])
        if abs(dx) > 12 or abs(dy) > 12:
            raise ValueError(f"blink donor registration exceeds limit: {dx}, {dy}")
        donor = Image.fromarray(closed.astype(np.uint8)).transform(
            (base.shape[1], base.shape[0]), Image.AFFINE,
            (1, 0, -dx, 0, 1, -dy), resample=Image.BILINEAR)
        closed = np.asarray(donor).astype(np.float64)
    mask = rect_mask(base.shape[:2], EYE_RECTS, FEATHER)
    blink = base * (1 - mask) + closed * mask
    variants = {
        "open": Image.fromarray(base.astype(np.uint8)),
        "closed": Image.fromarray(blink.clip(0, 255).astype(np.uint8)),
    }
    for i, (eye, bob) in enumerate(PLAN):
        frame = vshift(variants[eye], bob) if bob else variants[eye]
        frame.save(Path(args.outdir) / f"{args.prefix}_{i:02d}.png")
    print(f"composed {len(PLAN)} frames (tight eye-rect blink)")


if __name__ == "__main__":
    main()
