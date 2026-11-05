"""VisionDelta visual QA: registration, structural differences, region analysis.

A reproducible, classical computer vision portfolio prototype. Candidate changes
are not certified defects. No external inference or API credentials are required.
"""
from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile, BadZipFile
import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

MAX_EDGE = 900
MAX_PIXELS = 12_000_000


def demo_pair(seed: int = 17):
    """Industrial inspection fixture with textured features, real local changes and drift."""
    rng = np.random.default_rng(seed)
    width, height = 800, 500
    yy, xx = np.mgrid[:height, :width]
    background = np.stack((
        225 + 8*np.sin(xx/19) + rng.normal(0, 3, (height,width)),
        230 + 6*np.cos(yy/17) + rng.normal(0, 3, (height,width)),
        235 + 5*np.sin((xx+yy)/23) + rng.normal(0,3,(height,width))),
        axis=-1).clip(0,255).astype("uint8")
    before = Image.fromarray(background)
    d = ImageDraw.Draw(before)
    d.rounded_rectangle((42,37,755,458),radius=18,fill=(40,52,70),outline=(8,22,33),width=6)
    d.rounded_rectangle((70,68,730,217),radius=11,fill=(99,117,136),outline=(179,202,205),width=4)
    for j in range(9):
        x = 94 + j*73
        d.rounded_rectangle((x,88,x+45,191),radius=7,fill=(156,175,177),outline=(228,240,234),width=3)
        d.ellipse((x+12,106,x+32,126),fill=(24,43,53))
        d.line((x+10,160,x+35,160),fill=(37,60,72),width=4)
    d.line([(72,253),(726,253)], fill=(62,184,170),width=18)
    for row in range(2):
        for col in range(9):
            x,y=105+col*73,316+row*102
            d.rounded_rectangle((x-24,y-23,x+27,y+25),radius=7,fill=(183,200,204),
                                outline=(241,245,243),width=3)
            d.ellipse((x-10,y-10,x+10,y+10),fill=(40,61,79))
    after=before.copy()
    a=ImageDraw.Draw(after)
    truth=Image.new("L",(width,height),0)
    td=ImageDraw.Draw(truth)
    # Missing fastener, thermally discoloured module and thin surface scratch.
    a.ellipse((527,409,547,430),fill=(184,201,203))
    td.ellipse((526,408,548,431),fill=255)
    a.rounded_rectangle((313,98,351,187),radius=5,fill=(181,84,70))
    td.rounded_rectangle((313,98,351,187),radius=5,fill=255)
    scratch=[(115,448),(184,440),(250,446),(311,420)]
    a.line(scratch,fill=(243,231,204),width=9,joint="curve")
    td.line(scratch,fill=255,width=12,joint="curve")
    # Deliberately include camera movement and exposure drift in the demo.
    array=np.clip(np.asarray(after,dtype=np.float32)*1.025+2,0,255).astype("uint8")
    transform=cv2.getRotationMatrix2D((width/2,height/2),.8,1)
    transform[:,2]+= [6,-4]
    drifted=cv2.warpAffine(array,transform,(width,height),flags=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_REFLECT)
    return before,Image.fromarray(drifted),truth


def _image_array(image: Image.Image):
    if image.width*image.height>MAX_PIXELS or min(image.size)<40:
        raise ValueError("Images must be at least 40x40 and at most 12 megapixels.")
    rgb=np.asarray(image.convert("RGB"))
    h,w=rgb.shape[:2]
    scale=min(1,MAX_EDGE/max(h,w))
    return cv2.resize(rgb,(round(w*scale),round(h*scale)),interpolation=cv2.INTER_AREA) if scale<1 else rgb


