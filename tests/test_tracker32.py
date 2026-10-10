# b40: 패치 후 % / 갱신완료 HH:MM / 초록 드롭 칩(체크 없음, 크기 그대로) / 검마 정렬순
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8832/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8832','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
live=json.load(open(os.path.join(ROOT,'prices.json'),encoding='utf-8')); live.pop('upcoming',None)
demo=json.loads(json.dumps(live)); demo['upcoming']={'demo':True,'source':{'title':'[데모] 테스트'},'rows':[{'boss':r['boss'],'new':int(r['new']*0.9)} for r in live['rows']]}
def B(d): return {'enabled':True,'diff':d,'party':1}
now=int(time.time()*1000)
def C(i,w,gm,world='스카니아'):
    return {'id':f'c{i}','name':f'캐릭{i:02d}','level':280,'job':'히어로','world':world,'ocid':f'o{i}','accId':'','isMain':i==0,'image':'',
      'bosses':{'limbo':B('hard'),'seren':B('hard'),'blackmage':B('hard')},'weekly':{'limbo':True} if w else {},'monthly':{'blackmage':True} if gm else {},
      'auto':{},'drops':{},'sync':{'ok':True,'at':now,'clear':1,'limit':12}}
chars=[C(i,False,i%3==0) for i in range(11)]
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.route('**/prices.json*',lambda r:r.fulfill(status=200,content_type='application/json',body=json.dumps(demo)))
    pg.goto(URL)
    ST={'version':5,'theme':'dark','activeId':'c1','characters':chars,'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[],'lastSync':now}}
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(900)
    # 3) 갱신완료 HH:MM
    hm=time.strftime('%H:%M',time.localtime(now/1000))
    pg.evaluate("S.settings.accounts=[{id:'a1',name:'x',key:'k'}];S.characters.forEach(c=>c.accId='a1');render()"); pg.wait_for_timeout(150)
    check('갱신완료 + time', f'갱신완료 {hm}' in pg.inner_text('#view'), hm)
    # 1) %
    pg.click('[data-pctab="after"]'); pg.wait_for_timeout(150)
    ds=pg.eval_on_selector_all('.pa-d','e=>e.map(x=>x.textContent)')
    import re
    check('change + (−x.x%) on rows and total', len(ds)>=2 and all(re.search(r'−[\d억만, ]+ \(−\d+\.\d%\)$',d) for d in ds), ds[:3])
    pg.locator('.pricecard').screenshot(path='/workspace/shots/b40_after_pct.png')
    # 4) 초록 칩
    chip='[data-drop="limbo|r_white"], [data-drop^="limbo|"]'
    first=pg.eval_on_selector_all('[data-drop^="limbo|"]','e=>e.map(x=>x.dataset.drop)')[0]
    sz0=pg.evaluate("k=>{const r=document.querySelector(`[data-drop=\"${k}\"]`).getBoundingClientRect();return [r.width,r.height,document.querySelector('.drops').getBoundingClientRect().height]}",first)
    pg.evaluate("k=>{const [b,i]=k.split('|'); const c=activeChar(); (c.drops||(c.drops={}))[k]=1; render()}",first); pg.wait_for_timeout(150)
    st=pg.evaluate("k=>{const e=document.querySelector(`[data-drop=\"${k}\"]`),s=getComputedStyle(e),r=e.getBoundingClientRect();return {got:e.classList.contains('got'),bg:s.backgroundColor,bd:s.borderColor,chk:e.textContent.includes('✓'),sz:[r.width,r.height,document.querySelector('.drops').getBoundingClientRect().height]}}",first)
    check('selected chip: green bg+border, no ✓, size unchanged', st['got'] and 'rgba(63, 185, 111' in st['bg'] and st['bd']=='rgb(63, 185, 111)' and not st['chk'] and st['sz']==sz0, (st,sz0))
    pg.locator('.boss:has([data-drop^="limbo|"])').first.screenshot(path='/workspace/shots/b40_limbo_green.png')
    # 5) 정렬: 아래 왼쪽, 3가지
    btns=pg.eval_on_selector_all('#charFoot .charsort [data-csort]','e=>e.map(x=>x.textContent)')
    check('sort controls in bottom foot with 3 options', btns==['기본순','보스 미완료순','검마 정렬순'] and pg.locator('#worldTabs .charsort').count()==0, btns)
    lb=pg.evaluate("[document.querySelector('#charList').getBoundingClientRect().left,document.querySelector('#charFoot .charsort').getBoundingClientRect().left,document.querySelector('#charFoot').getBoundingClientRect().top>=document.querySelector('#charList').getBoundingClientRect().bottom-1]")
    check('foot left-aligned under list', abs(lb[0]-lb[1])<30 and lb[2], lb)
    pg.click('[data-csort="gm"]'); pg.wait_for_timeout(200)
    ids=pg.eval_on_selector_all('#charList .char[data-id]','e=>e.map(x=>x.dataset.id)')
    exp=[f'c{i}' for i in range(11) if i%3] + [f'c{i}' for i in range(11) if i%3==0]
    check('gm: uncleared first (base order), page 1 = 8', ids==exp[:8], ids)
    pg.mouse.move(5,5); pg.locator(':is(.card,aside):has(> #charList), :is(.card,aside):has(#charFoot)').last.screenshot(path='/workspace/shots/b40_gm_sort.png')
    pg.click('[data-cpage="2"]'); pg.wait_for_timeout(150)
    ids2=pg.eval_on_selector_all('#charList .char[data-id]','e=>e.map(x=>x.dataset.id)')
    dim=pg.eval_on_selector_all('#charList .char.gmdone','e=>e.map(x=>[x.dataset.id,getComputedStyle(x).opacity,x.querySelector(".dov")?.textContent||""])')
    check('gm page 2: cleared dimmed + ★이번 달 검마 완료', ids2==exp[8:] and len(dim)==3 and all(float(o)<.8 and '이번 달 검마 완료' in t for _,o,t in dim), (ids2,dim))
    star=pg.evaluate("getComputedStyle(document.querySelector('.gmdone .dov-star')).color")
    check('★ yellow', star.startswith('rgb(2'), star)
    pg.mouse.move(5,5)
    pg.click('[data-csort="base"]'); pg.wait_for_timeout(150)
    check('base: no gm dim', pg.locator('.gmdone').count()==0)
    pg.reload(); pg.wait_for_timeout(600)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
