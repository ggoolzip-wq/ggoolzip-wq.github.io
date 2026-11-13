"""b419: 벨로나 보상 맵 금빛 나무 배경 인식. 문턱 .78, 다른 맵·듄켈 전투 오탐 없음. 듄켈 배경은 미적용."""
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _tutil
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX418 = os.path.join(ROOT, 'tests', 'fixtures', 'b418')
FX328 = os.path.join(ROOT, 'tests', 'fixtures', 'b328')
FX300 = os.path.join(ROOT, 'tests', 'fixtures', 'b300')
fails, errs = [], []

def check(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' — ' + str(d)[:500]) if d != '' else ''))
    if not c:
        fails.append(n)

def u(path):
    return 'data:image/jpeg;base64,' + base64.b64encode(open(path, 'rb').read()).decode()

def upng(path):
    return 'data:image/png;base64,' + base64.b64encode(open(path, 'rb').read()).decode()

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

JS = r'''async ([src,k]) => {
  ARX.cfg.boxWorker = false;
  const im = new Image(); im.src = src; await im.decode();
  const scene = await arSceneScore(im, k);
  const box = await arBoxScore(im, k);
  return {scene:+(+scene).toFixed(4), box:+(+box).toFixed(4),
          sThr:(AR_SCENE[k]&&AR_SCENE[k].thr)||0, bThr:AR_BOX[k]?AR_BOX[k].thr:0,
          hasDunk:!!AR_SCENE.dunkel};
}'''

try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',
                              args=['--no-sandbox'])
        pg = b.new_page(viewport={'width':1400,'height':900}, locale='ko-KR')
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html')
        pg.wait_for_timeout(800)
        has = pg.evaluate("()=>({keys:Object.keys(AR_SCENE||{}), thr:AR_SCENE.bellona&&AR_SCENE.bellona.thr, dunk:!!(AR_SCENE||{}).dunkel})")
        print('SCENE', has)
        check('벨로나 나무 템플릿이 있고 문턱은 .78', has['keys']==['bellona'] and abs(has['thr']-0.78)<1e-9 and not has['dunk'], has)

        def sc(path, k, ispng=False):
            src = upng(path) if ispng or path.endswith('.png') else u(path)
            r = pg.evaluate(JS, [src, k])
            print('SC', os.path.basename(path), k, r)
            return r

        v3 = [sc(os.path.join(FX418, n+'.jpg'), 'bellona') for n in ['v3_t00','v3_t10','v3_t20']]
        check('v3 초반(가림) 나무 ≥.78', all(x['scene']>=0.78 for x in v3), v3)
        check('v3 초반 상자 공식은 문턱 미달(문턱 안 낮춤)', all(x['box']<0.75 for x in v3), v3)

        v07 = sc(os.path.join(FX300, 'v07_0120.jpg'), 'bellona')
        check('벨로나 보상 기준 화면 나무 ≥.78', v07['scene']>=0.78, v07)

        v4 = sc(os.path.join(FX418, 'v4_t00.jpg'), 'bellona')
        v4b = sc(os.path.join(FX418, 'v4_t40.jpg'), 'bellona')
        check('스우 영상4는 벨로나 나무 문턱 미만', v4['scene']<0.78 and v4b['scene']<0.78, [v4,v4b])

        fight = sc(os.path.join(FX328, 'v4_fight.jpg'), 'bellona')
        dunkr = sc(os.path.join(FX328, 'v5_dunkel.jpg'), 'bellona')
        check('듄켈 전투·보상 화면은 벨로나 나무 문턱 미만', fight['scene']<0.78 and dunkr['scene']<0.78, [fight,dunkr])

        # dunkel scene not applied
        dsf = pg.evaluate("async src=>{ const im=new Image(); im.src=src; await im.decode(); return typeof arSceneScore==='function'?await arSceneScore(im,'dunkel'):0; }", u(os.path.join(FX328,'v5_dunkel.jpg')))
        check('듄켈 배경 템플릿은 없음(미적용, 점수 0)', dsf==0, dsf)

        # box official still 0.75; dunkel combat box still below (regression)
        dfight = sc(os.path.join(FX328, 'v4_fight.jpg'), 'dunkel')
        check('듄켈 전투 상자 공식은 문턱 미만(기존)', dfight['box']<0.75, dfight)
        drew = sc(os.path.join(FX328, 'v5_dunkel.jpg'), 'dunkel')
        check('듄켈 보상 상자 공식은 문턱 이상(기존)', drew['box']>=0.75, drew)
        b.close()
finally:
    srv.terminate()
    shutil.rmtree(site, ignore_errors=True)
if errs:
    print('PAGE ERRORS', errs); fails.append('pageerror')
if fails:
    print('FAILED', fails); sys.exit(1)
print('PASS b419')
