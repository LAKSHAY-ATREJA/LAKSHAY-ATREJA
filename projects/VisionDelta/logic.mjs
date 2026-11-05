/** Explainable pixel-based inspection of two aligned RGBA images. */
export function inspectPixels(reference,candidate,width,height,{threshold=45,minArea=12}={}){
  if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||reference.length!==width*height*4||candidate.length!==reference.length)throw new Error('Image dimensions do not match');
  if(threshold<0||threshold>255||!Number.isInteger(minArea)||minArea<1)throw new Error('Invalid sensitivity settings');
  const size=width*height,mask=new Uint8Array(size),heat=new Uint8ClampedArray(size*4);
  let changed=0,allDelta=0;
  for(let i=0;i<size;i++){
    const p=i*4;const delta=Math.max(Math.abs(reference[p]-candidate[p]),Math.abs(reference[p+1]-candidate[p+1]),Math.abs(reference[p+2]-candidate[p+2]));
    allDelta+=delta;mask[i]=delta>=threshold?1:0;changed+=mask[i];
    heat[p]=255;heat[p+1]=80;heat[p+2]=84;heat[p+3]=mask[i]?Math.min(225,100+delta):0;
  }
  const visited=new Uint8Array(size),regions=[];const neighbours=[[1,0],[-1,0],[0,1],[0,-1]];
  for(let i=0;i<size;i++){
    if(!mask[i]||visited[i])continue;
    const stack=[i];visited[i]=1;let area=0,left=width,top=height,right=0,bottom=0;
    while(stack.length){const idx=stack.pop(),x=idx%width,y=Math.floor(idx/width);area++;left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);
      for(const [dx,dy] of neighbours){const xx=x+dx,yy=y+dy;if(xx<0||xx>=width||yy<0||yy>=height)continue;const j=yy*width+xx;if(mask[j]&&!visited[j]){visited[j]=1;stack.push(j);}}
    }
    if(area>=minArea)regions.push({x:left,y:top,width:right-left+1,height:bottom-top+1,area});
  }
  regions.sort((a,b)=>b.area-a.area);
  return {width,height,changedPixels:changed,changedPercent:100*changed/size,averageDifference:allDelta/size,regions,mask,heat};
}
export function syntheticPair(size=360){
  // Browser-only, deterministic reference and candidate renders. No external image assets.
  if(typeof document==='undefined')throw new Error('Requires browser canvas');
  const make=()=>{const c=document.createElement('canvas');c.width=c.height=size;return c;};
  const a=make(),b=make();for(const canvas of [a,b]){const c=canvas.getContext('2d');c.fillStyle='#d4dbe2';c.fillRect(0,0,size,size);c.fillStyle='#526475';c.fillRect(50,50,size-100,size-100);c.fillStyle='#91a5b5';c.fillRect(74,73,size-148,size-146);c.strokeStyle='#edf4fc';c.lineWidth=5;c.strokeRect(104,105,size-208,size-210);}
  const c=b.getContext('2d');c.fillStyle='#272f35';c.fillRect(Math.round(size*.41),Math.round(size*.32),38,8);c.fillRect(Math.round(size*.61),Math.round(size*.6),11,37);
  return {reference:a,candidate:b};
}
