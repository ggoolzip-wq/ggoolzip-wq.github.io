# test_b269: '진행중/완료' = 디지털 한글(MrjUnitKo) · 숫자와 높이/아래 끝 맞춤, % = 소수 둘째 자리 내림, X/Y 앞 '이번 주 결정석 진행도',
#   바로 아래 '이번 달 검마 진행도' 게이지(검은 마법사만, 월간) 회색/노랑/분홍/빛나는 빨강, 두 테마, 키 지운 캐릭 제외, 페이지 스크롤 늘지 않음
# MBT_ROOT = 다른 빌드(변경 전 사진용, MBT_NOCHECK=1) · MBT_SHOTDIR = 사진 폴더 · MBT_SHOT = before/after
# MBT_ROOT = 다른 빌드(변경 전 사진용, MBT_NOCHECK=1) · MBT_SHOTDIR = 사진 폴더 · MBT_SHOT = before/after
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SRCR=os.environ.get('MBT_ROOT') or ROOT
NOCHK=os.environ.get('MBT_NOCHECK')=='1'; SD=os.environ.get('MBT_SHOTDIR'); PFX=os.environ.get('MBT_SHOT','after')
fails=[]; errs=[]
def check(n,c,d=''):
    if NOCHK: return
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp(); shutil.copy(os.path.join(SRCR,'index.html'),site); shutil.copy(os.path.join(ROOT,'prices.json'),site); shutil.copytree(os.path.join(ROOT,'data'),os.path.join(site,'data'))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SETUP="""n=>{ const W=BOSSES.filter(b=>b.type==='weekly').slice(0,12);
  S.characters=Array.from({length:n},(_,i)=>({id:'c'+i,name:'zet'+i,level:280,job:'히어로',world:'스카니아',ocid:'',accId:'',isMain:!i,image:'',
    bosses:Object.assign(Object.fromEntries(W.map(b=>[b.id,{enabled:true,diff:b.diffs[0],party:1}])),{blackmage:{enabled:true,diff:'hard',party:1}}),weekly:{},monthly:{},auto:{},drops:{},sync:{}}));
  S.activeId='c0'; save&&save(); render(); return W.map(b=>b.id); }"""
SET="""([ks,k,m])=>{ S.characters.forEach((c,i)=>{ c.weekly={}; ks.slice(0,k[i]).forEach(s=>c.weekly[s]=true); c.monthly={}; if(m[i]) c.monthly.blackmage=S.period.week; }); render();
  const f=g=>g?{cls:g.className,xy:g.querySelector('.rpg-xy').textContent,pc:g.querySelector('.rpg-num .rpg-t').textContent,ing:g.querySelector('.rpg-ing').textContent,
     kfont:getComputedStyle(g.querySelector('.rpg-ing')).fontFamily,col:getComputedStyle(g.querySelector('.rpg-num')).color,flt:getComputedStyle(g.querySelector('.rpg-num')).filter,
     dH:g.querySelector('.rpg-num .rpg-t').getBoundingClientRect().height,dB:g.querySelector('.rpg-num .rpg-t').getBoundingClientRect().bottom,
     kB:g.querySelector('.rpg-ing').getBoundingClientRect().bottom,kH:g.querySelector('.rpg-ing').getBoundingClientRect().height}:null;
  return {w:f(document.querySelector('.revpanel .rp-gauge.rpg-w')),m:f(document.querySelector('.revpanel .rp-gauge.rpg-m')),order:(()=>{const w=document.querySelector('.revpanel .rpg-w');return !!w&&w.nextElementSibling===document.querySelector('.revpanel .rpg-m')})(),
    sh:document.scrollingElement.scrollHeight}; }"""
