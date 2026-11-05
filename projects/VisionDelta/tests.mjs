import assert from 'node:assert/strict';import {inspectPixels} from './logic.mjs';
const w=12,h=12,a=new Uint8ClampedArray(w*h*4),b=new Uint8ClampedArray(a);
for(let y=4;y<8;y++)for(let x=3;x<7;x++){const p=(y*w+x)*4;b[p]=230;}
let r=inspectPixels(a,b,w,h,{threshold:40,minArea:3});
assert.equal(r.regions.length,1);assert.equal(r.regions[0].area,16);
assert.deepEqual([r.regions[0].x,r.regions[0].y,r.regions[0].width,r.regions[0].height],[3,4,4,4]);
assert.equal(r.changedPixels,16);assert.ok(r.changedPercent>11&&r.changedPercent<12);
assert.equal(inspectPixels(a,b,w,h,{threshold:250,minArea:3}).regions.length,0);
assert.equal(inspectPixels(a,b,w,h,{threshold:40,minArea:17}).regions.length,0);
assert.throws(()=>inspectPixels(a,b,w,8),/dimensions/);
assert.throws(()=>inspectPixels(a,b,w,h,{minArea:0}),/settings/);
console.log('VisionDelta: 9 assertions passed');