def register(reference: np.ndarray,candidate: np.ndarray,method="auto"):
    """ORB/RANSAC homography, ECC affine fallback, or deliberate bypass."""
    h,w=reference.shape[:2]
    if candidate.shape[:2]!=(h,w):
        candidate=cv2.resize(candidate,(w,h),interpolation=cv2.INTER_AREA)
    valid=np.full((h,w),255,dtype="uint8")
    info={"method":"Unaligned","success":False,"matches":0,"inliers":0,
          "quality":None,"note":"Registration could not be established; inspect alignment."}
    if method=="off":
        info["note"]="Geometric alignment disabled by user."
        return candidate,valid,info
    if method not in ("auto","feature","ecc"):
        raise ValueError("Invalid registration mode.")
    gray_a=cv2.cvtColor(reference,cv2.COLOR_RGB2GRAY)
    gray_b=cv2.cvtColor(candidate,cv2.COLOR_RGB2GRAY)
    if method in ("auto","feature"):
        orb=cv2.ORB_create(nfeatures=1600)
        key_a,des_a=orb.detectAndCompute(gray_a,None)
        key_b,des_b=orb.detectAndCompute(gray_b,None)
        if des_a is not None and des_b is not None and len(des_a)>9 and len(des_b)>9:
            pairs=cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(des_b,des_a,k=2)
            matches=[first for first,second in pairs if first.distance<.75*second.distance]
            info["matches"]=len(matches)
            if len(matches)>=10:
                src=np.float32([key_b[m.queryIdx].pt for m in matches]).reshape(-1,1,2)
                dst=np.float32([key_a[m.trainIdx].pt for m in matches]).reshape(-1,1,2)
                matrix,mask=cv2.findHomography(src,dst,cv2.RANSAC,4)
                inliers=int(mask.sum()) if mask is not None else 0
                info["inliers"]=inliers
                if matrix is not None and inliers>=9 and .6<np.linalg.det(matrix[:2,:2])<1.5:
                    mapped=cv2.warpPerspective(candidate,matrix,(w,h))
                    valid=cv2.warpPerspective(valid,matrix,(w,h),flags=cv2.INTER_NEAREST)
                    info.update({"method":"ORB + RANSAC","success":True,
                                 "quality":round(inliers/len(matches),3),
                                 "note":"Feature-correspondence registration."})
                    return mapped,valid,info
    if method in ("auto","ecc"):
        try:
            a=cv2.GaussianBlur(cv2.equalizeHist(gray_a),(5,5),0).astype("float32")/255
            b=cv2.GaussianBlur(cv2.equalizeHist(gray_b),(5,5),0).astype("float32")/255
            warp=np.eye(2,3,dtype="float32")
            criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,90,1e-5)
            corr,warp=cv2.findTransformECC(a,b,warp,cv2.MOTION_AFFINE,criteria)
            if corr>.32:
                mapped=cv2.warpAffine(candidate,warp,(w,h),flags=cv2.WARP_INVERSE_MAP|cv2.INTER_LINEAR)
                valid=cv2.warpAffine(valid,warp,(w,h),flags=cv2.WARP_INVERSE_MAP|cv2.INTER_NEAREST)
                info.update({"method":"ECC affine","success":True,"quality":round(float(corr),3),
                             "note":"Intensity-based affine registration."})
                return mapped,valid,info
        except cv2.error:
            pass
    return candidate,valid,info


