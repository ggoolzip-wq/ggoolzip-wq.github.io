# b45: 캐릭터 정보 칸 3개(최고 전투력 삭제)가 줄을 고르게 채움 / 목록: 본캐 배지 없음, 이름 전체, 줄 가운데
import os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); URL='http://localhost:8834/index.html'
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
srv=subprocess.Popen([sys.executable,'-m','http.server','8834','--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
chars=[{'id':f'c{i}','name':n,'level':294,'job':'렌','world':'스카니아','ocid':f'o{i}','accId':'','isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}} for i,n in enumerate(['림강혼망','부캐','MapleWarrior1'])]
ST={'version':5,'theme':'dark','activeId':'c0','characters':chars,'history':[],'monthHistory':[],'worldOrder':[],'settings':{'accounts':[]}}
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    for vw in (1920,1600,1280):
      pg=b.new_page(viewport={'width':vw,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
      cp=[]; pg.route('**/api/cp*',lambda r:(cp.append(1),r.abort()))
      pg.goto(URL)
      pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s))}",ST); pg.reload(); pg.wait_for_timeout(800)
      v=pg.inner_text('#view'); check(f'{vw}: no 최고 전투력 / 헥사 환산', '최고 전투력' not in v and '헥사 환산' not in v and pg.locator('.cpstat').count()==0)
      st=pg.evaluate("(()=>{const g=document.querySelector('#view .stats'),G=g.getBoundingClientRect();const k=[...g.children].map(e=>e.getBoundingClientRect());return {n:k.length,w:k.map(r=>Math.round(r.width)),top:k.map(r=>Math.round(r.top)),fill:Math.round(k[k.length-1].right-G.right)}})()")
      check(f'{vw}: 3 info blocks, one row, equal widths, filling the row', st['n']==3 and len(set(st['top']))==1 and max(st['w'])-min(st['w'])<=2 and abs(st['fill'])<=1, st)
      if vw==1600: pg.locator('#view .card').first.screenshot(path='/workspace/shots/b45_info.png')
      r=pg.evaluate("(()=>{const r=document.querySelector('.char[data-id=c0]'),R=r.getBoundingClientRect(),nm=r.querySelector('.nm'),a=r.querySelector('.avatar').getBoundingClientRect(),e=r.querySelector('[data-edit]').getBoundingClientRect();return {badge:r.querySelectorAll('.mainbadge').length,txt:nm.textContent,clip:nm.scrollWidth>nm.clientWidth,gap:[a.left-R.left,R.right-e.right]}})()")
      check(f'{vw}: main row: no orange badge, full name, centered', r['badge']==0 and r['txt']=='림강혼망' and not r['clip'] and abs(r['gap'][0]-r['gap'][1])<=1.5, r)
      if vw==1600: pg.locator('#charList').screenshot(path='/workspace/shots/b45_rows.png')
      lay=pg.evaluate("(()=>{const m=document.querySelector('main').getBoundingClientRect();const cut=[...document.querySelectorAll('.pricecard .pc-nm')].filter(n=>n.scrollWidth>n.clientWidth+0.5).length;return {l:m.left,r:innerWidth-m.right,cut,rcol:document.querySelector('.rcol').getBoundingClientRect().width}})()")
      check(f'{vw}: price rows not cut, page centered', lay['cut']==0 and abs(lay['l']-lay['r'])<=1 and lay['rcol']>=290, lay)
      check(f'{vw}: no /api/cp calls', not cp)
      pg.close()
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
