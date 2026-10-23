# test_b251: 공식 공지에서 새 보스·새 난이도 자동 추가 (scripts/boss_auto.py → data/bosses_auto.json → 사이트 applyAutoBosses)
#  + 림보·발드릭스 익스트림(1.2.420, 2026-10-22) 인식 + 부분 가격표(카링 익스트림↔유피테르 하드) 반영
import os, sys, json, copy, shutil, tempfile, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT,'scripts'))
import boss_auto as A
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
FX=os.path.join(ROOT,'tests','fx_b251'); rd=lambda f: open(os.path.join(FX,f),encoding='utf-8').read()
key=lambda fs:{(f['name'],f['diff']):f for f in fs}
# 1) 파서 — 실제 공지(본섭 815, 테섭 202)
for f in ('live_815.html','test_202.html'):
    k=key(A.parse_notice(rd(f)))
    check(f'{f}: 림보·발드릭스 익스트림 찾음', ('림보','extreme') in k and ('발드릭스','extreme') in k, list(k))
    check(f'{f}: 익스트림 가격·파티·드롭은 공지에 없음 → 빈 칸', all(x not in k[('림보','extreme')] for x in ('price','partyMax','drops')), k[('림보','extreme')])
    check(f'{f}: 가격표 줄(카링 익스트림 4,845,000,000)', k.get(('카링','extreme'),{}).get('price')==4845000000, k.get(('카링','extreme')))
# 2) 합성 새 보스
k=key(A.parse_notice(rd('synthetic_new_boss.html')))
n=k.get(('아케론','normal'),{}); h=k.get(('아케론','hard'),{})
check('합성: 아케론 노멀·하드', bool(n) and bool(h), list(k))
check('합성: 노멀 가격 1.2억×10, 파티 3, 주간', n.get('price')==1200000000 and n.get('partyMax')==3 and n.get('type')=='weekly', n)
check('합성: 하드 가격 999 = 범위 밖 → 빼기', 'price' not in h, h)
check('합성: 하드 드롭 아케론의 눈', h.get('drops')==['아케론의 눈'] and 'drops' not in n, (n,h))
check('합성: 스우(하드) 가격 1 → 범위 밖이라 안 받음', 'price' not in k.get(('스우','hard'),{}), k.get(('스우','hard')))
# 3) 합치기: 테섭 = 대기, 본섭 = 확정, 중복·덮어쓰기 없음, 내장 우선
built=A.builtin(); tmp=tempfile.mkdtemp(); P=os.path.join(tmp,'b.json')
src_t={'url':'https://maplestory.nexon.com/Testworld/News/Update/999','title':'t','date':'2026-11-01','server':'test'}
src_l={'url':'https://maplestory.nexon.com/News/Update/999','title':'l','date':'2026-11-08','server':'live'}
d=A.load(P); fs=A.parse_notice(rd('synthetic_new_boss.html'))
check('테섭 → 변경됨', A.apply(d,fs,src_t,False,built,'T1'))
check('테섭 → pending 에만, bosses 비어 있음', not d['bosses'] and [e['name'] for e in d['pending']]==['아케론','스우'], d)
check('스우 이지(내장에 없는 난이도) = 기존 id lotus 로', A._entry(d['pending'],'스우')['id']=='lotus' and list(A._entry(d['pending'],'스우')['diffs'])==['easy'])
check('같은 테섭 공지 다시 → 변경 없음(중복 없음)', not A.apply(d,fs,src_t,False,built,'T2'))
check('내장 보스·난이도(스우 하드, 카링 익스트림)는 추가 안 함', all(e['name']!='카링' for e in d['pending']) and 'hard' not in A._entry(d['pending'],'스우')['diffs'])
fs_l=copy.deepcopy(fs); [f.update(price=5000000000) for f in fs_l if f['name']=='아케론' and f['diff']=='normal']
check('본섭 확인 → 변경됨', A.apply(d,fs_l,src_l,True,built,'L1'))
a=A._entry(d['bosses'],'아케론')
check('본섭 확인 → bosses 로, pending 비움', a and set(a['diffs'])=={'normal','hard'} and not d['pending'], d['pending'])
check('본섭 가격 사용, id auto_해시, 주간', a['diffs']['normal']['price']==5000000000 and a['id'].startswith('auto_') and a.get('type')=='weekly', a)
fs2=[{'name':'아케론','diff':'normal','price':7000000000,'partyMax':6},{'name':'아케론','diff':'hard','price':3000000000}]
A.apply(d,fs2,src_l,True,built,'L2')
check('이미 있는 칸은 덮어쓰지 않음, 빈 칸만 채움', a['diffs']['normal']['price']==5000000000 and a['diffs']['normal']['partyMax']==3 and a['diffs']['hard']['price']==3000000000, a)
check('log: pending·confirm·add·fill 기록', {'pending','confirm','add','fill'}<={x['action'] for x in d['log']}, [x['action'] for x in d['log']])
A.save(d,P); check('저장·다시 읽기', A.load(P)['bosses'][0]['name']==d['bosses'][0]['name'])
d2=A.load(P); A.apply(d2,[],src_l,True,built,'L3'); check('빈 결과로는 아무것도 안 지움', len(d2['bosses'])==len(d['bosses']))
# process(): 본섭 815 → 림보·발드릭스 익스트림, 저장소 data/bosses_auto.json 과 같은 내용
P2=os.path.join(tmp,'c.json'); A.process([{'url':'https://maplestory.nexon.com/News/Update/815','title':'x','date':'2026-10-22'}],True,lambda u:rd('live_815.html'),P2,built)
c=A.load(P2); check('process(815): 림보·발드릭스 익스트림만 추가', sorted((e['id'],list(e['diffs'])) for e in c['bosses'])==[('baldrix',['extreme']),('limbo',['extreme'])], c['bosses'])
R=json.load(open(os.path.join(ROOT,'data','bosses_auto.json'),encoding='utf-8'))
check('저장소 data/bosses_auto.json = 815 출처 림보·발드릭스 익스트림(가격 없음)', sorted((e['id'],list(e['diffs']),e['diffs']['extreme']['src']['url'],'price' in e['diffs']['extreme']) for e in R['bosses'])==[('baldrix',['extreme'],'https://maplestory.nexon.com/News/Update/815',False),('limbo',['extreme'],'https://maplestory.nexon.com/News/Update/815',False)], R['bosses'])
# 4) 부분 가격표 (update_feed.merge_partial)
import update_feed as U
pr={'source':{'url':'https://maplestory.nexon.com/News/Update/813'},'rows':[{'boss':f'보스{i}(노멀)','new':i*1000000} for i in range(1,21)]+[{'boss':'카링 (익스트림)','new':5387000000},{'boss':'유피테르 (하드)','new':4845000000}],
    'upcoming':{'rows':[{'boss':'카링(익스트림)','new':4845000000},{'boss':'유피테르(하드)','new':5387000000}]}}
