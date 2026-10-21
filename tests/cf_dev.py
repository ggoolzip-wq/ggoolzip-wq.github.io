# wrangler dev(로컬 D1) + 넥슨 모의 서버를 띄우는 테스트 도우미
import os, subprocess, shutil, tempfile, time, urllib.request, atexit
import _tutil  # zosu-testfix: 포트 사용 중이면 바로 실패, 자식 정리(atexit/PDEATHSIG), 시작 실패 시에도 정리
SERVER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'server')
TEST_PASS='Test Invite 7'  # 테스트용 초대 비밀번호 (실제 비밀번호 아님)
import hashlib
TEST_PASS_HASH=hashlib.sha256(('ggoolzip-invite:'+TEST_PASS).encode()).hexdigest()
NODE_BIN=os.environ.get('WRANGLER_NODE_BIN','/home/box/.local/node22/bin')  # wrangler 4 는 Node 22 이상 필요
def available():
    return os.path.exists(os.path.join(SERVER,'node_modules','.bin','wrangler')) and os.path.exists(os.path.join(NODE_BIN,'node'))
class Dev:
    def __init__(self,port,nexon_port,no_pass=False,approval=False,extra=None,persist=None,args=()):  # b132: persist = 예전 Dev.dir 재사용(같은 D1로 설정만 바꿔 다시 띄움)
         # b68: approval=False → AUTO_APPROVE=1 (예전 테스트는 승인 없이), True → 가입 승인 흐름
        self.port=port; self.dir=persist or tempfile.mkdtemp(prefix='cfdev'); env=dict(os.environ,PATH=NODE_BIN+':'+os.environ.get('PATH',''),WRANGLER_SEND_METRICS='false',CI='1')
        w=os.path.join(SERVER,'node_modules','.bin','wrangler')
        if not persist: subprocess.run([w,'d1','execute','ggoolzip-sync','--local','--persist-to',self.dir,'--file=schema.sql'],cwd=SERVER,env=env,check=True,capture_output=True)
        if not _tutil.port_free(port,wait=15): raise RuntimeError(f'wrangler dev: 포트 {port} 이미 사용 중 (남은 서버?)')
        self.log=open(os.path.join(self.dir,'dev.log'),'w')
        self.p=subprocess.Popen([w,'dev','--local','--ip','127.0.0.1','--port',str(port),'--persist-to',self.dir,'--var',f'NEXON_BASE:http://127.0.0.1:{nexon_port}',*([] if no_pass else ['--var',f'SITE_PASS_HASH:{TEST_PASS_HASH}']),*((['--var','APPROVAL_REQUIRED:1'] if 'APPROVAL_REQUIRED' not in (extra or {}) else []) if approval else ['--var','AUTO_APPROVE:1']),*[x for k,v in (extra or {}).items() for x in ('--var',f'{k}:{v}')],'--show-interactive-dev-session=false','--inspector-port',str(_tutil.free_port()),*args],
                                cwd=SERVER,env=env,stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=_tutil._pdeath)
        atexit.register(self.stop)
        for _ in range(240):
            if self.p.poll() is not None: break  # bind 실패 등으로 끝남 → 남의 서버에 붙지 않게 바로 실패
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=1)
                if self.p.poll() is None: return
                break
            except Exception: time.sleep(0.25)
        self.stop()
        raise RuntimeError('wrangler dev did not start: '+open(os.path.join(self.dir,'dev.log')).read()[-2000:])
    def sql(self,q):
        env=dict(os.environ,PATH=NODE_BIN+':'+os.environ.get('PATH',''),CI='1')
        r=subprocess.run([os.path.join(SERVER,'node_modules','.bin','wrangler'),'d1','execute','ggoolzip-sync','--local','--persist-to',self.dir,'--json','--command',q],cwd=SERVER,env=env,capture_output=True,text=True)
        import json; return json.loads(r.stdout)[0]['results']
    def stop(self):
        import signal
        if getattr(self,'_stopped',False): return
        self._stopped=True
        try: os.killpg(self.p.pid,signal.SIGTERM)
        except Exception: pass
        try: self.p.wait(timeout=10)
        except Exception:
            try: os.killpg(self.p.pid,signal.SIGKILL)
            except Exception: pass
        try: self.log.close()
        except Exception: pass