def inspect_pair(before: Image.Image,after: Image.Image,sensitivity=.31,min_area=90,
                 alignment="auto",edge_margin=2,truth:Image.Image|None=None):
    if not .08<=sensitivity<=.9 or not 10<=min_area<=10000:
        raise ValueError("Invalid sensitivity or minimum area.")
    if not 0<=edge_margin<=12:
        raise ValueError("Edge exclusion out of bounds.")
    ref=_image_array(before)
    cand=_image_array(after)
    aligned,valid,reg=register(ref,cand,alignment)
    h,w=ref.shape[:2]
    # Eliminate registration boundary contamination.
    roi=cv2.erode(valid,np.ones((11,11),dtype="uint8"))>0
    margin=round(min(h,w)*edge_margin/100)
    if margin:
        roi[:margin,:]=False
        roi[-margin:,:]=False
        roi[:,:margin]=False
        roi[:,-margin:]=False
    gray_a=cv2.cvtColor(ref,cv2.COLOR_RGB2GRAY)
    gray_b=cv2.cvtColor(aligned,cv2.COLOR_RGB2GRAY)
    clahe=cv2.createCLAHE(clipLimit=1.8,tileGridSize=(8,8))
    a=clahe.apply(gray_a).astype("float32")/255
    b=clahe.apply(gray_b).astype("float32")/255
    # Local structural similarity without a pretrained image model.
    mu_a=cv2.GaussianBlur(a,(9,9),1.5)
    mu_b=cv2.GaussianBlur(b,(9,9),1.5)
    sigma_a=cv2.GaussianBlur(a*a,(9,9),1.5)-mu_a**2
    sigma_b=cv2.GaussianBlur(b*b,(9,9),1.5)-mu_b**2
    cov=cv2.GaussianBlur(a*b,(9,9),1.5)-mu_a*mu_b
    ssim=((2*mu_a*mu_b+.01**2)*(2*cov+.03**2))/(
          (mu_a**2+mu_b**2+.01**2)*(sigma_a+sigma_b+.03**2)+1e-9)
    structural=np.clip(1-ssim,0,1)
    lab_a=cv2.cvtColor(ref,cv2.COLOR_RGB2LAB).astype("float32")
    lab_b=cv2.cvtColor(aligned,cv2.COLOR_RGB2LAB).astype("float32")
    chroma=np.clip(np.linalg.norm(lab_a-lab_b,axis=2)/110,0,1)
    # Require stronger response for purely chromatic drift than for structural change.
    evidence=.77*structural+.23*chroma
    mask=((evidence>=sensitivity)&roi).astype("uint8")*255
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),dtype="uint8"))
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),dtype="uint8"))
    count,labels,stats,_=cv2.connectedComponentsWithStats(mask,8)
    final=np.zeros_like(mask)
    regions=[]
    for idx in range(1,count):
        x,y,bw,bh,area=[int(v) for v in stats[idx]]
        if area<min_area:
            continue
        local=labels[y:y+bh,x:x+bw]==idx
        score=float(evidence[y:y+bh,x:x+bw][local].mean())
        final[labels==idx]=255
        regions.append({"x":x,"y":y,"width":bw,"height":bh,"area_px":area,
                        "change_score":round(score,3),
                        "priority":"High" if score>.58 else ("Medium" if score>.38 else "Review")})
    regions.sort(key=lambda q:q["area_px"],reverse=True)
    for i,r in enumerate(regions,1):
        r["region"]=f"R-{i:02}"
    annotated=aligned.copy()
    for r in regions[:50]:
        x,y,bw,bh=(r[k] for k in ("x","y","width","height"))
        cv2.rectangle(annotated,(x,y),(x+bw,y+bh),(240,84,80),3)
        cv2.putText(annotated,r["region"],(x,max(20,y-8)),cv2.FONT_HERSHEY_SIMPLEX,.55,
                    (248,105,90),2,cv2.LINE_AA)
    heat=cv2.applyColorMap(np.clip(evidence*255,0,255).astype("uint8"),cv2.COLORMAP_INFERNO)
    heat=cv2.cvtColor(heat,cv2.COLOR_BGR2RGB)
    heat[~roi]=0
    evaluation=None
    if truth is not None:
        truth_array=np.asarray(truth.convert("L").resize((w,h),Image.Resampling.NEAREST))>127
        predicted=final>0
        tp=int((truth_array&predicted&roi).sum())
        fp=int((~truth_array&predicted&roi).sum())
        fn=int((truth_array&~predicted&roi).sum())
        evaluation={"precision":round(tp/(tp+fp),3) if tp+fp else 0.0,
                    "recall":round(tp/(tp+fn),3) if tp+fn else 0.0,
                    "iou":round(tp/(tp+fp+fn),3) if tp+fp+fn else 1.0}
    summary={"regions":regions[:100],"region_count":len(regions),
             "flagged_area_pct":round(float((final>0).sum()/max(1,roi.sum())*100),2),
             "structural_similarity":round(float(ssim[roi].mean()),3) if roi.any() else 0.0,
             "valid_overlap_pct":round(float(roi.mean()*100),1),
             "registration":reg,"evaluation":evaluation,
             "parameters":{"sensitivity":sensitivity,"min_area":min_area,"alignment":alignment},
             "note":"Potential changes require human verification. Lighting and imperfect alignment cause false positives."}
    images={"Reference":Image.fromarray(ref),"Candidate":Image.fromarray(cand),
            "Registered":Image.fromarray(aligned),
            "Overlay":Image.fromarray(cv2.addWeighted(ref,.5,aligned,.5,0)),
            "Regions":Image.fromarray(annotated),"Evidence heatmap":Image.fromarray(heat),
            "Segmentation mask":Image.fromarray(final)}
    return {"images":images,"summary":summary}


def png_bytes(image:Image.Image)->bytes:
    out=BytesIO()
    image.save(out,format="PNG")
    return out.getvalue()


def batch_inspect(data:bytes,sensitivity=.31,min_area=90):
    """Small archive format: before/name.png matched with after/name.png."""
    if len(data)>35_000_000:
        raise ValueError("Archive exceeds 35 MB.")
    try:
        z=ZipFile(BytesIO(data))
    except BadZipFile as exc:
        raise ValueError("Invalid ZIP archive.") from exc
    with z:
        members=z.infolist()
        if len(members)>36 or sum(m.file_size for m in members)>70_000_000:
            raise ValueError("Archive is too large.")
        candidates={"before":{},"after":{}}
        for info in members:
            path=info.filename.replace("\\","/")
            parts=path.split("/")
            if len(parts)==2 and parts[0] in candidates and parts[1].lower().endswith((".png",".jpg",".jpeg")):
                candidates[parts[0]][parts[1]]=info
        names=sorted(set(candidates["before"])&set(candidates["after"]))
        if not names or len(names)>6:
            raise ValueError("Provide 1 to 6 matching before/ and after/ image pairs.")
        results=[]
        for name in names:
            images=[]
            for folder in ("before","after"):
                entry=candidates[folder][name]
                if entry.file_size>9_000_000:
                    raise ValueError("Each uncompressed image must be under 9 MB.")
                with Image.open(BytesIO(z.read(entry))) as picture:
                    picture.load()
                    images.append(picture.copy())
            s=inspect_pair(images[0],images[1],sensitivity,min_area)["summary"]
            results.append({"image":name,"regions":s["region_count"],"flagged_area_pct":s["flagged_area_pct"],
                            "similarity":s["structural_similarity"],
                            "registration":s["registration"]["method"]})
        return pd.DataFrame(results)
