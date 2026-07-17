"""Generate animation frames one image at a time from a JSON config.

Each frame is generated as an individual 1:1 image using a fixed base
reference image, then post-processed with slice_and_key.py --frames.

Config format (anims/<name>.json):
{
  "name": "idle1_loop",
  "ref": "refs/chibi_base.png",
  "frames": ["pose description for frame 0", "..."]
}
"""
import argparse
import json
import os
import subprocess
import sys

GEN = os.path.expanduser(
    "~/.claude/skills/lite-image/scripts/generate_image_v2.py")

PREAMBLE = (
    "Single frame of a sprite animation. One cute chibi character, full body "
    "from the top of the head to the soles of her shoes fully visible, centered, "
    "occupying about 60% of image height, generous empty margin on all sides, "
    "front-facing, standing on an invisible floor, solid pure green chroma-key "
    "background (#00FF00), no text, no borders. Exactly the same character, "
    "outfit, proportions, art style, outline thickness and line weight as the "
    "reference image."
)

CHARACTER = (
    "a cute chibi girl (2.5-head proportion), long blonde hair, big yellow-gold "
    "eyes, small lemon-slice hair clip, oversized white lab coat with rolled "
    "sleeves over a white button-up shirt, pastel yellow pleated mini skirt with "
    "a lemon print, white crew socks, brown penny loafers."
)

STYLE = (
    "[STYLE] high-quality anime, clean vector linework, bold thick dark-brown "
    "outline around the entire character silhouette, consistent heavy line "
    "weight, crisp hard edges against the background, no glow, no outer halo, "
    "no drop shadow. soft pastel lemon palette, cozy desktop-pet mascot "
    "design, sticker-like thick contour."
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("config", help="anims/<name>.json")
    p.add_argument("--outdir", default="sprites/raw")
    p.add_argument("--only", type=int, default=None,
                   help="generate a single frame index (retry helper)")
    a = p.parse_args()

    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)
    name = cfg["name"]
    os.makedirs(a.outdir, exist_ok=True)

    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    failed = []
    for i, pose in enumerate(cfg["frames"]):
        if a.only is not None and i != a.only:
            continue
        prompt = f"{PREAMBLE} {pose} {CHARACTER} {STYLE}"
        out = os.path.join(a.outdir, f"{name}_{i:02d}.png")
        print(f"[{i + 1}/{len(cfg['frames'])}] {name}_{i:02d}", flush=True)
        r = subprocess.run(
            [sys.executable, GEN, "--prompt", prompt, "--ref", cfg["ref"],
             "--output", out, "--aspect", "1:1", "--size", "1K"],
            env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print(r.stdout[-500:], r.stderr[-500:])
            failed.append(i)
    if failed:
        print(f"FAILED frames: {failed}")
        sys.exit(1)
    print("done")


if __name__ == "__main__":
    main()
