# 동기화 서버 테스트용 넥슨 /maplestory/v1/character/list 모의 서버 (키 → account_id)
import json, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
KEYS={'live_KEY_A_0123456789abcdef':['acc-A'],'live_KEY_B_0123456789abcdef':['acc-B'],'live_KEY_AC_0123456789abcde':['acc-A','acc-C'],
      'live_KEY_D_0123456789abcdef':['acc-D'],'live_KEY_E_0123456789abcdef':['acc-E'],'live_RATE_0123456789abcdef':'429',
      'live_KEY_F_0123456789abcdef':['acc-F'],'live_KEY_G_0123456789abcdef':['acc-G'],'live_BK_A_0123456789abcdefg':['acc-A'],'live_BK_G_0123456789abcdefg':['acc-G']}
SEEN=[]
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        k=self.headers.get('x-nxopen-api-key',''); SEEN.append((self.path,k))
        v=KEYS.get(k)
        if self.path.split('?')[0]!='/maplestory/v1/character/list': code,body=404,{'error':{'name':'OPENAPI0004'}}
        elif v=='429': code,body=429,{'error':{'name':'OPENAPI0007','message':'rate'}}
        elif v is None: code,body=400,{'error':{'name':'OPENAPI0006','message':'invalid key'}}
        else: code,body=200,{'account_list':[{'account_id':a,'character_list':[{'ocid':'o-'+a,'character_name':'캐릭'+a[-1],'world_name':'스카니아','character_class':'히어로','character_level':280}]} for a in v]}
        b=json.dumps(body).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
def start(port):
    s=ThreadingHTTPServer(('127.0.0.1',port),H); threading.Thread(target=s.serve_forever,daemon=True).start(); return s
