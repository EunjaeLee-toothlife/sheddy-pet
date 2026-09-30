"""Merge only completed, validated clips owned by isolated animation workers."""
import argparse
import copy
import hashlib
from pathlib import Path
from rebuild_animations import ROOT, read_manifest, save_manifest, audit

OWNERS = {
    "dance": {"happy3_loop", "dance1_loop", "yaho1_loop", "parapara1_loop", "dance2_loop", "dance3_loop"},
    "pastry": {"pastry1_start", "pastry1_loop", "pastry1_outro", *[f"pastry1_end{i}" for i in range(1, 6)]},
    "pastry_extra": {"pastry1_end6", "pastry1_end7", "pastry1_end8"},
    "special": {"doze1_loop", "lemon1_loop", "chem1_start", "chem1_loop", "chem1_end1", "chem1_end3"},
}
SOURCE_FIELDS = ["clip", "frames", "webm", "count", "sourceDuration", "sourceFrameHashes",
                 "sourceVideoHash", "holds", "repeats", "rate", "state", "part"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("worker", choices=OWNERS, nargs="+")
    parser.add_argument("--clip", action="append", help="merge selected completed clips only")
    args = parser.parse_args()
    central = read_manifest()
    by_name = {c["clip"]: c for c in central["clips"]}
    merged = []
    for name in args.worker:
        worker = read_manifest(ROOT / f"anims/rebuild_worker_{name}.json")
        if worker["canonicalReference"] != central["canonicalReference"]:
            raise ValueError("worker uses a different canonical style")
        for candidate in worker["clips"]:
            clip = candidate["clip"]
            if clip not in OWNERS[name] or (args.clip and clip not in args.clip):
                continue
            if candidate["status"] not in ("generated", "reviewed") or not candidate.get("candidate"):
                continue
            current = by_name[clip]
            for field in SOURCE_FIELDS:
                if candidate.get(field) != current.get(field):
                    raise ValueError(f"worker changed source contract: {clip} {field}")
            path = ROOT / candidate["candidate"]
            expected = candidate.get("evidence", {}).get("videoSha256")
            if not expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f"worker asset changed after its audit: {clip}")
            checked = copy.deepcopy(candidate)
            audit(checked)
            if checked["evidence"]["framesTouchingCanvas"]:
                raise ValueError(f"worker frames touch canvas; visual repair needed: {clip}")
            if current.get("evidence", {}).get("videoSha256") == expected:
                continue
            by_name[clip] = checked
            merged.append(clip)
    central["clips"] = [by_name[c["clip"]] for c in central["clips"]]
    save_manifest(central)
    print("Merged: " + (", ".join(merged) or "no newly completed worker clips"))


if __name__ == "__main__":
    main()
