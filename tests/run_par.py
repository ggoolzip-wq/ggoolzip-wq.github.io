#!/usr/bin/env python3
"""병렬 전체 테스트 (b107, 2026-10-14). run_all.sh 와 같은 목록·같은 로그(tests/out/r*.log)·같은 판정.
동시에 최대 JOBS(기본 8, MBT_JOBS)개. 테스트 파일에 적힌 포트(8000~9999 숫자)가 겹치는 테스트는 동시에 돌리지 않음(포트 충돌 방지).
zosu-testfix: 서버 포트는 이제 _tutil.free_port() 로 매번 빈 포트를 받으므로 파일에 포트 숫자가 거의 없음(남은 9996~9999 는 Playwright route 로만 잡는 가짜 주소).
직렬로 돌리려면 MBT_JOBS=1 또는 bash tests/run_all.sh"""
import os, re, subprocess, sys, time
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.makedirs('tests/out',exist_ok=True)
sh=open('tests/run_all.sh').read()
nums=re.search(r'for n in ([\d ]+); do',sh).group(1).split(); others=re.search(r'for t in ([\w ]+); do',sh).group(1).split()
T=[(f'tests/test_tracker{n}.py',f'tests/out/r{n}.log') for n in nums]+[(f'tests/test_{t}.py',f'tests/out/r_{t}.log') for t in others]
ports=lambda f:set(re.findall(r'(?<!\d)(8\d{3}|9\d{3})(?!\d)',open(f).read()))
P={f:ports(f) for f,_ in T}; JOBS=int(os.environ.get('MBT_JOBS','8'))
todo=list(T); run={}; failed=[]; t0=time.time()
while todo or run:
    for p,(f,lg,fh) in list(run.items()):
        if p.poll() is not None:
            fh.close(); del run[p]
            if p.returncode: failed.append((f,lg))
            out=open(lg,errors='replace').read().splitlines(); bad=[l for l in out if re.search(r'FAIL|ERRORS|Error',l)][-3:]
            print('==',f,'(exit %d)'%p.returncode); [print(l) for l in bad]
    busy=set().union(*[P[f] for f,_,_ in run.values()]) if run else set()
    for x in list(todo):
        if len(run)>=JOBS: break
        if P[x[0]]&busy: continue
        fh=open(x[1],'w'); p=subprocess.Popen([sys.executable,x[0]],stdout=fh,stderr=subprocess.STDOUT); run[p]=(x[0],x[1],fh); busy|=P[x[0]]; todo.remove(x)
    time.sleep(0.2)
# 병렬 부하로 타이밍이 빠듯한 테스트가 가끔 실패 → 실패한 것만 끝에 하나씩(직렬) 한 번 더
fail=0
for f,lg in failed:
    with open(lg,'w') as fh: rc=subprocess.call([sys.executable,f],stdout=fh,stderr=subprocess.STDOUT)
    print('== RETRY(직렬)',f,'(exit %d)'%rc); fail|=rc!=0
print('TOTAL %.1fs'%(time.time()-t0)); sys.exit(1 if fail else 0)
