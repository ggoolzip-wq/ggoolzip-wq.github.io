"use strict";
function reference(I,W,H,Tp,tw,th,sums,bx,by,bright,tt){
 const N=tw*th;let best=-1,bxy=null;
 for(let y=0;y+th<=H;y++) for(let x=0;x+tw<=W;x++){
  if(I[(y+by)*W+x+bx]<bright)continue;
  const z=y*sums.stride+x,z1=z+tw,z2=(y+th)*sums.stride+x,z3=z2+tw,b=sums.s[z3]-sums.s[z1]-sums.s[z2]+sums.s[z],cc=sums.q[z3]-sums.q[z1]-sums.q[z2]+sums.q[z];
  let a=0;for(let j=0;j<th;j++){const r=(y+j)*W+x,q=j*tw;for(let i=0;i<tw;i++){const v=I[r+i];a+=Tp[q+i]*v;}}
  const vv=cc-b*b/N;if(vv>1e-6){const n=a/Math.sqrt(vv*tt);if(n>best){best=n;bxy=[x,y];}}
 }
 return {best,xy:bxy};
}
let seed=0x7c1bad;
function random(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return(seed>>>0)/4294967296;}
function int(n){return Math.floor(random()*n);}
function make(W,H,tw,th,mode=0,pad=0){
 const I=new Float32Array(W*H),T=new Float32Array(tw*th);
 for(let i=0;i<I.length;i++) I[i]=mode===1?5:mode===2?-random()*255:mode===3?((i%W+Math.floor(i/W))%2?7:-3):mode===4?(random()-.5)*Math.pow(2,int(60)-30):random()*255;
 for(let i=0;i<T.length;i++) T[i]=mode===1?0:mode===3?((i%tw+Math.floor(i/tw))%2?7:-3):mode===4?(random()-.5)*Math.pow(2,int(60)-30):(random()-.5)*255;
 let mean=0;for(const v of T)mean+=v;mean/=T.length;let tt=0;for(let i=0;i<T.length;i++){T[i]-=mean;tt+=T[i]*T[i];}
 const stride=W+1+pad,s=new Float64Array(stride*(H+1)),q=new Float64Array(s.length);
 for(let y=1;y<=H;y++){let row=0,rowq=0;for(let x=1;x<=W;x++){const v=I[(y-1)*W+x-1];row+=v;rowq+=v*v;s[y*stride+x]=s[(y-1)*stride+x]+row;q[y*stride+x]=q[(y-1)*stride+x]+rowq;}}
 const bi=int(T.length),bx=bi%tw,by=Math.floor(bi/tw),bright=mode===2?-300:mode===3?-10:mode===4?-Infinity:0;
 return [I,W,H,T,tw,th,{stride,s,q},bx,by,bright,tt];
}
function same(a,b){return b!==null&&Object.is(a.best,b.best)&&(a.xy===null?b.xy===null:b.xy!==null&&Object.is(a.xy[0],b.xy[0])&&Object.is(a.xy[1],b.xy[1]));}
async function correctness(api,browser=false){
 const first=make(8,8,2,2,3),firstUse=api.match(...first);
 if(browser&&firstUse!==null)throw Error('browser first use did not defer');
 if(!await api.ready(!browser))throw Error('WASM unavailable');
 let cases=0,thresholdComparisons=0,maxAbsDifference=0,ties=0,empty=0;
 for(let i=0;i<220;i++){
  const tw=1+int(6),th=1+int(5),W=tw+int(12),H=th+int(12),mode=i%5;
  const args=make(W,H,tw,th,mode,i%3),a=reference(...args),b=api.match(...args);
  if(!same(a,b))throw Error('case '+i+' mismatch '+JSON.stringify({a,b}));
  if(a.xy===null)empty++;if(mode===3&&a.xy)ties++;
  maxAbsDifference=Math.max(maxAbsDifference,Math.abs(a.best-b.best));
  for(const t of [.75,.8,.9,a.best,a.best+Number.EPSILON,a.best-Number.EPSILON]){
   thresholdComparisons+=2;if((a.best>t)!==(b.best>t)||(a.best>=t)!==(b.best>=t))throw Error('threshold mismatch');
  }
  cases++;
 }
 const tie=make(8,8,2,2,3);tie[7]=0;tie[8]=0;
 const ta=reference(...tie),tb=api.match(...tie);if(!same(ta,tb)||tb.xy[0]!==0||tb.xy[1]!==0)throw Error('earliest tie');cases++;
 const z=make(3,3,2,2,1);if(!same(reference(...z),api.match(...z)))throw Error('zero variance');cases++;
 const retained=api.match(...tie),retainedJSON=JSON.stringify(retained);api.match(...make(16,14,5,4));if(JSON.stringify(retained)!==retainedJSON)throw Error('output alias');
 const invalid=[...tie];invalid[1]=1.5;if(api.match(...invalid)!==null)throw Error('invalid dimension accepted');
 const invalid2=[...tie];invalid2[0]=new Float64Array(64);if(api.match(...invalid2)!==null)throw Error('invalid type accepted');
 const invalid3=[...tie];invalid3[6]={stride:9,s:new Float64Array(1),q:new Float64Array(1)};if(api.match(...invalid3)!==null)throw Error('short sums accepted');
 // Grow memory, then reuse smaller allocations with different template dimensions.
 for(const args of [make(128,80,4,3),make(8,9,3,2),make(12,7,2,5)]){if(!same(reference(...args),api.match(...args)))throw Error('growth/reuse mismatch');cases++;}
 return {cases,strictObjectIs:true,maxAbsDifference,thresholdComparisons,randomPatternTieCases:ties,explicitEarliestTie:tb.xy,zeroVarianceAndNoMatchCases:empty,invalidInputChecks:3,growthAndOutputIsolation:true,wasmBytes:api.byteLength};
}
function benchmark(api){
 const output=[];let checksum=0;
 for(const [W,H,tw,th]of [[160,90,8,6],[854,480,20,10]]){
  const args=make(W,H,tw,th);args[9]=200;
  if(!same(reference(...args),api.match(...args)))throw Error('benchmark input mismatch');
  for(let i=0;i<2;i++){reference(...args);api.match(...args);}
  const values={js:[],wasmWithCopies:[]};
  for(let r=0;r<5;r++)for(const name of r%2?['wasmWithCopies','js']:['js','wasmWithCopies']){
   const start=performance.now(),v=name==='js'?reference(...args):api.match(...args);values[name].push(performance.now()-start);checksum+=v.best;
  }
  const median=a=>a.slice().sort((x,y)=>x-y)[2],js=median(values.js),wasm=median(values.wasmWithCopies);
  output.push({W,H,tw,th,brightnessCutoff:args[9],warmupsPerFunction:2,runs:5,medianJsMs:js,medianWasmIncludingValidationGrowthChecksAndAllInputCopiesMs:wasm,speedup:js/wasm,reductionPercent:(1-wasm/js)*100,samples:values});
 }
 return {measurements:output,checksum,scope:'Standalone Node pure arithmetic; not an application or user-PC measurement'};
}
if(typeof module!=='undefined'){
 module.exports={reference,correctness,benchmark};
 if(require.main===module){const fs=require('fs'),api=(()=>{const s=fs.readFileSync(require('path').join(__dirname,'../src/autorec.js'),'utf8');return new Function(s.slice(s.indexOf('const OrderedNcc'),s.indexOf('function arMesoTpl'))+';return OrderedNcc;')();})();correctness(api).then(result=>{console.log(JSON.stringify(result));if(process.argv.includes('--bench')){const b=benchmark(api);console.log(JSON.stringify(b));}}).catch(e=>{console.error(e);process.exitCode=1;});}
}else globalThis.NccTest={reference,correctness,benchmark};
