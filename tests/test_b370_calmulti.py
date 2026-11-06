# test_b370 (t684): 파티 보스 일정 — 여러 캐릭터 선택(공통 보스·난이도·인원만), 클리어 비활성(누가), 묶음 일정 1개·상세 한 줄·배지 1개, b367 단일 호환.
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
SD=os.environ.get('B370_SHOTDIR') or OUT
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{}});
  const c0=mk('c0','트딕이'), c1=mk('c1','부캐냥'), c2=mk('c2','솔로만');
  c0.bosses={lucid:{enabled:true,party:2,diff:'hard'},seren:{enabled:true,party:3,diff:'hard'},lotus:{enabled:true,party:2,diff:'extreme'},star:{enabled:true,party:2,diff:'normal'},will:{enabled:true,party:1,diff:'hard'}};
  c1.bosses={lucid:{enabled:true,party:2,diff:'hard'},seren:{enabled:true,party:2,diff:'hard'},lotus:{enabled:true,party:2,diff:'hard'},star:{enabled:true,party:2,diff:'normal'}};
  c2.bosses={will:{enabled:true,party:1,diff:'hard'}}; S.characters=[c0,c1,c2];
  S.history=[{week:'2026-10-15',perChar:[{id:'c1',name:'부캐냥',bosses:['찬란한 흉성(노말)'],bvals:[1e8]}]}];
  S.activeId='c0'; save(); render(); }"""
LIST="[...document.querySelectorAll('#calBossModal .calbi')].map(e=>e.dataset.calbs+(e.disabled?'X':'')+(e.querySelector('.calbclr')?e.querySelector('.calbclr').textContent:''))"
SD3=os.environ.get('B370B_SHOTDIR') or OUT
BD="""(id)=>{const e=document.querySelector(`[data-calday="${id}"]`),c=getComputedStyle(e);return [c.borderTopColor,c.outlineStyle,c.animationName,e.className]}"""
def cells(pg,theme):
    pg.evaluate(f"""()=>{{ document.documentElement.dataset.theme='{theme}'; S.calNotes=S.calNotes||{{}};
      const t=dayId(Date.now()), ym=t.slice(0,8);
      S.calNotes[ym+'03']={{m:{{a:{{t:'메모',at:1}}}},b:{{}}}};
      S.calNotes[ym+'05']={{m:{{}},b:{{x:{{cids:['c0'],ns:['트딕이'],slot:'lucid',boss:'lucid',d:'hard',p:2,h:20,mi:0,at:1}}}}}};
      S.calNotes[ym+'06']={{m:{{a:{{t:'메모',at:1}}}},b:{{x:{{cids:['c0'],ns:['트딕이'],slot:'lucid',boss:'lucid',d:'hard',p:2,h:20,mi:0,at:1}}}}}};
      calSel=ym+'06'; save(); renderCal(); }}""")
    pg.wait_for_timeout(300)
    ym=pg.evaluate("dayId(Date.now()).slice(0,8)")
    return {k:pg.evaluate(BD,ym+k) for k in ['03','05','06','07']}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1400,'height':1000},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(200)
    day=pg.evaluate("dayId(Date.now())"); pg.locator(f'[data-calday="{day}"]').click(); pg.wait_for_timeout(150)
    check('버튼 이름', pg.locator('[data-calboss]').text_content()=='+파티 보스 일정 추가')
    pg.click('[data-calboss]'); pg.wait_for_timeout(100)
    o=pg.evaluate("({h:document.querySelector('#calBossModal h3').textContent, c:[...document.querySelectorAll('#calBossModal .calbc')].map(e=>e.dataset.calbc)})")
    check('제목 + 2인 이상 보스 없는 캐릭터 숨김', o=={'h':'파티 보스 일정 추가','c':['c0','c1']}, o)
    pg.click('[data-calbc="c0"]'); r0=pg.evaluate(LIST); check('1명: 그 캐릭터 파티 보스 전부', sorted(r0)==['lotus','lucid','seren','star'], r0)
    pg.click('[data-calbc="c1"]'); pg.wait_for_timeout(100)
    on=pg.evaluate("[...document.querySelectorAll('#calBossModal .calbc.on')].map(e=>e.dataset.calbc)")
    r=pg.evaluate(LIST); check('여러 명 선택(토글 .on) → 같은 보스·난이도·인원만 (세렌 인원 다름·스우 난이도 다름 제외)', on==['c0','c1'] and sorted(r)==['lucid','star'], [on,r])
    pg.locator('#calBossModal .modal').screenshot(path=os.path.join(SD,'multi_select.png'))
    r=pg.evaluate("(()=>{ calBM={day:'2026-10-21',cids:['c0','c1']}; calBossRender(); return "+LIST+"; })()")
    check('한 명이라도 그 주 클리어 → 비활성 + 누가', 'starX·이번 주 클리어 완료 (부캐냥)' in r and 'lucid' in r, r)
    pg.evaluate(f"calBM={{day:'{day}',cids:['c0','c1']}}; calBossRender()")
    pg.click('[data-calbc="c1"]'); check('토글 해제', pg.locator('#calBossModal .calbc.on').count()==1); pg.click('[data-calbc="c1"]')
    pg.click('[data-calbs="lucid"]'); pg.wait_for_timeout(100)
    sub=pg.evaluate("document.querySelector('#calBossModal .calbsub').textContent")
    check('부제 = 닉네임1, 닉네임2, 보스 (난이도)', sub=='트딕이, 부캐냥, 루시드 ()' and pg.locator('#calBossModal .calbsub .db-hard').count()==1, sub)
    pg.select_option('.calbh','20'); pg.click('[data-calbsave]'); pg.wait_for_timeout(150)
    check('저장 뒤 선택 유지·모달 유지', pg.locator('#calBossModal .calbc.on').count()==2 and pg.locator('#calBossModal .calbi').count()==2)
    pg.click('#calBossModal .calbcls')
    e=pg.evaluate(f"Object.values(S.calNotes['{day}'].b)")
    check('묶음 일정 1개 저장(cids)', len(e)==1 and e[0]['cids']==['c0','c1'] and e[0]['boss']=='lucid' and e[0]['p']==2, e)
    pg.evaluate(f"""()=>{{ S.calNotes['{day}'].b.old={{cid:'c0',n:'트딕이',slot:'seren',boss:'seren',d:'hard',p:3,h:9,mi:0,at:1}}; save(); renderCal(); }}""")
    rows=pg.evaluate("[...document.querySelectorAll('#calDet .calsi')].map(e=>e.querySelector('.calst').textContent+'|'+e.querySelector('.calsn').textContent.replace(/\\s+/g,' ').trim()+'|'+[...e.querySelectorAll('.calscc>span')].map(x=>x.textContent).join(',')+'|'+e.querySelectorAll('.calscc .avatar').length)")
    check('상세: 묶음 한 줄(시간·보스·인원·캐릭터들) + b367 단일 호환', rows==['09:00|선택받은 세렌 3인|트딕이|1','20:00|루시드 2인|트딕이,부캐냥|2'], rows)
    bd=pg.evaluate(f"document.querySelector('[data-calday=\"{day}\"] .calbb').textContent")
    check('칸 배지: 묶음 = 1개', bd=='·보스 일정 2개', bd)
    pg.wait_for_timeout(600); pg.locator('#calDet').screenshot(path=os.path.join(SD,'grouped_detail.png'))
    pg.click('#calDet .calcls') if pg.locator('#calDet .calcls').count() else None
    for th,B,M in [('dark','rgb(255, 59, 107)','rgb(62, 224, 138)'),('light','rgb(224, 20, 76)','rgb(15, 157, 88)')]:
        r=cells(pg,th)
        check(th+' 과거 보스=일반, 메모만=초록, 없음=기본', r['05'][0] not in (B,M) and r['03'][0]==M and r['07'][0] not in (B,M), r)
        check(th+' 정적(애니메이션 없음) + 선택 칸 outline 유지', all(v[2]=='none' for v in r.values()) and r['06'][1]=='solid' and r['05'][1]!='solid', r)
        tc=pg.evaluate("(()=>{const e=document.querySelector('.calc.today');return getComputedStyle(e).borderTopColor})()")
        check(th+' 오늘 칸 분홍 테두리 유지', tc=='rgb(255, 79, 216)', tc)
        pg.locator('.calgrid').screenshot(path=os.path.join(SD3,'cell_borders.png' if th=='dark' else 'cell_borders_light.png'))
    check('페이지 오류 없음',not errs,errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
