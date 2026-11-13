"""b418 (t539u): 벨로나 상자 가림 누적 · 영문 닉네임 1글자 OCR 오독."""
import os, sys, tempfile, shutil, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _tutil
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FX = os.path.join(ROOT, 'tests', 'fixtures', 'b418')
fails, errs = [], []

def check(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' — ' + str(d)[:500]) if d != '' else ''))
    if not c:
        fails.append(n)

def u(n):
    return 'data:image/jpeg;base64,' + base64.b64encode(open(os.path.join(FX, n + '.jpg'), 'rb').read()).decode()

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

JS_LAT = r'''() => {
  const out = {};
  const chars = (arr) => { S.characters = arr.map((n,i)=>({id:'c'+i, name:n})); };
  const vote = (hist) => { ARX.eHist = hist.slice(); return arLatVote(); };
  chars(['zetking']);
  out.fuzzy = vote(['zetkina','zetkina']);
  out.exact = vote(['zetking','zetking']);
  out.num = vote(['26100','26100','26100']);
  out.one = vote(['zetkina']); // only 1 vote → no
  out.mix = vote(['zetkina','26100','zetkina']);
  chars(['zetking','zetkina']);
  out.pair = vote(['zetkina','zetkina','zetkina']); // ambiguous pair
  chars(['abc','abd']);
  out.short = vote(['abd','abd']); // short: exact abd only, abc not fuzzy
  out.shortMiss = (() => { chars(['abc']); return vote(['abd','abd']); })();
  chars(['2터래플','zetking']);
  out.withKor = vote(['zetkina','Zetkina']);
  return out;
}'''

JS_ACC = r'''() => {
  const out = {};
  ARX.boxAcc = {};
  out.t1 = arBoxAccPush('bellona', 0.73, 1000);
  out.t2 = arBoxAccPush('bellona', 0.74, 1100);
  out.t3 = arBoxAccPush('bellona', 0.725, 1200);
  ARX.boxAcc = {};
  out.low1 = arBoxAccPush('bellona', 0.70, 2000);
  out.low2 = arBoxAccPush('bellona', 0.71, 2100);
  out.low3 = arBoxAccPush('bellona', 0.687, 2200);
  ARX.boxAcc = {};
  out.stale1 = arBoxAccPush('bellona', 0.74, 3000);
  out.stale2 = arBoxAccPush('bellona', 0.74, 3100);
  out.stale3 = arBoxAccPush('bellona', 0.74, 4000); // 1000ms gap > 800 window, only 1 remains
  out.thr = AR_BOX.bellona.thr;
  out.accThr = AR_BOX_ACC_THR;
  out.accN = AR_BOX_ACC_N;
  return out;
}'''

JS_FOOT = r'''async ([src,k]) => {
  ARX.cfg.boxWorker = false;
  const im = new Image(); im.src = src; await im.decode();
  const sc = await arBoxScore(im, k);
  return {sc, foot: +(+ARX.boxFootSc||0).toFixed(4), thr: AR_BOX[k].thr};
}'''

try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',
                              args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': 1400, 'height': 900}, locale='ko-KR')
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{PORT}/index.html')
        pg.wait_for_timeout(800)

        lat = pg.evaluate(JS_LAT)
        check('zetkina×2 → zetking', lat['fuzzy']['cid']=='c0', lat['fuzzy'])
        check('zetking exact → zetking', lat['exact']['cid']=='c0', lat['exact'])
        check('26100 숫자는 영문 이름 아님', lat['num']['cid']=='', lat['num'])
        check('zetkina 1회는 부족', lat['one']['cid']=='', lat['one'])
        check('zetkina 2 + 26100 1 → zetking (절반 이상)', lat['mix']['cid']=='c0', lat['mix'])
        check('zetking·zetkina 동시 목록이면 정하지 않음', lat['pair']['cid']=='', lat['pair'])
        check('짧은 abd 정확 일치는 abd', lat['short']['cid']=='c1', lat['short'])
        check('짧은 abc 는 abd 로 퍼지 안 됨', lat['shortMiss']['cid']=='', lat['shortMiss'])
        check('한글 이름과 같이 있어도 zetkina→zetking', lat['withKor']['cid']=='c1', lat['withKor'])

        acc = pg.evaluate(JS_ACC)
        check('가림누적 1틱은 미확정', acc['t1'] is None, acc['t1'])
        check('가림누적 2틱은 미확정', acc['t2'] is None, acc['t2'])
        check('가림누적 3틱(.72+) 인정', acc['t3'] and acc['t3']['k']=='bellona' and abs(acc['t3']['sc']-0.725)<1e-9, acc['t3'])
        check('0.70 이하는 누적 안 함', acc['low1'] is None and acc['low2'] is None and acc['low3'] is None, acc)
        check('0.8초 지난 발 점수는 창에서 제외', acc['stale3'] is None, acc['stale3'])
        check('상자 공식 문턱은 그대로 0.75', acc['thr']==0.75 and acc['accThr']==0.72 and acc['accN']==3, acc)

        # real frames: v3 early official below 0.75, foot >= 0.72; v4 bellona foot < 0.72
        v3 = []
        for name in ['v3_t00','v3_t10','v3_t20']:
            r = pg.evaluate(JS_FOOT, [u(name),'bellona'])
            v3.append(r)
            print('FOOT', name, r)
        check('v3 초반 공식 점수는 문턱 미달(문턱 안 낮춤)', all(x['sc']<0.75 for x in v3), v3)
        check('v3 초반 발 점수는 0.72 이상', all(x['foot']>=0.72 for x in v3), v3)
        v4 = []
        for name in ['v4_t00','v4_t40']:
            r = pg.evaluate(JS_FOOT, [u(name),'bellona'])
            v4.append(r)
            print('FOOT', name, r)
        check('v4(스우) 벨로나 발 점수는 0.72 미만(오탐 없음)', all(x['foot']<0.72 for x in v4), v4)
        # lotus official on v4 should be unchanged (not our concern if already high)
        b.close()
finally:
    srv.terminate()
    shutil.rmtree(site, ignore_errors=True)

if errs:
    print('PAGE ERRORS', errs)
    fails.append('pageerror')
if fails:
    print('FAILED:', fails)
    sys.exit(1)
print('PASS b418')
