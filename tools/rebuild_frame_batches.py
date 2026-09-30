"""Prepare/ingest at most four ImageGen animation poses at full cell resolution.

Only assemble, chroma-key and place generated cells; generation uses Codex.
Run encode/audit from rebuild_animations.py once the entire clip is staged.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "anims/rebuild_manifest.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "ingest"])
    parser.add_argument("clip")
    parser.add_argument("--indices", type=int, nargs="+", required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--keep-components", action="store_true")
    parser.add_argument("--green-region", nargs=4, type=int)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    clips = [c for c in data["clips"] if c["clip"] == args.clip]
    if len(clips) != 1:
        parser.error("unknown clip")
    clip = clips[0]
    indices = args.indices
    if not 1 <= len(indices) <= 4 or len(set(indices)) != len(indices) or any(i < 0 or i >= clip["count"] for i in indices):
        parser.error("select one to four unique valid source indices")
    name = args.clip + "_" + "-".join(f"{i:02d}" for i in indices)
    if args.action == "prepare":
        sheet = Image.new("RGBA", (1024, 1024), (0, 255, 0, 255))
        for cell, index in enumerate(indices):
            sprite = Image.open(ROOT / clip["frames"][index]).convert("RGBA")
            if sprite.size != (512, 512):
                raise ValueError("source dimensions changed")
            sheet.alpha_composite(sprite, ((cell % 2) * 512, (cell // 2) * 512))
        target = ROOT / "sprites/rebuilt/inputs" / (name + ".png")
        target.parent.mkdir(parents=True, exist_ok=True)
        sheet.convert("RGB").save(target)
        print(target)
        return
    if args.source is None:
        parser.error("ingest requires --source")
    with Image.open(args.source) as source:
        if source.width != source.height or source.width < 1024:
            raise ValueError("2x2 generated grid must be square and at least 1024px")
    raw = ROOT / "sprites/rebuilt/sheets" / (name + ".png")
    raw.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.source, raw)
    donors = ROOT / "sprites/rebuilt/poses/batches" / name
    command = [sys.executable, str(ROOT / "tools/slice_and_key.py"), "--sheet", str(raw),
               "--cols", "2", "--rows", "2", "--outdir", str(donors), "--prefix", "cell",
               "--no-align", "--no-scale-norm"]
    if args.keep_components:
        command.append("--keep-components")
    if args.green_region:
        command.extend(['--green-region', *map(str, args.green_region)])
    subprocess.run(command, cwd=ROOT, check=True)
    outdir = ROOT / "sprites/rebuilt/frames" / args.clip
    outdir.mkdir(parents=True, exist_ok=True)
    for cell, index in enumerate(indices):
        shutil.copyfile(donors / f"cell_{cell:02d}.png", outdir / f"{args.clip}_{index:02d}.png")
    batches = clip.setdefault("frameBatches", [])
    batches[:] = [b for b in batches if b["indices"] != indices]
    batches.append({"indices": indices, "source": raw.relative_to(ROOT).as_posix(),
                    "cols": 2, "rows": 2, "keepComponents": args.keep_components,
                    "greenRegion": args.green_region})
    clip["review"] = {key: False for key in clip["review"]}
    clip["status"] = "staged"
    clip.pop("candidate", None)
    clip.pop("evidence", None)
    clip.pop("browserEvidence", None)
    args.manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Staged {args.clip} frames {indices}; encode and visual QA still required")


if __name__ == "__main__":
    main()
