# test_b302 (t520u): 최근 보유 메소 — 프로필 고정 영역 OCR (인벤 / 창고 열림 시 창고+창고 옆 인벤), 닉네임 앞뒤 확인,
#   메이플 ID(character/list 의 account_list[].account_id)별 묶음, '이번달 검마' 칸 바로 위 표시(다크/라이트), 새로고침 유지
import os, sys, json, base64, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FX=os.path.join(ROOT,'tests','fixtures'); OUT=os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
du=lambda f:'data:image/png;base64,'+base64.b64encode(open(f,'rb').read()).decode()
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
pm=json.load(open(os.path.join(FX,'t523','meta.json'))); mm=json.load(open(os.path.join(FX,'t520','meta.json')))
V={3:22564195389,4:22564195389,7:22564211971,8:22564211971,11:22564231214,12:22564231214,15:22564245632,16:22564245632,19:22564257269,20:22564257269}
COMP="""async ([w,h,bl,cr])=>{ const ld=u=>new Promise(r=>{ const im=new Image(); im.onload=()=>r(im); im.src=u; });
  const cv=document.createElement('canvas'); cv.width=w; cv.height=h; const g=cv.getContext('2d'); g.fillStyle='#000'; g.fillRect(0,0,w,h);
  const b=await ld(bl); g.drawImage(b,0,h-b.height); for(const [u,x,y] of cr) g.drawImage(await ld(u),x,y); return cv; }"""
