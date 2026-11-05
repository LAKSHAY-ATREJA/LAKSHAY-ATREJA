"""Pure image comparison logic for VisionDelta. Classical CV, not trained AI."""
from __future__ import annotations
from collections import deque
from io import BytesIO
import json
import numpy as np
from PIL import Image, ImageDraw, ImageOps

SIZE = (360, 300)


def demo_images() -> tuple[Image.Image, Image.Image]:
    """Illustrative paired inspection images; all synthetic."""
    a = Image.new('RGB', SIZE, (226,231,238))
    d = ImageDraw.Draw(a)
    d.rounded_rectangle((25,25,335,270),radius=20,fill=(245,247,248),outline=(71,91,115),width=4)
    for x in (65,140,215,290):
        for y in (75,155,235):
            d.ellipse((x-11,y-11,x+11,y+11),fill=(58,93,135))
    b = a.copy()
    d = ImageDraw.Draw(b)
    d.rectangle((119,134,160,173),fill=(217,99,70))
    d.ellipse((205,55,234,84),fill=(241,247,248))
    return a,b


def normalise_image(image: Image.Image, size=SIZE) -> Image.Image:
    """Compare images in aligned common canvas. Crops to fill if proportions differ."""
    return ImageOps.fit(image.convert('RGB'),size,method=Image.Resampling.LANCZOS)


def _components(mask: np.ndarray, minimum_area: int) -> list[dict]:
    """Four-connected components. 360x300 canvas limits the computational cost."""
    height,width=mask.shape
    visited=np.zeros(mask.shape,dtype=bool)
    boxes=[]
    for yy in range(height):
        for xx in range(width):
            if not mask[yy,xx] or visited[yy,xx]: continue
            queue=deque([(xx,yy)])
            visited[yy,xx]=True
            count=0
            x0=x1=xx; y0=y1=yy
            while queue:
                x,y=queue.popleft(); count+=1
                x0=min(x0,x); x1=max(x1,x); y0=min(y0,y); y1=max(y1,y)
                for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0<=nx<width and 0<=ny<height and mask[ny,nx] and not visited[ny,nx]:
                        visited[ny,nx]=True;queue.append((nx,ny))
            if count>=minimum_area:
                boxes.append({'x':int(x0),'y':int(y0),'width':int(x1-x0+1),'height':int(y1-y0+1),'changed_pixels':int(count)})
    return sorted(boxes,key=lambda item:-item['changed_pixels'])


def inspect(first: Image.Image, second: Image.Image, threshold: int=45, minimum_area: int=20) -> dict:
    if not 0<=threshold<=255: raise ValueError('Threshold out of bounds')
    if not 1<=minimum_area<=10000: raise ValueError('Area out of bounds')
    a=normalise_image(first)
    b=normalise_image(second)
    delta=np.abs(np.asarray(a,dtype=np.int16)-np.asarray(b,dtype=np.int16))
    magnitude=delta.mean(axis=2)
    mask=magnitude>=threshold
    boxes=_components(mask,minimum_area)
    annotated=b.copy()
    draw=ImageDraw.Draw(annotated)
    for i,box in enumerate(boxes[:30],1):
        x=box['x']; y=box['y']; w=box['width']; h=box['height']
        draw.rectangle((x,y,x+w-1,y+h-1),outline=(236,70,59),width=3)
        draw.text((x,max(0,y-13)),str(i),fill=(170,20,20))
    heat=np.zeros((SIZE[1],SIZE[0],3),dtype=np.uint8)
    heat[:,:,0]=np.minimum(magnitude*3,255).astype(np.uint8)
    heat[:,:,1]=np.where(mask,80,0).astype(np.uint8)
    summary={
        'canvas':{'width':SIZE[0],'height':SIZE[1]},
        'threshold':threshold,
        'minimum_area':minimum_area,
        'changed_pixel_percent':round(float(mask.mean()*100),2),
        'mean_rgb_difference':round(float(magnitude.mean()),2),
        'regions':boxes[:100]
    }
    return {'reference':a,'candidate':b,'annotated':annotated,'heatmap':Image.fromarray(heat),'summary':summary}


def png_bytes(img: Image.Image) -> bytes:
    buf=BytesIO();img.save(buf,format='PNG');return buf.getvalue()
