"""zosu-testfix (2026-10-19): 테스트 공용 도우미 — import _tutil 하면

1) free_port(): 127.0.0.1 에 bind(0) 해서 받은 빈 포트 (하드코딩 포트 충돌 방지).
2) Popen(...): subprocess.Popen 과 같지만
   - 부모(테스트) 프로세스가 어떻게 죽어도 자식이 SIGTERM 을 받음 (prctl PR_SET_PDEATHSIG),
   - atexit(정상 종료·예외·SIGTERM/SIGHUP)에서 terminate,
   - 'http.server' 면 포트가 열릴 때까지 기다리고, 그 전에 프로세스가 끝나면(= bind 실패) 바로 RuntimeError.
   → 예전처럼 테스트가 중간에 죽어도 http.server 가 남아서 다음 테스트가 남의 서버(예전 index.html)를 읽는 일이 없음.
3) 운영 Worker(https://ggoolzip-sync.bossmaple.workers.dev/**, 특히 /api/live 30초 폴링)를 모든 브라우저 컨텍스트에서
   빈 JSON {} 로 막음 (file:// 의 CORS 오류 로그·운영 썬데이/가격 데이터가 테스트에 섞이는 것 방지).
   테스트가 직접 ctx.route/pg.route 로 같은 주소를 잡으면 그쪽이 먼저(나중에 등록한 route 우선).
   실제 Worker 가 필요하면 MBT_REAL_WORKER=1.
"""
import os, sys, socket, subprocess, atexit, signal, time, ctypes

WORKER = 'https://ggoolzip-sync.bossmaple.workers.dev'
_used = set()

def free_port():
    for _ in range(100):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close()
        if p not in _used:
            _used.add(p); return p
    raise RuntimeError('free port not found')

def port_free(port, wait=0):
    """포트에 지금 아무도 listen 안 하면 True. wait 초 동안 다시 확인(같은 포트로 서버를 다시 띄울 때 이전 프로세스가 내려가는 시간)."""
    t0 = time.time()
    while True:
        if _bindable(port): return True
        if time.time() - t0 >= wait: return False
        time.sleep(0.2)

def _bindable(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # TIME_WAIT 는 무시 (서버들도 reuse 로 bind)
    try: s.bind(('127.0.0.1', int(port))); return True
    except OSError: return False
    finally: s.close()

def _pdeath():
    try: ctypes.CDLL('libc.so.6', use_errno=True).prctl(1, signal.SIGTERM)  # PR_SET_PDEATHSIG
    except Exception: pass

_procs = []
def track(p):
    _procs.append(p); return p

def _cleanup():
    for p in reversed(_procs):
        try:
            if p.poll() is None:
                p.terminate()
                try: p.wait(timeout=5)
                except Exception: p.kill()
        except Exception: pass
atexit.register(_cleanup)

def _on_sig(sig, frm): sys.exit(128 + sig)  # → atexit 실행
for _s in (signal.SIGTERM, signal.SIGHUP):
    try:
        if signal.getsignal(_s) in (signal.SIG_DFL, None): signal.signal(_s, _on_sig)
    except Exception: pass

def Popen(args, **kw):
    kw.setdefault('preexec_fn', _pdeath)
    a = [str(x) for x in args]
    port = a[a.index('http.server') + 1] if 'http.server' in a and a.index('http.server') + 1 < len(a) else None
    if port and not port_free(port, wait=5):
        raise RuntimeError(f'http.server: 포트 {port} 이미 사용 중 (남은 서버?)')
    p = track(subprocess.Popen(a, **kw))
    if port:
        t0 = time.time()
        while True:
            if p.poll() is not None:
                raise RuntimeError(f'http.server: 포트 {port} bind 실패 (exit {p.returncode})')
            try:
                socket.create_connection(('127.0.0.1', int(port)), timeout=0.5).close(); break
            except OSError:
                if time.time() - t0 > 15: raise RuntimeError(f'http.server: 포트 {port} 15초 안에 안 열림')
                time.sleep(0.05)
    return p

# ---- 운영 Worker 차단 (모든 Browser.new_context / Browser.new_page) ----
def _stub(route):
    route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body='{}')

def stub_worker(target):
    if os.environ.get('MBT_REAL_WORKER') == '1': return target
    target.route(WORKER + '/**', _stub); return target

try:
    from playwright.sync_api._generated import Browser
    if not getattr(Browser, '_tutil_wrapped', False):
        _nc, _np = Browser.new_context, Browser.new_page
        def _new_context(self, *a, **k): return stub_worker(_nc(self, *a, **k))
        def _new_page(self, *a, **k):
            p = _np(self, *a, **k); stub_worker(p.context); return p
        Browser.new_context, Browser.new_page = _new_context, _new_page
        Browser._tutil_wrapped = True
except Exception:
    pass
