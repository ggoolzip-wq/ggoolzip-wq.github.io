# 에테르넬 장비 조각 정보 칩 · 드롭 칩 툴팁(마우스·터치) · 반지 상자 리렌4/컨티4 확률 (2026-10-10)
import os, sys, json, subprocess, time, urllib.request, shutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR')
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d) if d!='' else ''))
    if not c: fails.append(n)
def shot(pg,name,clip=None):
    path=os.path.join(OUT,name); pg.screenshot(path=path,clip=clip)
    if SHOTDIR: shutil.copy(path,os.path.join(SHOTDIR,name))
PORT=8796
srv=subprocess.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
URL=f'http://localhost:{PORT}/index.html'
def B(d): return {'enabled':True,'diff':d,'party':1}
c1={'id':'c1','name':'단풍용사','level':290,'job':'히어로','world':'스카니아','ocid':'','accId':'','isMain':True,'image':'',
    'bosses':{'kalos':B('normal'),'adversary':B('extreme'),'kaling':B('hard'),'star':B('hard'),'limbo':B('normal'),'bellona':B('normal'),'jupiter':B('hard'),'lotus':B('hard')},
    'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
PRESET={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[c1],'settings':{'accounts':[],'autoSync':False}}
ROW=lambda s: f'.boss:has([data-party="{s}"])'
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for touch in (False,True):
      ctx=b.new_context(viewport={'width':1280,'height':900} if not touch else {'width':390,'height':844},locale='ko-KR',has_touch=touch,is_mobile=touch)
      ctx.route('https://accounts.google.com/**',lambda r:r.abort()); ctx.route('https://open.api.nexon.com/**',lambda r:r.abort())
      ctx.route('**/feed.json*',lambda r:r.fulfill(status=404,body=''))
      pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
      pg.goto(URL); pg.evaluate("p=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(p))}",PRESET); pg.reload()
      pg.wait_for_selector('[data-party="kaling"]'); pg.wait_for_timeout(300)
      st=lambda: pg.evaluate("JSON.parse(localStorage.getItem('mapleBossTracker.v1')).characters[0]")
      tip=lambda: pg.evaluate("(()=>{const t=document.getElementById('mbtTip');return t&&t.classList.contains('show')?t.textContent:''})()")
      if not touch:
        ex=pg.evaluate("""(()=>{const f=(id,d)=>{const e=eternalFor(findBoss(id),d);return e?[e.k,e.n]:null};
          return [f('kalos','easy'),f('kalos','normal'),f('kalos','chaos'),f('kalos','extreme'),f('adversary','easy'),f('adversary','normal'),f('adversary','hard'),f('adversary','extreme'),
            f('kaling','easy'),f('kaling','normal'),f('kaling','hard'),f('kaling','extreme'),f('star','normal'),f('star','hard'),
            f('bellona','easy'),f('bellona','normal'),f('bellona','hard'),f('limbo','hard'),f('baldrix','normal'),f('jupiter','hard'),f('seren','extreme')]})()""")
        exp=[None,['e_kalos_f',3],['e_kalos',5],['e_kalos',14],None,['e_adv_f',4],['e_adv',6],['e_adv',16],['e_kaling_f',1],['e_kaling_f',5],['e_kaling',7],['e_kaling',18],
             ['e_star_f',6],['e_star',18],None,['e_bellona',1],['e_bellona',2],['e_limbo',2],['e_baldrix',1],['e_jupiter',2],None]
        check('eternal amounts per boss/difficulty (namu table)', ex==exp, ex)
        check('every eternal item has its own icon', pg.evaluate("Object.keys(ITEMS).filter(k=>k.startsWith('e_')).every(k=>!!ITEM_ICONS[k])"))
        d=pg.evaluate(f"""(()=>{{const r=document.querySelector('{ROW("kaling")} .drops');const ch=[...r.children];
          return {{cls:ch.slice(0,2).map(e=>e.className),badge:ch[1].querySelector('.ecnt')?.textContent,img:!!ch[1].querySelector('img'),click:ch[1].hasAttribute('data-drop'),
            bl:ch[1].querySelector('.ecnt').getBoundingClientRect().left-ch[1].querySelector('img').getBoundingClientRect().left}}}})()""")
        check('kaling hard: erda chip then eternal chip (badge 7, icon, not clickable, badge top-left)', 'erda' in d['cls'][0] and 'eter' in d['cls'][1] and d['badge']=='7' and d['img'] and not d['click'] and d['bl']<=2, d)
        before=json.dumps(st().get('drops'))
        pg.click(f'{ROW("kaling")} .drop.eter'); pg.wait_for_timeout(150)
        check('clicking eternal chip records nothing', json.dumps(st().get('drops'))==before and not st()['weekly'].get('kaling'))
        pg.hover(f'{ROW("kaling")} .drop.eter'); pg.wait_for_timeout(150); t=tip()
        check('eternal tooltip: name, count, parts', '뒤엉킨 흉수의 고리 7개' in t and '모자·상의·하의·어깨장식' in t, t)
        r=pg.locator(f'{ROW("kaling")} .drop.eter').bounding_box(); shot(pg,'tip_eternal.png',{'x':max(0,r['x']-200),'y':max(0,r['y']-130),'width':560,'height':190})
        pg.hover(f'{ROW("kalos")} .drop.eter'); pg.wait_for_timeout(150); t=tip()
        check('normal kalos tooltip: 조각 3개 + 2→1 exchange', '남겨진 칼로스의 의지 조각 3개' in t and '2개 → 남겨진 칼로스의 의지 1개' in t, t)
        pg.hover(f'{ROW("limbo")} .drop.eter'); pg.wait_for_timeout(150); t=tip()
        check('limbo tooltip: 장갑·신발·망토, 개인 보상', '왜곡된 욕망의 결정 1개' in t and '장갑·신발·망토' in t and '개인 보상' in t, t)
        pg.hover(f'{ROW("kaling")} [data-drop="kaling|chaosbox"]'); pg.wait_for_timeout(150); t=tip()
        check('chaos box tooltip lists 7 accessories', all(x in t for x in ['루즈 컨트롤 머신 마크','마력이 깃든 안대','몽환의 벨트','저주받은 마도서','거대한 공포','커맨더 포스 이어링','고통의 근원']), t)
        r=pg.locator(f'{ROW("kaling")} [data-drop="kaling|chaosbox"]').bounding_box(); shot(pg,'tip_chaosbox.png',{'x':max(0,r['x']-150),'y':max(0,r['y']-200),'width':520,'height':250})
        firsts={}
        for k,row in [('r_life','kaling'),('r_white','bellona'),('r_red','lotus')]:
            sel=f'{ROW(row)} [data-drop="{row}|{k}"]'
            if pg.locator(sel).count()==0: continue
            pg.hover(sel); pg.wait_for_timeout(150); firsts[k]=tip().split('\n')[0]
            if k=='r_life':
                t=tip(); check('life box tooltip: level range, rings, 연마석', '3~4레벨' in t and '리스트레인트 링' in t and '생명의 연마석' in t and '얼티메이덤' not in t, t)
                r=pg.locator(sel).bounding_box(); shot(pg,'tip_ringbox_life.png',{'x':max(0,r['x']-220),'y':max(0,r['y']-150),'width':600,'height':200})
        check('ring box first lines', firsts.get('r_life')=='리렌4 10.16% · 컨티4 10.16%' and firsts.get('r_white')=='리렌4 5.00% · 컨티4 5.00%' and firsts.get('r_red')=='리렌4 0.69% · 컨티4 0.69%', firsts)
        r4=pg.evaluate("Object.fromEntries(['r_green','r_red','r_black','r_white','r_life'].map(k=>[k,fmtPct(ring4(k).r4)+'/'+fmtPct(ring4(k).c4)]))")
        check('r4/c4 all boxes (green none, black 2.50%)', r4=={'r_green':'없음/없음','r_red':'0.69%/0.69%','r_black':'2.50%/2.50%','r_white':'5.00%/5.00%','r_life':'10.16%/10.16%'}, r4)
        pg.click(f'{ROW("kaling")} [data-drop="kaling|chaosbox"]'); pg.wait_for_timeout(150)
        check('click on chaos box still records +1', st()['drops'].get('kaling|chaosbox')==1, st()['drops'])
        pg.click(f'{ROW("kaling")} [data-drop="kaling|r_life"]'); pg.wait_for_timeout(150)
        check('click on ring box still opens result modal', pg.is_visible('#ringModal')); pg.click('#ringModal [data-ring="r4"]'); pg.wait_for_timeout(200)
        check('r4 result recorded', st()['drops'].get('kaling|r_life')==1 and st().get('dropOut',{}).get('kaling|r_life')==['r4'], (st()['drops'],st().get('dropOut')))
        pg.click(f'{ROW("kaling")} [data-drop="kaling|chaosbox"]',button='right'); pg.wait_for_timeout(150)
        check('mouse right-click still −1', not st()['drops'].get('kaling|chaosbox'))
        check('no native title on drop chips (custom tooltip instead)', pg.locator('.drop[title]').count()==0)
      else:
        pg.locator(f'{ROW("kaling")} .drop.eter').scroll_into_view_if_needed()
        pg.tap(f'{ROW("kaling")} .drop.eter'); pg.wait_for_timeout(200); t=tip()
        check('touch: tap eternal chip shows tooltip', '뒤엉킨 흉수의 고리 7개' in t, t)
        r=pg.locator(f'{ROW("kaling")} .drop.eter').bounding_box(); shot(pg,'tip_touch_eternal.png',{'x':0,'y':max(0,r['y']-140),'width':390,'height':200})
        pg.tap(f'{ROW("kaling")} [data-drop="kaling|chaosbox"]'); pg.wait_for_timeout(200); t=tip()
        check('touch: tap chaos box shows tooltip AND records +1', '고통의 근원' in t and st()['drops'].get('kaling|chaosbox')==1, (t[:40],st()['drops']))
        pg.wait_for_timeout(3300); check('touch tooltip auto-hides after ~3s', tip()=='')
      ctx.close()
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
