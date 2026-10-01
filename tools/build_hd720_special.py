"""승인된 특수 동작의 원시 이미지를 720px 자산으로 직접 재구성한다."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import minimum_filter
from slice_and_key import chroma_key, body_box
from compose_anim import bbox, foot_center
from compose_talk import rect_mask

ROOT = Path(__file__).resolve().parent.parent
SIZE = 720
RATIO = SIZE / 512
BASE = ROOT / 'sprites/hd720'
SPECIAL = ('doze1_loop', 'lemon1_loop', 'chem1_loop', 'chem1_start',
           'chem1_end1', 'chem1_end2', 'chem1_end3')
ALCHEMY = tuple('alchemy1_' + p for p in ('start', 'loop', 'end1', 'end2', 'end3', 'outro'))
SOURCES = {}
OVERRIDES = {
    'chem1_opposite_00.png': 'chem1_loop_opposite_fixed.png',
    'chem1_swirl_opposite_00.png': 'chem1_loop_swirl_opposite_fixed.png',
    'chem1_crosswipe_00.png': 'chem1_end1_crosswipe_fixed.png',
    'chem1_finalhide_00.png': 'chem1_end1_hide_cloth_final.png',
    'chem1_end3_proud_00.png': 'chem1_end3_proud.png',
}
MATTE_QA = BASE / 'qa/special_green_repair'
LEMON_ROIS = {
    2: (145, 360, 250, 460), 3: (205, 220, 320, 355),
    4: (260, 220, 355, 335), 5: (260, 220, 355, 335),
    6: (260, 260, 355, 380), 7: (105, 270, 235, 400),
    8: (110, 270, 245, 410), 9: (235, 260, 350, 405),
    10: (200, 310, 325, 440), 11: (205, 285, 335, 430),
    12: (195, 460, 295, 595),
}


def read(path):
    path = ROOT / path
    SOURCES[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return Image.open(path).convert('RGBA')


def load(path):
    path = ROOT / path
    SOURCES[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text(encoding='utf-8'))


def save(clip, index, im):
    target = BASE / 'frames' / clip / f'{clip}_{index:02d}.png'
    target.parent.mkdir(parents=True, exist_ok=True)
    im.save(target)


def hd(clip, index=0):
    return Image.open(BASE / 'frames' / clip / f'{clip}_{index:02d}.png').convert('RGBA')


def place(native, scale512, dx512, dy512):
    # 512 중간 PNG를 읽지 않고 원시 셀에서 목적 크기로 단 한 번 축소/확대한다.
    scale = scale512 * SIZE / native.width
    resized = native.resize((round(native.width * scale), round(native.height * scale)),
                            Image.Resampling.LANCZOS)
    out = Image.new('RGBA', (SIZE, SIZE))
    out.alpha_composite(resized, (round(dx512 * RATIO), round(dy512 * RATIO)))
    return out


def cell(clip, index, manifest):
    info = manifest[clip]
    batch = next(b for b in info['frameBatches'] if index in b['indices'])
    sheet = read(batch['source'])
    n = batch['indices'].index(index)
    w, h = sheet.width // batch['cols'], sheet.height // batch['rows']
    crop = sheet.crop(((n % batch['cols']) * w, (n // batch['cols']) * h,
                       (n % batch['cols'] + 1) * w, (n // batch['cols'] + 1) * h))
    region = batch.get('greenRegion')
    if region:
        region = [round(v * w / 512) for v in region]
    if clip == 'chem1_end3' and index == 12:
        # 넓은 액체 보호 영역이 머리 사이 배경까지 살리던 기존 결함을 교정한다.
        # 검수한 플라스크 사각형 안의 녹색 무지개 띠만 불투명하게 보존한다.
        region = [round(v * w / 627) for v in (210, 60, 290, 180)]
    keyed = chroma_key(crop, keep_components=batch.get('keepComponents', False), green_region=region)
    return keyed, {'source': batch['source'], 'sourceCell': n, 'nativeSize': list(crop.size),
                   'sourceLimited': min(crop.size) < SIZE, 'fallback512': False,
                   'nativeGreenRegion': region}


def donor(record, clip, manifest):
    path = record.get('donor', '')
    leaf = Path(path).name
    if leaf in OVERRIDES:
        rawpath = 'sprites/rebuilt/raw_poses/' + OVERRIDES[leaf]
        raw = read(rawpath)
        return chroma_key(raw, keep_components=True), {'source': rawpath,
            'nativeSize': list(raw.size), 'sourceLimited': raw.width < SIZE, 'fallback512': False}
    return cell(clip, record.get('sourceCell', record['frame']), manifest)


def despill(im):
    a = np.asarray(im).copy()
    limit = np.maximum(a[..., 0], a[..., 2])
    spill = ((a[..., 3] > 0) & (a[..., 3] < 128)
             & (a[..., 1].astype(int) - limit.astype(int) > 20))
    a[..., 1] = np.where(spill, limit, a[..., 1])
    return Image.fromarray(a, 'RGBA')


def build_special(manifest, selection=None):
    proofs = {}
    for clip in SPECIAL:
        if selection and clip not in selection:
            continue
        records = []
        if clip == 'chem1_end2':
            plan = load('sprites/rebuilt/configs/chem1_end2_plan.json')
            base512 = read(plan['base'])
            bx0, by0, bx1, by1 = bbox(base512)
            for index in range(manifest[clip]['count']):
                key = f'p{index}'
                small = read(plan['poses'][key])
                s = plan['pose_scales'][key]
                resized = small.resize((round(512 * s), round(512 * s)), Image.Resampling.LANCZOS)
                _, _, _, sy1 = bbox(resized)
                dx = round(foot_center(base512) - foot_center(resized))
                dy = round(by1 - sy1)
                native, proof = cell(clip, index, manifest)
                im = place(native, s, dx, dy)
                if index == 4:
                    # 승인된 느린 깜박임은 새 원시 기준 이미지의 눈 사각형만 복원한다.
                    blink = read('sprites/rebuilt/poses/chem1_end2_04_blink_special_native.png')
                    blink = blink.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
                    rectangle = [round(v * RATIO) for v in [210, 128, 302, 162]]
                    mask = rect_mask((SIZE, SIZE), rectangle, round(3 * RATIO))
                    a, b = np.asarray(im), np.asarray(blink)
                    patched = np.rint(a.astype(float)*(1-mask)+b.astype(float)*mask).astype('uint8')
                    patched[..., 3] = a[..., 3]
                    im = Image.fromarray(patched, 'RGBA')
                    proof['blink'] = {'source': 'sprites/rebuilt/poses/chem1_end2_04_blink_special_native.png',
                                      'rect720': rectangle, 'alphaUnchanged': True}
                save(clip, index, im)
                records.append(dict(proof, frame=index, scale512=s, dx512=dx, dy512=dy))
        else:
            planname = 'doze1_registration.json' if clip == 'doze1_loop' else clip + '_registration.json'
            plan = load('sprites/rebuilt/configs/' + planname)
            for record in plan['frames']:
                index = record['frame']
                native, proof = donor(record, clip, manifest)
                im = place(native, record['scale'], record['dx'], record['dy'])
                if plan.get('despillAfterResize'):
                    im = despill(im)
                save(clip, index, im)
                records.append(dict(proof, frame=index, scale512=record['scale'],
                                    dx512=record['dx'], dy512=record['dy']))
        # 공통 접합점은 같은 720 PNG를 복사하여 크기/색 불연속을 예방한다.
        anchors = {}
        if clip == 'chem1_loop':
            save(clip, 18, hd(clip, 0)); anchors[18] = 'chem1_loop:0'
        elif clip == 'lemon1_loop':
            for i in (0, 15):
                save(clip, i, hd('idle1_loop')); anchors[i] = 'idle1_loop:0'
        elif clip == 'chem1_start':
            save(clip, 0, hd('idle1_loop')); save(clip, 11, hd('chem1_loop'))
            anchors = {0: 'idle1_loop:0', 11: 'chem1_loop:0'}
        elif clip in ('chem1_end1', 'chem1_end2', 'chem1_end3'):
            save(clip, 0, hd('chem1_loop')); save(clip, manifest[clip]['count'] - 1, hd('idle1_loop'))
            anchors = {0: 'chem1_loop:0', manifest[clip]['count'] - 1: 'idle1_loop:0'}
        proofs[clip] = {'frames': records, 'exactAnchors': anchors, 'rate': manifest[clip].get('rate', 1),
                        'count': manifest[clip]['count'], 'fps': manifest[clip].get('fps', 10),
                        'holds': manifest[clip].get('holds', {}), 'repeats': manifest[clip].get('repeats', [])}
        print('built', clip, flush=True)
    return proofs


def solid(im):
    return im.getchannel('A').point(lambda v: 255 if v > 200 else 0).getbbox()


def build_alchemy():
    tiles, configs = {}, {}
    for clip in ALCHEMY:
        cfg = load(f'anims/{clip}.json'); configs[clip] = cfg
        sheet = read(cfg['sheet'])
        if SOURCES[cfg['sheet']] != cfg['sha256']:
            raise ValueError('원시 시트 해시 불일치: ' + clip)
        tiles[clip] = []
        for box in cfg['cellBoxes']:
            im = sheet.crop(box)
            im.putalpha(im.getchannel('A').point(lambda a: 0 if a < 8 else a))
            tiles[clip].append(im)
    # 기존 512 계획의 공통 배율을 계산하고 목적 좌표만 720으로 환산한다.
    original_idle = read('sprites/rebuilt/frames/idle1_loop/idle1_loop_00.png')
    ref, first = solid(original_idle), solid(tiles['alchemy1_start'][0])
    boxes = [solid(f) for group in tiles.values() for f in group]
    scale512 = min((ref[3] - ref[1])/(first[3] - first[1]),
                   480/max(b[2]-b[0] for b in boxes), 480/max(b[3]-b[1] for b in boxes))
    frames, proofs = {}, {}
    for clip, group in tiles.items():
        frames[clip] = []; records = []
        for index, im in enumerate(group):
            box = solid(im)
            s = scale512 * RATIO
            resized = im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS)
            out = Image.new('RGBA',(SIZE,SIZE))
            # 원래 각 셀의 중앙과 발바닥496에 등록한 배치를 동일 비율로 유지한다.
            old_w = round(im.width*scale512)
            dx512, dy512 = round(256-old_w/2), round(496-box[3]*scale512)
            out.alpha_composite(resized,(round(dx512*RATIO),round(dy512*RATIO)))
            frames[clip].append(out)
            records.append({'frame':index,'source':configs[clip]['sheet'],
                'cellBox':configs[clip]['cellBoxes'][index], 'nativeSize':list(im.size),
                'sourceLimited': min(im.size)<SIZE,'fallback512':False,
                'scaleNativeTo720':s,'placement720':[round(dx512*RATIO),round(dy512*RATIO)]})
        proofs[clip] = {'frames':records,'uniformSourceScale512':scale512}
    anchor = frames['alchemy1_loop'][0]
    frames['alchemy1_start'][0] = hd('idle1_loop')
    frames['alchemy1_start'][-1] = anchor.copy()
    frames['alchemy1_loop'][-1] = anchor.copy()
    frames['alchemy1_outro'][0] = anchor.copy()
    frames['alchemy1_outro'][-1] = hd('idle1_loop')
    for clip in ('alchemy1_end1','alchemy1_end2','alchemy1_end3'):
        frames[clip][0] = anchor.copy(); frames[clip][-1] = anchor.copy()
    for clip, group in frames.items():
        for index, im in enumerate(group): save(clip,index,im)
        print('built',clip,flush=True)
    return proofs


def build_note():
    cfg = load('anims/note1_loop.json')
    small = chroma_key(read('sprites/raw/note1_loop_00.jpg').resize((512,512),Image.Resampling.LANCZOS))
    ref = read('sprites/idle1_loop/idle1_loop_00.png')
    rt, rb, rcx = body_box(ref); t,b,cx = body_box(small)
    scale = (rb-rt)/(b-t); tx,ty = rcx-scale*cx, rb-scale*b
    records = []
    for index in range(len(cfg['frames'])):
        source = f'sprites/raw/note1_loop_{index:02d}.jpg'
        raw = read(source)
        # 원시 JPG에 승인된 보정이 포함됨을 512 재현 비교로 전체19프레임에서 확인했다.
        native = chroma_key(raw)
        im = place(native,scale,tx,ty)
        save('note1_loop',index,im)
        records.append({'frame':index,'source':source,'nativeSize':list(raw.size),
            'sourceLimited':False,'fallback512':False,'scale512':scale,'dx512':tx,'dy512':ty})
    save('note1_loop',18,hd('note1_loop',0))
    print('built note1_loop',flush=True)
    return {'note1_loop':{'frames':records,'exactAnchors':{18:'note1_loop:0'},
        'sourceRepairs':'Raw JPG already contains reviewed retouch; original512 key/match reproduces all19 approved PNGs pixel exactly.',
        'idleStyleNote':'Note uses its approved Flux character, preserving its original identity and registration.'}}


def expanded(cfg,count):
    repeats = {r['frames'][0]:(r['frames'][1],r['times']) for r in cfg.get('repeats',[])}
    order=[]; i=0
    while i<count:
        if i in repeats:
            end,times=repeats[i]; order += list(range(i,end+1))*max(1,times); i=end+1
        else: order.append(i); i+=1
    return sum(max(1,int(cfg.get('holds',{}).get(str(i),1))) for i in order)


def protected_rois(clip, index, proof):
    """의도된 녹색 소품과 무지개 액체의 검수된 범위를 보호한다."""
    anchor = proof.get('exactAnchors', {}).get(str(index), proof.get('exactAnchors', {}).get(index))
    if anchor:
        source_clip, source_index = anchor.split(':')
        if source_clip != clip:
            clip, index = source_clip, int(source_index)
    regions = []
    if clip == 'lemon1_loop' and index in LEMON_ROIS:
        regions.append(LEMON_ROIS[index])
    if clip == 'note1_loop' and index in (13, 14):
        regions.append((285, 295, 475, 480))
    if clip == 'chem1_end3':
        record = next((r for r in proof['frames'] if r['frame'] == index), None)
        if record and record.get('nativeGreenRegion'):
            x0, y0, x1, y1 = record['nativeGreenRegion']
            factor = record['scale512'] * SIZE / record['nativeSize'][0]
            dx, dy = round(record['dx512'] * RATIO), round(record['dy512'] * RATIO)
            regions.append((int(np.floor(x0*factor+dx))-3, int(np.floor(y0*factor+dy))-3,
                            int(np.ceil(x1*factor+dx))+3, int(np.ceil(y1*factor+dy))+3))
    return regions


def matte_mask(before, regions):
    """반투명 외곽의 녹색 초과분만 선택하며 보호 영역은 제외한다."""
    alpha = before[..., 3]
    limit = np.maximum(before[..., 0], before[..., 2])
    excess = before[..., 1].astype(int) - limit.astype(int)
    mask = (minimum_filter(alpha, size=9) < 250) & (excess > 20) & (alpha > 20) & (alpha < 250)
    for x0, y0, x1, y1 in regions:
        mask[max(0,y0):min(SIZE,y1),max(0,x0):min(SIZE,x1)] = False
    return mask


def repair_matte(clip, proof):
    """확실한 키 배경 외곽 프린지만 고치고 알파·빨강·파랑·불투명 내부를 보존한다."""
    if clip in ALCHEMY:
        # 투명 원시 시트의 초록 마법빛·김·슬라임·반사광은 의도된 효과다.
        proof['matteRepair'] = {'skipped': True, 'reason': 'Native transparent RGBA magic, steam and slime are intentional; all pixels preserved.'}
        return
    MATTE_QA.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted((BASE/'frames'/clip).glob('*.png')):
        index = int(path.stem.rsplit('_',1)[1])
        current = np.array(Image.open(path).convert('RGBA'))
        baseline = MATTE_QA / (path.stem + '_before.png')
        before = np.array(Image.open(baseline).convert('RGBA')) if baseline.exists() else current
        rois = protected_rois(clip, index, proof)
        mask = matte_mask(before, rois)
        after = before.copy()
        after[...,1] = np.where(mask, np.maximum(before[...,0],before[...,2]), before[...,1])
        # 동일 원시 입력의 재구성 또는 이미 보정된 상태만 받아 반복 실행을 안정화한다.
        assert np.array_equal(current,before) or np.array_equal(current,after), path
        assert np.array_equal(after[...,3],before[...,3])
        assert np.array_equal(after[...,[0,2]],before[...,[0,2]])
        assert np.array_equal(after[~mask],before[~mask])
        assert np.array_equal(after[before[...,3]>=250],before[before[...,3]>=250])
        assert Image.fromarray(after).getbbox()==Image.fromarray(before).getbbox()
        if mask.any():
            if not baseline.exists():Image.fromarray(before).save(baseline)
            Image.fromarray(after).save(path)
            maskpath = MATTE_QA / (path.stem+'_mask.png')
            Image.fromarray(mask.astype('uint8')*255).save(maskpath)
        ys,xs=np.where(mask)
        records.append({'frame':index,'changedPixels':int(mask.sum()),
            'changedBBox':None if not len(xs) else [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],
            'beforeSHA256':hashlib.sha256((baseline if baseline.exists() else path).read_bytes()).hexdigest(),
            'beforePixelsSHA256':hashlib.sha256(Image.fromarray(before).tobytes()).hexdigest(),
            'afterSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'protectedROIs720':rois,'alphaRBOutsideMaskOpaqueBBoxExact':True})
    proof['matteRepair']={'condition':'minimum_filter(alpha,size=9)<250 & G-max(R,B)>20 & 20<alpha<250; protectedROIs excluded',
        'operation':'G=max(R,B) only','frames':records,'changedPixels':sum(r['changedPixels'] for r in records)}


def validate(clip,proof,encode=True):
    if clip in SPECIAL:
        cfg={k:proof[k] for k in ('fps','holds','repeats')}; cfg['name']=clip
        configpath=BASE/'configs'/f'{clip}.json';configpath.parent.mkdir(exist_ok=True)
        configpath.write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
    else:
        configpath=ROOT/f'anims/{clip}.json';cfg=load(f'anims/{clip}.json')
    folder=BASE/'frames'/clip; paths=sorted(folder.glob(f'{clip}_*.png'))
    count=proof['count'] if clip in SPECIAL else len(cfg['frames']) if isinstance(cfg.get('frames'),list) else len(cfg.get('cellBoxes',[]))
    if len(paths)!=count: raise ValueError(f'프레임 수 불일치 {clip}: {len(paths)} != {count}')
    touched=[]; hashes=[]
    contact=Image.new('RGB',(1000,((count+4)//5)*220),'#e6e6e6'); draw=ImageDraw.Draw(contact)
    for i,p in enumerate(paths):
        im=Image.open(p)
        if im.mode!='RGBA' or im.size!=(SIZE,SIZE): raise ValueError(str(p))
        box=im.getbbox()
        if not box or min(box[:2])<=0 or max(box[2:])>=SIZE: touched.append(i)
        hashes.append({'frame':i,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bbox':box})
        bg=Image.new('RGBA',im.size,'#e6e6e6'); bg.alpha_composite(im)
        contact.paste(bg.convert('RGB').resize((200,200),Image.Resampling.LANCZOS),((i%5)*200,(i//5)*220+20))
        draw.text(((i%5)*200+6,(i//5)*220+5),f'{clip} {i:02d}',fill='black')
    qa=BASE/'qa';qa.mkdir(exist_ok=True);contact.save(qa/f'{clip}_contact.png')
    if touched: raise ValueError(f'가장자리 잘림 {clip}: {touched}')
    fps=cfg.get('fps',10); ticks=expanded(cfg,count)
    proof.update({'count':count,'size':[SIZE,SIZE],'framesTouchingCanvas':touched,'frameHashes':hashes,
                  'fps':fps,'ticks':ticks,'expectedDuration':ticks/fps,'holds':cfg.get('holds',{}),
                  'repeats':cfg.get('repeats',[]),'review':{'staticVisual':False,'runtime':False}})
    if not encode: return
    video=BASE/'videos'/f'anim_{clip}.webm';video.parent.mkdir(exist_ok=True)
    subprocess.run([sys.executable,str(ROOT/'tools/encode_holds.py'),str(configpath),
        '--frames-dir',str(folder),'--out',str(video),'--fps',str(fps)],cwd=ROOT,check=True)
    proc=subprocess.Popen(['ffmpeg','-v','error','-c:v','libvpx-vp9','-i',str(video),'-f','rawvideo','-pix_fmt','rgba','pipe:1'],stdout=subprocess.PIPE)
    decoded=0; alltransparent=True; allopaque=True
    while True:
        buf=proc.stdout.read(SIZE*SIZE*4)
        if not buf:break
        if len(buf)!=SIZE*SIZE*4:raise ValueError('잘린 디코드 프레임')
        arr=np.frombuffer(buf,np.uint8).reshape(SIZE,SIZE,4)
        alltransparent &= bool(np.all(arr[[0,0,-1,-1],[0,-1,0,-1],3]==0))
        allopaque &= bool(np.any(arr[...,3]>240));decoded+=1
    if proc.wait()!=0 or decoded!=ticks or not alltransparent or not allopaque:raise ValueError('알파/타이밍 검증 실패 '+clip)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
    duration=float(probe['format']['duration'])
    if abs(duration-ticks/fps)>.02:raise ValueError('영상 길이 불일치 '+clip)
    proof.update({'video':video.relative_to(ROOT).as_posix(),'videoSHA256':hashlib.sha256(video.read_bytes()).hexdigest(),
        'bytes':video.stat().st_size,'duration':duration,'decodedAlpha':{'decoder':'libvpx-vp9','frames':decoded,
        'allCornersTransparent':alltransparent,'opaqueForegroundEveryFrame':allopaque},'encoding':{'crf':24,'pixFmt':'yuva420p'}})
    print('verified',clip,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames-only',action='store_true')
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--matte-repair-only',action='store_true')
    parser.add_argument('--clips',nargs='+')
    args=parser.parse_args()
    target=ROOT/'anims/hd720_special.json'
    if args.verify_only or args.matte_repair_only:
        previous=json.loads(target.read_text(encoding='utf-8'))
        proof=previous['clips']; SOURCES.update(previous['originalSources'])
    else:
        manifest={c['clip']:c for c in load('anims/rebuild_manifest.json')['clips']}
        if not (BASE/'frames/idle1_loop/idle1_loop_00.png').exists():
            raise ValueError('root720 idle anchor가 먼저 필요합니다')
        previous=json.loads(target.read_text(encoding='utf-8')) if args.clips and target.exists() else {}
        proof=previous.get('clips',{});SOURCES.update(previous.get('originalSources',{}))
        proof.update(build_special(manifest,args.clips))
        if not args.clips or any(c in ALCHEMY for c in args.clips):proof.update(build_alchemy())
        if not args.clips or 'note1_loop' in args.clips:proof.update(build_note())
    for clip,p in proof.items():
        if args.clips and clip not in args.clips:continue
        if not args.verify_only:repair_matte(clip,p)
        validate(clip,p,not args.frames_only)
        target.write_text(json.dumps({'size':SIZE,'clips':proof,'originalSources':SOURCES},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for path,sha in SOURCES.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=sha:raise ValueError('원본 변경 감지 '+path)


if __name__=='__main__':main()
