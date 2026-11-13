"""b417 (t538u): 꺾쇠 없는 난이도 접미 · 2터래플을 2러래플로만 읽는 OCR."""
import os, sys, tempfile, shutil, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _tutil
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails, errs = [], []

def check(n, c, d=''):
    print(('PASS ' if c else 'FAIL ') + n + ((' — ' + str(d)[:500]) if d != '' else ''))
    if not c:
        fails.append(n)

site = tempfile.mkdtemp()
for f in ['index.html', 'prices.json']:
    shutil.copy(os.path.join(ROOT, f), site)
for d in ['data', 'ocr']:
    shutil.copytree(os.path.join(ROOT, d), os.path.join(site, d),
                    ignore=shutil.ignore_patterns('__pycache__'))
PORT = _tutil.free_port()
srv = _tutil.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'],
                   cwd=site, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

JS = r'''() => {
  const out = {};
  const D = t => { const b = arDetectBMap(t); return b ? [b.boss, b.diff, b.kind] : null; };
  ARX.runDiff = null; ARX.tplNoDiff = false;
  out.v2 = D('가룸글까기솔라톰의유산이지:');
  ARX.runDiff = null;
  out.v2sp = D('솔라툼 골짜기 솔라툼의 유산이지:');
  ARX.runDiff = null;
  out.bracket = D('솔라툼 골짜기：솔라툼의 유산 <이지>');
  ARX.runDiff = {boss:'bellona', diff:'easy'};
  out.keep = D('솔라툼 골짜기：솔라툼의 유산'); // no trailing word → keep runDiff
  ARX.runDiff = null;
  out.none = D('라무라무 신전');
  ARX.runDiff = null;
  out.hardGlue = D('의지가 증명된 자리하드');
  ARX.runDiff = null;
  out.extreme = D('블랙헤븐고요해진함선익스트림');

  // arMapTplDiff: glued vs spaced (b405 '울메 가까운 끗 하드' still rejected)
  ARX.mapSt = {boss:'bellona', kind:'r', diff:''}; ARX.runDiff = null;
  ARX.det = {cid:'', boss:'', diff:''}; ARX.rew = ARX.rwl = ARX.lock = ARX.box = null;
  const cv = document.createElement('canvas'); cv.width = 1920; cv.height = 1080;
  const hint = {text:'솔라툼의 유산 <이지>', boss:'bellona', sc:.999};
  out.tplSpace = arMapTplDiff('울메 가까운 끗 하드', {...hint, boss:'dunkel', text:'끝에 가까운 곳 <이지>'}, cv);
  ARX.mapSt = {boss:'dunkel', kind:'br', diff:''}; ARX.runDiff = null;
  out.tplSpace2 = arMapTplDiff('울메 가까운 끗 하드', {text:'끝에 가까운 곳 <이지>', boss:'dunkel', sc:.999}, cv);
  out.tplSpaceRun = ARX.runDiff;
  ARX.mapSt = {boss:'bellona', kind:'r', diff:''}; ARX.runDiff = null;
  out.tplGlue = arMapTplDiff('가룸글까기솔라톰의유산이지:', hint, cv);
  out.tplGlueRun = ARX.runDiff && ARX.runDiff.diff;
  ARX.runDiff = null;
  out.tplBracket = arMapTplDiff('솔라툼의 유산 <하드>', hint, cv);
  out.tplBracketRun = ARX.runDiff && ARX.runDiff.diff;

  // name vote
  const C = (id,n) => ({id, name:n, level:285, job:'', world:'', ocid:'', accId:'', image:'',
    bosses:{}, weekly:{}, monthly:{}, auto:{}, drops:{}, sync:{}});
  const nm = id => (S.characters.find(x => x.id === id) || {}).name || '';
  const vote = (names, hist, lead) => {
    S.characters = names.map((n,i) => C('c'+i, n));
    ARX.nHist = hist.slice();
    ARX.nLead = (lead || hist.map(() => true)).slice();
    ARX.nLock = null; ARX.det = {cid:'',boss:'',diff:'',src:''};
    return {cid: nm(arNameVote2().cid), no: arNameVote2().no};
  };
  out.ter = vote(['2터래플','zetking'], ['러래플','러래플','러래플','러래플']);
  out.terDeo = vote(['2터래플','더래플'], ['러래플','러래플','러래플','러래플']);
  out.terPlain = vote(['2터래플'], ['러래플','러래플','러래플','러래플'], [false,false,false,false]);
  out.terPair = vote(['2터래플','2러래플'], ['러래플','러래플','러래플','러래플']);
  out.tdic = vote(['트딕이'], ['드딕이','드딕이','드딕이','드딕이'], [false,false,false,false]);
  out.kol = vote(['콜더쇼츠'], ['골더쇼츠','골더쇼츠','골더쇼츠','골더쇼츠'], [false,false,false,false]);
  out.exact = vote(['2터래플'], ['터래플','터래플','터래플','터래플']);
  return out;
}'''

