# test_b367 (t681): 캘린더 상세 +메모 추가 · +보스 일정 추가(모달) — 저장·목록·칸 배지(깜빡임)·로컬 저장·동기화 병합·라이트.
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
SD=os.environ.get('B367_SHOTDIR') or OUT
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{}});
  const c0=mk('c0','트딕이'), c1=mk('c1','부캐냥'); S.characters=[c0,c1];
  c0.bosses={lucid:{enabled:true,party:2,diff:'hard'},will:{enabled:true,party:1,diff:'hard'},seren:{enabled:true,party:3,diff:'hard'},dusk:{enabled:false,party:2,diff:'chaos'}};
  c1.bosses={will:{enabled:true,party:1,diff:'normal'}}; S.activeId='c0'; save(); render(); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1400,'height':1100},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(300)
    day=pg.evaluate("dayId(Date.now())"); pg.locator(f'[data-calday="{day}"]').click(); pg.wait_for_timeout(200)
    o=pg.evaluate("""()=>{ const n=document.querySelector('#calDet .calnb'); return {prev:n&&n.previousElementSibling.className, next:n&&n.nextElementSibling&&n.nextElementSibling.className, t:n&&[...n.querySelectorAll('button')].map(b=>b.textContent)}; }""")
    check('상세: 날짜 머리 바로 아래 두 버튼', o['prev']=='caldh' and o['t']==['+메모 추가','+보스 일정 추가'], o)
    pg.locator('#calDet').screenshot(path=os.path.join(SD,'detail_buttons.png'))
    pg.click('[data-calmemo]'); pg.wait_for_timeout(100)
    check('메모 입력창 열림·포커스', pg.evaluate("document.activeElement&&document.activeElement.classList.contains('calmt')"))
    pg.fill('.calmt','첫 메모\n둘째 줄'); pg.locator('#calDet').screenshot(path=os.path.join(SD,'memo_edit.png'))
    pg.click('[data-calmsave]'); pg.wait_for_timeout(100)
    pg.click('[data-calmemo]'); pg.click('[data-calmcancel]'); check('취소 → 입력창 닫힘', pg.locator('.calmt').count()==0)
    pg.click('[data-calmemo]'); pg.fill('.calmt','레이드 준비'); pg.click('[data-calmsave]'); pg.wait_for_timeout(100)
    check('메모 여러 개 목록', pg.locator('#calDet .calmi').count()==2, pg.locator('#calDet .calmi').count())
    cell=f'[data-calday="{day}"]'
    bm=pg.evaluate(f"""()=>{{ const e=document.querySelector('{cell} .calbm'); if(!e) return null; const cs=getComputedStyle(e); return {{t:e.textContent,c:cs.color,a:cs.animationName,d:cs.animationDuration,next:e.parentElement.previousElementSibling.className}}; }}""")
    check('칸 배지 ·메모 2개 (초록·깜빡임 2.4s, 날짜 옆)', bm and bm['t']=='·메모 2개' and bm['a']=='calblink' and bm['d']=='2.4s' and bm['next']=='cald' and bm['c']=='rgb(62, 224, 138)', bm)
    kf=pg.evaluate("""()=>{ for(const s of document.styleSheets){ try{ for(const r of s.cssRules) if(r.type===7&&r.name==='calblink') return [...r.cssRules].map(k=>k.style.cssText).join('|'); }catch(e){} } return ''; }""")
    check('깜빡임 = 투명도만', 'opacity' in kf and 'transform' not in kf and 'color' not in kf, kf)
    check('로컬 저장 + 동기화 데이터에 포함', pg.evaluate(f"""()=>{{ const L=JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEY)); return Object.keys(L.calNotes['{day}'].m).length===2&&Object.keys(backupData(true).calNotes['{day}'].m).length===2; }}"""))
    # 보스 일정
    pg.click('[data-calboss]'); pg.wait_for_timeout(100)
    o=pg.evaluate("""()=>{ const m=document.querySelector('#calBossModal'); return {h:m.querySelector('h3').textContent, s:m.querySelector('.calbsub').textContent, n:[...m.querySelectorAll('.calbc span')].map(e=>e.textContent), av:m.querySelectorAll('.calbc .avatar').length}; }""")
    check('모달 제목·부제·캐릭터 전체(초상화+닉네임)', o['h']=='보스 일정 추가' and o['s']=='보스 일정 캐릭터를 추가하세요.' and o['n']==['트딕이','부캐냥'] and o['av']==2, o)
    pg.locator('#calBossModal .modal').screenshot(path=os.path.join(SD,'boss_modal_chars.png'))
    pg.click('[data-calbc="c0"]'); pg.wait_for_timeout(100)
    o=pg.evaluate("[...document.querySelectorAll('#calBossModal .calbi')].map(e=>e.dataset.calbs+':'+e.querySelector('.calsp').textContent)")
    check('보스 목록: 스케줄러 저장분·몇인, 1인 제외', o==['lucid:2인','seren:3인'], o)
    pg.locator('#calBossModal .modal').screenshot(path=os.path.join(SD,'boss_modal_list.png'))
    pg.click('[data-calbc="c1"]'); check('1인뿐인 캐릭터 → 빈 안내', pg.locator('#calBossModal .calbi').count()==0 and pg.locator('#calBossModal .calbe').count()==1)
    pg.click('[data-calbc="c0"]'); pg.click('[data-calbs="lucid"]'); pg.wait_for_timeout(100)
    o=pg.evaluate("""()=>{ const m=document.querySelector('#calBossModal'); return {h:m.querySelector('h3').textContent, s:m.querySelector('.calbsub').textContent, ic:!!m.querySelector('.calbsub .dbadge.db-hard'), hs:m.querySelectorAll('.calbh option').length, ms:[...m.querySelectorAll('.calbmi option')].map(o=>o.textContent).join(',')}; }""")
    check('보스 고르면 부제 = 닉네임, 보스 (난이도 아이콘)', o['h']=='보스 일정 추가' and o['s']=='트딕이, 루시드 ()' and o['ic'], o)
    check('시 0~23 · 분 00~55 5분 단위', o['hs']==24 and o['ms']=='00,05,10,15,20,25,30,35,40,45,50,55', o)
    pg.select_option('.calbh','22'); pg.select_option('.calbmi','30')
    pg.locator('#calBossModal .modal').screenshot(path=os.path.join(SD,'boss_modal_time.png'))
    pg.click('[data-calbsave]'); pg.wait_for_timeout(150)
    check('저장 → 모달 유지, 그 캐릭터 보스 목록으로', pg.locator('#calBossModal').count()==1 and pg.locator('#calBossModal .calbi').count()==2 and pg.locator('#calBossModal .calbc.on').get_attribute('data-calbc')=='c0')
    pg.click('[data-calbs="seren"]'); pg.select_option('.calbh','9'); pg.click('[data-calbsave]'); pg.wait_for_timeout(100)
    pg.locator('#calBossModal .calbab [data-calbx]').count()==0 or None
    pg.click('[data-calbs="seren"]'); pg.click('#calBossModal .calbab [data-calbx]'); pg.wait_for_timeout(100)
    check('취소 → 모달 닫힘', pg.locator('#calBossModal').count()==0)
    o=pg.evaluate("[...document.querySelectorAll('#calDet .calsi')].map(e=>e.querySelector('.calst').textContent+' '+e.querySelector('.calsn').textContent.replace(/\\s+/g,' ').trim())")
    check('상세에 보스 일정(시간순)', o==['09:00 트딕이 · 선택받은 세렌 3인','22:30 트딕이 · 루시드 2인'], o)
    bb=pg.evaluate(f"""()=>{{ const g=document.querySelector('{cell} .calbg'); return {{t:[...g.children].map(e=>e.className+':'+e.textContent), c:getComputedStyle(g.querySelector('.calbb')).color, a:getComputedStyle(g.querySelector('.calbb')).animationName}}; }}""")
    check('칸 배지 순서 메모 → 보스 일정(선홍·깜빡임)', bb['t']==['calbm:·메모 2개','calbb:·보스 일정 2개'] and bb['c']=='rgb(255, 59, 107)' and bb['a']=='calblink', bb)
    pg.locator('.calgrid').screenshot(path=os.path.join(SD,'cal_badges.png'))
    pg.click(f'#calDet .calsi [data-calndel]'); check('일정 삭제', pg.locator('#calDet .calsi').count()==1)
    r=pg.evaluate("""()=>{ const L={calNotes:{'2026-11-05':{m:{x:{t:'A',at:1}}}}}, R={calNotes:{'2026-11-05':{m:{y:{t:'B',at:2}},b:{z:{cid:'c0',boss:'lucid',d:'hard',p:2,h:1,mi:0}}}}}, ctx={base:true,prefer:'l',conf:[]};
      const o=gdMerge({},L,R,ctx); return {m:Object.keys(o.calNotes['2026-11-05'].m).sort().join(), b:Object.keys(o.calNotes['2026-11-05'].b||{}).join(), conf:ctx.conf.length}; }""")
    check('다른 PC 동기화 병합: 양쪽 메모·일정 합쳐짐, 충돌 없음', r=={'m':'x,y','b':'z','conf':0}, r)
    pg.reload(); pg.wait_for_timeout(800); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(200); pg.locator(cell).click(); pg.wait_for_timeout(150)
    check('새로고침 뒤 유지', pg.locator('#calDet .calmi').count()==2 and pg.locator('#calDet .calsi').count()==1)
    pg.evaluate("document.documentElement.dataset.theme='light'"); pg.wait_for_timeout(200)
    check('라이트 테마 배지 색', pg.evaluate(f"getComputedStyle(document.querySelector('{cell} .calbm')).color")=='rgb(15, 157, 88)')
    ff=pg.evaluate("getComputedStyle(document.querySelector('#calDet .calnbt')).fontFamily"); check('Paperlogy 글꼴', 'Paperlogy' in ff, ff)
    pg.locator('.calcard').screenshot(path=os.path.join(SD,'light.png'))
    pg.click('[data-calboss]'); ff=pg.evaluate("getComputedStyle(document.querySelector('#calBossModal h3')).fontFamily"); check('모달 Paperlogy', 'Paperlogy' in ff, ff)
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
