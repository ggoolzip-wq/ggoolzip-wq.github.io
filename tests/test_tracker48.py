import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8848=_tutil.free_port()
# b63: 캐릭터 추가 모달 — 키별 '등록 완료 · N캐릭 등록 중' + 헤더 '(총 N캐릭 등록 중)', 초록, 한 줄, 수동(키 없음) 제외, 라이브 갱신
import os, sys, json, time, subprocess, shutil
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.environ.get('MBT_OUT') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
SHOTDIR=os.environ.get('MBT_SHOTDIR') or '/workspace/maple-boss-tracker'
os.makedirs(SHOTDIR, exist_ok=True)
PORT=_P8848
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:400] if d!='' else ''))
    if not c: fails.append(n)
def ch(i, acc, name=None):
    return {'id':f'c{i}','name':name or f'캐릭{i}','level':280+i,'job':'히어로','world':'스카니아','ocid':f'o{i}','accId':acc,'isMain':i==0,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
chars=[ch(0,'a1','본캐1'),ch(1,'a1','본캐2'),ch(2,'a1','본캐3'),
       ch(3,'a2','부캐1'),ch(4,'a2','부캐2'),
       {'id':'cm','name':'수동캐릭','level':200,'job':'초보자','world':'스카니아','ocid':'','accId':'','isMain':False,'image':'','bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}]
ST={'version':5,'theme':'dark','activeId':'c0','characters':chars,'history':[],'monthHistory':[],'worldOrder':[],
    'settings':{'accounts':[
      {'id':'a1','label':'본계정','key':'live_MAIN_xxx','status':{'ok':True},'bk':'live_MAIN_BK','bkLabel':'본계정 예비'},
      {'id':'a2','label':'부계정','key':'live_SUB_xxx','status':{'ok':True}},
      {'id':'a3','label':'예비계정','key':'live_EMPTY_xxx','status':{'ok':True}},
    ],'lastSync':int(time.time()*1000)}}
srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(0.8)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1600,'height':1000},locale='ko-KR'); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"items":[]}'))
    pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST)
    pg.reload(); pg.wait_for_timeout(500)
    pg.click('#addCharBtn'); pg.wait_for_selector('#importModal.show'); pg.wait_for_timeout(300)
    pg.evaluate("accounts().forEach(a=>a.status={ok:true}); renderAccList()")
    ht=pg.inner_text('#accKeyTotal')
    check("헤더 '(총 5캐릭 등록 중)' (수동 1명 제외)", ht.strip()=='(총 5캐릭 등록 중)', ht)
    gre=pg.evaluate("getComputedStyle(document.querySelector('#accKeyTotal')).color")
    check('헤더 초록(#3ccf6e)', gre=='rgb(60, 207, 110)', gre)
    rows=pg.eval_on_selector_all('#accList .accrow .regok',"e=>e.map(x=>x.textContent.replace(/\\s+/g,' ').trim())")
    check('본계정 3캐릭', rows[0]=='✔ 등록 완료 · 3캐릭 등록 중', rows)
    check('부계정 2캐릭', rows[1]=='✔ 등록 완료 · 2캐릭 등록 중', rows)
    check('예비계정 0캐릭 (b216: 0캐릭 문구 없음)', rows[2]=='✔ 등록 완료', rows)
    wrap=pg.evaluate("""()=>{
      const h=document.querySelector('.addsec-h');
      const rs=[...document.querySelectorAll('#accList .accrow .regok, #accList .bkrow .regok')];
      const hr=h.getBoundingClientRect();
      return {hH:hr.height, heights:rs.map(e=>e.getBoundingClientRect().height),
        ok: hr.height<=32 && rs.every(e=>e.getBoundingClientRect().height<=22)};
    }""")
    check('헤더·등록완료 문구 한 줄', wrap['ok'], wrap)
    g2=pg.evaluate("getComputedStyle(document.querySelector('#accList .accrow .regok')).color")
    check('행 등록완료 초록', g2=='rgb(60, 207, 110)', g2)
    pg.evaluate("S.characters=S.characters.filter(c=>c.name!=='본캐3'); save(); render();")
    pg.wait_for_timeout(150)
    rows2=pg.eval_on_selector_all('#accList .accrow .regok',"e=>e.map(x=>x.textContent.replace(/\\s+/g,' ').trim())")
    check('삭제 후 본계정 2 · 총 4', pg.inner_text('#accKeyTotal').strip()=='(총 4캐릭 등록 중)' and rows2[0]=='✔ 등록 완료 · 2캐릭 등록 중', (pg.inner_text('#accKeyTotal'), rows2))
    pg.evaluate("S.characters.push({id:'c9',name:'본캐3',level:283,job:'히어로',world:'스카니아',ocid:'o9',accId:'a1',isMain:false,image:'',bosses:{},weekly:{},monthly:{},auto:{},drops:{},sync:{}}); save(); render();")
    pg.wait_for_timeout(150)
    check('추가 후 총 5·본계정 3', pg.inner_text('#accKeyTotal').strip()=='(총 5캐릭 등록 중)' and '등록 완료 · 3캐릭 등록 중' in pg.locator('#accList .accrow').nth(0).inner_text())
    gl=pg.evaluate("getComputedStyle(document.querySelector('#accKeyTotal')).color")
    check('초록 가독 (b67: 다크 전용)', gl=='rgb(60, 207, 110)' and pg.evaluate("document.documentElement.dataset.theme")=='dark', gl)
    pth=os.path.join(OUT,'oct12c_keycount.png')
    pg.locator('#importModal .modal').screenshot(path=pth)
    dest=os.path.join(SHOTDIR,'oct12c_keycount.png'); shutil.copy(pth, dest)
    print('SHOT', dest)
    check('no page errors', not errs, errs[:3])
    b.close()
finally:
    srv.terminate()
print('FAILS:',fails); sys.exit(1 if fails else 0)
