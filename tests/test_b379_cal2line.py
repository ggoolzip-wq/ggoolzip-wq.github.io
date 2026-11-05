# test_b379 (t415u): 묶음 일정 보스가 많으면 상세 = 1줄 시간+보스+삭제 / 2줄 캐릭터. 카드·배지는 1개(분리 금지).
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _tutil
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.environ.get('MBT_SHOTDIR') or os.path.join(ROOT,'tests','out'); os.makedirs(OUT,exist_ok=True)
fails=[]; errs=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:500] if d!='' else ''))
    if not c: fails.append(n)
from playwright.sync_api import sync_playwright
site=tempfile.mkdtemp()
for f in ['index.html','prices.json']: shutil.copy(os.path.join(ROOT,f),site)
for d in ['data','ocr']: shutil.copytree(os.path.join(ROOT,d),os.path.join(site,d))
PORT=_tutil.free_port(); srv=_tutil.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=site,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
SD=os.environ.get('B379_SHOTDIR') or OUT
SETUP="""()=>{ const mk=(id,n)=>({id,name:n,level:285,job:'',world:'스카니아',ocid:'',accId:'',image:'',bosses:{},weekly:{},monthly:{},auto:{}});
  const B={lucid:{enabled:true,party:2,diff:'hard'},seren:{enabled:true,party:2,diff:'hard'},lotus:{enabled:true,party:2,diff:'extreme'},damien:{enabled:true,party:2,diff:'hard'},will:{enabled:true,party:2,diff:'hard'}};
  const c0=mk('c0','트딕이'), c1=mk('c1','부캐냥'), c2=mk('c2','메보기');
  for(const c of [c0,c1,c2]) c.bosses=JSON.parse(JSON.stringify(B));
  S.characters=[c0,c1,c2]; S.calNotes={}; S.activeId='c0'; save(); render(); }"""
