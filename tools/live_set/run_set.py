#!/usr/bin/env python3
"""Live recognizer replay on 1920x1080-converted n1-n7 videos."""
import os, sys, json, time, shutil, tempfile, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = os.environ['LIVE_ROOT']
VIDDIR = Path(os.environ.get('LIVE_VIDDIR','/workspace/reward_report_1114/src555'))
OUT = Path(os.environ['LIVE_OUT'])
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, 'tests'))
import _tutil

VIDEOS = json.loads(Path(os.environ['LIVE_SPEC']).read_text())
if os.environ.get('LIVE_ONLY'): VIDEOS=[v for v in VIDEOS if v['id'] in os.environ['LIVE_ONLY'].split(',')]
CHARS = json.loads(os.environ.get('LIVE_CHARS','["2터래플","림강혼망","zetking"]'))

SETUP = """() => {
  const all = {};
  for (const b of BOSSES) {
    const d = b.diffs.includes('hard') ? 'hard' : b.diffs[0];
    all[b.id] = {enabled:true, party:1, diff:d};
  }
  const mk = (id,n,lv) => ({
    id, name:n, level:lv, job:'', world:'스카니아', ocid:'', accId:'', image:'',
    bosses: JSON.parse(JSON.stringify(all)), weekly:{}, monthly:{}, mdate:{}, auto:{}, drops:{}, sync:{}
  });
  S.characters = __CHARS__.map((n,i)=>mk('c'+i,n,280));
  S.activeId = 'c0'; save(); render();
}"""

SNAP = """() => {
  const A = ARX;
  const det = A.det || {};
  const char = (S.characters||[]).find(c => c.id === det.cid);
  const P = A.prof;
  const logs = (A.log && A.log.slice) ? A.log.slice(-8) : (A.logs||[]).slice(-8);
  const profLogs = (logs||[]).filter(x => typeof x==='string' && x.includes('해상도'));
  return {
    vt: (window._v && isFinite(_v.currentTime)) ? +_v.currentTime.toFixed(3) : 0,
    ended: !!(window._v && _v.ended),
    build: document.documentElement.dataset.build||'',
    vw: window._v && _v.videoWidth, vh: window._v && _v.videoHeight,
    prof: P ? {id:P.id, s:P.s, lab:P.lab, sc:P.score, est:!!P.est, gw:P.gw, gh:P.gh} : null,
    profLogs,
    det: {cid:det.cid||'', boss:det.boss||'', diff:det.diff||'', src:det.src||''},
    cidName: char ? char.name : '',
    nameOk: !!A.nameOk,
    nameText: A.nameText||'',
    mapText: A.mapText||'',
    mapSt: A.mapSt ? {boss:A.mapSt.boss, kind:A.mapSt.kind, diff:A.mapSt.diff||'', name:A.mapSt.name||'', src:A.mapSt.src||''} : null,
    box: A.box ? {boss:A.box.boss, score:A.box.score, via:A.box.via||A.box.src||''} : null,
    runRec: (A.runRec||[]).slice(0,8),
  };
}"""

PLAY = """async (src) => {
  const v = document.createElement('video');
  v.muted = true; v.playsInline = true; v.crossOrigin = 'anonymous';
  v.src = src; v.style.position='fixed'; v.style.left='0'; v.style.top='0'; v.style.width='960px'; v.style.zIndex='1';
  document.body.appendChild(v);
  await new Promise((res, rej) => {
    const t = setTimeout(() => rej(new Error('video timeout')), 25000);
    v.onloadeddata = () => { clearTimeout(t); res(); };
    v.onerror = () => { clearTimeout(t); rej(new Error('video error')); };
  });
  try { await v.play(); } catch (e) { return {err: String(e)}; }
  window._v = v;
  ARX.testSrc = v;
  try { ARX.stream = v.captureStream(); } catch (e) { console.warn('captureStream', e); }
  window._allLog=[]; if(!window._arLogO){ window._arLogO=arLog; arLog=function(x){ try{ _allLog.push([+(v.currentTime||0).toFixed(2),String(x)]); }catch(e){} return window._arLogO(x); }; }
  arStart(v);
  const tab = document.querySelector('#tabs [data-tab="auto"]');
  if (tab) tab.click();
  return {w:v.videoWidth, h:v.videoHeight, d:v.duration, ready:true, build: document.documentElement.dataset.build||''};
}"""

def copy_site():
    site = tempfile.mkdtemp(prefix='live1920_')
    skip = {'.git', 'tests', 'HANDOFF.md', 'scripts', 'server', 'tools'}
    for f in os.listdir(ROOT):
        if f in skip or f.startswith('.'):
            continue
        src, dst = os.path.join(ROOT, f), os.path.join(site, f)
        if os.path.isdir(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('*.map', 'node_modules'))
        else:
            shutil.copy2(src, dst)
    vdir = Path(site) / 'vids'
    vdir.mkdir()
    for v in VIDEOS:
        shutil.copy2(VIDDIR / v['file'], vdir / v['file'])
    return site

