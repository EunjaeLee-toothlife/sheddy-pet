"""Validate and build a local Pages payload; this does not publish anything."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def plan(assets, require_reviewed=False):
    widget = (ROOT / 'widget.html').read_text(encoding='utf-8')
    # Evaluate only the local, pure registry declaration, including Array.from
    # endings. A filename regex alone misses the ten template-built endings.
    registry = 'const ANIMS =' + widget.split('const ANIMS =', 1)[1].split('const DEFAULT_STATE', 1)[0]
    script = "const fs=require('fs'),vm=require('vm'); const s=fs.readFileSync(0,'utf8'); process.stdout.write(JSON.stringify(vm.runInNewContext(s+';ANIMS',{}, {timeout:1000})));"
    result = subprocess.run(['node', '-e', script], input=registry, text=True,
                            encoding='utf-8', capture_output=True, check=True)
    states = json.loads(result.stdout)
    names = set()
    for state in states.values():
        for part in ('start', 'loop', 'end', 'outro'):
            value = state.get(part, [])
            names.update(value if isinstance(value, list) else [value])
    ledger = json.loads((ROOT / 'anims/rebuild_manifest.json').read_text(encoding='utf-8'))
    clips = {Path(c['webm']).name: c for c in ledger['clips']}
    if names != set(clips):
        raise ValueError(f'Runtime/ledger mismatch: {sorted(names ^ set(clips))}')
    files = []
    for name in sorted(names):
        clip = clips[name]
        if assets == 'rebuilt':
            if clip['status'] not in ('generated', 'reviewed') or not clip.get('candidate'):
                raise ValueError(f'Missing reconstructed clip: {clip["clip"]}')
            if require_reviewed and (clip['status'] != 'reviewed' or not all(clip['review'].values())):
                raise ValueError(f'Review incomplete: {clip["clip"]}')
            path = ROOT / clip['candidate']
            expected = clip.get('evidence', {}).get('videoSha256')
        else:
            path = ROOT / clip['webm']
            expected = clip['sourceVideoHash']
        if not path.is_file() or not expected or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Missing or unaudited asset: {path}')
        files.append(path)
    marker = re.compile(r'const DEFAULT_ASSET_SET = "(?:original|rebuilt)";')
    if len(marker.findall(widget)) != 1:
        raise ValueError('Runtime asset default marker is missing or ambiguous')
    widget = marker.sub(f'const DEFAULT_ASSET_SET = "{assets}";', widget)
    relative = Path('sprites/rebuilt/videos') if assets == 'rebuilt' else Path('sprites')
    return widget, files, relative


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', choices=('original', 'rebuilt'), default='original')
    parser.add_argument('--require-reviewed', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    # Validate the complete plan before writes. Preserve unrelated docs files.
    widget, files, relative = plan(args.assets, args.require_reviewed)
    docs = (ROOT / 'docs').resolve()
    if docs.parent != ROOT or docs.name != 'docs':
        raise ValueError('Pages destination must be the repository docs directory')
    target = docs / relative
    if not target.resolve().is_relative_to(docs):
        raise ValueError('Asset destination escapes docs')
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)
        for source in files:
            shutil.copyfile(source, target / source.name)
        (docs / 'index.html').write_text(widget, encoding='utf-8')
        (docs / '.nojekyll').write_text('', encoding='utf-8')
    total = sum(p.stat().st_size for p in files)
    print(f'{"Validated" if args.dry_run else "Built"} {args.assets} Pages payload: '
          f'{len(files)} runtime clips, {total / 1024:.0f} KB')


if __name__ == '__main__':
    main()