SETUP="""()=>{ const all={}; for(const b of BOSSES) all[b.id]={enabled:true,party:1,diff:b.diffs.includes('hard')?'hard':b.diffs[0]};
 const mk=(id,name,ocid)=>({id,name,level:285,job:'',world:'스카니아',ocid,accId:'',isMain:id==='c0',image:'',bosses:all,weekly:{},monthly:{},auto:{},drops:{},sync:{}});
 S.characters=[mk('c0','트딕이','o-1'),mk('c1','부캐하나','o-2'),mk('c2','딴계정','o-3')]; S.activeId='c0'; S.meso={}; save(); render(); return 1; }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    # 넥슨 character/list 실제 응답 구조: { account_list:[ { account_id, character_list:[ {ocid, character_name, world_name, character_class, character_level} ] } ] }
    LIST={'account_list':[{'account_id':'maple-A','character_list':[{'ocid':'o-1','character_name':'트딕이','world_name':'스카니아','character_class':'히어로','character_level':285},{'ocid':'o-2','character_name':'부캐하나','world_name':'스카니아','character_class':'비숍','character_level':260}]},
                          {'account_id':'maple-B','character_list':[{'ocid':'o-3','character_name':'딴계정','world_name':'스카니아','character_class':'팔라딘','character_level':250}]}]}
    pg.route('https://open.api.nexon.com/**',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(LIST)) if 'character/list' in r.request.url else r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP)
    check('메소 표기 "1조 2345억 6789만 1234메소"',pg.evaluate("fmtMesoFull(1234567891234)")=='1조 2345억 6789만 1234메소',pg.evaluate("fmtMesoFull(1234567891234)"))
    check('OCR 문자열 해석 (먹→억·반→만 보정)',pg.evaluate("[arMesoParse('225먹 6419만 5389'),arMesoParse('1조 2345억 6789반 1234'),arMesoParse('0'),arMesoParse('가나')]")==[22564195389,1234567891234,0,None])
    # 20장: 창 열림 판단 + 값
    for n in range(1,21):
      w,h=pm[str(n)]; cr=[[du(os.path.join(FX,'t520',f)),x,y] for f,x,y in mm[str(n)]]
      r=pg.evaluate("async a=>{ const cv=await ("+COMP+")(a); const A=window.AR; A.bbox=null;A.bbKey='';A.prof=null;A.geo=null; await arProfDetect(cv);"
        " const so=arMesoPanel(cv,'sto')&&arMesoPanel(cv,'stoInv'), io=!so&&arMesoPanel(cv,'inv'); const o={so,io};"
        " if(so){ o.inv=(await arMesoRead(cv,'stoInv')).v; o.sto=(await arMesoRead(cv,'sto')).v; } else if(io) o.inv=(await arMesoRead(cv,'inv')).v; return o; }",[w,h,du(os.path.join(FX,'t523','bl%02d.png'%n)),cr])
      if n in V: ok=r['inv']==V[n] and (r['so']==(n%2==0)) and (r.get('sto')==0 if n%2==0 else True)
      else: ok=not r['so'] and not r['io']
      check(f'{n:02d}번 {w}x{h} 메소 ' + ('창고 열림' if n in V and n%2==0 else '인벤' if n in V else '창 닫힘'),ok,r)
    # 닉네임 앞뒤 확인 + 메이플 ID 묶음
    pg.evaluate("async()=>{ await listAccount({id:'k1',key:'live_test'}); }")
    check('character/list account_id → 캐릭터 메이플 ID',pg.evaluate("S.characters.map(c=>c.mapleAcc)")==['maple-A','maple-A','maple-B'],pg.evaluate("S.characters.map(c=>c.mapleAcc)"))
    w,h=pm['4']; cr=[[du(os.path.join(FX,'t520',f)),x,y] for f,x,y in mm['4']]
    pg.evaluate("async a=>{ window._cv=await ("+COMP+")(a); }",[w,h,du(os.path.join(FX,'t523','bl04.png')),cr])
    T0=pg.evaluate("new Date(2026,9,30,21,18).getTime()")
    r=pg.evaluate("""async t=>{ const A=window.AR; A.bbox=null;A.bbKey='';A.prof=null;A.geo=null; await arProfDetect(window._cv); const on=Date.now;
      let seq=['c1']; A.nameOf=()=>seq.shift()||'c2'; seq=['c2']; Date.now=()=>t; A.det.cid='c1'; const bad=await arMesoNow(window._cv); const savedBad=JSON.stringify(S.meso);
      seq=['c1']; A.nameOf=()=>'c1'; A.det.cid='c1'; const good=await arMesoNow(window._cv); A.nameOf=null; Date.now=on; return {bad,savedBad,good,meso:S.meso}; }""",T0)
    check('닉네임이 메소 읽는 사이 바뀌면 저장 안 함',r['bad'].get('why')=='name' and r['savedBad']=='{}',r)
    check('닉네임 같으면 메이플 ID(maple-A)로 저장 (인벤+창고)',r['good'].get('inv')==22564195389 and r['meso'].get('a:maple-A',{}).get('inv')==22564195389 and r['meso']['a:maple-A'].get('sto')==0,r)
    # 표시
    for th in ['dark','light']:
      pg.evaluate(f"document.documentElement.dataset.theme='{th}'; S.activeId='c0'; render()"); pg.wait_for_timeout(300)
      q=pg.evaluate("""()=>{ const m=document.querySelector('.mesorow .mesolast'); if(!m) return null; const st=[...document.querySelectorAll('.stat')].find(s=>s.querySelector('.k')?.textContent.startsWith('이번달 검마'));
        const a=m.getBoundingClientRect(), c=st.getBoundingClientRect(); return {t:m.textContent, dx:Math.round(a.right-c.right), full:m.scrollWidth<=m.clientWidth+1, gap:Math.round(c.top-a.bottom), next:m.parentElement.nextElementSibling===st.parentElement, col:getComputedStyle(m).color}; }""")
      check(f'{th}: 같은 메이플 ID 다른 캐릭터(본캐 카드)에 "최근 보유 메소" 표시',q and q['t'].startswith('최근 보유 메소 : 225억 6419만 5389메소 (10/30 21:18)'),q)
      check(f'{th}: "이번달 검마" 칸 바로 위 (오른쪽 끝 맞춤·안 잘림)',q and q['next'] and abs(q['dx'])<=2 and q['full'] and 0<=q['gap']<=12,q)
      el=pg.query_selector('.mesorow'); box=el.bounding_box(); pg.screenshot(path=os.path.join(OUT,f'b302_meso_{th}.png'),clip={'x':max(0,box['x']-20),'y':max(0,box['y']-120),'width':min(1100,1600-box['x']+20),'height':260})
    pg.evaluate("S.activeId='c0'; S.meso['a:maple-A']={...S.meso['a:maple-A'],sto:100000000}; render()"); pg.wait_for_timeout(200)
    tt=pg.evaluate("(document.querySelector('.mesorow .mesolast')||{}).textContent||''")
    check('창고 메소는 인벤에 합산해 한 금액만 표시 (창고 별도 표기 없음)',tt.startswith('최근 보유 메소 : 226억 6419만 5389메소 (') and '창고' not in tt,tt)
    pg.evaluate("S.meso['a:maple-A'].sto=0")
    pg.evaluate("S.activeId='c2'; render()")
    check('다른 메이플 ID 캐릭터에는 표시 안 함',pg.evaluate("!document.querySelector('.mesorow')"))
    pg.reload(); pg.wait_for_timeout(800); pg.evaluate("S.activeId='c0'; render()")
    check('새로고침 뒤에도 유지',pg.evaluate("(document.querySelector('.mesorow .mesolast')||{}).textContent||''").startswith('최근 보유 메소 : 225억'))
    b.close()
finally:
  srv.kill()
check('페이지 오류 없음',not errs,errs)
print('FAILS:',fails); sys.exit(1 if fails else 0)