info=__import__('nexon_prices').parse_post(rd('live_815.html'))
it={'url':'https://maplestory.nexon.com/News/Update/815','title':'1.2.420','date':'2026-10-22'}
pr1=copy.deepcopy(pr); ok=U.merge_partial(pr1,info['rows'],it,info); m={r['boss'].replace(' ',''):r['new'] for r in pr1['rows']}
check('부분 가격표 2줄 → 그 줄만 교체, 나머지 그대로', ok and m['카링(익스트림)']==4845000000 and m['유피테르(하드)']==5387000000 and len(pr1['rows'])==22 and m['보스3(노멀)']==3000000, m)
check('부분 가격표 → 테섭 예정 정리, 출처·변동일', 'upcoming' not in pr1 and pr1['partial']['url'].endswith('/815') and pr1['changedAt']=='2026-10-22')
pr2=copy.deepcopy(pr); it_old=dict(it,url='https://maplestory.nexon.com/News/Update/800')
check('예전 공지의 부분 표는 무시', not U.merge_partial(pr2,info['rows'],it_old,info))
check('라벨 이상한 표는 무시', not U.merge_partial(copy.deepcopy(pr),[{'boss':'아무거나','new':5000000}],it,info))
P0=json.load(open(os.path.join(ROOT,'prices.json'),encoding='utf-8')); m0={r['boss'].replace(' ',''):r['new'] for r in P0['rows']}
check('저장소 prices.json: 카링 익스트림 4,845,000,000 / 유피테르 하드 5,387,000,000', m0.get('카링(익스트림)')==4845000000 and m0.get('유피테르(하드)')==5387000000, (m0.get('카링(익스트림)'),m0.get('유피테르(하드)')))
# 5) 사이트: 합치기·스케줄러·드롭·수익
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); os.makedirs(os.path.join(site,'data'))
syn=copy.deepcopy(d); syn['bosses']+=[{'id':'lotus','name':'스우','diffs':{'hard':{'price':1},'easy':{'price':200000000,'partyMax':6}}},{'id':'limbo','name':'림보','diffs':{'extreme':{'partyMax':6,'price':100000000000}}},{'id':'evil','name':'<img src=x onerror=alert(1)>','diffs':{'hard':{}}}]
json.dump(syn,open(os.path.join(site,'data','bosses_auto.json'),'w'),ensure_ascii=False)
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
C={'id':'c0','name':'zetking','level':285,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
ST={'version':5,'theme':'dark','activeId':'c0','characters':[C],'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
Q="()=>{const f=id=>BOSSES.find(b=>b.id===id);return {limbo:f('limbo').diffs,baldrix:f('baldrix').diffs,lotus:f('lotus').diffs,ak:(BOSSES.find(b=>b.name==='아케론')||{}),akp:PRICE_CONFIG[(BOSSES.find(b=>b.name==='아케론')||{}).id+'_normal'],evil:BOSSES.some(b=>/img/.test(b.name)),lh:PRICE_CONFIG.lotus_hard,le:PRICE_CONFIG.lotus_easy,lx:PRICE_CONFIG.limbo_extreme,pl:partyMax(f('limbo'),'extreme'),ke:PRICE_CONFIG.kaling_extreme,jh:PRICE_CONFIG.jupiter_hard}}"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('dialog',lambda dl:(errs.append('dialog'),dl.dismiss()))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(1500)
    r=pg.evaluate(Q)
    check('사이트(내장 파일): 림보·발드릭스 익스트림', r['limbo']==['normal','hard','extreme'] and r['baldrix']==['normal','hard','extreme'], r)
    check('사이트(받은 파일): 아케론 주간, 노멀·하드, 가격 50억', r['ak'].get('diffs')==['normal','hard'] and r['ak'].get('type')=='weekly' and r['akp']==5000000000, r)
    check('사이트: 아케론은 월간 보스 앞에', pg.evaluate("()=>{const i=BOSSES.findIndex(b=>b.name==='아케론');return BOSSES.slice(0,i).every(b=>b.type==='weekly')&&BOSSES[i+1].type==='monthly'}"))
    check('내장 우선: 스우 하드 가격 그대로, 이지만 추가(난이도 순서)', r['lh']>1 and r['le']==200000000 and r['lotus']==['easy','normal','hard','extreme'], r)
    check('범위 밖 가격·내장 파티 인원은 무시 (림보 익스트림 가격 없음, 파티 3)', r['lx'] is None and r['pl']==3, r)
    check('id 가 auto_ 형식이 아닌 새 보스는 무시', not r['evil'])
    check('카링 익스트림 4,845,000,000 / 유피테르 하드 5,387,000,000', r['ke']==4845000000 and r['jh']==5387000000, r)
    check('드롭 표: 아케론 하드 → 아케론의 눈', pg.evaluate("()=>{const b=BOSSES.find(b=>b.name==='아케론');return dropsFor(b,'hard').map(k=>ITEMS[k]?.n).includes('아케론의 눈')&&!dropsFor(b,'normal').map(k=>ITEMS[k]?.n).includes('아케론의 눈')}"))
    check('파티 한도: 아케론 3', pg.evaluate("()=>partyMax(BOSSES.find(b=>b.name==='아케론'),'normal')")==3)
    wk=pg.evaluate("()=>S.period.week")
    REG=[('림보','extreme'),('발드릭스','extreme'),('아케론','normal')]; ALL={'림보':['normal','hard','extreme'],'발드릭스':['normal','hard','extreme'],'아케론':['normal','hard']}
    rows=[{'content_name':n,'difficulty':x,'cycle':'bossWeekly','registration_flag':'true' if (n,x) in REG else 'false','complete_flag':'true' if (n,x)==('아케론','normal') else 'false'} for n,ds in ALL.items() for x in ds]
    pg.evaluate("r=>{applyScheduler(S.characters[0],r); save(); render();}",{'date':wk+'T00:00+09:00','boss_contents':rows,'weekly_boss_clear_count':1,'weekly_boss_clear_limit_count':12})
    s=pg.evaluate("()=>{const c=S.characters[0];const ak=BOSSES.find(b=>b.name==='아케론').id;return {um:c.sync.unmatched,l:c.bosses.limbo,bx:c.bosses.baldrix,ak:c.bosses[ak],done:!!c.weekly[ak]}}")
    check('스케줄러: 림보·발드릭스 익스트림·아케론 매칭(매칭 안 된 보스 없음)', s['um']==[] and s['l']['diff']=='extreme' and s['bx']['diff']=='extreme' and s['ak']['diff']=='normal' and s['done'], s)
    body=pg.inner_text('body')
    check('화면: 림보·발드릭스·아케론 행, 가격 미확인 표시', '아케론' in body and '림보' in body and '가격 미확인' in body)
    check('수익: 아케론 노멀 처치 50억 반영', '50억' in body.replace(',',''), '')
    pg.reload(); pg.wait_for_timeout(1500)
    s2=pg.evaluate("()=>{const c=S.characters[0];const ak=(BOSSES.find(b=>b.name==='아케론')||{}).id;return [c.bosses.limbo?.diff,c.bosses.limbo?.enabled,ak&&c.bosses[ak]?.enabled,ak&&!!c.weekly[ak]]}")
    check('새로고침 뒤에도 유지(림보 익스트림, 아케론 처치)', s2==['extreme',True,True,True], s2)
    pg.screenshot(path=os.path.join(tmp,'b251.png'))
    b.close()
finally: srv.terminate()
check('no page errors', not errs, errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
