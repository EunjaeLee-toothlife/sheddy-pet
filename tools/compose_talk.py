"""Compose the talking (mouth-flap) loop: transplant ONLY the mouth region
from the talk poses onto the frozen base sprite, like the idle blink."""
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, "tools")
from slice_and_key import phase_offset  # noqa: E402

BASE = "sprites/idle1_donor/donor_00.png"
OPEN = "sprites/talk_poses/talk_pose_00.png"
HALF = "sprites/talk_poses/talk_pose_01.png"
OUT = "sprites/talk/talk_loop_{:02d}.png"

MOUTH_RECT = (222, 155, 276, 202)
FEATHER = 4

# mouth per frame: irregular flapping reads as natural chatter at 10fps
# (입 모양은 대체로 2프레임=0.2s 유지, 가끔 1프레임으로 불규칙하게)
PLAN = ["base", "half", "half", "open", "open", "half", "base", "base",
        "open", "half", "open", "open", "base", "half", "half", "open",
        "base", "half"]


def register(img: Image.Image, base: Image.Image) -> Image.Image:
    a_ref = np.asarray(base)[..., 3].astype(np.float64)
    a_img = np.asarray(img)[..., 3].astype(np.float64)
    dx, dy = phase_offset(a_ref, a_img)
    return img.transform(img.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy),
                         resample=Image.BILINEAR)


def rect_mask(size, rect, feather):
    x0, y0, x1, y1 = rect
    m = np.zeros(size, dtype=np.float64)
    m[y0:y1, x0:x1] = 1.0
    for _ in range(feather):
        p = np.pad(m, 1, mode="edge")
        m = sum(p[dy:dy + size[0], dx:dx + size[1]]
                for dy in range(3) for dx in range(3)) / 9.0
    return m[..., None]


def main():
    import os
    os.makedirs("sprites/talk", exist_ok=True)
    base_img = Image.open(BASE).convert("RGBA")
    base = np.asarray(base_img).astype(np.float64)
    mask = rect_mask(base.shape[:2], MOUTH_RECT, FEATHER)
    variants = {"base": base_img}
    for key, path in [("open", OPEN), ("half", HALF)]:
        donor = np.asarray(register(Image.open(path).convert("RGBA"),
                                    base_img)).astype(np.float64)
        merged = base * (1 - mask) + donor * mask
        variants[key] = Image.fromarray(merged.clip(0, 255).astype(np.uint8))
    for i, key in enumerate(PLAN):
        variants[key].save(OUT.format(i))
    print(f"composed {len(PLAN)} talk frames")


if __name__ == "__main__":
    main()
