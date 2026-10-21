import _tutil  # zosu-testfix: 빈 포트·서버 정리(atexit/PDEATHSIG)·bind 실패 감지·운영 Worker 차단 (tests/_tutil.py)
_P8898=_tutil.free_port()
# b99: 길드 현황 — '길드' 제목 아이콘 = 길드의 축복 아이콘, 길드 이름 앞 = 그 길드의 길드 마크 (guild/id → guild/basic: guild_mark_custom(base64) 우선, 없으면 guild_mark(URL), 둘 다 없으면 기본 아이콘)
import os, sys, json, subprocess, time, urllib.request, base64, io
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _legacy
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
PORT=_P8898
srv=_tutil.Popen(['python3','-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
for _ in range(50):
    try: urllib.request.urlopen(f'http://127.0.0.1:{PORT}/index.html',timeout=1); break
    except Exception: time.sleep(0.1)
from PIL import Image
def png(c):
    im=Image.new('RGBA',(17,17),c); b=io.BytesIO(); im.save(b,'PNG'); return b.getvalue()
CUSTOM=base64.b64encode(png((255,0,0,255))).decode(); MARKPNG=png((0,0,255,255))
def ch(id,name,guild): return {'id':id,'name':name,'level':280,'job':'히어로','world':'스카니아','ocid':'o-'+id,'image':'','accId':'a1','guild':guild,'guildAt':1,'bosses':{},'weekly':{},'monthly':{},'auto':{},'drops':{},'sync':{}}
G=[{'world':'스카니아','name':'커스텀길드'},{'world':'스카니아','name':'기본마크길드'},{'world':'스카니아','name':'마크없는길드'}]
ST={'version':5,'theme':'dark','activeId':'c1','worldOrder':[],'history':[],'monthHistory':[],'characters':[ch('c1','캐릭1','커스텀길드')],
 'settings':{'accounts':[{'id':'a1','label':'본계정','key':_legacy.LEGACY_KEY,'main':True}],'guilds':G,'suroChars':[]}}
calls=[]
def nexon(r):
    u=r.request.url; calls.append(u.split('/maplestory/v1/')[-1].split('?')[0])
    from urllib.parse import urlparse, parse_qs
    q={k:v[0] for k,v in parse_qs(urlparse(u).query).items()}
    J=lambda d: r.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps(d))
    if '/guild/id' in u: return J({'oguild_id':'og-'+q.get('guild_name','')})
    if '/guild/basic' in u:
        gid=q.get('oguild_id','')
        if gid=='og-커스텀길드': return J({'guild_name':'커스텀길드','guild_mark':'https://open.api.nexon.com/static/maplestory/guild/mark/x.png','guild_mark_custom':CUSTOM})
        if gid=='og-기본마크길드': return J({'guild_name':'기본마크길드','guild_mark':'https://open.api.nexon.com/static/maplestory/guild/mark/blue.png','guild_mark_custom':None})
        return J({'guild_name':'마크없는길드','guild_mark':None,'guild_mark_custom':None})
    if '/ranking/guild' in u: return J({'ranking':[{'guild_name':q.get('guild_name'),'world_name':'스카니아','guild_level':30,'guild_master_name':'마스터','guild_point':1234,'ranking':5}]})
    if '/static/' in u: return r.fulfill(status=200,content_type='image/png',body=MARKPNG)
    return J({})
SHOT=os.environ.get('SHOT'); BEFORE=bool(SHOT and 'before' in SHOT)
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':1000},device_scale_factor=2); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/feed.json*',lambda r:r.fulfill(status=200,content_type='application/json',body='{"version":1,"sources":{},"items":{}}'))
    pg.route('https://open.api.nexon.com/**',nexon)
    pg.goto(f'http://localhost:{PORT}/index.html'); pg.evaluate("s=>{localStorage.clear();localStorage.setItem('mapleBossTracker.v1',JSON.stringify(s));localStorage.setItem('mapleBossTracker.loadSyncAt',String(Date.now()))}",ST); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate("tab='guild'; render(); refreshGuild(true)"); pg.wait_for_timeout(2500)
    if SHOT: pg.locator('#guildCard').screenshot(path=SHOT)
    if not BEFORE:
      h=pg.locator('#guildCard h2 img.gbless'); check("title icon = 길드의 축복 image", h.count()==1 and h.get_attribute('src').startswith('data:image'), h.count())
      marks=pg.evaluate("[...document.querySelectorAll('#guildCard .gblk-h')].map(e=>{const i=e.querySelector('.gmark'); return [e.innerText.split('\\n')[0], i?i.tagName:'', i&&i.src?i.src.slice(0,40):(i?i.textContent:'')]})")
      check('custom mark preferred (base64)', marks[0][1]=='IMG' and marks[0][2].startswith('data:image/png;base64,'), marks)
      check('else guild_mark URL', marks[1][1]=='IMG' and marks[1][2].startswith('https://open.api.nexon.com/static'), marks)
      check('neither → neutral icon', marks[2][1]!='IMG' and marks[2][1]!='', marks)
      n=len([c for c in calls if c.startswith('guild/')]); pg.evaluate("refreshGuild(true)"); pg.wait_for_timeout(1500)
      check('mark cached (no extra guild/id·basic calls on refresh)', len([c for c in calls if c.startswith('guild/')])==n, calls)
    check('JS 오류 없음', not errs, errs)
    b.close()
except Exception as e:
    import traceback; traceback.print_exc(); errs.append(str(e))
finally:
    srv.terminate()
print('FAILS:',fails); print('ERRORS:',errs)
sys.exit(1 if fails or errs else 0)
