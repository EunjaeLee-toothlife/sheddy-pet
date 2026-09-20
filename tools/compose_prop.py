"""키잉된 캐릭터 프레임 위에 소품(프롭)을 합성하고 캐릭터를 좌우로 옮긴다.

칠판처럼 캐릭터와 떨어져 있는 큰 소품은 프레임마다 생성하면 모양이 흔들리고,
`slice_and_key.py`의 매트 정리(최대 연결 성분 유지)가 본체와 떨어진 조각을 지워 버린다.
그래서 소품은 한 번만 생성해 `sprites/props/`에 두고, 키잉이 끝난 뒤 이 스크립트로 합친다.
소품이 캐릭터 뒤에 깔리므로 합성 순서는 프롭 → 캐릭터다.

프레임별 지시는 `anims/<name>.json`의 `compose` 키에 적는다:

    "compose": {
      "prop": "sprites/props/blackboard.png",
      "floor": 501,                 # 프롭 바닥이 닿는 y (캐릭터 발높이와 맞춤)
      "frames": [
        { "shift": 0 },                                    # 프롭 없음
        { "shift": 20, "prop": { "h": 120, "right": 300, "sx": 1.15 } },
        { "shift": 85, "prop": { "h": 420, "right": 230 },
          "sparkle": { "n": 5, "seed": 1, "box": [20, 80, 240, 480] } }
      ]
    }

프롭 항목: h=높이(px), right=오른쪽 끝 x, sx=가로만 추가 배율(스쿼시), dy=바닥에서 띄우기,
alpha=불투명도(0~1), rot=회전(도). sparkle은 프롭이 나타나고 사라질 때의 반짝임.
좌표는 모두 512px 캔버스 기준.
"""
import argparse
import glob
import json
import math
import os
import random

from PIL import Image, ImageDraw


def load_prop(path):
    """프롭 PNG를 알파 bbox로 잘라서 반환."""
    im = Image.open(path).convert("RGBA")
    bbox = im.split()[3].getbbox()
    if not bbox:
        raise SystemExit(f"프롭이 비어 있다: {path}")
    return im.crop(bbox)


def place_prop(canvas, prop, spec, floor):
    h = int(round(spec["h"]))
    if h < 2:
        return
    w = max(2, int(round(prop.width * h / prop.height * spec.get("sx", 1.0))))
    im = prop.resize((w, h), Image.LANCZOS)
    if spec.get("rot"):
        im = im.rotate(spec["rot"], resample=Image.BICUBIC, expand=True)
    a = spec.get("alpha", 1.0)
    if a < 1.0:
        alpha = im.split()[3].point(lambda v: int(v * a))
        im.putalpha(alpha)
    x = int(round(spec["right"])) - im.width
    y = int(round(floor + spec.get("dy", 0))) - im.height
    canvas.alpha_composite(im, (x, y))


def draw_sparkles(canvas, spec):
    """4각 반짝임. 캐릭터 art style에 맞춰 흰색 + 옅은 레몬빛 중심."""
    rng = random.Random(spec.get("seed", 0))
    x0, y0, x1, y1 = spec["box"]
    lo, hi = spec.get("size", [7, 15])
    a = spec.get("alpha", 1.0)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(spec.get("n", 5)):
        cx = rng.uniform(x0, x1)
        cy = rng.uniform(y0, y1)
        r = rng.uniform(lo, hi)
        w = r * 0.26          # 별 허리 두께
        for col, s in ((( 255, 249, 214, int(255 * a)), 1.0),
                       ((255, 255, 255, int(255 * a)), 0.55)):
            rr, ww = r * s, w * s
            d.polygon([(cx, cy - rr), (cx + ww, cy), (cx, cy + rr), (cx - ww, cy)], fill=col)
            d.polygon([(cx - rr, cy), (cx, cy - ww), (cx + rr, cy), (cx, cy + ww)], fill=col)
    canvas.alpha_composite(layer)


def shift_char(im, dx):
    if not dx:
        return im
    # PIL의 AFFINE 계수는 출력 → 입력 변환이라 부호가 반대다
    return im.transform(im.size, Image.AFFINE, (1, 0, -dx, 0, 1, 0),
                        resample=Image.BICUBIC)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("config", help="anims/<name>.json")
    p.add_argument("--frames", default=None,
                   help="키잉된 캐릭터 프레임 glob (기본 sprites/<name>_char/<name>_*.png)")
    p.add_argument("--outdir", default=None, help="기본 sprites/<name>")
    a = p.parse_args()

    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)
    name = cfg["name"]
    comp = cfg.get("compose")
    if not comp:
        raise SystemExit(f"{a.config}에 compose 키가 없다")
    src = a.frames or os.path.join("sprites", f"{name}_char", f"{name}_*.png")
    outdir = a.outdir or os.path.join("sprites", name)
    paths = sorted(glob.glob(src))
    if not paths:
        raise SystemExit(f"no files match {src}")
    specs = comp["frames"]
    if len(specs) != len(paths):
        raise SystemExit(f"compose.frames {len(specs)}개 != 프레임 {len(paths)}개")
    prop = load_prop(comp["prop"]) if comp.get("prop") else None
    floor = comp.get("floor", 501)
    os.makedirs(outdir, exist_ok=True)

    for i, (path, spec) in enumerate(zip(paths, specs)):
        char = Image.open(path).convert("RGBA")
        canvas = Image.new("RGBA", char.size, (0, 0, 0, 0))
        if spec.get("prop") and prop is not None:
            place_prop(canvas, prop, spec["prop"], floor)
        canvas.alpha_composite(shift_char(char, spec.get("shift", 0)))
        if spec.get("sparkle"):
            draw_sparkles(canvas, spec["sparkle"])
        canvas.save(os.path.join(outdir, f"{name}_{i:02d}.png"))
    print(f"composed {len(paths)} frames -> {outdir}")


if __name__ == "__main__":
    main()
