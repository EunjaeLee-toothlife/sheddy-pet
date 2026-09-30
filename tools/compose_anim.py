"""Generic animation composer: build start/loop/end frames from a base
sprite + a few keyed key-pose sprites, per a JSON plan.

Plan format (anims/<name>_plan.json):
{
  "name": "basic1",
  "base": "sprites/idle1_donor/donor_00.png",
  "poses": { "left": "sprites/basic1_poses/basic1_pose_00.png", ... },
  "match_to_base": true,          // scale/foot-align poses to the base
  "parts": {
    "loop": [ {"img": "base", "deg": 0, "dx": 0, "dy": 0}, ... ],
    "start": [...], "end": [...]   // optional
  }
}
"img" refers to "base" or a key in poses. deg rotates about the feet pivot.
Frames are written to sprites/<name>/<name>_<part>_NN.png.
"""
import argparse
import json
import os
import numpy as np
from PIL import Image


def bbox(img):
    a = np.asarray(img)[..., 3]
    ys, xs = np.nonzero(a > 10)
    return xs.min(), ys.min(), xs.max(), ys.max()


def foot_center(img):
    """Center of the bottom shoe band; excludes asymmetric arms and effects."""
    a = np.asarray(img)[..., 3]
    _, _, _, bottom = bbox(img)
    _, xs = np.nonzero(a[max(0, bottom - 20):bottom + 1] > 10)
    return (xs.min() + xs.max()) / 2


def match_to_base(img: Image.Image, base: Image.Image,
                  do_scale: bool = True, scale_override=None,
                  center_on_feet=False) -> Image.Image:
    """Translate (and optionally scale) img so bbox height, foot line and
    horizontal center match the base sprite (keeps feet planted).
    Set do_scale=False for poses whose silhouette height legitimately
    differs (e.g. arms stretched overhead)."""
    bx0, by0, bx1, by1 = bbox(base)
    x0, y0, x1, y1 = bbox(img)
    s = (by1 - by0) / (y1 - y0) if do_scale else 1.0
    if scale_override is not None:
        s = float(scale_override)
        if not np.isfinite(s) or s <= 0:
            raise ValueError("pose scale must be finite and positive")
    w, h = img.size
    scaled = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    sx0, sy0, sx1, sy1 = bbox(scaled)
    dx = round((bx0 + bx1) / 2 - (sx0 + sx1) / 2)
    if center_on_feet:
        dx = round(foot_center(base) - foot_center(scaled))
    dy = round(by1 - sy1)
    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    out.alpha_composite(scaled, (dx, dy))
    return out


def render(img: Image.Image, deg: float, dx: float, dy: float,
           pivot) -> Image.Image:
    f = img
    if deg:
        f = f.rotate(deg, resample=Image.BICUBIC, center=pivot)
    if dx or dy:
        f = f.transform(f.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy),
                        resample=Image.BILINEAR)
    return f


def main():
    p = argparse.ArgumentParser()
    p.add_argument("plan")
    p.add_argument("--outdir", help="override the default sprites/<name> output directory")
    a = p.parse_args()
    with open(a.plan, encoding="utf-8") as f:
        plan = json.load(f)

    name = plan["name"]
    base = Image.open(plan["base"]).convert("RGBA")
    sprites = {"base": base}
    no_scale = set(plan.get("no_scale_poses", []))
    anchor = plan.get("horizontal_anchor", "silhouette")
    if anchor not in ("silhouette", "feet"):
        raise ValueError("unknown horizontal anchor")
    for key, path in plan.get("poses", {}).items():
        img = Image.open(path).convert("RGBA")
        if plan.get("match_to_base", True):
            img = match_to_base(img, base, do_scale=key not in no_scale,
                                scale_override=plan.get("pose_scales", {}).get(key),
                                center_on_feet=anchor == "feet")
        sprites[key] = img

    _, _, _, foot_y = bbox(base)
    pivot = (base.width / 2, int(foot_y))
    outdir = a.outdir or f"sprites/{name}"
    os.makedirs(outdir, exist_ok=True)
    for part, frames in plan["parts"].items():
        for i, fr in enumerate(frames):
            img = sprites[fr["img"]]
            out = render(img, fr.get("deg", 0), fr.get("dx", 0),
                         fr.get("dy", 0), pivot)
            out.save(f"{outdir}/{name}_{part}_{i:02d}.png")
        print(f"{name}_{part}: {len(frames)} frames")


if __name__ == "__main__":
    main()
