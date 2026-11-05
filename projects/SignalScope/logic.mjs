/** Explainable, causal anomaly detection; uses only observations preceding each point. */
export const median = values => {
  if (!values.length) return NaN;
  const sorted = [...values].sort((a,b)=>a-b), mid=Math.floor(sorted.length/2);
  return sorted.length%2 ? sorted[mid] : (sorted[mid-1]+sorted[mid])/2;
};
export const mad = values => {
  const m=median(values);
  return median(values.map(v=>Math.abs(v-m)));
};
export function parseCSV(text) {
  const lines=text.trim().split(/\r?\n/).filter(s=>s.trim());
  if(lines.length<2) throw new Error('CSV must include a header and at least one row.');
  const headers=lines[0].split(',').map(s=>s.trim().toLowerCase());
  const d=headers.indexOf('date'), v=headers.findIndex(x=>['value','volume','demand','count'].includes(x));
  if(d<0||v<0) throw new Error('Expected date and value (or demand/volume/count) columns.');
  const seen=new Set();
  const records=lines.slice(1).map((line,i)=>{
    const cells=line.split(',').map(s=>s.trim()); const date=cells[d], value=Number(cells[v]);
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||Number.isNaN(Date.parse(date+'T00:00:00Z'))||!Number.isFinite(value)||value<0) throw new Error(`Invalid date or non-negative number on row ${i+2}.`);
    if(seen.has(date))throw new Error(`Duplicate date: ${date}`);seen.add(date);
    return {date,value};
  }).sort((a,b)=>a.date.localeCompare(b.date));
  for(let i=1;i<records.length;i++)if((Date.parse(records[i].date)-Date.parse(records[i-1].date))/86400000!==1)throw new Error('Data must be daily and have no missing dates.');
  return records;
}
export function analyzeSeries(rows,{window=14,threshold=3.5}={}) {
  if(!Number.isInteger(window)||window<7||!Number.isFinite(threshold)||threshold<=0)throw new Error('Invalid settings');
  return rows.map((row,i)=>{
    const history=rows.slice(Math.max(0,i-window),i).map(x=>x.value);
    if(history.length<7)return {...row,expected:null,score:null,flag:false,severity:'Insufficient history'};
    const expected=median(history), dispersion=1.4826*mad(history);
    // Floor avoids division by zero for constant-volume series.
    const sigma=Math.max(1,dispersion,Math.sqrt(Math.max(1,expected))*0.35);
    const score=(row.value-expected)/sigma, magnitude=Math.abs(score);
    return {...row,expected,score,flag:magnitude>=threshold,severity:magnitude>=threshold*2?'Critical':magnitude>=threshold?'Review':'Normal'};
  });
}
export function forecastSeries(rows,horizon=7){
  if(!rows.length || !Number.isInteger(horizon)||horizon<1||horizon>30) throw new Error('Need input history and horizon of 1-30 days');
  const hist=rows.slice(-56); const base=median(hist.map(x=>x.value));
  // Least-squares trend, capped to avoid extreme extrapolation on short histories.
  const n=hist.length, avgX=(n-1)/2, avgY=hist.reduce((a,b)=>a+b.value,0)/n;
  let numer=0,denom=0;
  for(let i=0;i<n;i++){numer+=(i-avgX)*(hist[i].value-avgY);denom+=(i-avgX)**2;}
  const rawSlope=denom ? numer/denom : 0;
  const slope=Math.max(-base*0.025,Math.min(base*0.025,rawSlope));
  const weekdayOffsets=Array.from({length:7},()=>[]);
  hist.forEach((r,i)=>weekdayOffsets[new Date(r.date+'T00:00:00Z').getUTCDay()].push(r.value-(avgY+slope*(i-avgX))));
  const offsets=weekdayOffsets.map(v=>v.length?median(v):0);
  const last=Date.parse(rows.at(-1).date+'T00:00:00Z');
  return Array.from({length:horizon},(_,k)=>{
    const date=new Date(last+(k+1)*86400000).toISOString().slice(0,10);
    const w=new Date(date+'T00:00:00Z').getUTCDay();
    return {date,forecast:Math.round(Math.max(0,avgY+slope*(n+k-avgX)+offsets[w])*10)/10};
  });
}
export function demoData(){
  const start=Date.UTC(2026,7,1);
  return Array.from({length:84},(_,i)=>{
    const date=new Date(start+i*86400000).toISOString().slice(0,10);
    const weekday=(i+6)%7;const cycle=weekday===0||weekday===6?-18:0;
    const noise=[-4,0,3,1,-2,4,-1][i%7];let value=130+0.28*i+cycle+noise;
    if(i===48)value+=100;if(i===62)value-=88;
    return {date,value:Math.round(value)};
  });
}
export const asCSV=rows=>['date,value,expected,robust_score,flag,severity',...rows.map(x=>[x.date,x.value,x.expected??'',x.score?.toFixed(2)??'',x.flag?'YES':'NO',x.severity].join(','))].join('\n');
