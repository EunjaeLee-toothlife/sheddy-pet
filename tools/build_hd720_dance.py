"""담당 댄스·OBS 후보를 원본 셀에서 직접 추출해 720px로 조립한다.

원본·512px 자산과 중앙 장부는 수정하지 않는다. 314/627px 원본 셀의
해상도 한계를 기록하며 새로 생성한 고해상도 디테일이라고 주장하지 않는다.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from slice_and_key import chroma_key, body_box
from finalize_dance_rebuild import PLANS
from compose_dance_sparkles import PLAN as EFFECTS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'sprites/hd720'
RATIO = 720 / 512


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_native(path, keep=False):
    im = Image.open(path)
    return key_native(im, keep)


def key_native(im, keep=False):
    if im.mode == 'RGBA' and im.getchannel('A').getextrema()[0] < 255:
        im = im.copy()
        im.putalpha(im.getchannel('A').point(lambda a: 0 if a < 8 else a))
        return im
    return chroma_key(im, keep_components=keep)


def affine720(im, scale, tx, ty):
    # 원본 크기로 키잉한 이미지에서 직접 한 번만 리샘플링한다.
    return im.transform((720, 720), Image.Transform.AFFINE,
                        (1/scale, 0, -tx/scale, 0, 1/scale, -ty/scale),
                        resample=Image.Resampling.BICUBIC)


def native_cells(path, cols, rows, row_offset=0, keep=False):
    im = Image.open(path)
    result = []
    for i in range(cols * rows):
        x, y = i % cols, i // cols
        box = (round(x*im.width/cols), round(y*im.height/rows)+row_offset,
               round((x+1)*im.width/cols), round((y+1)*im.height/rows)+row_offset)
        result.append((key_native(im.crop(box), keep), list(box)))
    return result


def shoe_place(im, height):
    box = im.getchannel('A').point(lambda a: 255 if a > 10 else 0).getbbox()
    tight = im.crop(box)
    band = max(12, round(tight.height * .065))
    foot = tight.getchannel('A').crop((0,tight.height-band,tight.width,tight.height))
    fb = foot.point(lambda a: 255 if a > 10 else 0).getbbox()
    center = (fb[0]+fb[2])/2
    scale = height/tight.height
    return affine720(tight, scale, 360-center*scale, 498*RATIO-height)


def clean_green_edge(im, name, index, native_transparent=False):
    """배경과 연결된 반투명 녹색 테두리만 정리하고 내부 초록 잎은 보존한다."""
    before=np.array(im)
    rgb=before[:,:,:3].astype(int)
    alpha=before[:,:,3]
    candidates=(ndimage.minimum_filter(alpha,size=9)<250)&(alpha>20)&(alpha<250)&(rgb[:,:,1]-np.maximum(rgb[:,:,0],rgb[:,:,2])>20)
    seeds=np.zeros(alpha.shape,dtype=bool)
    seeds[0,:]=seeds[-1,:]=seeds[:,0]=seeds[:,-1]=True
    background=ndimage.binary_propagation(seeds,mask=alpha<250)
    # 원래 투명한 시트에는 크로마 배경이 없으므로 이 보정을 적용하지 않는다.
    mask=candidates&background if not native_transparent else np.zeros_like(candidates)
    after=before.copy()
    after[:,:,1]=np.where(mask,np.maximum(rgb[:,:,0],rgb[:,:,2]),rgb[:,:,1]).astype(np.uint8)
    assert np.array_equal(after[:,:,3],before[:,:,3])
    assert np.array_equal(after[:,:,[0,2]],before[:,:,[0,2]])
    assert np.array_equal(after[~mask],before[~mask])
    assert np.array_equal(after[alpha>=250],before[alpha>=250])
    result=Image.fromarray(after,'RGBA')
    assert result.getbbox()==im.getbbox()
    folder=OUT/'qa/dance/green_repair';folder.mkdir(parents=True,exist_ok=True)
    baseline=folder/f'{name}_{index:02d}_before.png'
    im.save(baseline)
    maskpath=folder/f'{name}_{index:02d}_mask.png'
    Image.fromarray(mask.astype(np.uint8)*255).save(maskpath)
    protectedpath=folder/f'{name}_{index:02d}_protected_enclosed.png'
    protected=candidates&~background
    Image.fromarray(protected.astype(np.uint8)*255).save(protectedpath)
    yy,xx=np.where(mask)
    samples=[{'xy':[int(x),int(y)],'beforeRGBA':before[y,x].tolist(),'afterRGBA':after[y,x].tolist()} for y,x in list(zip(yy,xx))[::max(1,len(xx)//8)][:8]]
    return result,{'index':index,'changedPixels':int(mask.sum()),'enclosedIntentionalGreenCandidatesPreserved':int((candidates&~background).sum()),
                   'nativeTransparencyExcluded':native_transparent,
                   'before':baseline.relative_to(ROOT).as_posix(),'beforeSHA256':sha(baseline),
                   'mask':maskpath.relative_to(ROOT).as_posix(),'maskSHA256':sha(maskpath),
                   'protectedEnclosedMask':protectedpath.relative_to(ROOT).as_posix(),'protectedEnclosedMaskSHA256':sha(protectedpath),'rawColorSamples':samples,
                   'alphaExact':True,'redBlueExact':True,'outsideMaskExact':True,'bboxExact':True,'opaquePixelsExact':True}


def dance_frames(clip, reference):
    donors, evidence = {}, []
    for batch in clip['frameBatches']:
        src = ROOT / batch['source']
        cells = native_cells(src, batch['cols'], batch['rows'], keep=batch.get('keepComponents', False))
        for cell, index in enumerate(batch['indices']):
            donors[index] = cells[cell][0]
            evidence.append({'index': index, 'source': batch['source'], 'sourceSHA256': sha(src),
                             'nativeCellBox': cells[cell][1], 'nativeCellSize': list(cells[cell][0].size)})
    name = clip['clip']
    if name == 'yaho1_loop':
        src = ROOT / 'sprites/rebuilt/raw_poses/yaho12.png'
        donors[12] = read_native(src)
        evidence.append({'index':12,'source':src.relative_to(ROOT).as_posix(),'sourceSHA256':sha(src), 'nativeCellSize':list(donors[12].size)})
    frames = [reference.copy() if name == 'yaho1_loop' and i == 13
              else shoe_place(donors[i], PLANS[name][i]*RATIO) for i in range(clip['count'])]
    if name in EFFECTS:
        donor = read_native(ROOT / 'sprites/rebuilt/raw_poses/dance_sparkle.png')
        donor = donor.crop(donor.getbbox())
        for i, stars in EFFECTS[name].items():
            for x,y,h in stars:
                hh = round(h*RATIO)
                star = donor.resize((max(3,round(donor.width*hh/donor.height)),hh),Image.Resampling.LANCZOS)
                frames[i].alpha_composite(star,(round(x*RATIO)-star.width//2,round(y*RATIO)-star.height//2))
    return frames, evidence


def reaction_frames(cfg, reference):
    cols, rows = cfg.get('grid',[4,2])
    src = ROOT/cfg['sheet']
    assert sha(src) == cfg['sha256'], f'Original source changed: {src}'
    cells = native_cells(src,cols,rows,cfg.get('row_offset',0))
    cleanup = {}
    # 투명 모션 시트에는 낮은 알파의 배경 잡점과 셀 경계를 넘은 머리 조각이 있다.
    # 이 세 클립의 계획에는 본체와 떨어진 반짝임·소품 효과가 없다.
    # 연결된 본체와 주변 2px의 안티앨리어싱을 보존하고 제거한 픽셀을 기록한다.
    if cfg.get('preserve_motion',False):
        for i,(native,_) in enumerate(cells):
            arr=np.array(native)
            labels,n=ndimage.label(arr[:,:,3]>8)
            areas=np.bincount(labels.ravel());areas[0]=0
            body=labels==int(areas.argmax())
            near=ndimage.distance_transform_edt(~body)<=2
            remove=(arr[:,:,3]>0)&~near
            count=int(remove.sum())
            if count:
                arr[remove]=0
                cells[i]=(Image.fromarray(arr,'RGBA'),cells[i][1])
                cleanup[i]={'removedNonbodyAlphaPixels':count,'criterion':'outside largest connected character body plus2 native pixels; sheet has no specified disconnected effects'}
    # 512px 중간 이미지를 만들지 않고 기존 셀 중앙 배치의 좌표를 맞춘다.
    # 직사각형 반응 셀의 종횡비는 유지한다.
    frames = []
    for native,_ in cells:
        s = 720/max(native.size)
        frames.append(affine720(native,s,(720-native.width*s)/2,(720-native.height*s)/2))
    rt,rb,rc = body_box(reference)
    top,bottom,center = body_box(frames[0])
    if cfg.get('preserve_motion',False):
        boxes = [f.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox() for f in frames]
        left,upper = min(b[0] for b in boxes),min(b[1] for b in boxes)
        right,lower = max(b[2] for b in boxes),max(b[3] for b in boxes)
        scale = min((rb-rt)/(bottom-top),480*RATIO/(right-left),480*RATIO/(lower-upper))
        tx = min(max(rc-scale*center,16*RATIO-scale*left),496*RATIO-scale*right)
        ty = min(max(rb-scale*bottom,16*RATIO-scale*upper),496*RATIO-scale*lower)
        # 전체 변환을 계산해 원본 셀에서 직접 최종 출력을 만든다.
        # 위의 임시 프레임은 측정용이며 최종 출력의 입력으로 사용하지 않는다.
        output=[]
        for native,_ in cells:
            s=720/max(native.size)
            ox,oy=(720-native.width*s)/2,(720-native.height*s)/2
            output.append(affine720(native,s*scale,ox*scale+tx,oy*scale+ty))
    else:
        scale=(rb-rt)/(bottom-top)
        output=[]
        for (native,_),frame in zip(cells,frames):
            _,b,c=body_box(frame)
            s=720/max(native.size)
            ox,oy=(720-native.width*s)/2,(720-native.height*s)/2
            output.append(affine720(native,s*scale,(ox-c)*scale+rc,(oy-b)*scale+rb))
    output[-1]=output[0].copy()  # 기존 검수된 조립 방식의 루프 닫힘을 유지한다.
    evidence=[{'index':i,'source':cfg['sheet'],'sourceSHA256':sha(src),'nativeCellBox':box,
               'nativeCellSize':list(native.size),'nativeMatteCleanup':cleanup.get(i)} for i,(native,box) in enumerate(cells)]
    return output,evidence


def expand(count,cfg):
    repeats={r['frames'][0]:(r['frames'][1],int(r['times'])) for r in cfg.get('repeats',[])}
    order=[];i=0
    while i<count:
        if i in repeats:
            end,times=repeats[i];order+=list(range(i,end+1))*max(1,times);i=end+1
        else:order.append(i);i+=1
    return [i for i in order for _ in range(max(1,int(cfg.get('holds',{}).get(str(i),1))))]


def contact(name,frames):
    sheet=Image.new('RGB',(5*180,((len(frames)+4)//5)*200),(28,30,37))
    d=ImageDraw.Draw(sheet)
    for i,im in enumerate(frames):
        tile=im.resize((180,180),Image.Resampling.LANCZOS)
        x,y=(i%5)*180,(i//5)*200
        sheet.paste(tile,(x,y),tile);d.text((x+5,y+183),f'{name} {i:02d}',fill='white')
    path=OUT/'qa/dance'/f'{name}_contact.png';path.parent.mkdir(parents=True,exist_ok=True);sheet.save(path)
    return path.relative_to(ROOT).as_posix()


def audit_video(path,expected_frames,duration):
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
    stream=probe['streams'][0]
    assert stream['width']==720 and stream['height']==720 and stream['codec_name']=='vp9'
    assert abs(float(probe['format']['duration'])-duration)<.006
    p=subprocess.Popen(['ffmpeg','-v','error','-c:v','libvpx-vp9','-i',str(path),'-f','rawvideo','-pix_fmt','rgba','pipe:1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    n=0;corners=True;foreground=True
    while True:
        buf=p.stdout.read(720*720*4)
        if not buf:break
        assert len(buf)==720*720*4
        a=np.frombuffer(buf,np.uint8).reshape(720,720,4)[:,:,3]
        corners &= not bool(a[0,0] or a[0,-1] or a[-1,0] or a[-1,-1])
        foreground &= bool(a.max()>200)
        n+=1
    assert p.wait()==0,p.stderr.read().decode()
    assert n==expected_frames and corners and foreground
    return {'codec':'vp9','dimensions':[720,720],'duration':float(probe['format']['duration']),
            'decodedFrames':n,'decodedAlphaCornersZero':corners,'decodedOpaqueForeground':foreground,'videoSHA256':sha(path)}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--clip',nargs='*')
    args=ap.parse_args()
    reference=Image.open(args.reference).convert('RGBA')
    assert reference.size==(720,720)
    manifest=json.loads((ROOT/'anims/rebuild_manifest.json').read_text(encoding='utf-8'))
    reactions=json.loads((ROOT/'anims/obs_reactions.json').read_text())
    ledger_path=ROOT/'anims/hd720_dance.json'
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'version':1,'clips':[]}
    ledger['reference']={'path':args.reference.as_posix(),'sha256':sha(args.reference)}
    sources=[]
    for c in manifest['clips']:
        if c['clip'] in PLANS:sources.append((c['clip'],c,True))
    for cfg in reactions.values():sources.append((cfg['name'],cfg,False))
    for name,cfg,is_dance in sources:
        if args.clip and name not in args.clip:continue
        old=ROOT/('sprites/rebuilt/frames' if is_dance else 'sprites')/name
        preserved={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(old.glob('*.png'))}
        if is_dance:
            frames,evidence=dance_frames(cfg,reference);fps=cfg['fps'];rate=cfg['rate'];timing=ROOT/'sprites/rebuilt/configs'/f'{name}.json'
            native_transparent=False
        else:
            frames,evidence=reaction_frames(cfg,reference);fps=cfg.get('fps',10);rate=1;timing=ROOT/'anims'/f'{name}.json'
            source_image=Image.open(ROOT/cfg['sheet'])
            native_transparent=source_image.mode=='RGBA' and source_image.getchannel('A').getextrema()[0]<255
        settings=json.loads(timing.read_text(encoding='utf-8'))
        order=expand(len(frames),settings)
        dest=OUT/'frames'/name;dest.mkdir(parents=True,exist_ok=True)
        framehash=[];boxes=[];matte_repair=[]
        for i,im in enumerate(frames):
            im,repair=clean_green_edge(im,name,i,native_transparent)
            frames[i]=im
            matte_repair.append(repair)
            assert im.mode=='RGBA' and im.size==(720,720)
            a=np.asarray(im)[:,:,3];assert not np.any(np.concatenate([a[0],a[-1],a[:,0],a[:,-1]])), f'Canvas clipping {name} {i}'
            p=dest/f'{name}_{i:02d}.png';im.save(p);framehash.append(sha(p));boxes.append(im.getbbox())
        video=OUT/'videos'/f'anim_{name}.webm';video.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([sys.executable,str(ROOT/'tools/encode_holds.py'),str(timing),'--fps',str(fps),'--frames-dir',str(dest),'--out',str(video)],check=True,cwd=ROOT)
        audit=audit_video(video,len(order),len(order)/fps)
        original_video=ROOT/'sprites'/f'anim_{name}.webm'
        original_probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(original_video)]))
        original_duration=float(original_probe['format']['duration'])
        assert abs(original_duration-audit['duration'])<.006
        assert all(sha(ROOT/p)==h for p,h in preserved.items())
        entry={'clip':name,'framesDir':dest.relative_to(ROOT).as_posix(),'video':video.relative_to(ROOT).as_posix(),
               'count':len(frames),'fps':fps,'rate':rate,'holds':settings.get('holds',{}),'repeats':settings.get('repeats',[]),
               'expandedTicks':len(order),'sourceLimited':True,'limitation':'Native 314/627px cells constrain real detail; 720px registration is not new ImageGen detail.',
               'method':'Native cell crop/key then one uniform affine registration into720; no final512 frame upscaling; existing gesture/closure/effect/timing plan retained',
               'sourceCells':evidence,'original512FrameHashes':preserved,'generatedFrameSHA256':framehash,'bboxes':boxes,
               'matteRepair':{'condition':'minimum_filter(alpha,size=9)<250 & G-max(R,B)>20 & 20<alpha<250 & background-connected through alpha<250; enclosed greens preserved',
                              'frames':matte_repair,'changedPixels':sum(x['changedPixels'] for x in matte_repair)},
               'originalVideo':{'path':original_video.relative_to(ROOT).as_posix(),'sha256':sha(original_video),'duration':original_duration,'unchangedTimingVerified':True},
               'contact':contact(name,frames),'audit':audit,'review':{'staticVisual':False,'alphaTechnical':True,'runtimeSeams':False}}
        ledger['clips']=[x for x in ledger['clips'] if x['clip']!=name]+[entry]
        ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
        print(f'PASS {name}: {len(frames)} frames / {len(order)} ticks / {fps}fps',flush=True)


if __name__=='__main__':main()
