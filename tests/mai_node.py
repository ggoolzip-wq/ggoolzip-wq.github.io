# b208: 아이템 ↔ maple.ai.kr 이름 짝은 server/worker.js 하나(MAI_NAMES) — 테스트는 node 로 Worker 의 maiMap 을 그대로 부름
import os, json, subprocess, shutil, tempfile
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _call(fn,*args):
    d=tempfile.mkdtemp(); shutil.copy(os.path.join(ROOT,'server','worker.js'),os.path.join(d,'w.mjs'))
    js="const W=await import(process.argv[2]);const a=JSON.parse(process.argv[3]);const r=W[a.fn](...a.args);console.log(JSON.stringify(r instanceof Set?[...r]:r));"
    open(os.path.join(d,'t.mjs'),'w').write(js)
    out=subprocess.check_output(['node',os.path.join(d,'t.mjs'),os.path.join(d,'w.mjs'),json.dumps({'fn':fn,'args':list(args)})]).decode().strip().splitlines()[-1]
    shutil.rmtree(d,ignore_errors=True); return json.loads(out)
def mai_map(items,t): return _call('maiMap',items,t)
def mai_unmatched(items): return _call('maiUnmatched',items)
def mai_keys(): return json.loads(json.dumps(_call('maiKeysList')))