try:
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',
                              args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': 1200, 'height': 800}, locale='ko-KR')
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.route('https://open.api.nexon.com/**', lambda r: r.abort())
        pg.goto(f'http://127.0.0.1:{PORT}/index.html', wait_until='domcontentloaded', timeout=60000)
        pg.evaluate('localStorage.clear()')
        pg.reload(wait_until='domcontentloaded')
        pg.wait_for_timeout(800)
        r = pg.evaluate(JS)
        print('RAW', r)
        check('v2 OCR 솔라톰의유산이지: → 벨로나 이지', r['v2'] == ['bellona', 'easy', 'r'], r['v2'])
        check('띄어 쓴 같은 문장도 이지', r['v2sp'] == ['bellona', 'easy', 'r'], r['v2sp'])
        check('기존 꺾쇠 <이지> 유지', r['bracket'] == ['bellona', 'easy', 'r'], r['bracket'])
        check('난이도 단어 없으면 runDiff 유지', r['keep'] == ['bellona', 'easy', 'r'], r['keep'])
        check('라무라무 신전 난이도 없음', r['none'] == ['slime', '', 'b'], r['none'])
        check('붙은 하드', r['hardGlue'] and r['hardGlue'][0] == 'adversary' and r['hardGlue'][1] == 'hard', r['hardGlue'])
        check('붙은 익스트림', r['extreme'] and r['extreme'][0] == 'lotus' and r['extreme'][1] == 'extreme', r['extreme'])
        check('b405 띄어 쓴 끗 하드 는 템플릿 난도 거부', r['tplSpace2'] is False and not r['tplSpaceRun'], (r['tplSpace2'], r['tplSpaceRun']))
        check('붙은 유산이지: 는 템플릿 난도 이지', r['tplGlue'] is True and r['tplGlueRun'] == 'easy', (r['tplGlue'], r['tplGlueRun']))
        check('꺾쇠 <하드> 는 기존대로 하드', r['tplBracket'] is True and r['tplBracketRun'] == 'hard', (r['tplBracket'], r['tplBracketRun']))
        check('2러래플 읽기 → 2터래플 (짝 없음)', r['ter']['cid'] == '2터래플', r['ter'])
        check('더래플이 같은 꼴 짝이면 거센 없이 안 잡음(오인 방지)', r['terDeo']['cid'] == '', r['terDeo'])
        check('앞 기호 없는 2터래플만 등록이면 안 잡음(b375)', r['terPlain']['cid'] == '', r['terPlain'])
        check('2러래플이 목록에 있으면 정확한 2러래플로', r['terPair']['cid'] == '2러래플', r['terPair'])
        check('드딕이→트딕이(ㄷ)는 기존대로 거부 (b409)', r['tdic']['cid'] == '', r['tdic'])
        check('콜더쇼츠 ㅋ 규칙 유지 (b409)', r['kol']['cid'] == '콜더쇼츠', r['kol'])
        check('정확한 터래플 읽기는 2터래플', r['exact']['cid'] == '2터래플', r['exact'])
        check('페이지 오류 없음', not errs, errs)
        b.close()
finally:
    srv.terminate()
    shutil.rmtree(site, ignore_errors=True)

print('RESULT', 'FAIL' if fails else 'OK', len(fails))
sys.exit(1 if fails else 0)
