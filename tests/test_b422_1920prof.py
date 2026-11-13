# test_b422 (t551u·t552u): 1920x1080 전용 배율 인식 범위.
# 1366 UI를 키운 기본 비율(n1·n3·n5 포함)은 기본, 실 1920 최적 픽스처(b415)는 최적.
# 다른 해상도(1366·1600·2560) 프로필은 기존과 같음.
import os, sys, json, base64, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _tutil
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX = os.path.join(ROOT, 'tests', 'fixtures', 'b422')
FX415 = os.path.join(ROOT, 'tests', 'fixtures', 'b415')
FX295 = os.path.join(ROOT, 'tests', 'fixtures', 'b295')
fails, errs = [], []

def check(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' — ' + str(d)[:400]) if d != '' else ''))
    if not c:
        fails.append(n)

def u(path, mime=None):
    raw = open(path, 'rb').read()
    if mime is None:
        mime = 'image/png' if path.endswith('.png') else 'image/jpeg'
    return f'data:{mime};base64,' + base64.b64encode(raw).decode()

DET = r'''async (spec) => {
  const im = new Image(); im.src = spec.u; await im.decode();
  let src = im;
  if (spec.pad1080) {
    const cv = document.createElement('canvas'); cv.width = 1920; cv.height = 1080;
    const g = cv.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0,0,1920,1080);
    g.drawImage(im, 0, 1080 - im.height);
    src = cv;
  }
  ARX.bbox = (typeof arBBox==='function') ? arBBox(src) : null;
  ARX.bbKey = ''; ARX.prof = null; ARX.geo = null;
  const ims = await arLvTpls();
  const G = arGeom(src.width||src.videoWidth||1920, src.height||src.videoHeight||1080);
  const sc = s => Math.max(...ims.map(t => arLvScore(src, G, t, s)));
  const sO = +sc(1).toFixed(4), sB = +sc(1.40625).toFixed(4);
  const P = await arProfDetect(src);
  return {
    w: src.width, h: src.height, gw: G.gw, gh: G.gh, sO, sB,
    prof: P ? {id:P.id, s:P.s, lab:P.lab, sc:P.score, est:!!P.est} : null
  };
}'''

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

def is_base(r):
    return r and r['prof'] and r['prof']['id']=='1920b' and abs(r['prof']['s']-1.40625)<1e-6 and not r['prof']['est']

def is_opt(r):
    return r and r['prof'] and r['prof']['id']=='1920o' and r['prof']['s']==1 and not r['prof']['est'] and r['prof']['sc']>=.8

try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',
                              args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': 1200, 'height': 800}, locale='ko-KR')
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route('https://open.api.nexon.com/**', lambda r: r.abort())
        pg.goto(f'http://127.0.0.1:{PORT}/index.html')
        pg.evaluate('localStorage.clear()')
        pg.reload()
        pg.wait_for_function('() => typeof arProfDetect==="function" && typeof arLvScore==="function"', timeout=30000)

        # 1920 기본: 1366 UI를 키운 n1·n3·n5(예전에 최적 오인)와 n2·n7
        for fn, tag in [('n1_1920b.jpg','n1 약함'),('n2_1920b.jpg','n2 선명'),('n3_1920b.jpg','n3 약함'),
                        ('n5_1920b.jpg','n5 약함'),('n7_1920b.jpg','n7 선명')]:
            r = pg.evaluate(DET, {'u': u(os.path.join(FX, fn))})
            print('BASE', fn, r)
            check(f'{tag} 1920 → 기본 비율 s=1.40625', is_base(r), r)
            check(f'{tag} 1배 점수는 최적 범위(.96) 미만(오인 띠 ~.92)', r['sO'] < 0.96, r)

        # 실 1920 최적: b415 상태바를 1080 캔버스에 붙인 방식(기존 회귀와 동일) + 전체 화면
        for fn, tag in [('status_v2.png','벨로나 보상 상태바'),('status_v3.png','세렌 보상 상태바')]:
            r = pg.evaluate(DET, {'u': u(os.path.join(FX415, fn)), 'pad1080': True})
            print('OPT pad', fn, r)
            check(f'{tag} 1920 → 최적 비율 s=1', is_opt(r), r)
            check(f'{tag} 1배 점수는 최적 범위 ≥.96', r['sO'] >= 0.96, r)

        r = pg.evaluate(DET, {'u': u(os.path.join(FX295, 'v07_1080.jpg'))})
        print('OPT full', r)
        check('v07 1920 전체 화면 → 최적 비율 s=1', is_opt(r), r)
        check('v07 1배 ≥.96, 1.406배는 최적보다 낮음', r['sO']>=0.96 and r['sB']<r['sO'], r)

        # 다른 해상도는 기존 규칙
        r = pg.evaluate(DET, {'u': u(os.path.join(FX, 'n2_orig.jpg'))})
        print('ORIG', r)
        check('원본 1376×776 → 1366 UI 1 (창 여분 규칙)', r['prof'] and r['prof']['id']=='1366' and r['prof']['s']==1, r)
        r = pg.evaluate(DET, {'u': u(os.path.join(FX, 'n2_1366.jpg'))})
        print('1366', r)
        check('정확 1366×768 → 1366 UI 1', r['prof'] and r['prof']['id']=='1366' and r['prof']['s']==1 and r['prof']['sc']>=.8, r)
        r = pg.evaluate(DET, {'u': u(os.path.join(FX, 'n2_1600.jpg'))})
        print('1600', r)
        check('1600×900 → 기본 추정 s≈1.172', r['prof'] and '추정' in (r['prof']['lab'] or '') and '기본' in r['prof']['lab'] and abs(r['prof']['s']-1.17188)<0.01, r)
        r = pg.evaluate(DET, {'u': u(os.path.join(FX, 'n2_2560.jpg'))})
        print('2560', r)
        check('2560×1440 → 기본 비율 s=1.875', r['prof'] and r['prof']['id']=='2560b' and abs(r['prof']['s']-1.875)<1e-6, r)

        b.close()
finally:
    srv.terminate()
    shutil.rmtree(site, ignore_errors=True)
if errs:
    print('PAGE ERRORS', errs[:5]); fails.append('pageerror')
if fails:
    print('FAILED', fails); sys.exit(1)
print('PASS b422')