try:
  with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None,args=['--no-sandbox'])
    # 좁은 상세 폭에서 찌부됨이 드러나도록 뷰포트 조금 작게
    pg=b.new_page(viewport={'width':1100,'height':950},locale='ko-KR',color_scheme='dark',timezone_id='Asia/Seoul',device_scale_factor=2); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://open.api.nexon.com/**',lambda r:r.abort())
    pg.goto(f'http://127.0.0.1:{PORT}/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(800)
    pg.evaluate(SETUP); pg.locator('#tabs [data-tab=cal]').click(); pg.wait_for_timeout(200)
    day=pg.evaluate("dayId(Date.now())")
    pg.evaluate(f"""()=>{{
      const day='{day}';
      S.calNotes[day]={{b:{{
        g:{{cids:['c0','c1','c2'],ns:['트딕이','부캐냥','메보기'],slot:'lucid',boss:'lucid',d:'hard',p:2,
          bs:[{{slot:'lucid',boss:'lucid',d:'hard',p:2}},{{slot:'seren',boss:'seren',d:'hard',p:2}},{{slot:'lotus',boss:'lotus',d:'extreme',p:2}},{{slot:'damien',boss:'damien',d:'hard',p:2}},{{slot:'will',boss:'will',d:'hard',p:2}}],
          h:21,mi:30,at:1}},
        s:{{cid:'c0',n:'트딕이',slot:'lotus',boss:'lotus',d:'extreme',p:2,h:9,mi:0,at:2}}
      }}}};
      save(); calSel=day; renderCal();
    }}""")
    pg.wait_for_timeout(400)
    info=pg.evaluate("""()=>{
      const rows=[...document.querySelectorAll('#calDet .calsi')];
      const m=rows.find(e=>e.classList.contains('calsim'));
      const s=rows.find(e=>!e.classList.contains('calsim'));
      const R=e=>e.getBoundingClientRect();
      const cs=m&&m.querySelector('.calsc'), bs=m&&m.querySelector('.calsbs'), st=m&&m.querySelector('.calst'), del=m&&m.querySelector('.calndel');
      const csS=cs&&getComputedStyle(cs);
      return {
        n:rows.length, nSim:rows.filter(e=>e.classList.contains('calsim')).length,
        bosses:m?[...m.querySelectorAll('.calsb .calsn')].map(x=>x.textContent.replace(/\\s+/g,' ').trim()):null,
        chars:m?[...m.querySelectorAll('.calscc>span')].map(x=>x.textContent):null,
        badge:document.querySelector(`[data-calday="${document.querySelector('#calDet .caldh b')?'' : ''}"]`) ? null : null,
        lay: m?{
          rowH:R(m).height, stB:R(st).bottom, bsB:R(bs).bottom, delT:R(del).top, delB:R(del).bottom,
          csT:R(cs).top, csL:R(cs).left, stL:R(st).left, bsL:R(bs).left, stT:R(st).top,
          display:getComputedStyle(m).display, area:csS.gridArea.split(' ')[0],
          delArea:getComputedStyle(del).gridArea.split(' ')[0], bossesArea:getComputedStyle(bs).gridArea.split(' ')[0]
        }:null,
        single:s?{chars:[...s.querySelectorAll('.calscc>span')].map(x=>x.textContent), h:R(s).height}:null,
        bb: document.querySelector('#view .calc.on .calbb, #view .calc.sel .calbb, [data-calday].on .calbb')?.textContent
          || [...document.querySelectorAll('.calbb')].map(e=>e.textContent)
      };
    }""")
    # badge via day attribute
    badge=pg.evaluate(f"document.querySelector('[data-calday=\"{day}\"] .calbb')?.textContent")
    print(info, badge)
    check('묶음 1카드 + 단일 1카드 (분리 안 됨)', info['n']==2 and info['nSim']==1, info)
    check('묶음에 보스 5·캐릭터 3 전부', info['bosses'] and len(info['bosses'])==5 and info['chars']==['트딕이','부캐냥','메보기'], info)
    lay=info['lay']
    check('calsim = grid 2행(캐릭터 area=chars)', lay and lay.get('display')=='grid' and lay.get('area')=='chars', lay)
    check('2줄: 캐릭터 줄이 보스 줄 아래', lay and lay['csT']>=lay['bsB']-1, lay)
    check('삭제는 1줄(시간과 같은 행, 캐릭터 위)', lay and lay['delArea']=='del' and abs(lay['delT']-lay['stT'])<=6 and lay['delB']<=lay['csT']+2, lay)
    check('칸 배지: 일정 2개(묶음1+단일1, 쪼개지지 않음)', badge=='·보스 일정 2개', badge)
    check('단일 일정은 한 줄 유지(캐릭터 1)', info['single'] and info['single']['chars']==['트딕이'] and info['single']['h']<50, info['single'])
    pg.locator('#calDet').screenshot(path=os.path.join(SD,'b379_cal_2line.png'))
    # 더 좁게: 보스도 여러 줄이어도 카드는 1개, 캐릭터는 그 아래
    pg.set_viewport_size({'width':720,'height':950}); pg.wait_for_timeout(300)
    narrow=pg.evaluate("""()=>{
      const m=document.querySelector('#calDet .calsim'); if(!m) return null; const R=e=>e.getBoundingClientRect();
      const cs=m.querySelector('.calsc'), bs=m.querySelector('.calsbs');
      return {n:document.querySelectorAll('#calDet .calsi').length, nSim:document.querySelectorAll('#calDet .calsim').length,
        csT:R(cs).top, bsB:R(bs).bottom, bsH:R(bs).height, rowH:R(m).height};
    }""")
    print('narrow', narrow)
    check('좁아도 묶음 카드 1개 + 캐릭터는 보스 아래', narrow and narrow['n']==2 and narrow['nSim']==1 and narrow['csT']>=narrow['bsB']-1, narrow)
    pg.locator('#calDet').screenshot(path=os.path.join(SD,'b379_cal_2line_narrow.png'))
    check('페이지 오류 없음', not errs, errs)
    b.close()
finally:
  srv.terminate()
print('RESULT','FAIL' if fails else 'OK',len(fails)); sys.exit(1 if fails else 0)