def shot(pg,name):
    if not SD: return
    os.makedirs(SD,exist_ok=True); pg.mouse.move(5,5); pg.wait_for_timeout(400); pg.locator('.revpanel').first.screenshot(path=os.path.join(SD,f'{PFX}_{name}.png'))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
    ks=pg.evaluate(SETUP,3)
    # 주간 k (캐릭당 12칸, 3캐릭 = 36) · 검마 m (3캐릭)
    for th in ['dark','light']:
      pg.evaluate(f"document.documentElement.dataset.theme='{th}'")
      for k,m,name in [([0,0,0],[0,0,0],'w0_m0of3_gray'),([12,9,0],[1,0,0],'w21_m1of3_yel'),([12,12,6],[1,1,0],'w30_m2of3_pink'),([12,12,12],[1,1,1],'w36_m3of3_red_done')]:
        r=pg.evaluate(SET,[ks,k,m]); pg.evaluate(f"document.documentElement.dataset.theme='{th}'"); shot(pg,f'{th}_{name}')
        if NOCHK: continue
        w,mm=r['w'],r['m']; wd=sum(k); md=sum(m)
        wp='100.00%' if wd==36 else '%.2f%%'%(int(wd*10000/36)/100); mp='100.00%' if md==3 else '%.2f%%'%(int(md*10000/3)/100)
        check(f'[{th}] 주간 {wd}/36 = {wp} · 라벨', w and w['pc']==wp and w['xy']==f'이번 주 결정석 진행도 {wd}/36' and w['ing']==('완료' if wd==36 else '진행중'), w)
        mc={0:'g-gray',1:'g-yel',2:'g-pink',3:'g-mred'}[md]
        check(f'[{th}] 검마 {md}/3 = {mp} {mc} · 라벨', mm and mm['pc']==mp and mm['xy']==f'이번 달 검마 진행도 {md}/3' and mc in mm['cls'] and mm['ing']==('완료' if md==3 else '진행중'), mm)
        check(f'[{th}] 검마 게이지 = 주간 게이지 바로 아래', r['order'])
        for g in (w,mm):
            check(f'[{th}] (b271) 진행중/완료 = 주보 결정석 글씨체(Orbit) · 숫자와 높이(±25%)·아래 끝(±2px)', 'Orbit' in g['kfont'] and abs(g['kH']-g['dH'])<=g['dH']*.25 and abs(g['kB']-g['dB'])<=2, g)
        if md==3: check(f'[{th}] 검마 100% = 빛나는 빨강', 'drop-shadow' in mm['flt'] and mm['col'].startswith('rgb(2'), mm)
    if not NOCHK:
        cl=pg.evaluate("monthGaugeData.toString()"); check('검마 분류식', "pct>=66?'g-pink':pct>=33?'g-yel':'g-gray'" in cl and 'blackmage' in cl)
        pcs=pg.evaluate("[[7,12],[143,144],[2,3],[9999,10000],[1,1],[0,5]].map(([d,t])=>weekGaugePct({done:d,total:t,pct:d/t*100}))")
        check('소수 둘째 자리 내림', pcs==['58.33','99.30','66.66','99.99','100.00','0.00'], pcs)
        # 키 지운 계정 캐릭 제외 (검마도)
        pg.evaluate(SETUP,2); pg.evaluate("()=>{ S.settings.accounts=[{id:'A',name:'a',key:''}]; S.characters[1].accId='A'; render(); }")
        r=pg.evaluate(SET,[ks,[3,12],[0,1]]); check('키 지운 캐릭 제외 → 검마 0/1', r['m'] and r['m']['xy'].endswith(' 0/1'), r['m'])
        # 검마 꺼 둔 캐릭만 있으면 검마 게이지 없음
        pg.evaluate(SETUP,1); pg.evaluate("()=>{ delete S.characters[0].bosses.blackmage; render(); }"); r=pg.evaluate(SET,[ks,[3],[0]]); check('검마 안 켠 캐릭만 → 검마 게이지 없음', r['m'] is None and r['w'], r)
        # 페이지 스크롤 늘지 않음: 검마 게이지가 생겨도 문서 높이 그대로(수익 카드는 옆 열보다 짧음)
        pg.evaluate(SETUP,3); r=pg.evaluate(SET,[ks,[3,3,3],[1,0,0]]); pg.evaluate("()=>{ S.characters.forEach(c=>delete c.bosses.blackmage); }"); r0=pg.evaluate(SET,[ks,[3,3,3],[0,0,0]])
        check('페이지 높이 안 늘어남(검마 게이지 있어도 = 없을 때)', r['m'] and r0['m'] is None and r['sh']<=r0['sh'], [r['sh'],r0['sh']])
    b.close()
finally: srv.terminate()
if NOCHK: print('shots done'); sys.exit(0)
check('페이지 오류 없음', not errs, errs)
print('ALL PASS' if not fails else f'FAILED: {fails}'); sys.exit(1 if fails else 0)
