"""Generate animation frames one image at a time from a JSON config.

Each frame is generated as an individual 1:1 image using a fixed base
reference image, then post-processed with slice_and_key.py --frames.

Config format (anims/<name>.json):
{
  "name": "idle1_loop",
  "ref": "refs/chibi_base.png",
  "chain": true,           # optional: attach the PREVIOUS frame as a 2nd ref
  "frames": ["pose description for frame 0", "..."]
}

Chain mode: each frame i>0 is generated with TWO reference images —
the base character ref (style anchor) and the previously generated frame
(temporal anchor). This keeps per-frame details (hand grips, props,
hem length) consistent across frames, which text alone cannot pin down.
"""
import argparse
import base64
import glob
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from io import BytesIO

GEN = os.path.expanduser(
    "~/.claude/skills/lite-image/scripts/generate_image_v2.py")
MODEL = "gemini-3.1-flash-image"

PREAMBLE = (
    "Single frame of a sprite animation. One cute chibi character, full body "
    "from the top of the head to the soles of her shoes fully visible, centered, "
    "occupying about 60% of image height, generous empty margin on all sides, "
    "front-facing, standing on an invisible floor, solid pure green chroma-key "
    "background (#00FF00), no text, no borders. Exactly the same character, "
    "outfit, proportions, art style, outline thickness and line weight as the "
    "reference image."
)

# chain 모드에서 두 번째 레퍼런스(직전 프레임)가 붙을 때의 지시문
CHAIN_NOTE = (
    "TWO reference images are attached. IMAGE 1 is the character's official "
    "design reference (style anchor). IMAGE 2 is the PREVIOUS FRAME of this "
    "animation. Keep everything EXACTLY the same as IMAGE 2 — the outfit, the "
    "skirt length, the exact way her hands hold or grip things, body "
    "proportions, line weight and art style — and change ONLY the specific "
    "pose difference described below. The motion between IMAGE 2 and this new "
    "frame must be small and smooth."
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


def _magic_ext(data: bytes) -> str:
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    return ".bin"


def _find_image_b64(obj):
    """응답 JSON을 재귀 탐색해 base64 이미지 데이터를 찾음."""
    if isinstance(obj, dict):
        mime = obj.get("mime_type") or obj.get("mimeType") or ""
        if obj.get("data") and (str(mime).startswith("image") or obj.get("type") == "image"):
            return obj["data"]
        for k in ("inlineData", "inline_data"):
            if isinstance(obj.get(k), dict) and obj[k].get("data"):
                return obj[k]["data"]
        for key, v in obj.items():
            if key == "signature":
                continue
            r = _find_image_b64(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_image_b64(v)
            if r:
                return r
    return None


def _ref_part(path, ref_max=512):
    """레퍼런스 이미지를 최장변 ref_max로 축소해 inlineData 파트로."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if max(w, h) > ref_max:
        s = ref_max / max(w, h)
        im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    buf = BytesIO()
    im.save(buf, "JPEG", quality=90)
    return {"inlineData": {"mimeType": "image/jpeg",
                           "data": base64.b64encode(buf.getvalue()).decode()}}


def gen_multi_ref(prompt, refs, output):
    """레퍼런스 여러 장을 첨부하는 generateContent 호출 (chain 모드용)."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY not set")
    parts = [_ref_part(r) for r in refs] + [{"text": prompt}]
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "1:1"},
        },
    }
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent")
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        d = json.loads(resp.read().decode())
    b64 = _find_image_b64(d)
    if not b64:
        raise RuntimeError("no image in response")
    import re as _re
    raw = base64.b64decode(_re.sub(r"\s", "", b64))
    out = output
    ext = _magic_ext(raw)
    base_name, cur = os.path.splitext(output)
    if cur.lower() != ext and ext != ".bin":
        out = base_name + ext
    with open(out, "wb") as f:
        f.write(raw)
    return out


def prev_frame_path(outdir, name, i):
    """직전 프레임 파일(확장자 무관)을 찾는다."""
    hits = sorted(glob.glob(os.path.join(outdir, f"{name}_{i - 1:02d}.*")))
    return hits[0] if hits else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("config", help="anims/<name>.json")
    p.add_argument("--outdir", default="sprites/raw")
    p.add_argument("--only", type=int, default=None,
                   help="generate a single frame index (retry helper)")
    p.add_argument("--chain", action="store_true",
                   help="attach the previous frame as a 2nd reference "
                        "(config \"chain\": true does the same)")
    a = p.parse_args()

    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)
    name = cfg["name"]
    chain = a.chain or cfg.get("chain", False)
    os.makedirs(a.outdir, exist_ok=True)

    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    failed = []
    for i, pose in enumerate(cfg["frames"]):
        if a.only is not None and i != a.only:
            continue
        out = os.path.join(a.outdir, f"{name}_{i:02d}.png")
        prev = prev_frame_path(a.outdir, name, i) if (chain and i > 0) else None
        print(f"[{i + 1}/{len(cfg['frames'])}] {name}_{i:02d}"
              + (" (chained)" if prev else ""), flush=True)
        if prev:
            prompt = f"{PREAMBLE} {CHAIN_NOTE} {pose} {CHARACTER} {STYLE}"
            try:
                gen_multi_ref(prompt, [cfg["ref"], prev], out)
            except Exception as e:
                print(f"  chain gen failed: {e}")
                failed.append(i)
        else:
            prompt = f"{PREAMBLE} {pose} {CHARACTER} {STYLE}"
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
