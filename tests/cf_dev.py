# wrangler dev(로컬 D1) + 넥슨 모의 서버를 띄우는 테스트 도우미
import os, subprocess, shutil, tempfile, time, urllib.request
SERVER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'server')
TEST_PASS='Test Invite 7'  # 테스트용 초대 비밀번호 (실제 비밀번호 아님)
import hashlib
TEST_PASS_HASH=hashlib.sha256(('ggoolzip-invite:'+TEST_PASS).encode()).hexdigest()
NODE_BIN=os.environ.get('WRANGLER_NODE_BIN','/home/box/.local/node22/bin')  # wrangler 4 는 Node 22 이상 필요
def available():
    return os.path.exists(os.path.join(SERVER,'node_modules','.bin','wrangler')) and os.path.exists(os.path.join(NODE_BIN,'node'))
class Dev:
    def __init__(self,port,nexon_port,no_pass=False):
        self.port=port; self.dir=tempfile.mkdtemp(prefix='cfdev'); env=dict(os.environ,PATH=NODE_BIN+':'+os.environ.get('PATH',''),WRANGLER_SEND_METRICS='false',CI='1')
        w=os.path.join(SERVER,'node_modules','.bin','wrangler')
        subprocess.run([w,'d1','execute','ggoolzip-sync','--local','--persist-to',self.dir,'--file=schema.sql'],cwd=SERVER,env=env,check=True,capture_output=True)
        self.log=open(os.path.join(self.dir,'dev.log'),'w')
        self.p=subprocess.Popen([w,'dev','--local','--ip','127.0.0.1','--port',str(port),'--persist-to',self.dir,'--var',f'NEXON_BASE:http://127.0.0.1:{nexon_port}',*([] if no_pass else ['--var',f'SITE_PASS_HASH:{TEST_PASS_HASH}']),'--show-interactive-dev-session=false'],
                                cwd=SERVER,env=env,stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True)
        for _ in range(120):
            try: urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=1); return
            except Exception: time.sleep(0.25)
        raise RuntimeError('wrangler dev did not start: '+open(os.path.join(self.dir,'dev.log')).read()[-2000:])
    def sql(self,q):
        env=dict(os.environ,PATH=NODE_BIN+':'+os.environ.get('PATH',''),CI='1')
        r=subprocess.run([os.path.join(SERVER,'node_modules','.bin','wrangler'),'d1','execute','ggoolzip-sync','--local','--persist-to',self.dir,'--json','--command',q],cwd=SERVER,env=env,capture_output=True,text=True)
        import json; return json.loads(r.stdout)[0]['results']
    def stop(self):
        import signal
        try: os.killpg(self.p.pid,signal.SIGTERM)
        except Exception: pass
        try: self.p.wait(timeout=10)
        except Exception: os.killpg(self.p.pid,signal.SIGKILL)
        self.log.close()
