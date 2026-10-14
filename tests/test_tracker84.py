# b112: 가격 카드 '결정석 가격 / 아이템 가격' 탭, 관리자 '시세 등록', 익셉셔널 해머 시세 이름(얼장/눈장/벨트),
# 수익 기록 전체 수정 = 보스별 묶음(초상화 1번 + 난이도 배지), '이번주 획득 아이템' 앞 아이콘, 캐릭터 정보 결정석/아이템 판매 두 줄, '이번달 검마 (10월 8일 격파 완료)',
# 429: 초당 한도는 1번 재시도 + '오늘 한도 도달' 아님. MBT_ROOT/MBT_SHOTDIR/MBT_TAG/MBT_NOCHECK. Worker·넥슨은 가짜 응답.
import os, sys, json, time, subprocess, urllib.request
from playwright.sync_api import sync_playwright
ROOT=os.environ.get('MBT_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT='8900'
SHOT=os.environ.get('MBT_SHOTDIR'); TAG=os.environ.get('MBT_TAG','after'); NOCHK=os.environ.get('MBT_NOCHECK')=='1'
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
def shot(loc,name):
    if SHOT:
        try: loc.screenshot(path=os.path.join(SHOT,f'b112_{TAG}_{name}.png'))
        except Exception as e: print('shot skip',name,str(e)[:80])
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT,'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
B=lambda d,p=1:{'enabled':True,'diff':d,'party':p}
C={'id':'c1','name':'테스트캐','level':285,'job':'히어로','world':'스카니아','image':'','accId':'a1','ocid':'',
   'bosses':{'lucid':B('hard'),'kaling':B('normal'),'blackmage':B('extreme'),'zakum':B('chaos')},'weekly':{'lucid':True,'kaling':True},'monthly':{},'auto':{},'sync':{},
   'drops':{'lucid|whisper':1,'lucid|g_faith':1,'kaling|oath':1},'drev':{'lucid|whisper':{'m':500000000,'a':5,'p':1,'i':'whisper'},'kaling|oath':{'m':900000000,'a':9,'p':1,'i':'oath'}}}
ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[C],'settings':{'accounts':[{'id':'a1','label':'본계정','key':'live_K1_0123456789abcdefgh','main':True}]}}
SRV={'prices':{'whisper':{'p':6200000000,'t':1760000000000},'h_face':{'p':6199000000,'t':1760000000000}},'puts':[],'pub':0,'nx':[]}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1600,'height':1000},locale='ko-KR')
    H={'Access-Control-Allow-Origin':'*'}
    def api(r):
        u=r.request.url
        if u.endswith('/api/me'): return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'admin':True,'user':'u0','accounts':[]}))
        if u.endswith('/api/prices'): SRV['pub']+=1; return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'prices':SRV['prices']}))
        if '/api/admin/prices' in u:
            if r.request.method=='PUT': d=json.loads(r.request.post_data)['prices']; SRV['puts'].append(d); SRV['prices'].update(d)
            return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'prices':SRV['prices']}))
        if '/api/admin/users' in u: return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'users':[]}))
        return r.fulfill(status=200,content_type='application/json',headers=H,body='{}')
    def nxapi(r):  # /maplestory/v1/id: 첫 호출 429(초당), 두 번째 200
        SRV['nx'].append(time.time())
        if 'tst429' in r.request.url and len([1 for _ in SRV['nx']])==1: return r.fulfill(status=429,content_type='application/json',headers=H,body=json.dumps({'error':{'name':'OPENAPI00007','message':'rate'}}))
        return r.fulfill(status=200,content_type='application/json',headers=H,body=json.dumps({'ocid':'x1'}))
    ctx.route('http://127.0.0.1:9998/**',lambda r: r.fulfill(status=204,headers={**H,'Access-Control-Allow-Methods':'GET,PUT,POST,DELETE','Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else api(r))
    ctx.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    ctx.route('https://open.api.nexon.com/**',lambda r: r.fulfill(status=204,headers={**H,'Access-Control-Allow-Headers':'*'}) if r.request.method=='OPTIONS' else nxapi(r) if 'tst429' in r.request.url else r.abort())
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.syncApi','http://127.0.0.1:9998');localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin','1')}",ST)
    pg.reload(); pg.wait_for_timeout(1500)
    pg.evaluate("()=>{localStorage.setItem('mapleBossTracker.svToken','t'.repeat(43));localStorage.setItem('mapleBossTracker.svAdmin','1')}")
    pg.evaluate("typeof itemPriceLoad==='function'&&itemPriceLoad()"); pg.wait_for_timeout(300)
    pg.evaluate("s=>{S.characters=s.characters;S.settings.accounts=s.settings.accounts;S.activeId='c1';save();render()}",ST); pg.wait_for_timeout(300)
    pg.evaluate("()=>{const c=S.characters[0];c.monthly.blackmage=S.period.week;c.mdate={blackmage:'2026-10-08'};save();render()}"); pg.wait_for_timeout(300)
    shot(pg.locator('.pricecard'),'pricecard'); shot(pg.locator('.revpanel'),'revpanel'); shot(pg.locator('.stats.s3').first,'charinfo')
    pg.evaluate("openRevAll()"); pg.wait_for_timeout(300); shot(pg.locator('#revAllModal .modal'),'revall'); pg.evaluate("document.querySelector('#revAllModal')?.remove()")
    if not NOCHK:
        k=pg.eval_on_selector_all('.pricecard [data-pckind]',"e=>e.map(x=>[x.dataset.pckind,x.innerText.trim(),x.classList.contains('on')])")
        check('가격 카드 탭: 결정석 가격(선택) / 아이템 가격', [x[1] for x in k]==['결정석 가격','아이템 가격'] and k[0][2], k)
        check('결정석 가격 탭에 내가 잡는 보스만 보기', pg.locator('.pricecard #pcMine').count()==1)
        pg.click('[data-pckind=item]'); pg.wait_for_timeout(250)
        check('아이템 가격 탭: 체크박스 없음', pg.locator('.pricecard #pcMine').count()==0)
        rows=pg.eval_on_selector_all('.pc-it',"e=>e.map(x=>[x.dataset.pit,x.querySelector('.pc-nm').innerText,x.querySelector('b').innerText,!!x.querySelector('img')])")
        exp=pg.evaluate("revItems()")
        check('목록 = 수익 기록 가능한 아이템 전부, itemCmp 순서, 아이콘', [x[0] for x in rows]==exp and pg.evaluate("(l=>l.every((k,i)=>!i||itemCmp(l[i-1],k)<=0))(revItems())") and all(x[3] for x in rows) and len(rows)>20, len(rows))
        check('칠흑 상자 대신 장신구, 반지 상자 대신 리4·컨4·생명의 연마석', 'chaosbox' not in exp and 'cb:belt' in exp and 'ring:r4' in exp and 'g_life' in exp and not any(x.startswith('r_') for x in exp), exp[:8])
        d={x[0]:x[2] for x in rows}
        check('시세 표시 (서버 /api/prices): 근원의 속삭임 62억, 익셉셔널 해머(얼굴장식) 61억 9,900만', d.get('whisper')=='62억 메소' and d.get('h_face')=='61억 9,900만 메소' and SRV['pub']>=1, (d.get('whisper'),d.get('h_face'),SRV['pub']))
        check("시세 없는 아이템 = '- 메소'", d.get('oath')=='- 메소', d.get('oath'))
        shot(pg.locator('.pricecard'),'pricecard_items')
        mm=pg.evaluate("Object.keys(maiMap({'익셉셔널 얼장':{main:61.99},'익셉셔널 눈장':{main:221.33},'익셉셔널 벨트':{main:57.78},'익셉셔널 훈장':{main:800}},1))")
        check('maple.ai.kr 익셉셔널 얼장/눈장/벨트 → 해머 3종 (훈장 제외)', sorted(mm)==['h_belt','h_eye','h_face'], mm)
        pg.evaluate("openAdmin()"); pg.wait_for_timeout(400)
        check("관리자 창 '시세 등록' 버튼", pg.locator('#mktBtn').count()==1)
        shot(pg.locator('#adminModal .modal'),'admin')
        pg.click('#mktBtn'); pg.wait_for_timeout(300)
        n=pg.locator('#mktModal [data-mk]').count(); vals=pg.evaluate("[...document.querySelectorAll('#mktModal .rarow')].map(r=>[r.querySelector('.raname').innerText,r.querySelector('input').value])")
        check('시세 등록 창: 모든 아이템 + 등록된 시세 채움(근원의 속삭임 62)', n==len(exp) and any(v[1]=='62' and '근원의 속삭임' in v[0] for v in vals), (n,len(exp)))
        check('시세 등록 창: 안내 문구 없음', pg.locator('#mktModal .rvguide, #mktModal .note, #mktModal .muted:not(.ram)').count()==0)
        shot(pg.locator('#mktModal .modal'),'mkt')
        i=exp.index('oath'); pg.fill(f'#mktModal [data-mk="{i}"]','12.5'); pg.locator('#mktModal [data-mkb=ok]').click(); pg.wait_for_timeout(600)
        check('저장 → 서버 PUT (고친 것만)', SRV['puts'] and list(SRV['puts'][-1])==['oath'] and SRV['puts'][-1]['oath']['p']==1250000000, SRV['puts'])
        pg.evaluate("document.querySelector('#adminModal')?.classList.remove('show')")
        check('바로 반영: 아이템 가격 탭 죽음의 맹세 12억 5,000만', pg.inner_text(".pc-it[data-pit=oath] b")=='12억 5,000만 메소', pg.inner_text(".pc-it[data-pit=oath] b"))
        pg.click('[data-pckind=cry]'); pg.wait_for_timeout(200); check('결정석 가격 탭으로 돌아감', pg.locator('.pricecard #pcMine').count()==1)
        ic=pg.evaluate("(()=>{const e=document.querySelector('.rp-sale .rpsico');return e?[e.title,e.nextSibling&&e.nextSibling.textContent]:null})()")
        check("'이번주 획득 아이템' 앞 = 가장 비싸게 판 아이템(죽음의 맹세 9억) 아이콘", ic and ic[0]=='죽음의 맹세' and ic[1].startswith('이번주 획득 아이템'), ic)
        cs=pg.evaluate("[document.querySelector('#ciCry')?.innerText,document.querySelector('#ciSale')?.innerText,meso(cRev(S.characters[0]).meso+price(findBoss('blackmage'),'extreme'))]")
        check("캐릭터 정보: '결정석 …' · '아이템 판매 14억 메소'", cs[1]=='아이템 판매 14억 메소' and cs[0]=='결정석 '+cs[2], cs)
        st=pg.inner_text('.stats.s3').replace('\n',' ')
        check("'이번달 검마 (10월 8일 격파 완료)'", '이번달 검마 (10월 8일 격파 완료)' in st, st[:200])
        pg.evaluate("openRevAll()"); pg.wait_for_timeout(300)
        g=pg.evaluate("[...document.querySelectorAll('#revAllModal .ragrp')].map(g=>[g.querySelector(':scope>.rabi').dataset.boss,g.querySelector('.dbadge')?.innerText,g.querySelector('.dbadge')?getComputedStyle(g.querySelector('.dbadge')).backgroundColor:'',g.querySelectorAll('.rarow').length,g.querySelectorAll('.rarow .rabi').length])")
        check('보스별 묶음: 루시드(2개)·카링(1개), 초상화 1번(줄에는 없음)', [(x[0],x[3]) for x in g][:2]==[('lucid',2),('kaling',1)] and all(x[4]==0 for x in g), g)
        check('난이도 배지: 하드 H 빨강, 노말 N 연두', g[0][1]=='H' and g[0][2]=='rgb(220, 38, 38)' and g[1][1]=='N' and g[1][2]=='rgb(134, 239, 172)', g)
        pos=pg.evaluate("(()=>{const g=document.querySelector('#revAllModal .ragrp');return g.querySelector(':scope>.rabi').getBoundingClientRect().right<=g.querySelector('.rarow .raic').getBoundingClientRect().left})()")
        check('보스 초상화가 왼쪽, 아이템 아이콘이 오른쪽 (자리 바꿈)', pos)
        bd=pg.evaluate("['easy','normal','hard','chaos','extreme'].map(d=>diffBadge(d).match(/>(\\w)</)[1]).join('')")
        check('배지 글자 E N H C X', bd=='ENHCX', bd)
        pg.locator('#revAllModal [data-ra="0"]').fill('7'); pg.locator('#revAllModal [data-rab=ok]').click(); pg.wait_for_timeout(300)
        check('묶어도 입력 번호대로 저장 (첫 칸 = 루시드 근원의 속삭임 7억)', pg.evaluate("S.characters[0].drev['lucid|whisper'].m")==700000000)
        # 429 (초당 한도) → 1번 재시도, 하루 한도 표시 아님
        r=pg.evaluate("(async()=>{ const t=Date.now(); const d=await nx('/maplestory/v1/id',{character_name:'tst429'},'live_K9_zzzzzzzzzzzzzzzzzz'); return [d.ocid, Date.now()-t, quotaOf('live_K9_zzzzzzzzzzzzzzzzzz'), quotaHtml('live_K9_zzzzzzzzzzzzzzzzzz')]; })()")
        check('초당 429 → 1.2초 뒤 1번 재시도해서 성공, 오늘 한도 아님, 배지 = 초당 호출 제한', r[0]=='x1' and r[1]>=1150 and len(SRV['nx'])==2 and not r[2]['over'] and '초당 호출 제한' in r[3] and '호출 한도 도달' not in r[3], r)
        check('호출 속도: 키마다 1.1초에 4건', pg.evaluate("CONFIG.API_RATE_N")==4)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
if not NOCHK: print('FAILS:',fails,'ERRORS:',errs[:3]); sys.exit(1 if fails or errs else 0)
