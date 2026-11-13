"""b420 (t545u): 듄켈 맵 OCR(곳→끗/꽃)·청록 배경, 릴캉혼망 느슨 투표. 전투 오탐 없음. 공식 상자 문턱 .75 유지."""
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _tutil
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX420 = os.path.join(ROOT, 'tests', 'fixtures', 'b420')
FX328 = os.path.join(ROOT, 'tests', 'fixtures', 'b328')
FX300 = os.path.join(ROOT, 'tests', 'fixtures', 'b300')
fails, errs = [], []

def check(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' — ' + str(d)[:500]) if d != '' else ''))
    if not c:
        fails.append(n)

def u(path):
    return 'data:image/jpeg;base64,' + base64.b64encode(open(path, 'rb').read()).decode()

site = tempfile.mkdtemp()
for f in ['index.html', 'prices.json']:
    shutil.copy(os.path.join(ROOT, f), site)
for d in ['data', 'ocr']:
    if os.path.isdir(os.path.join(ROOT, d)):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(site, d),
                        ignore=shutil.ignore_patterns('__pycache__'))
PORT = _tutil.free_port()
srv = _tutil.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'],
                   cwd=site, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

MAPJS = r'''() => {
  const D = t => { ARX.runDiff=null; ARX.tplNoDiff=false; ARX.mapSt=null; const b=arDetectBMap(t); return b?{boss:b.boss,diff:b.diff,kind:b.kind,name:b.name,src:b.src,sc:b.sc}:null; };
  return {
    glue: D('메 가까운 끗 하드'),
    brkt: D('에 가까운 끗 <하드>'),
    flower: D('베 가까운 꽃 하드'),
    wait: D('메 가까운 꽂 앞'),
    exact: D('리멘 끝에 가까운 곳 <하드>'),
    oldt625: D('멘 :메 가까운 곳 <하드>'),
    spaced_only: D('끗 하드'),
    other: D('솔라툼의 유산 <이지>'),
    kalos: D('카로테 마천루 <노멀>'),
    junk: D('8 가까운 본 하느'),
  };
}'''

NAMEJS = r'''() => {
  S.characters = [
    {id:'c0', name:'2터래플'},
    {id:'c1', name:'릴캉혼망'},
    {id:'c2', name:'zetking'},
  ];
  ARX.nHist = ['림감온망','림감온망','림감혼망','림감몬망','림감온망','림감몬망','림감온망','림감혼망'];
  ARX.nLead = [false,false,false,false,false,false,false,false];
  const v = arNameVote2();
  ARX.nHist = ['림감온망','림감온망'];
  ARX.nLead = [false,false];
  const few = arNameVote2();
  return {v, few};
}'''

CYAN = r'''async (src) => {
  const im=new Image(); im.src=src; await im.decode();
  const scene=await arSceneScore(im,'dunkel');
  const box=await arBoxScore(im,'dunkel');
  const tree=await arSceneScore(im,'bellona');
  return {scene:+(+scene).toFixed(4), box:+(+box).toFixed(4), tree:+(+tree).toFixed(4),
          sThr:AR_SCENE.dunkel.thr, mode:AR_SCENE.dunkel.mode};
}'''

try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',
                              args=['--no-sandbox'])
        pg = b.new_page(viewport={'width':1400,'height':900}, locale='ko-KR')
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html')
        pg.wait_for_function('() => typeof arDetectBMap==="function" && typeof arSceneScore==="function"', timeout=30000)

        m = pg.evaluate(MAPJS)
        print('MAP', m)
        def isdunk(x, kind='br', diff='hard'):
            return x and x['boss']=='dunkel' and kind in x['kind'] and (not diff or x.get('diff')==diff)
        check('메 가까운 끗 하드 → 듄켈 하드 보상/전투', isdunk(m['glue']), m['glue'])
        check('에 가까운 끗 <하드> → 듄켈 하드', isdunk(m['brkt']), m['brkt'])
        check('베 가까운 꽃 하드 → 듄켈 하드', isdunk(m['flower']), m['flower'])
        check('메 가까운 꽂 앞 → 듄켈 대기', isdunk(m['wait'], kind='w', diff='') or (m['wait'] and m['wait']['boss']=='dunkel' and 'w' in m['wait']['kind']), m['wait'])
        check('정확한 이름 유지', isdunk(m['exact']), m['exact'])
        check('기존 t625 메가까운곳 유지', isdunk(m['oldt625']), m['oldt625'])
        check('끗 하드 만으로는 맵이 아님', not m['spaced_only'], m['spaced_only'])
        check('벨로나 이지 유지', m['other'] and m['other']['boss']=='bellona' and m['other']['diff']=='easy', m['other'])
        check('칼로스 노멀 유지', m['kalos'] and m['kalos']['boss']=='kalos', m['kalos'])
        check('8 가까운 본 하느 는 거부', not m['junk'], m['junk'])

        nv = pg.evaluate(NAMEJS)
        print('NAME', nv)
        check('릴캉혼망 느슨 읽기 4회 이상 → 확정', nv['v']['cid']=='c1', nv['v'])
        check('느슨 읽기 2회는 아직 미확정', nv['few']['cid']!='c1', nv['few'])

        def sc(path):
            r = pg.evaluate(CYAN, u(path))
            print('SC', os.path.basename(path), r)
            return r

        c = sc(os.path.join(FX420, 'n4_combat.jpg'))
        o = sc(os.path.join(FX420, 'n4_rew_occ.jpg'))
        bx = sc(os.path.join(FX420, 'n4_rew_box.jpg'))
        w = sc(os.path.join(FX420, 'n4_wait.jpg'))
        v5 = sc(os.path.join(FX328, 'v5_dunkel.jpg'))
        v03 = sc(os.path.join(FX300, 'v03_0120.jpg'))
        ft = sc(os.path.join(FX328, 'v4_fight.jpg'))

        check('n4 전투 청록 <.15, 상자 <.75', c['scene']<0.15 and c['box']<0.75, c)
        check('n4 가림 보상 청록 ≥.15, 상자 공식은 문턱 미달', o['scene']>=0.15 and o['box']<0.75, o)
        check('n4 상자 보임 공식 ≥.75, 청록 ≥.15', bx['scene']>=0.15 and bx['box']>=0.75, bx)
        check('n4 대기 청록 <.15', w['scene']<0.15, w)
        check('v5·v03 보상 청록 ≥.15, 상자 ≥.75', v5['scene']>=0.15 and v03['scene']>=0.15 and v5['box']>=0.75 and v03['box']>=0.75, [v5,v03])
        check('기존 전투 픽스처 청록 <.15, 상자 <.75', ft['scene']<0.15 and ft['box']<0.75, ft)
        check('모드 cyan 문턱 .15', v5['mode']=='cyan' and abs(v5['sThr']-0.15)<1e-9, v5)
        check('듄켈 화면에 벨로나 나무는 문턱 미만', o['tree']<0.78 and ft['tree']<0.78, [o,ft])
        b.close()
finally:
    srv.terminate()
    shutil.rmtree(site, ignore_errors=True)
if errs:
    print('PAGE ERRORS', errs); fails.append('pageerror')
if fails:
    print('FAILED', fails); sys.exit(1)
print('PASS b420')
