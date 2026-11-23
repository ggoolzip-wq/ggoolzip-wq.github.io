import _tutil  # 빈 포트·서버 정리·운영 Worker 차단 (tests/_tutil.py)
_PA=_tutil.free_port(); _PB=_tutil.free_port(); _PC=_tutil.free_port()
# b435 (t583u): 관리자 창에서 아이디(이름) 누르면 그 사용자 기록을 읽기 전용으로 봄 — GET /api/admin/view (로컬 wrangler dev D1)
#  서버: 비관리자 403·토큰 없음 401·GET 외 405·키/계정해시/메모/설정 빠짐·대상 rev/세션/기록 그대로·관리자 토큰으로 남의 state 못 씀
#  화면: 보기 열고 닫는 동안 쓰기 요청 0건(PUT/POST/DELETE), 관리자 자신의 localStorage·S 그대로. MBT_SHOTDIR 에 b435_admin_*.png
import os, sys, json, subprocess, time, urllib.request, urllib.error
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_dev, mock_nexon_list as MN
from playwright.sync_api import sync_playwright
SHOT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(SHOT,exist_ok=True)
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
T=open(os.path.join(ROOT,'tests','test_b216.py'),encoding='utf-8').read(); exec(T[T.index("KA,KF="):T.index("if not cf_dev")])
if not cf_dev.available(): print('SKIP: wrangler/node22 not installed'); print('FAILS: []'); sys.exit(0)
PORT, WP, NP = _PA, _PB, _PC
API=f'http://127.0.0.1:{WP}'; URL=f'http://localhost:{PORT}/index.html'
KB='live_KEY_B_0123456789abcdef'
def req(m,path,body=None,tok=None):
    h={'Content-Type':'application/json','Origin':'https://bossmaple.pages.dev',**({'Authorization':'Bearer '+tok} if tok else {})}
    r=urllib.request.Request(API+path,data=json.dumps(body).encode() if body is not None else None,method=m,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=15) as res: return res.status, json.loads(res.read() or b'null')
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b'null')
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
ms=MN.start(NP); dev=cf_dev.Dev(WP,NP)
try:
    # 사용자 B (테스트 계정) — 기록 있는 state
    s,bl=req('POST','/api/login',{'key':KB}); TB=bl['token']; UB=dev.sql("SELECT user_id FROM accounts WHERE acct_hash=(SELECT acct_hash FROM accounts ORDER BY created_at DESC LIMIT 1)")[0]['user_id']
    mk=lambda i,n,lv,main,acc: {'id':i,'name':n,'level':lv,'job':'비숍','world':'스카니아','accId':acc,'isMain':main,'image':'','mapleAcc':'RAW-ACCOUNT-ID-123',
        'bosses':{'lucid':{'enabled':True,'diff':'hard','party':1},'will':{'enabled':True,'diff':'hard','party':2},'blackmage':{'enabled':True,'diff':'hard','party':1}},
        'weekly':{'lucid':True,'will':True},'monthly':{'blackmage':'2026-11-19'},'mdate':{'blackmage':'2026-11-20'},'auto':{},'drops':{'lucid|belt':1,'will|book':1},'mdrops':{'blackmage|genesis':1},'sync':{}}
    BST={'version':5,'characters':[mk('b1','테스트본캐',287,True,'a1'),mk('b2','테스트부캐',275,False,'a1')],'history':[{'week':'2026-11-12','total':12300000000,'cleared':14,'items':1,'perChar':[]}],
         'meso':{'c:b1':{'inv':65963924492,'sto':1200000000,'at':1763800000000,'by':'b1','name':'테스트본캐'}},'period':{'week':'2026-11-19','day':'2026-11-23','month':'2026-11'},
         'calNotes':{'2026-11-20':'비밀 메모'},'settings':{'accounts':[{'id':'a1','label':'본계정','main':True,'ah':bl['accounts'][0]}]}}
    s,_=req('PUT','/api/state',{'baseRev':0,'updatedAt':5,'data':BST},tok=TB); check('B state saved', s==200, s)
    snapB=lambda: dev.sql(f"SELECT rev, saved_at, updated_at, data FROM state WHERE user_id='{UB}'")[0]
    sessB=lambda: dev.sql(f"SELECT COUNT(*) n FROM sessions WHERE user_id='{UB}'")[0]['n']
    histB=lambda: dev.sql(f"SELECT COUNT(*) n FROM state_history WHERE user_id='{UB}'")[0]['n']
    B0=snapB(); S0=sessB(); H0=histB()
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
        c1,p1=mkctx(b); fresh(p1); login(p1,KA); wait_on(p1)
        UA=dev.sql("SELECT id FROM users WHERE id<>'"+UB+"'")[0]['id']; TA=p1.evaluate("svTok()")
        # 비관리자 상태에서 거부
        s,r=req('GET','/api/admin/view?user='+UA,tok=TB); check('비관리자 → 403 not_admin', s==403 and r.get('error')=='not_admin', (s,r))
        s,r=req('GET','/api/admin/view?user='+UB); check('토큰 없음 → 401', s==401, (s,r))
        s,r=req('GET','/api/admin/view?user='+UB,tok=TA); check('A 가 아직 관리자 아님 → 403', s==403, (s,r))
        dev.sql(f"INSERT OR REPLACE INTO meta (k,v) VALUES ('admin_user','{UA}')")
        s,r=req('GET','/api/admin/view?user='+UB,tok=TA); print(json.dumps(r,ensure_ascii=False)[:600])
        d=r.get('data') or {}
        check('관리자 GET → 200, 캐릭터·주간·드롭·메소·주간 기록', s==200 and [c['name'] for c in d.get('characters',[])]==['테스트본캐','테스트부캐'] and d['characters'][0]['drops']=={'lucid|belt':1,'will|book':1} and d['meso']['c:b1']['inv']==65963924492 and len(d['history'])==1, (s,list(d)))
        txt=json.dumps(r,ensure_ascii=False)
        check('키·계정 해시·원본 계정 id·메모·설정 없음', KB not in txt and bl['accounts'][0] not in txt and 'RAW-ACCOUNT-ID' not in txt and '비밀 메모' not in txt and 'settings' not in d and 'calNotes' not in d and d['accounts']==[{'id':'a1','label':'본계정','main':True}], txt[:300])
        for M in ['POST','PUT','DELETE','PATCH']:
            s,r=req(M,'/api/admin/view?user='+UB,{'data':{'characters':[]}},tok=TA); check(f'{M} /api/admin/view → 405 read_only', s==405 and r.get('error')=='read_only', (s,r))
        s,r=req('GET','/api/admin/view?user=nope',tok=TA); check('없는 사용자 → 404', s==404, (s,r))
        # 관리자 토큰으로 B 데이터 쓰기 시도 (user 필드·쿼리) → 관리자 자신의 데이터에만 적용, B 는 그대로
        s,ma=req('GET','/api/state',tok=TA)
        s,r=req('PUT','/api/state?user='+UB,{'baseRev':ma['rev'],'updatedAt':9,'user':UB,'data':ma['data'] or {'characters':[]}},tok=TA)
        check('관리자 PUT /api/state(user 지정) 는 관리자 자신의 것만 바꿈', B0==snapB(), s)
        # 화면: 관리자 창 → 이름 클릭 → 읽기 전용 보기 (쓰기 요청 0)
        p1.evaluate("svAdminCheck()"); p1.wait_for_timeout(500)
        before=p1.evaluate("localStorage.getItem('mapleBossTracker.v1')"); sigA=p1.evaluate("JSON.stringify(S.characters)")
        p1.evaluate("openAdmin()"); p1.wait_for_selector(f"#admBody [data-admview='{UB}']",timeout=10000); p1.wait_for_timeout(300)
        p1.locator('#adminModal .modal').first.screenshot(path=os.path.join(SHOT,'b435_admin_list.png'))
        W=[]; p1.on('request',lambda q: W.append(q.method+' '+q.url) if q.method!='GET' and '127.0.0.1:'+str(WP) in q.url else None)
        p1.click(f"#admBody [data-admview='{UB}']"); p1.wait_for_selector('#admvBody .admv-card',timeout=10000); p1.wait_for_timeout(400)
        t=p1.inner_text('#admvBody'); print(t[:500])
        check('보기: 두 캐릭터·주간 클리어·득템·메소·월간·주간 기록', '테스트본캐' in t and '테스트부캐' in t and '주간 클리어 2' in t and '몽환의 벨트' in t and '창세의 뱃지' in t and '659.64억' in t and '창고 12.00억' in t and '123.00억' in t and '검은 마법사(하드)' in t, t[:300])
        ro=p1.evaluate("()=>{ const m=document.querySelector('#admViewModal'); return {inputs:m.querySelectorAll('input,select,textarea,[contenteditable=true]').length, btns:[...m.querySelectorAll('button')].map(b=>b.id||b.textContent), title:document.querySelector('#admvTitle').textContent}; }")
        check('보기 창: 입력칸 0, 버튼은 닫기(✕)뿐, 제목에 읽기 전용', ro['inputs']==0 and ro['btns']==['admvClose'] and '읽기 전용' in ro['title'], ro)
        p1.locator('#admViewModal .modal').screenshot(path=os.path.join(SHOT,'b435_admin_view.png'))
        # 보기 안을 여러 곳 클릭해도 아무 것도 안 바뀜
        for sel in ['.admv-card','.admv-chip','.admv-meta','h4']:
            try: p1.locator('#admvBody '+sel).first.click(timeout=2000)
            except Exception: pass
        p1.wait_for_timeout(300); p1.click('#admvClose'); p1.wait_for_timeout(300)
        st2=p1.evaluate("()=>({view:document.querySelector('#admViewModal').classList.contains('show'), admin:document.querySelector('#adminModal').classList.contains('show')})")
        check('닫으면 보기만 닫히고 관리자 창 그대로', not st2['view'] and st2['admin'], st2)
        p1.click(f"#admBody [data-admview='{UB}']"); p1.wait_for_selector('#admvBody .admv-card'); p1.keyboard.press('Escape'); p1.wait_for_timeout(300)
        check('Esc 도 보기만 닫음', p1.evaluate("()=>!document.querySelector('#admViewModal').classList.contains('show')&&document.querySelector('#adminModal').classList.contains('show')"))
        p1.wait_for_timeout(2500)
        check('보기 동안 쓰기 요청 0건 (PUT/POST/DELETE)', W==[], W)
        check('관리자 자신의 데이터(localStorage·S) 그대로 — B 기록이 섞이지 않음', p1.evaluate("localStorage.getItem('mapleBossTracker.v1')")==before and p1.evaluate("JSON.stringify(S.characters)")==sigA and '테스트본캐' not in (before or ''), '')
        check('B 서버 기록·rev·기록 이력·세션 수 그대로 (위장·토큰 발급 없음)', snapB()==B0 and histB()==H0 and sessB()==S0, (snapB()['rev'],B0['rev'],sessB(),S0))
        # 모바일 390px — 보기 한 줄 카드, 가로 넘침 없음
        p1.set_viewport_size({'width':390,'height':844}); p1.click(f"#admBody [data-admview='{UB}']"); p1.wait_for_selector('#admvBody .admv-card'); p1.wait_for_timeout(300)
        mw=p1.evaluate("()=>{ const m=document.querySelector('#admViewModal .modal'), g=document.querySelector('.admv-grid'); return {ov:m.scrollWidth<=m.clientWidth+1, cols:getComputedStyle(g).gridTemplateColumns.split(' ').length, vw:document.documentElement.scrollWidth}; }")
        check('모바일: 1열·가로 넘침 없음', mw['ov'] and mw['cols']==1 and mw['vw']<=391, mw)
        p1.locator('#admViewModal .modal').screenshot(path=os.path.join(SHOT,'b435_admin_view_m.png'))
        p1.set_viewport_size({'width':1280,'height':800}); p1.wait_for_timeout(300)
        g=p1.evaluate("()=>getComputedStyle(document.querySelector('.admv-grid')).gridTemplateColumns.split(' ').length"); p1.keyboard.press('Escape')
        check('PC: 2열', g==2, g)
        check('JS 오류 없음', not errs, errs)
        b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e)); fails.append('exception')
finally:
    dev.stop(); ms.shutdown(); srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
