"""Quick local D1/R2 + isolated headless IndexedDB retention checks. No production data."""
import os,sys,json,time,urllib.request,urllib.error,urllib.parse,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import cf_dev,mock_nexon_list as MN,_tutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
NP,WP,HP=[_tutil.free_port() for _ in range(3)]
MN.start(NP); key='b393_TEST_0123456789abcdef'; MN.KEYS[key]=['b393-account']
def req(method,path,tok=None,raw=None,meta=None):
 h={'Origin':'https://bossmaple.pages.dev','Content-Type':'application/json'}
 if tok:h['Authorization']='Bearer '+tok
 if meta:h['X-Epic-Meta']=urllib.parse.quote(json.dumps(meta))
 r=urllib.request.Request(f'http://127.0.0.1:{WP}'+path,data=raw,headers=h,method=method)
 try:
  with urllib.request.urlopen(r) as x:return x.status,x.read()
 except urllib.error.HTTPError as e:return e.code,e.read()
with_dev=None
try:
 with_dev=cf_dev.Dev(WP,NP,args=('-c',str(ROOT/'server/wrangler.toml'),str(ROOT/'tests/fixtures/b393/purge_entry.js')))
 s,b=req('POST','/api/login',raw=json.dumps({'key':key}).encode()); assert s==200,(s,b); tok=json.loads(b)['token']
 now=int(time.time()*1000); ids=['ec'+str(now+i) for i in range(2)]
 for id in ids:
  assert req('POST','/api/epic/clip?id='+id,tok,b'WEBMtestbytes',{'id':id,'t0':int(id[2:]),'format':'webm'})[0]==200
 cut=json.loads(req('GET','/__week?now='+str(now))[1])['cut']
 assert json.loads(req('GET','/__week?now='+str(cut-1))[1])['cut']==cut-7*86400000
 assert json.loads(req('GET','/__week?now='+str(cut))[1])['cut']==cut
 oldkey=with_dev.sql(f"SELECT r2key FROM epic_clips WHERE id='{ids[0]}'")[0]['r2key']
 assert json.loads(req('GET','/__r2?key='+urllib.parse.quote(oldkey))[1])['exists']
 with_dev.sql(f"UPDATE epic_clips SET t0={cut-1} WHERE id='{ids[0]}'")
 assert json.loads(req('GET','/api/epic/clips',tok)[1])['total']==1
 assert req('GET','/api/epic/clip/'+ids[0],tok)[0]==404
 assert json.loads(req('GET','/__purge?fail=1')[1])['failed']
 assert with_dev.sql('SELECT COUNT(*) n FROM epic_clips')[0]['n']==2
 assert json.loads(req('GET','/__purge')[1])['deleted']==1
 assert json.loads(req('GET','/__purge')[1])['deleted']==0
 assert not json.loads(req('GET','/__r2?key='+urllib.parse.quote(oldkey))[1])['exists']
 assert with_dev.sql('SELECT COUNT(*) n FROM epic_clips')[0]['n']==1
 assert req('GET','/api/epic/clip/'+ids[1],tok)[1]==b'WEBMtestbytes'
 old='ec'+str(cut-1)
 assert req('POST','/api/epic/clip?id='+old,tok,b'oldbytes',{'t0':cut-1})[0]==400
 assert req('DELETE','/api/epic/clip/'+ids[1],tok)[0]==404
 print('PASS server: KST boundary, old hidden, R2 failure retry, purge, current preserved, idempotent, expired upload blocked, single delete removed')
finally:
 if with_dev:with_dev.stop()
srv=_tutil.Popen([sys.executable,'-m','http.server',str(HP),'--bind','127.0.0.1'],cwd=str(ROOT),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--no-sandbox']);page=b.new_page(); page.goto(f'http://127.0.0.1:{HP}/?example=1');page.wait_for_function('typeof ecList === "function"')
  result=page.evaluate('''async()=>{
   const cut=weekStartMs(),old={id:'ec'+(cut-1),t0:cut-1},cur={id:'ec'+Date.now(),t0:Date.now()};
   await ecTx(['meta','frames'],'readwrite',t=>{for(const m of [old,cur]){t.objectStore('meta').put(m);t.objectStore('frames').put({id:m.id,video:new Blob(['test'])});}});
   const L=await ecList();await ecPutMeta(old);const again=await ecList();
   return {ids:L.map(x=>x.id),old:!!(await ecFrames(old.id)),cur:!!(await ecFrames(cur.id)),again:again.length,removed:typeof ecDeleteClip==='undefined',label:document.querySelector('[data-tab="epic"]').textContent.trim()};
  }''')
  assert result['old']==False and result['cur']==True and result['again']==1 and result['removed'] and result['label']=='이번 주 에픽빔',result
  b.close(); print('PASS client: IndexedDB old metadata+video deleted, current kept, expired metadata cannot return, rename')
finally:srv.terminate()
print('ALL PASS b393')
