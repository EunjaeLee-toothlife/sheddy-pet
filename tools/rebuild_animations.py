"""Prepare original-pose sheets and ingest ImageGen edits, preserving clip timing.

Image generation itself is performed through Codex's built-in ImageGen tool.
This script only assembles inputs, invokes existing matte/encoding tools and
records evidence. Generated output is kept separate until all clips pass QA.
"""
import argparse
import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "anims/rebuild_manifest.json"


def read_manifest(path=MANIFEST):
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(data, path=MANIFEST):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare(clip):
    cols, rows = clip["cols"], clip["rows"]
    sheet = Image.new("RGBA", (cols * 512, rows * 512), (0, 255, 0, 255))
    for i, source in enumerate(clip["frames"]):
        frame = Image.open(ROOT / source).convert("RGBA")
        if frame.size != (512, 512):
            raise ValueError(f"unexpected source frame size: {source} {frame.size}")
        sheet.alpha_composite(frame, ((i % cols) * 512, (i // cols) * 512))
    path = ROOT / "sprites/rebuilt/inputs" / f"{clip['clip']}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(path)
    return path


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_name,width,height:stream_tags=alpha_mode:format=duration",
        "-of", "json", str(path)], text=True))


def pixel_invariants(clip, frames):
    rules = clip.get("pixelInvariants")
    if not rules:
        return {}
    base = np.asarray(Image.open(ROOT / rules["base"]).convert("RGBA"))
    indices = rules.get("canonicalFrames", [])
    for index in indices:
        if not np.array_equal(np.asarray(Image.open(frames[index])), base):
            raise ValueError(f"canonical transition frame changed: {frames[index]}")
    result = {"canonicalFramesExact": indices}
    if "stableOutsideRect" in rules:
        from compose_talk import rect_mask
        mask = rect_mask(base.shape[:2], rules["stableOutsideRect"], rules["feather"])[..., 0]
        for frame in frames:
            if not np.array_equal(np.asarray(Image.open(frame))[mask == 0], base[mask == 0]):
                raise ValueError(f"pixels outside local edit changed: {frame}")
        result["outsideEditPixelsExact"] = True
    return result


def audit(clip):
    if len(clip["frames"]) != clip["count"] or len(clip["sourceFrameHashes"]) != clip["count"]:
        raise ValueError("source frame ledger is incomplete")
    for source, expected in zip(clip["frames"], clip["sourceFrameHashes"]):
        if hashlib.sha256((ROOT / source).read_bytes()).hexdigest() != expected:
            raise ValueError(f"original source was changed: {source}")
    if hashlib.sha256((ROOT / clip["webm"]).read_bytes()).hexdigest() != clip["sourceVideoHash"]:
        raise ValueError(f"original video was changed: {clip['webm']}")
    if not clip.get("candidate"):
        return
    outdir = ROOT / "sprites/rebuilt/frames" / clip["clip"]
    frames = sorted(outdir.glob("*.png"))
    if len(frames) != clip["count"]:
        raise ValueError("candidate frame count differs from source")
    if [frame.name for frame in frames] != [f"{clip['clip']}_{i:02d}.png" for i in range(clip["count"])]:
        raise ValueError("candidate frame filenames or index sequence changed")
    evidence = []
    clipped = []
    for path in frames:
        im = Image.open(path)
        if im.mode != "RGBA" or im.size != (512, 512) or im.getbbox() is None:
            raise ValueError(f"invalid candidate: {path}")
        if im.getchannel("A").getextrema()[0] != 0:
            raise ValueError(f"candidate has no transparent pixels: {path}")
        alpha = np.asarray(im)[..., 3]
        if np.any(alpha[0] > 10) or np.any(alpha[-1] > 10) or np.any(alpha[:, 0] > 10) or np.any(alpha[:, -1] > 10):
            clipped.append(path.name)
        evidence.append({"file": path.name, "bbox": list(im.getbbox()),
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    video = ROOT / clip["candidate"]
    result = probe(video)
    stream = result["streams"][0]
    if stream["width"] != 512 or stream["height"] != 512 or stream.get("tags", {}).get("alpha_mode") != "1":
        raise ValueError("candidate video geometry or alpha failed")
    if abs(float(result["format"]["duration"]) - clip["sourceDuration"]) > 0.015:
        raise ValueError("candidate duration differs from source")
    # The metadata tag alone does not prove that VP9 contains usable alpha.
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(video),
        "-f", "rawvideo", "-pix_fmt", "rgba", "pipe:1"])
    decoded = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 512, 512, 4)
    expected_ticks = round(clip["sourceDuration"] * clip["fps"])
    if len(decoded) != expected_ticks:
        raise ValueError("decoded video tick count changed")
    alpha = decoded[..., 3]
    if not np.all(alpha.min(axis=(1, 2)) == 0) or not np.all(alpha.max(axis=(1, 2)) == 255):
        raise ValueError("decoded video lost transparent background or opaque foreground")
    corners = alpha[:, [0, 0, -1, -1], [0, -1, 0, -1]]
    seam_anchors = clip.get("seamAnchors", [])
    for anchor in seam_anchors:
        own = np.asarray(Image.open(frames[anchor["ownFrame"]]).convert("RGBA"))
        other = np.asarray(Image.open(ROOT / anchor["otherFrame"]).convert("RGBA"))
        if not np.array_equal(own, other):
            raise ValueError(f"transition anchor changed: {clip['clip']} -> {anchor['otherFrame']}")
    clip["evidence"] = {"probe": result, "frameCount": len(frames), "timingPreserved": True,
                        "frames": evidence, "originalsUnchanged": True,
                        "videoSha256": hashlib.sha256(video.read_bytes()).hexdigest(),
                        "framesTouchingCanvas": clipped,
                        "exactSeamAnchors": seam_anchors,
                        "decodedAlpha": {"decoder": "libvpx-vp9", "frames": len(decoded),
                                         "allCornersTransparent": bool(np.all(corners == 0)),
                                         "allFramesOpaqueForeground": True},
                        "pixelInvariants": pixel_invariants(clip, frames)}


