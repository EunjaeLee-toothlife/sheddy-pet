"""Stage shared chef donors and verify the three separately owned food endings."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args):
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    manifest = args.manifest.as_posix()
    for clip in ['pastry1_end6', 'pastry1_end7', 'pastry1_end8']:
        folder = ROOT / 'sprites/rebuilt/frames' / clip
        shared = ROOT / 'sprites/rebuilt/poses/pastry_camera_source/pastry1_end1'
        for index in [0, 1, 2, 8, 9, 10, 11]:
            shutil.copyfile(shared / f'pastry1_end1_{index:02d}.png', folder / f'{clip}_{index:02d}.png')
        # Raw originals are kept independently so this camera pass is reproducible.
        backups = ROOT / 'sprites/rebuilt/poses/pastry_camera_source' / clip
        backups.mkdir(parents=True, exist_ok=True)
        for path in folder.glob('*.png'):
            shutil.copyfile(path, backups / path.name)
        run('tools/rebuild_pastry.py', 'camera', clip)
        for index, source in [(0, 'pastry1_loop/pastry1_loop_00.png'), (11, 'pastry1_outro/pastry1_outro_00.png')]:
            shutil.copyfile(ROOT / 'sprites/rebuilt/frames' / source, folder / f'{clip}_{index:02d}.png')
        run('tools/rebuild_animations.py', 'encode', clip, '--manifest', manifest)
        run('tools/rebuild_animations.py', 'audit', clip, '--manifest', manifest)
        run('tools/qa_dance_rebuild.py', clip, '--manifest', manifest)


if __name__ == '__main__':
    main()
