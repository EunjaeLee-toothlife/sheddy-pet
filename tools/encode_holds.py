"""Encode a keyed PNG sequence into a VP9+alpha WebM, holding selected frames.

Reads anims/<name>.json for the optional "holds" map:
    "holds": {"3": 3, "4": 3, "5": 2}   # frame index -> number of ticks
Frames not listed are shown for 1 tick. The sequence is expanded by
repeating each PNG `ticks` times and encoded at --fps, so a reaction beat
can be held longer without generating new frames (cheaper than regenerating
and keeps the flash/impact frames snappy while the reveal lingers).

Optional "repeats" plays a frame RANGE several times in a row (rapid-fire
punches, a shake, a double-take) — again without generating new frames:
    "repeats": [{"frames": [2, 3], "times": 4}]   # 2,3,2,3,2,3,2,3
Ranges are inclusive; holds apply inside each repetition.

usage: python tools/encode_holds.py anims/pastry1_end1.json [--fps 10]
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import tempfile


def main():
    p = argparse.ArgumentParser()
    p.add_argument("config")
    p.add_argument("--fps", type=int, default=10)
    p.add_argument("--frames-dir", default=None,
                   help="default sprites/<name>")
    p.add_argument("--out", default=None,
                   help="default sprites/anim_<name>.webm")
    a = p.parse_args()

    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)
    name = cfg["name"]
    holds = {int(k): int(v) for k, v in cfg.get("holds", {}).items()}
    repeats = {r["frames"][0]: (r["frames"][1], int(r["times"]))
               for r in cfg.get("repeats", [])}
    src_dir = a.frames_dir or os.path.join("sprites", name)
    out = a.out or os.path.join("sprites", f"anim_{name}.webm")

    frames = sorted(glob.glob(os.path.join(src_dir, f"{name}_*.png")))
    if not frames:
        raise SystemExit(f"no frames in {src_dir}")

    tmp = tempfile.mkdtemp(prefix=f"{name}_holds_")
    try:
        # expand frame order: repeated ranges first, then per-frame holds
        order = []
        i = 0
        while i < len(frames):
            if i in repeats:
                end, times = repeats[i]
                order += list(range(i, end + 1)) * max(1, times)
                i = end + 1
            else:
                order.append(i)
                i += 1
        n = 0
        for i in order:
            for _ in range(max(1, holds.get(i, 1))):
                shutil.copy(frames[i], os.path.join(tmp, f"f_{n:03d}.png"))
                n += 1
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps),
             "-i", os.path.join(tmp, "f_%03d.png"),
             "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0",
             "-crf", "24", "-an", out], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"{out}: {len(frames)} frames -> {n} ticks "
          f"({n / a.fps:.1f}s @{a.fps}fps)")


if __name__ == "__main__":
    main()