def ingest(clip, source, preserve_alpha=False):
    name = clip["clip"]
    raw = ROOT / "sprites/rebuilt/sheets" / f"{name}.png"
    raw.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, raw)
    outdir = ROOT / "sprites/rebuilt/frames" / name
    outdir.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, str(ROOT / "tools/slice_and_key.py"),
            "--sheet", str(raw), "--cols", str(clip["cols"]), "--rows", str(clip["rows"]),
            "--outdir", str(outdir), "--prefix", name, "--no-align", "--no-scale-norm"]
    if preserve_alpha:
        args.append("--preserve-alpha")
    subprocess.run(args, cwd=ROOT, check=True)
    # Padding cells are not animation frames and must not reach the encoder.
    for i in range(clip["count"], clip["cols"] * clip["rows"]):
        (outdir / f"{name}_{i:02d}.png").unlink()
    clip["sheet"] = raw.relative_to(ROOT).as_posix()
    encode(clip)


def encode(clip):
    """Encode already reconstructed PNGs without overwriting composed frames."""
    name = clip["clip"]
    outdir = ROOT / "sprites/rebuilt/frames" / name
    config = ROOT / "sprites/rebuilt/configs" / f"{name}.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({"name": name, "holds": clip["holds"], "repeats": clip["repeats"]}), encoding="utf-8")
    # Source durations include holds/repeats. Derive FPS from expanded ticks
    # rather than silently assuming every existing clip was encoded at 10 FPS.
    repeats = {r["frames"][0]: r for r in clip["repeats"]}
    order, i = [], 0
    while i < clip["count"]:
        if i in repeats:
            r = repeats[i]
            order.extend(list(range(i, r["frames"][1] + 1)) * max(1, int(r["times"])))
            i = r["frames"][1] + 1
        else:
            order.append(i)
            i += 1
    ticks = sum(max(1, int(clip["holds"].get(str(i), 1))) for i in order)
    fps = round(ticks / clip["sourceDuration"])
    if abs(ticks / fps - clip["sourceDuration"]) > 0.015:
        raise ValueError(f"cannot reproduce source timing: ticks={ticks}, duration={clip['sourceDuration']}")
    video = ROOT / "sprites/rebuilt/videos" / Path(clip["webm"]).name
    video.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(ROOT / "tools/encode_holds.py"), str(config),
                    "--frames-dir", str(outdir), "--out", str(video), "--fps", str(fps)], cwd=ROOT, check=True)
    result = probe(video)
    stream = result["streams"][0]
    if stream.get("tags", {}).get("alpha_mode") != "1":
        raise ValueError("encoded clip has no alpha_mode tag")
    if abs(float(result["format"]["duration"]) - clip["sourceDuration"]) > 0.015:
        raise ValueError("encoded duration changed")
    frames = sorted(outdir.glob("*.png"))
    if len(frames) != clip["count"]:
        raise ValueError("output frame count changed")
    frame_evidence = []
    for frame in frames:
        im = Image.open(frame)
        if im.mode != "RGBA" or im.size != (512, 512) or im.getchannel("A").getextrema()[0] != 0:
            raise ValueError(f"invalid keyed frame: {frame}")
        bbox = im.getbbox()
        if bbox is None:
            raise ValueError(f"empty animation cell: {frame}")
        frame_evidence.append({"file": frame.name, "bbox": list(bbox)})
    clip.update(status="generated", candidate=video.relative_to(ROOT).as_posix(), fps=fps)
    clip["review"]["alpha"] = True
    clip["evidence"] = {"probe": result, "frameCount": clip["count"], "timingPreserved": True,
                        "frames": frame_evidence}
    print(f"Generated {name}: {clip['count']} frames, {ticks} ticks, {fps} FPS; visual QA pending")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "ingest", "encode", "status", "audit"])
    parser.add_argument("clip", nargs="?")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--preserve-alpha", action="store_true")
    parser.add_argument("--manifest", type=Path, default=MANIFEST,
                        help="isolated worker ledger; asset paths remain relative to repository")
    args = parser.parse_args()
    data = read_manifest(args.manifest)
    if args.action == "audit":
        selected = [c for c in data["clips"] if not args.clip or c["clip"] == args.clip]
        if not selected:
            parser.error("unknown clip")
        for clip in selected:
            audit(clip)
        save_manifest(data, args.manifest)
        print(f"Audited {len(selected)} clips: source hashes, candidate PNGs, duration and alpha metadata")
        return
    if args.action == "status":
        counts = {}
        for clip in data["clips"]:
            counts[clip["status"]] = counts.get(clip["status"], 0) + 1
        print(json.dumps({"clips": len(data["clips"]), "frames": sum(c["count"] for c in data["clips"]), "status": counts}))
        return
    matches = [c for c in data["clips"] if c["clip"] == args.clip]
    if len(matches) != 1:
        parser.error("specify one clip from the manifest")
    clip = matches[0]
    if args.action == "prepare":
        print(prepare(clip))
    elif args.action == "encode":
        encode(clip)
        save_manifest(data, args.manifest)
    elif args.source is None:
        parser.error("ingest requires --source")
    else:
        ingest(clip, args.source, args.preserve_alpha)
        save_manifest(data, args.manifest)


if __name__ == "__main__":
    main()