def summarize(timeline, expect_name, expect_boss):
    profs = []
    for s in timeline:
        p = s.get('prof')
        if p and (not profs or profs[-1]['lab'] != p.get('lab')):
            profs.append({'t': s['vt'], **p})
    first_name = next((s['vt'] for s in timeline if s.get('nameOk') and s.get('cidName')==expect_name), None)
    first_map = next((s['vt'] for s in timeline if (s.get('mapSt') or {}).get('boss')==expect_boss), None)
    first_box = next((s['vt'] for s in timeline if s.get('box') and s['box'].get('boss')==expect_boss), None)
    last = timeline[-1] if timeline else {}
    # name hangul counts
    import collections, re
    hangs=collections.Counter()
    for s in timeline:
        for h in re.findall(r'[가-힣]{2,}', s.get('nameText') or ''):
            hangs[h]+=1
    maps=collections.Counter()
    for s in timeline:
        m=s.get('mapSt')
        if m: maps[(m.get('boss'), m.get('name'), m.get('kind'), m.get('diff'))]+=1
    return {
        'build': last.get('build'),
        'vw': last.get('vw'), 'vh': last.get('vh'),
        'profs': profs,
        'final_prof': last.get('prof'),
        'first_name': first_name,
        'final_name': last.get('cidName'),
        'nameOk': last.get('nameOk'),
        'first_map': first_map,
        'final_map': last.get('mapSt'),
        'first_box': first_box,
        'final_box': last.get('box'),
        'final_det': last.get('det'),
        'hangs': hangs.most_common(6),
        'maps': [(list(k),v) for k,v in maps.most_common(6)],
        'n': len(timeline),
        'runRec': last.get('runRec'),
    }

def main():
    site = copy_site()
    port = _tutil.free_port()
    srv = _tutil.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],
                       cwd=site, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f'http://127.0.0.1:{port}/index.html'
    print('SITE', site, 'ROOT', ROOT, flush=True)
    alls = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=os.environ.get('CHROME') or '/usr/bin/google-chrome',
                args=['--no-sandbox','--autoplay-policy=no-user-gesture-required','--disable-dev-shm-usage'])
            for spec in VIDEOS:
                print(f"\n======== {spec['id']} ========", flush=True)
                pg = browser.new_page(viewport={'width': 1400, 'height': 900}, locale='ko-KR',
                                      timezone_id='Asia/Seoul')
                errs=[]
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.route('https://open.api.nexon.com/**', lambda r: r.abort())
                pg.goto(url, wait_until='domcontentloaded', timeout=60000)
                pg.evaluate('localStorage.clear()')
                pg.reload(wait_until='domcontentloaded')
                pg.wait_for_timeout(800)
                pg.evaluate(SETUP.replace('__CHARS__', json.dumps(CHARS, ensure_ascii=False)))
                pg.wait_for_timeout(200)
                info = pg.evaluate(PLAY, f"/vids/{spec['file']}")
                print('PLAY', info, flush=True)
                timeline=[]
                t0=time.time()
                last_lab=None
                while True:
                    s=pg.evaluate(SNAP)
                    timeline.append(s)
                    lab=(s.get('prof') or {}).get('lab')
                    if lab!=last_lab or (len(timeline)%15==0):
                        print(f"  t={s['vt']:.2f} prof={s.get('prof')} name={s.get('cidName')!r} ok={s.get('nameOk')} map={s.get('mapSt')} box={s.get('box')}", flush=True)
                        last_lab=lab
                    if s.get('ended') or s['vt']>=spec['dur']-0.15 or time.time()-t0>spec['dur']+25:
                        break
                    pg.wait_for_timeout(250)
                allLog=pg.evaluate('()=>window._allLog||[]')
                drops=pg.evaluate('()=>{const o=[];for(const c of S.characters) o.push([c.name,c.drops||{}]);return o}')
                vout=OUT/spec['id']
                vout.mkdir(exist_ok=True)
                (vout/'timeline.json').write_text(json.dumps(timeline, ensure_ascii=False))
                sm=summarize(timeline, spec['name'], spec['boss'])
                sm['errs']=errs[:5]
                (vout/'log.json').write_text(json.dumps(allLog, ensure_ascii=False))
                sm['drops']=drops
                sm['airMax']=pg.evaluate('()=>{try{return JSON.parse(JSON.stringify({m:ARX.airMax||null,pf:arPf(),cand:(arCandidates(true)||[]).map(c=>c.k),cfg:{air:ARX.cfg.air,airFps:ARX.cfg.airFps}}))}catch(e){return String(e)}}')
                sm['itemLog']=[x for x in allLog if any(w in x[1] for w in ('득템','기록','획득','상자 확인 전','보류'))][:40]
                (vout/'summary.json').write_text(json.dumps(sm, ensure_ascii=False, indent=2))
                alls[spec['id']]=sm
                print('SUMMARY', json.dumps(sm, ensure_ascii=False), flush=True)
                pg.close()
            browser.close()
    finally:
        srv.terminate()
        shutil.rmtree(site, ignore_errors=True)
    (OUT/'all_summary.json').write_text(json.dumps(alls, ensure_ascii=False, indent=2))
    print('WROTE', OUT/'all_summary.json', flush=True)

if __name__=='__main__':
    main()
