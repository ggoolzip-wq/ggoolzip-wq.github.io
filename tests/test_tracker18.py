import os, sys
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 드롭 표 연마석·소울 에테르 · 솔 에르다의 기운 배지 · 시즌 보스(메이린) 매칭 제외 · 예상 주간 수익 · 보스별 최대 파티 인원
from playwright.sync_api import sync_playwright
import json, subprocess, time, urllib.request, shutil
sys.argv=[sys.argv[0]]
from mock_nexon import handle, KM
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name,**kw):
    path=os.path.join(OUT,name); loc.screenshot(path=path,**kw)
    if SHOTDIR: shutil.copy(path,os.path.join(SHOTDIR,name))
PORT=8798
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
NOW=int(time.time()*1000)
def B(d,p=1): return {'enabled':True,'diff':d,'party':p}
c1={'id':'c1','name':'단풍용사','level':287,'job':'히어로','world':'스카니아','ocid':'ocid-main','accId':'a1','isMain':True,'image':'',
    'bosses':{'lotus':B('extreme',6),'adversary':B('hard',5),'kaling':B('hard',2),'star':B('normal',4),'jupiter':B('hard',6),'seren':B('hard',3)},
    'weekly':{'seren':True},'monthly':{},'auto':{},'drops':{'kaling|chaosbox':2,'kaling|h_ear':1},
    'sync':{'at':NOW,'ok':True,'clear':1,'limit':12,'unmatched':['시즌 보스 메이린(normal)','시즌 보스 메이린(hard)','테스트 보스(hard)']}}
many={k:B(d) for k,d in [('lotus','hard'),('damien','hard'),('slime','chaos'),('lucid','hard'),('will','hard'),('dusk','chaos'),('jinhilla','hard'),
      ('dunkel','hard'),('seren','hard'),('kalos','normal'),('adversary','normal'),('kaling','normal'),('star','normal'),('limbo','normal')]}
many['lotus']['party']=6
c2={'id':'c2','name':'새부캐','level':265,'job':'비숍','world':'스카니아','ocid':'','accId':'','isMain':False,'image':'','bosses':many,'weekly':{},'monthly':{},'auto':{},'sync':{},'drops':{}}
c3={'id':'c3','name':'빈캐릭','level':200,'job':'팔라딘','world':'스카니아','ocid':'','accId':'','isMain':False,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'sync':{},'drops':{}}
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[c1,c2,c3],
  'settings':{'accounts':[{'id':'a1','label':'본계정','key':KM}],'autoSync':False,'lastSync':NOW}}
