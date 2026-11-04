# test_b374 (t690): 파티 보스 모달 — 보스 여러 개 선택, 묶음 일정(bs) 1개 저장, 상세 한 줄, 배지 1개, 같은 주 중복 막기, 예전 단일 호환.
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SD=os.environ.get('B374_SHOTDIR') or OUT
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{}});
  const B={lucid:{enabled:true,party:2,diff:'hard'},seren:{enabled:true,party:2,diff:'hard'},star:{enabled:true,party:2,diff:'normal'},lotus:{enabled:true,party:2,diff:'extreme'}};
  const c0=mk('c0','트딕이'), c1=mk('c1','부캐냥'); c0.bosses=JSON.parse(JSON.stringify(B)); c1.bosses=JSON.parse(JSON.stringify(B)); S.characters=[c0,c1];
  S.history=[{week:'2026-10-15',perChar:[{id:'c1',name:'부캐냥',bosses:['찬란한 흉성(노말)'],bvals:[1e8]}]}]; S.calNotes={};
  S.activeId='c0'; save(); render(); }"""
L="[...document.querySelectorAll('#calBossModal .calbi')].map(e=>e.dataset.calbs+(e.classList.contains('on')?'*':'')+(e.disabled?'X':''))"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1300,'height':950},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(200)
    r=pg.evaluate("(()=>{ calBM={day:'2026-10-21',cids:['c0','c1']}; calBossRender(); document.querySelector('[data-calbs=star]').click(); return "+L+"; })()")
    check('비활성 보스는 선택 안 됨', 'starX' in r and not any(x.startswith('star*') for x in r), r)
    day=pg.evaluate("dayId(Date.now())")
    pg.evaluate(f"calBM={{day:'{day}',cids:['c0','c1']}}; calBossRender()")
    check('선택 전: 시간·저장 없음', pg.locator('#calBossModal .calbh').count()==0)
    pg.click('[data-calbs="lucid"]'); pg.click('[data-calbs="seren"]'); pg.wait_for_timeout(80)
    r=pg.evaluate(L); check('보스 두 개 토글(.on)', 'lucid*' in r and 'seren*' in r and pg.locator('#calBossModal .calbi.on').count()==2, r)
    sub=pg.evaluate("document.querySelector('#calBossModal .calbsub').textContent")
    check('부제 = 닉1, 닉2, 보스1 (난이도), 보스2 (난이도)', sub=='트딕이, 부캐냥, 루시드 (), 선택받은 세렌 ()' and pg.locator('#calBossModal .calbsub .calbsb').count()==2, sub)
    ws=pg.evaluate("[...document.querySelectorAll('#calBossModal .calbsb')].map(e=>getComputedStyle(e).whiteSpace)"); check('보스+난이도 안 쪼개짐(nowrap)', ws==['nowrap','nowrap'], ws)
    check('시간·저장·취소 보임 + 목록 유지', pg.locator('#calBossModal .calbh').count()==1 and pg.locator('[data-calbsave]').count()==1 and pg.locator('[data-calbreset]').count()==1 and pg.locator('#calBossModal .calbi').count()==4)
    pg.locator('#calBossModal .modal').screenshot(path=os.path.join(SD,'multi_boss.png'))
    pg.click('[data-calbs="seren"]'); check('다시 누르면 해제', pg.locator('#calBossModal .calbi.on').count()==1); pg.click('[data-calbs="seren"]')
    pg.click('[data-calbreset]'); check('취소 = 보스 선택 비움', pg.locator('#calBossModal .calbi.on').count()==0 and pg.locator('#calBossModal .calbh').count()==0)
    pg.click('[data-calbs="lucid"]'); pg.click('[data-calbs="seren"]'); pg.select_option('.calbh','21'); pg.select_option('.calbmi','30'); pg.click('[data-calbsave]'); pg.wait_for_timeout(120)
    e=pg.evaluate(f"Object.values(S.calNotes['{day}'].b)")
    check('묶음 일정 1개(보스 2·캐릭터 2)', len(e)==1 and [x['boss'] for x in e[0]['bs']]==['lucid','seren'] and e[0]['cids']==['c0','c1'] and e[0]['h']==21 and e[0]['mi']==30, e)
    r=pg.evaluate(L); check('같은 주 중복: 묶음 안 보스 전부 비활성', 'lucidX' in r and 'serenX' in r and 'lotus' in r, r)
    lb=pg.evaluate("document.querySelector('[data-calbs=seren] .calbclr').textContent"); check('라벨 = 일정 등록됨 (닉, 날짜 시간)', lb.startswith('·이번 주 일정 등록됨 (트딕이, ') and lb.endswith(' 21:30 / 부캐냥, '+day[5:7]+'/'+day[8:]+' 21:30)'), lb)
    pg.click('#calBossModal .calbcls')
    pg.evaluate(f"()=>{{ S.calNotes['{day}'].b.old={{cid:'c0',n:'트딕이',slot:'lotus',boss:'lotus',d:'extreme',p:2,h:9,mi:0,at:1}}; save(); calSel='{day}'; renderCal(); }}")
    rows=pg.evaluate("[...document.querySelectorAll('#calDet .calsi')].map(e=>[e.querySelector('.calst').textContent,[...e.querySelectorAll('.calsn')].map(x=>x.textContent.replace(/\\s+/g,' ').trim()),e.querySelectorAll('.bicon').length,[...e.querySelectorAll('.calscc>span')].map(x=>x.textContent)])")
    check('상세: 묶음 한 줄(시간·보스 아이콘·이름·난이도·인원 전부·캐릭터) + 예전 단일', rows==[['09:00',['스우 2인'],1,['트딕이']],['21:30',['루시드 2인','선택받은 세렌 2인'],2,['트딕이','부캐냥']]], rows)
    check('칸 배지: 묶음 = 1개', pg.evaluate(f"document.querySelector('[data-calday=\"{day}\"] .calbb').textContent")=='·보스 일정 2개')
    pg.wait_for_timeout(500); pg.locator('#calDet').screenshot(path=os.path.join(SD,'grouped_multi_detail.png'))
    pg.evaluate(f"()=>{{ delete S.calNotes['{day}'].b[Object.keys(S.calNotes['{day}'].b).find(k=>k!=='old')]; save(); }}")
    r=pg.evaluate(f"(()=>{{ calBM={{day:'{day}',cids:['c0','c1']}}; calBossRender(); return "+L+"; })()")
    check('묶음 삭제 → 다시 활성', 'lucid' in r and 'seren' in r and 'lotusX' in r, r)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
