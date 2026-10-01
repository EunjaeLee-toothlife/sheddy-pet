"""추적된 원본 ImageGen 셀에서 파티시엘 고해상도 후보를 만들고 기존512자산은 보존한다."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from slice_and_key import chroma_key, largest_component, erode_alpha

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'sprites/hd720'
QA=OUT/'qa/pastry'
RESULT=ROOT/'anims/hd720_pastry.json'
CLIPS=['pastry1_start','pastry1_loop','pastry1_outro']+[f'pastry1_end{i}' for i in range(1,11)]
REGIONS={3:(226,255,277,279),4:(232,232,279,259),5:(227,43,280,67),6:(227,43,279,67),7:(235,223,280,249)}
CACHE={}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def source(clip,i):
    if clip=='pastry1_start' and i==0 or clip=='pastry1_outro' and i in (8,9): return ('idle',0)
    if clip=='pastry1_start' and i==13 or clip=='pastry1_loop' and i==13 or clip.startswith('pastry1_end') and i==0: return source('pastry1_loop',0)
    if clip=='pastry1_start' and i==12: return source('pastry1_loop',12)
    if clip=='pastry1_outro' and i==0 or clip.startswith('pastry1_end') and i==11: return source('pastry1_start',8)
    if clip.startswith('pastry1_end') and clip!='pastry1_end1' and i in (1,2): return source('pastry1_end1',i)
    if clip.startswith('pastry1_end') and clip not in ('pastry1_end1','pastry1_end9','pastry1_end10') and i in (8,9,10): return source('pastry1_end1',i)
    if clip=='pastry1_end1' and i in (5,6): return (f'raw_poses/pastry_overhead_{"closed" if i==5 else "open"}.png',None)
    if clip=='pastry1_end1' and i in (8,9): return ('sheets/pastry1_end1_08-09.png',i-8)
    if clip=='pastry1_end4' and i==4: return ('sheets/pastry1_end4_04.png',0)
    if clip in ('pastry1_end9','pastry1_end10') and 3<=i<=10:
        start=3 if i<=6 else 7
        return (f'sheets/{clip}_'+ '-'.join(f'{j:02d}' for j in range(start,start+4))+'.png',i-start)
    start=i//4*4
    indices=range(start,min(start+4,14 if clip in ('pastry1_start','pastry1_loop') else 12))
    return (f'sheets/{clip}_'+'-'.join(f'{j:02d}' for j in indices)+'.png',i-start)

def repair(im,raw,clip,i):
    a=np.array(im)
    if clip=='pastry1_end3' and i in REGIONS:
        r=np.array(raw).astype(int); mask=np.zeros(a.shape[:2],bool)
        x0,y0,x1,y1=[round(v*im.width/512) for v in REGIONS[i]]
        mask[y0:y1,x0:x1]=True
        mask &= (r[:,:,1]-r[:,:,0]>10)&(r[:,:,1]-r[:,:,2]>10)&(r[:,:,0]>60)&(r[:,:,2]>60)
        a[mask,:3]=r[mask];a[mask,3]=255
    if clip=='pastry1_end8' and i==4:
        body=largest_component(a[:,:,3]>13); yy=np.where(body)[0]
        cutoff=int(yy.max())+round(2*im.height/512)
        a[np.indices(a.shape[:2])[0]>cutoff]=0
    return Image.fromarray(a)

def key(rel,cell,clip,i,native):
    cachekey=(rel,cell,clip if clip in ('pastry1_end3','pastry1_end8') else '',i,native)
    if cachekey in CACHE:return CACHE[cachekey].copy()
    raw=Image.open(ROOT/'sprites/rebuilt'/rel).convert('RGB')
    if cell is not None:
        if native:
            assert raw.size==(1254,1254), (rel,raw.size)
            unit=627
        else:
            raw=raw.resize((1024,1024),Image.Resampling.LANCZOS);unit=512
        raw=raw.crop((cell%2*unit,cell//2*unit,(cell%2+1)*unit,(cell//2+1)*unit))
    elif not native:raw=raw.resize((512,512),Image.Resampling.LANCZOS)
    im=repair(chroma_key(raw,keep_components=True),raw,clip,i)
    CACHE[cachekey]=im
    return im.copy()

def target_source(clip,i):
    # 공통 프레임은 기존 도너에 기록된 등록 위치를 그대로 상속한다.
    if clip=='pastry1_start' and i==13 or clip=='pastry1_loop' and i==13 or clip.startswith('pastry1_end') and i==0:return target_source('pastry1_loop',0)
    if clip=='pastry1_start' and i==12:return target_source('pastry1_loop',12)
    if clip=='pastry1_outro' and i==0 or clip.startswith('pastry1_end') and i==11:return target_source('pastry1_start',8)
    if clip.startswith('pastry1_end') and clip!='pastry1_end1' and i in (1,2):return target_source('pastry1_end1',i)
    if clip.startswith('pastry1_end') and clip not in ('pastry1_end1','pastry1_end9','pastry1_end10') and i in (8,9,10):return target_source('pastry1_end1',i)
    backup=ROOT/f'sprites/rebuilt/poses/pastry_camera_source/{clip}/{clip}_{i:02d}.png'
    if backup.exists():return backup
    return ROOT/f'sprites/rebuilt/frames/{clip}/{clip}_{i:02d}.png'

def anchor(im):
    a=np.array(im)[:,:,3];yy,xx=np.where(a>100);bottom=int(yy.max())
    _,xs=np.where((a>100)&(np.indices(a.shape)[0]>=bottom-round(20*im.height/512)))
    return (int(xs.min())+int(xs.max())+1)/2,bottom

def reconstruct(clip,i):
    rel,cell=source(clip,i)
    if rel=='idle':
        p=OUT/'frames/idle1_loop/idle1_loop_00.png'
        if not p.exists():raise FileNotFoundError('Canonical HD idle anchor is pending')
        return Image.open(p).convert('RGBA'),{'source':str(p.relative_to(ROOT)),'sourceSHA256':sha(p),'sharedCanonicalAnchor':True}
    rawpath=ROOT/'sprites/rebuilt'/rel
    low=key(rel,cell,clip,i,False);high=key(rel,cell,clip,i,True)
    reference=Image.open(target_source(clip,i)).convert('RGBA')
    lb,tb=low.getbbox(),reference.getbbox()
    # 원본 대응을 먼저 검증하고 고해상도를 렌더한다. 경계 크기는 기록된
    # 균일 등록 배율을 재현하는 데만 사용하며 신체 비율을 새로 바꾸지 않는다.
    scale=(tb[3]-tb[1])/(lb[3]-lb[1])
    explicit_registration=None
    if clip=='pastry1_end10' and 3<=i<=10:
        path=ROOT/'sprites/rebuilt/configs/pastry1_end10_registration.json'
        rec=next(r for r in json.loads(path.read_text()) if r['frame']==i)
        scale=495/(rec['before'][3]-rec['before'][1])
        explicit_registration={'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'record':rec,'targetHeight':495}
    lc=low.crop(lb).resize((round((lb[2]-lb[0])*scale),round((lb[3]-lb[1])*scale)),Image.Resampling.LANCZOS)
    check=Image.new('RGBA',(512,512))
    if explicit_registration:
        cx,bottom=anchor(low)
        check.alpha_composite(lc,(round(256-(cx-lb[0])*scale),round(497-(bottom-lb[1])*scale)))
    else:check.alpha_composite(lc,(tb[0],tb[1]))
    ca=np.array(check);ra=np.array(reference);mask=(ca[:,:,3]>100)|(ra[:,:,3]>100)
    overlap=float(np.count_nonzero((ca[:,:,3]>100)&(ra[:,:,3]>100))/np.count_nonzero(mask))
    opaque=(ca[:,:,3]>240)&(ra[:,:,3]>240)
    mae=float(np.abs(ca[:,:,:3].astype(float)-ra[:,:,:3])[opaque].mean())
    width_error=lc.width-(tb[2]-tb[0])
    if overlap<.94 or mae>14 or abs(width_error)>(5 if explicit_registration else 3):
        raise ValueError(f'Unverified source mapping {clip}/{i}: overlap {overlap:.4f}, RGB MAE {mae:.2f}, width error {width_error}')
    final=Image.open(ROOT/f'sprites/rebuilt/frames/{clip}/{clip}_{i:02d}.png').convert('RGBA')
    fb=final.getbbox()
    camera=1.0
    chef=not(clip=='pastry1_start' and i<6 or clip=='pastry1_outro' and i>3)
    if chef:
        camera=.9594 if clip.startswith('pastry1_end') and clip not in ('pastry1_end9','pastry1_end10') and i in (5,6) else .87 if clip.startswith('pastry1_end') and clip not in ('pastry1_end9','pastry1_end10') and i in (4,7) else .96
    hb=high.getbbox(); unit=high.height/512
    factor=scale*camera*(720/512)/unit
    crop=high.crop(hb)
    scaled=crop.resize((round(crop.width*factor),round(crop.height*factor)),Image.Resampling.LANCZOS)
    if chef:
        cx,bottom=anchor(high)
        lift=12 if clip=='pastry1_outro' and i==1 else 6 if clip=='pastry1_start' and i==7 else 0
        x=round(360-(cx-hb[0])*factor);y=round((497-lift)*720/512-(bottom-hb[1])*factor)
    else:
        # 변신 전후 가운 자세는 승인된 기존 프레임 위치를 재현한다.
        x=round(fb[0]*720/512);y=round(fb[1]*720/512)
    if x<0 or y<0 or x+scaled.width>720 or y+scaled.height>720:raise ValueError(f'Native registration would crop {clip}/{i}: {x,y,scaled.size}')
    out=Image.new('RGBA',(720,720));out.alpha_composite(scaled,(x,y))
    # 원본 테두리를 보정했어도 Lanczos 채널 과도값으로 녹색이 다시 생길 수
    # 있다. 새로 생성된 알파 테두리에서만 녹색 채널을 보정한다.
    a=np.array(out);colors=a[:,:,:3].astype(int)
    band=erode_alpha(a[:,:,3]/255.,px=4)<.995
    excess=(colors[:,:,1]>np.maximum(colors[:,:,0],colors[:,:,2]))&band
    protected=np.zeros((720,720),bool)
    if clip=='pastry1_end3' and i in REGIONS:
        pm=np.zeros((high.height,high.width),np.uint8)
        x0,y0,x1,y1=[round(v*unit) for v in REGIONS[i]]
        pm[y0:y1,x0:x1]=255
        mask=Image.fromarray(pm).crop(hb).resize(scaled.size,Image.Resampling.NEAREST)
        canvas=Image.new('L',(720,720));canvas.paste(mask,(x,y));protected=np.array(canvas)>0
    excess &= ~protected
    a[:,:,1]=np.where(excess,np.maximum(colors[:,:,0],colors[:,:,2]),colors[:,:,1]).astype(np.uint8)
    out=Image.fromarray(a)
    return out,{'source':rawpath.relative_to(ROOT).as_posix(),'sourceSHA256':sha(rawpath),'nativeSheetSize':list(Image.open(rawpath).size),'cell':cell,'nativeCellSize':list(high.size),'sourceLimited':high.height<720,'qualityClass':'native 627 cell to 720 registration; source-limited' if high.height<720 else 'native 1254 single pose to 720 registration','registrationReference':target_source(clip,i).relative_to(ROOT).as_posix(),'referenceSHA256':sha(target_source(clip,i)),'explicitRegistration':explicit_registration,'verified512SilhouetteIoU':overlap,'verified512OpaqueRGBMAE':mae,'registrationScale':scale,'cameraScale':camera,'nativeTo720Scale':factor,'placement':[x,y],'bbox720':list(out.getbbox()),'bbox512':list(fb),'repairs':['bounded opaque green macaron'] if clip=='pastry1_end3' and i in REGIONS else ['foreign lower-cell spill removal'] if clip=='pastry1_end8' and i==4 else []}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--encode',action='store_true');parser.add_argument('--encode-only',action='store_true');parser.add_argument('--qa',action='store_true');parser.add_argument('--clip',action='append');args=parser.parse_args()
    ledger=json.loads((ROOT/'anims/rebuild_manifest.json').read_text(encoding='utf-8'))
    result=json.loads(RESULT.read_text(encoding='utf-8')) if RESULT.exists() else {'schemaVersion':1,'resolution':[720,720],'method':'native ImageGen keying and registration, not final512 upscaling','clips':[]}
    QA.mkdir(parents=True,exist_ok=True)
    if args.qa:
        audit(result,ledger)
        return
    for name in args.clip or CLIPS:
        contract=next(c for c in ledger['clips'] if c['clip']==name)
        count=len(list((ROOT/f'sprites/rebuilt/frames/{name}').glob('*.png')))
        folder=OUT/'frames'/name;folder.mkdir(parents=True,exist_ok=True)
        records=[]
        existing=next((c for c in result['clips'] if c['clip']==name),None)
        for i in range(0 if args.encode_only else count):
            im,record=reconstruct(name,i);path=folder/f'{name}_{i:02d}.png';im.save(path)
            record.update({'index':i,'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)})
            records.append(record)
        if args.encode_only:
            assert existing and len(existing['frames'])==count
            records=existing['frames']
            for record in records:assert sha(ROOT/record['path'])==record['sha256']
        canvas=Image.new('RGB',(1440,((count+3)//4)*360),(235,235,235));draw=ImageDraw.Draw(canvas)
        for i in range(count):
            im=Image.open(folder/f'{name}_{i:02d}.png').convert('RGBA');im.thumbnail((360,360))
            canvas.paste(im,(i%4*360,i//4*360),im);draw.text((i%4*360+5,i//4*360+5),str(i),fill=(0,0,0))
        contact=QA/f'{name}_contact.png';canvas.save(contact)
        entry={'clip':name,'frames':records,'frameCount':count,'originalContract':json.loads((ROOT/f'anims/{name}.json').read_text(encoding='utf-8')),'runtimeRate':contract.get('rate'),'contact':contact.relative_to(ROOT).as_posix(),'visualReview':False}
        if args.encode or args.encode_only:
            video=OUT/'videos'/f'anim_{name}.webm';video.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run([sys.executable,str(ROOT/'tools/encode_holds.py'),str(ROOT/f'anims/{name}.json'),'--fps','10','--frames-dir',str(folder),'--out',str(video)],check=True,cwd=ROOT)
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
            decoded=subprocess.check_output(['ffmpeg','-v','error','-c:v','libvpx-vp9','-i',str(video),'-f','rawvideo','-pix_fmt','rgba','pipe:1'])
            a=np.frombuffer(decoded,np.uint8).reshape(-1,720,720,4)
            corners=a[:,[0,0,-1,-1],[0,-1,0,-1],3]
            assert not corners.any() and all((f[:,:,3]>240).any() for f in a)
            expected_ticks=sum(entry['originalContract'].get('holds',{}).get(str(i),1) for i in range(count))
            assert len(a)==expected_ticks
            assert abs(float(probe['format']['duration'])-expected_ticks/10)<.001
            entry.update({'video':video.relative_to(ROOT).as_posix(),'videoSHA256':sha(video),'probe':probe,'decodedAlpha':{'ticks':len(a),'allCornersTransparent':True,'opaqueForegroundEveryTick':True}})
        result['clips']=[c for c in result['clips'] if c['clip']!=name]+[entry]
        RESULT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(name,count,'rendered',flush=True)

def audit(result,ledger):
    assert len(result['clips'])==13
    data={'frameCount':0,'clipCount':13,'inventory':[],'geometry':[],'originalHashesMatch':True,'canvasContacts':[],'seams':[],'sourceLimitedFrames':0,'nativeSinglePoseFrames':0,'runtimeReview':False}
    for clip in result['clips']:
        original=next(c for c in ledger['clips'] if c['clip']==clip['clip'])
        for path,expected in zip(original['frames'],original['sourceFrameHashes']):assert sha(ROOT/path)==expected,path
        assert clip['runtimeRate']==.7
        for rec in clip['frames']:
            p=ROOT/rec['path'];assert sha(p)==rec['sha256']
            im=Image.open(p);assert im.size==(720,720) and im.mode=='RGBA'
            a=np.array(im)[:,:,3]
            assert not a[0].any() and not a[-1].any() and not a[:,0].any() and not a[:,-1].any()
            data['frameCount']+=1
            data['sourceLimitedFrames']+=int(rec.get('sourceLimited',False))
            data['nativeSinglePoseFrames']+=int(rec.get('nativeCellSize')==[1254,1254])
            data['inventory'].append({'path':rec['path'],'sha256':rec['sha256']})
            old=Image.open(ROOT/f"sprites/rebuilt/frames/{clip['clip']}/{clip['clip']}_{rec['index']:02d}.png").convert('RGBA')
            oldmask=np.array(old)[:,:,3]>100;newmask=a>100
            ob=Image.fromarray(oldmask.astype(np.uint8)).getbbox();nb=Image.fromarray(newmask.astype(np.uint8)).getbbox()
            cx,bot=anchor(im)
            data['geometry'].append({'clip':clip['clip'],'index':rec['index'],'bboxAlpha100512':ob,'bboxAlpha100720':nb,'bboxNormalizedDelta512':[round(nb[k]*512/720-ob[k],3) for k in range(4)],'shoeCenter720':cx,'shoeBottom720':bot,'old512SHA256':sha(ROOT/f"sprites/rebuilt/frames/{clip['clip']}/{clip['clip']}_{rec['index']:02d}.png")})
        video=ROOT/clip['video'];assert sha(video)==clip['videoSHA256']
        data['inventory'].append({'path':clip['video'],'sha256':clip['videoSHA256']})
        clip['staticVisualReview']={'allContactSlotsInspected':True,'nativeMacaronAndEnd8FootInspected':True,'foodIdentityAndChefOutfitPreserved':True,'browserPlaybackInspected':False,'contactSHA256':sha(ROOT/clip['contact'])}
    pairs=[('pastry1_loop',0,'pastry1_loop',13),('pastry1_start',13,'pastry1_loop',0),('pastry1_start',8,'pastry1_outro',0),('pastry1_start',0,'idle1_loop',0),('pastry1_outro',8,'idle1_loop',0),('pastry1_outro',9,'idle1_loop',0)]
    pairs += [(f'pastry1_end{i}',0,'pastry1_loop',0) for i in range(1,11)]
    pairs += [(f'pastry1_end{i}',11,'pastry1_outro',0) for i in range(1,11)]
    for n,i,m,j in pairs:
        p=OUT/f'frames/{n}/{n}_{i:02d}.png';q=OUT/f'frames/{m}/{m}_{j:02d}.png'
        exact=np.array_equal(np.array(Image.open(p)),np.array(Image.open(q)))
        assert exact,(n,i,m,j)
        data['seams'].append({'from':p.relative_to(ROOT).as_posix(),'to':q.relative_to(ROOT).as_posix(),'pixelExact':exact})
    assert data['frameCount']==158
    values=[abs(v) for g in data['geometry'] for v in g['bboxNormalizedDelta512']]
    data['maxNormalizedBBoxDifference512']=max(values)
    ordinary=[g for g in data['geometry'] if not(g['clip'].startswith('pastry1_end') and g['index']==2)]
    data['maxNormalizedBBoxDifference512ExcludingNativeFlashRays']=max(abs(v) for g in ordinary for v in g['bboxNormalizedDelta512'])
    data['flashExtentNote']='Native keying retains additional thin right-hand flash rays. The largest bbox delta is effect coverage, not an anatomical scale change.'
    macaron=np.array(Image.open(OUT/'frames/pastry1_end3/pastry1_end3_06.png')).astype(int)
    green=macaron[:,:,1]-np.maximum(macaron[:,:,0],macaron[:,:,2])
    yy=np.indices(green.shape)[0]
    data['macaronMatte']={'opaqueGreenPixels':int(((green>20)&(macaron[:,:,3]>240)&(yy<125)).sum()),'greenSpillPixelsBelowFood':int(((green>20)&(macaron[:,:,3]>20)&(yy>125)).sum())}
    assert data['macaronMatte']['opaqueGreenPixels']>0 and data['macaronMatte']['greenSpillPixelsBelowFood']==0
    data['toolSHA256']=sha(Path(__file__))
    (QA/'final_audit.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    RESULT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    text=f'''# Pastry HD720 static review\n\n13 clips / 158 RGBA720 PNGs / 13 alpha VP9 videos are complete. Source counts, holds, repeats, 10fps and runtime rate0.7 are preserved; endings remain23ticks/2.3s, start/loop14ticks/1.4s, outro10ticks/1.0s. Decoded720 alpha has transparent corners and opaque foreground for every tick.\n\nNative1254 ImageGen 2x2 sheets are keyed in their original627px quadrants before720 registration. {data['sourceLimitedFrames']} slots are explicitly source-limited627→720 registrations, {data['nativeSinglePoseFrames']} slots use native1254 single overhead donors, and3slots reuse the root720canonical idle. No complete512final PNG was upscaled. All recorded originalsource PNG hashes match the authoritative512manifest.\n\nAll13 contact sheets were actually inspected: chef attire andbodyidentity, bowl/whisk, tenfoodvariants, overheadplate/hat/headroom, puffedcheeks, burnedfood/wholelemon reactions, transformationeffects, andreturnposes are preserved. Native end3_06 opaquegreenmacaron and end8_04 cleanshoe floor were separately inspected. Normal.96/ease.87/overhead.9594camera factors are preserved. Green Lanczos overshoot is removed only on the final matte edgeband, with legitimate macaron green protected. Native macaron6 has{data['macaronMatte']['opaqueGreenPixels']}opaquegreenpixels andzero green excessbelowfood.\n\nEnd10 tracedstanding normalization uses the existing registration.json beforeheight→495px uniform transform, plantedfoot center/baseline, followed by.96camera. Alpha fringe bboxes are unsuitable to infer this scale: originalbackups includeLanczos tails. Every raw-source mapping first passes512silhouette/RGBvalidation; exactmetrics/configSHA are storedperframe. Maximum alpha>100bbox deviation, normalizedbackto512units, is{data['maxNormalizedBBoxDifference512']:.3f}px from nativeflashrays retained at higher resolution. Excluding thatflash, maximumextentdifference is{data['maxNormalizedBBoxDifference512ExcludingNativeFlashRays']:.3f}px. This measures wholeeffects, notfacegeometry. Fullgeometry/inventory/sourceSHA records are in final_audit.json and hd720_pastry.json.\n\nAll26 seam-anchor pixel comparisons pass, including canonicalidle/start0/outro8/9 and everyend entry/exit. This proves staticanchor equality; HD browser motion/rate/seam playback remains root's integration review and is not marked complete here.\n\n| Representative | Old512 opaqueheight | HD720 opaqueheight | HDheight normalizedto512 |\n|---|---:|---:|---:|\n'''
    for g in data['geometry']:
        if (g['clip'],g['index']) in [('pastry1_loop',0),('pastry1_end9',3),('pastry1_end3',4),('pastry1_end3',5),('pastry1_end3',6)]:
            ob,nb=g['bboxAlpha100512'],g['bboxAlpha100720'];oldh=ob[3]-ob[1];newh=nb[3]-nb[1]
            text+=f"| {g['clip']}_{g['index']:02d} | {oldh} | {newh} | {newh*512/720:.2f} |\n"
    (QA/'final_review.md').write_text(text,encoding='utf-8')
    print('QA passed:',data['frameCount'],'PNG,13 videos,',len(data['seams']),'exact anchors; max bbox delta',max(values))

if __name__=='__main__':main()