ROW="s=>document.querySelector(`[data-party=\"${s}\"]`).closest('.boss')"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':900},locale='ko-KR'); ctx.route('https://open.api.nexon.com/**',handle)
    ctx.route('https://accounts.google.com/**',lambda r:r.abort())
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=404,body=''))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.evaluate("p=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p))}",PRESET); pg.reload()
    pg.wait_for_selector('[data-party="kaling"]')
    st=lambda: pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1'))")
    # ---- G: 최대 파티 인원 + 저장값 클램프 ----
    opts=pg.evaluate("s=>Object.fromEntries(['lotus','adversary','kaling','star','jupiter','seren'].map(k=>{const e=document.querySelector(`[data-party=\"${k}\"]`);return [k,[e.options.length,+e.value]]}))","")
    check('lotus extreme: 2 options, saved 6 clamped to 2', opts['lotus']==[2,2], opts['lotus'])
    check('adversary hard: max 3, saved 5 -> 3', opts['adversary']==[3,3], opts['adversary'])
    check('star/jupiter max 3', opts['star']==[3,3] and opts['jupiter']==[3,3], (opts['star'],opts['jupiter']))
    check('kaling unchanged (6 options, 2)', opts['kaling']==[6,2], opts['kaling'])
    check('seren unchanged (6 options, 3)', opts['seren']==[6,3], opts['seren'])
    s=st()['characters'][0]['bosses']
    check('saved party values clamped after load+save', s['lotus']['party']==2 and s['adversary']['party']==3 and s['jupiter']['party']==3 and s['kaling']['party']==2 and s['seren']['party']==3, {k:v['party'] for k,v in s.items()})
    # 노말로 바꾸면 6인까지 선택 가능 (값은 2 유지)
    pg.evaluate("S.characters[0].bosses.lotus.diff='hard';clampParty(S.characters[0],'lotus');save();render()"); pg.wait_for_timeout(100)
    o=pg.evaluate("(()=>{const e=document.querySelector('[data-party=\"lotus\"]');return [e.options.length,+e.value]})()")
    check('lotus hard: 6 options, value kept 2', o==[6,2], o)
    pg.select_option('[data-party="lotus"]','5'); pg.wait_for_timeout(100)
    pg.evaluate("S.characters[0].bosses.lotus.diff='extreme';clampParty(S.characters[0],'lotus');save();render()"); pg.wait_for_timeout(150)
    o=pg.evaluate("(()=>{const e=document.querySelector('[data-party=\"lotus\"]');return [e.options.length,+e.value]})()")
    check('switch to extreme clamps 5 -> 2', o==[2,2] and st()['characters'][0]['bosses']['lotus']['party']==2, o)
    # ---- E: 시즌 보스 제외 ----
    hd=pg.inner_text('.bosslay .card')
    check('season boss 메이린 not in unmatched line', '메이린' not in hd, hd[:300])
    check('other unmatched still shown', '매칭 안 된 보스: 테스트 보스(hard)' in hd)
    # ---- C/D: 드롭 표 ----
    d=pg.evaluate("""(()=>{const r=document.querySelector('[data-party="kaling"]').closest('.boss').querySelector('.drops');const f=r.firstElementChild;
      return {first:f.className,badge:f.querySelector('.ecnt')?.textContent,img:!!f.querySelector('img'),clickable:f.hasAttribute('data-drop')||f.getAttribute('role')==='button',
       bpos:(()=>{const a=f.getBoundingClientRect(),b=f.querySelector('.ecnt').getBoundingClientRect(),i=f.querySelector('img').getBoundingClientRect();return {bl:b.left-i.left,bt:b.top-i.top,rightOfCenter:b.left>i.left+i.width/2}})()}})()""")
    check('erda chip first in kaling hard drops with badge 500', 'erda' in d['first'] and d['badge']=='500' and d['img'] and not d['clickable'], d)
    check('erda badge at top-left of icon', d['bpos']['bl']<=2 and d['bpos']['bt']<=2 and not d['bpos']['rightOfCenter'], d['bpos'])
    before=json.dumps(st()['characters'][0].get('drops'),sort_keys=True)
    pg.click('.boss:has([data-party="kaling"]) .drop.erda'); pg.wait_for_timeout(150)
    after=st()['characters'][0]; 
    check('clicking erda records nothing', json.dumps(after.get('drops'),sort_keys=True)==before and not after['weekly'].get('kaling'), after.get('drops'))
    check('existing saved drop counts kept', after['drops'].get('kaling|chaosbox')==2 and after['drops'].get('kaling|h_ear')==1, after['drops'])
    check('no grouped +N chip anywhere (each item its own chip)', pg.locator('[data-dropmore], .drop.more').count()==0)
    icons=pg.evaluate("[...document.querySelector('[data-party=\"kaling\"]').closest('.boss').querySelectorAll('[data-drop]')].map(e=>[e.dataset.drop,e.querySelectorAll('img').length,e.getBoundingClientRect().height])")
    check('every kaling drop chip has exactly one icon, visible', all(i[1]==1 and i[2]>0 for i in icons), icons)
    ks=pg.evaluate("[...document.querySelector('[data-party=\"kaling\"]').closest('.boss').querySelectorAll('[data-drop]')].map(e=>e.dataset.drop.split('|')[1])")
    check('kaling hard drops include 신념 연마석 + 소울 에테르 1, not 생명', 'g_faith' in ks and 'se1' in ks and 'g_life' not in ks, ks)
    ex=pg.evaluate("""(()=>{const g=(id,d)=>dropsFor(findBoss(id),d), e=(id,d)=>erdaFor(findBoss(id),d);
      return {kn:g('kaling','normal'),sn:g('star','normal'),sh:g('star','hard'),lim:g('limbo','normal'),jh:g('jupiter','hard'),ae:g('adversary','extreme'),kc:g('kalos','chaos'),ke:g('kalos','easy'),
       e:[e('lotus','normal'),e('lotus','hard'),e('lotus','extreme'),e('jinhilla','normal'),e('kaling','extreme'),e('jupiter','hard'),e('zakum','chaos')]}})()""")
    check('star normal: 생명 + 에테르2', 'g_life' in ex['sn'] and 'se2' in ex['sn'] and 'g_faith' not in ex['sn'], ex['sn'])
    check('star hard: 신념 + 에테르2', 'g_faith' in ex['sh'] and 'se2' in ex['sh'], ex['sh'])
    check('limbo normal: 신념 + 에테르3', 'g_faith' in ex['lim'] and 'se3' in ex['lim'], ex['lim'])
    check('jupiter hard: 신념 + 에테르4', 'g_faith' in ex['jh'] and 'se4' in ex['jh'], ex['jh'])
    check('adversary extreme: 생명 + 에테르1', 'g_life' in ex['ae'] and 'se1' in ex['ae'], ex['ae'])
    check('kalos chaos 생명, easy none', 'g_life' in ex['kc'] and 'g_life' not in ex['ke'], (ex['kc'],ex['ke']))
    check('erda amounts', ex['e']==[0,50,280,70,800,750,0], ex['e'])
    shot(pg.locator('.boss:has([data-party="kaling"])'),'shot18_drops_kaling.png')
    shot(pg.locator('.boss-list'),'shot18_droptable.png')
    # ---- F: 예상 주간 수익 ----
    check('no expected-income badge for character with kills', pg.locator('.expinc').count()==0)
    pg.click('.char[data-id="c2"]'); pg.wait_for_selector('[data-party="limbo"]')
    calc=pg.evaluate("(()=>{const c=S.characters.find(x=>x.id==='c2');const l=BOSSES.filter(b=>b.type==='weekly'&&c.bosses[b.id]?.enabled).map(b=>Math.floor(price(b,c.bosses[b.id].diff)/Math.max(1,Math.min(partyMax(b,c.bosses[b.id].diff),c.bosses[b.id].party||1)))).sort((a,b)=>b-a);return {n:l.length,sum:l.slice(0,12).reduce((s,x)=>s+x,0),ex:expectedWeekly(c).meso,shown:document.querySelector('.expinc')?.textContent||'',icon:!!document.querySelector('.expinc img.ric'),tip:document.querySelector('.expinc')?.title||''}})()")
    check('expected income = top 12 of 14 enabled bosses', calc['n']==14 and calc['ex']==calc['sum'] and calc['sum']>0, calc)
    check('expected income badge with ipc icon', calc['icon'] and '상위 12개' in calc['shown'], calc['shown'])
    check('tooltip lists 12 bosses', calc['tip'].count('· ')==12, calc['tip'][:200])
    pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(150)
    bb=pg.locator('.bosslay .card').first.bounding_box(); path=os.path.join(OUT,'shot18_expected_income.png')
    pg.wait_for_timeout(300); bb=pg.locator('.bosslay .card').first.bounding_box()
    pg.screenshot(path=path,clip={'x':bb['x'],'y':bb['y'],'width':bb['width'],'height':bb['height']})
    if SHOTDIR: shutil.copy(path,os.path.join(SHOTDIR,'shot18_expected_income.png'))
    pg.click('[data-check="lotus"]'); pg.wait_for_timeout(150)
    check('badge hides after first weekly kill', pg.locator('.expinc').count()==0)
    pg.click('.char[data-id="c3"]'); pg.wait_for_timeout(200)
    check('no badge when no bosses selected', pg.locator('.expinc').count()==0)
    b.close()
finally:
    srv.terminate()
check('no page errors', not errs, errs)
print('FAILS',fails); print('ERRORS',errs)
sys.exit(1 if fails or errs else 0)
