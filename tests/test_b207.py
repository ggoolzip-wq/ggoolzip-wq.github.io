# b207: Worker maple.ai.kr 시세 자동 갱신 — maiCron(30분 :00·:30, 첫 배포 직후 1번 바로, 새 날짜 찾으면 그날 끝) · ETag 304 · 새 날짜일 때만 가격 · 손으로 넣은 다른 아이템 유지 · mai_seen 기록 · 빠른 파서
import os, sys, json, subprocess, shutil, tempfile
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
tmp=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'server','worker.js'),os.path.join(tmp,'w.mjs'))
js=r"""
const W=await import(process.argv[2]); const meta={}; let hits=[]; let page={status:200,etag:'"a"',body:''};
const DB={prepare(sql){const st={sql,args:[],bind(...a){st.args=a;return st;},
  async first(){const k=st.args[0];return k in meta?{v:meta[k]}:null;},
  async run(){let k,v; const m=sql.match(/VALUES \('(\w+)',\?\)/); if(m){k=m[1];v=st.args[0];} else {[k,v]=st.args;} meta[k]=v; return {};}};return st;},
  async batch(L){for(const s of L) await s.run();}};
globalThis.fetch=async(u,o)=>{hits.push({u,inm:o.headers['If-None-Match']||'',ua:o.headers['User-Agent']}); if(page.etag&&o.headers['If-None-Match']===page.etag) return new Response(null,{status:304});
  return new Response(page.body,{status:page.status,headers:{ETag:page.etag}});};
const rec=(d,eye)=>`{\\"date\\":\\"${d}\\",\\"items\\":{\\"마깃안\\":{\\"challenger\\":40,\\"main\\":${eye}},\\"리4\\":{\\"main\\":39},\\"익셉셔널 해머 (얼굴장식)\\":{\\"main\\":6.5}}}`;
const mk=(...R)=>'<html>'+'x'.repeat(300000)+'<script>self.__next_f.push([1,"x:{\\"data\\":['+R.join(',')+']}"])</script>'+'y'.repeat(300000)+'</html>';
const env={DB,MAI_URL:'https://maple.ai.kr/blog/item-price-tracker-2026'}; const K=(d,hm)=>Date.parse(d+'T'+hm+':00+09:00');
const P=()=>JSON.parse(meta.admin_prices||'{}'), C=()=>JSON.parse(meta.mai_cache||'null'), S=()=>JSON.parse(meta.mai_seen||'[]');
const out={};
meta.admin_prices=JSON.stringify({eye:{p:1,t:5},manual_x:{p:777,t:9}}); meta.mai_cache=JSON.stringify({date:'2026-10-13',items:{'마깃안':{main:1}},fetchedAt:5}); // 예전(b104) 캐시: auto 없음
page.body=mk(rec('2026-10-16',27.8),rec('2026-10-17',28));
out.boot=[await W.maiCron(env,K('2026-10-17','19:57')),hits.length,P(),C(),S(),hits[0]];
out.done=[await W.maiCron(env,K('2026-10-17','20:30')),hits.length];
out.skip=[await W.maiCron(env,K('2026-10-18','00:07')),hits.length];
out.n304=[await W.maiCron(env,K('2026-10-18','00:00')),hits.length,hits[hits.length-1].inm,C().checkedAt===K('2026-10-18','00:00')];
page.etag='"b"'; page.body=mk(rec('2026-10-17',28)).replace('xxxx','zzzz'); const p0=JSON.stringify(P());
out.nochg=[await W.maiCron(env,K('2026-10-18','00:30')),hits.length,JSON.stringify(P())===p0,C().etag,C().date];
out.skip2=[await W.maiCron(env,K('2026-10-18','15:10')),hits.length];
page.etag='"c"'; page.body=mk(rec('2026-10-17',28),rec('2026-10-18',31.5));
out.newd=[await W.maiCron(env,K('2026-10-18','15:30')),hits.length,P(),S(),C().foundDay];
out.done2=[await W.maiCron(env,K('2026-10-18','16:00')),hits.length];
const big=mk(...Array.from({length:20},(_,i)=>rec('2026-10-'+String(i+1).padStart(2,'0'),20+i))); W.parseMai(big,''); let t=process.hrtime.bigint(); let r; for(let i=0;i<10;i++) r=W.parseMai(big,''); out.ms=Number(process.hrtime.bigint()-t)/10e6; out.big=r.date;
console.log(JSON.stringify(out));
"""
open(os.path.join(tmp,'t.mjs'),'w').write(js)
O=json.loads(subprocess.check_output(['node',os.path.join(tmp,'t.mjs'),os.path.join(tmp,'w.mjs')]).decode().strip().splitlines()[-1])
st,n,P,C,S,h0=O['boot']; T=lambda hm:None
check('첫 배포 직후(:57, auto 없음) 바로 1번 확인 → 새 날짜 10-17', st=='new' and n==1 and C['date']=='2026-10-17' and C['foundDay']=='2026-10-17' and C['auto']==1, (st,n,C.get('date')))
check('설명하는 User-Agent · 예전 캐시(ETag 없음)엔 If-None-Match 없음', 'bossmaple' in h0['ua'] and h0['inm']=='', h0)
check('admin_prices = 페이지 PUT 모양 {p:메소,t:처음 본 시각}, 짝 있는 것만 덮고 손으로 넣은 manual_x 유지', P['eye']['p']==2800000000 and P['eye']['t']==C['fetchedAt'] and P['ring_r4']['p']==3900000000 and P['h_face']['p']==650000000 and P['manual_x']=={'p':777,'t':9}, P)
check('mai_seen 에 처음 본 시각 기록', len(S)==1 and S[0]['date']=='2026-10-17' and S[0]['at']==C['fetchedAt'] and S[0]['by']=='cron', S)
check('같은 KST 날 새 날짜 찾은 뒤 = 그날 끝(요청 없음)', O['done']==['done_today',1], O['done'])
check(':00·:30 아니면 요청 없음', O['skip']==['skip',1] and O['skip2'][0]=='skip', (O['skip'],O['skip2']))
check('다음 날 00:00 = If-None-Match 로 확인 → 304 → 가격 그대로', O['n304'][0]=='same' and O['n304'][1]==2 and O['n304'][2]=='"a"' and O['n304'][3], O['n304'])
check('페이지만 바뀜(ETag 새것, 시세 날짜 같음) → 가격 그대로, ETag 만 저장', O['nochg'][0]=='nochange' and O['nochg'][2] and O['nochg'][3]=='"b"' and O['nochg'][4]=='2026-10-17', O['nochg'])
st,n,P2,S2,fd=O['newd']
check('15:30 새 날짜 10-18 → 가격 바꿈 + mai_seen 2개, 그 뒤 16:00 은 그날 끝', st=='new' and P2['eye']['p']==3150000000 and len(S2)==2 and S2[1]['date']=='2026-10-18' and fd=='2026-10-18' and O['done2'][0]=='done_today' and O['done2'][1]==n, (st,P2.get('eye'),S2,O['done2']))
check(f'빠른 파서: 600KB+20일 기록 {O["ms"]:.2f}ms (가장 새 날짜만 해석)', O['big']=='2026-10-20' and O['ms']<4, O['ms'])
W=open(os.path.join(ROOT,'server','worker.js'),encoding='utf-8').read()
check('서브요청 예산: 시세 확인 회차는 공지 목록 조회 1번 덜(FEED_MAX_LIST - 1)', 'mai ? FEED_MAX_LIST - 1 : FEED_MAX_LIST' in W and 'getUTCMinutes() % 30 === 0' in W)
print('FAILS:',fails); sys.exit(1 if fails else 0)
