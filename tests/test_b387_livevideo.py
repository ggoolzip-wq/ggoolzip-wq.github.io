from pathlib import Path
p = Path(__file__).with_name('test_b384_video.py')
s = p.read_text()
a = 'window._v=v; return true;'
b = 'window._v=v; ARX.video=v; ARX.stream=v.captureStream(); window._cacheSeen=false; setInterval(()=>{if(EC.snapRead)window._cacheSeen=true;},20); return true;'
assert s.count(a) == 1
s = s.replace(a, b, 1)
a = '    L=pg.evaluate'
assert s.count(a) == 1
s = s.replace(a, "    check('b387 독립 작업자 녹화 프레임 사용',pg.evaluate('!!(ARS.clip&&ARS.clip.clipN>100)'),pg.evaluate('({frames:ARS.clip&&ARS.clip.clipN,clipError:ARS.clip&&ARS.clip.clipError,snap:ARS.n})'))\n    check('b387 실제 스트림 불투명 스냅샷 캐시 사용',pg.evaluate('!!window._cacheSeen'),pg.evaluate('({snap:ARS.n,opaque:ARS.bm&&ARS.bm.arOpaque})'))\n" + a, 1)
s = s.replace('_v.pause(); ARX.testSrc=null;', '_v.pause(); ARX.testSrc=null; arSnapStop(); ARX.stream=null; ARX.video=null;', 1)
exec(compile(s, str(p), 'exec'), {'__name__':'__main__', '__file__':str(p)})
