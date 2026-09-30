"""Reproduce the dance worker's six uniformly registered candidate clips."""
import argparse
import subprocess
import sys
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
PLANS={
 'happy3_loop':[451]*12+[435,415,365,365,425,445,451,451],
 'dance1_loop':[442,445,448,451,454,451,447,444]*2,
 'yaho1_loop':[451,454,458,451,454,451,451,451,451,451,444,454,451,451],
 'parapara1_loop':[442,447,454,447,447,454,447,447,454,447,447,454,442,454,447,447,442,451,470,463,450,447,444,442],
 'dance2_loop':[442,447,454,445,454,447,442,447,454,445,454,447,451,443,456,442],
 'dance3_loop':[442,447,454,445,454,447,442,447,454,445,454,447,451,443,456,442],
}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--clip',choices=list(PLANS))
    a=p.parse_args()
    def run(tool,*args):
        subprocess.run([sys.executable,str(ROOT/'tools'/tool),*map(str,args),'--manifest',str(a.manifest)],cwd=ROOT,check=True)
    for clip,heights in PLANS.items():
        if a.clip and a.clip!=clip:
            continue
        run('normalize_dance_rebuild.py',clip,'--heights',*heights)
        if clip=='yaho1_loop':
            shutil.copyfile(ROOT/'sprites/rebuilt/poses/idle_open_00.png',ROOT/'sprites/rebuilt/frames/yaho1_loop/yaho1_loop_13.png')
        if clip in ['happy3_loop','yaho1_loop','dance3_loop']:
            run('compose_dance_sparkles.py',clip,'--refresh')
        run('rebuild_animations.py','encode',clip)
        run('rebuild_animations.py','audit',clip)
        run('qa_dance_rebuild.py',clip)

if __name__=='__main__':
    main()
