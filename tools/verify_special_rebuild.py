"""Decoded alpha evidence for assigned special animation candidates."""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / 'anims/rebuild_worker_special.json'
data = json.loads(path.read_text(encoding='utf-8'))
for clip in data['clips']:
    if clip['clip'] not in sys.argv[1:]:
        continue
    raw = subprocess.check_output(['ffmpeg','-v','error','-c:v','libvpx-vp9','-i',str(ROOT / clip['candidate']),'-f','rawvideo','-pix_fmt','rgba','pipe:1'])
    frames = np.frombuffer(raw,dtype=np.uint8).reshape(-1,512,512,4)
    alpha = frames[:,:,:,3]
    assert (alpha[:,0,0] == 0).all()
    assert (alpha.max(axis=(1,2)) > 240).all()
    clip.setdefault('evidence',{})['decodedAlpha'] = {'frames':len(frames),'cornerAlphaAllZero':True,'opaqueForegroundEveryFrame':True}
    print(clip['clip'], len(frames), 'decoded alpha passed')
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
