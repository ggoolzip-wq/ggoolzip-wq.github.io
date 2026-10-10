# set_hexa.py / check_hexa.py (넥슨 API 는 가짜 응답, maplescouter 호출 없음)
import os, sys, json, tempfile, io, contextlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(ROOT,'scripts'))
import hexa_snapshot as hs, set_hexa, check_hexa
fails=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' — '+str(d)[:300] if d!='' else ''))
    if not c: fails.append(n)
W={'lv':290,'cp':'123456789','eq':'A'}
def fake(path,**q):
    return {'id':{'ocid':'o1'},'character/basic':{'character_level':W['lv'],'date':'x'},'character/item-equipment':{'item_equipment':[W['eq']],'date':'y'},
            'character/hexamatrix':{'c':1},'character/hexamatrix-stat':{'s':1},'character/stat':{'final_stat':[{'stat_name':'전투력','stat_value':W['cp']}]}}[path]
hs.uf.nx=fake; hs.HEXA=os.path.join(tempfile.mkdtemp(),'hexa.json')
out=io.StringIO()
with contextlib.redirect_stdout(out): rc=set_hexa.main(['림강혼망','123,456'])
d=json.load(open(hs.HEXA))['characters']['림강혼망']
check('set_hexa writes value + KST time + snapshot', rc==0 and d['value']==123456 and d['updatedAt'].endswith('+09:00') and d['snapshot']['level']==290 and d['snapshot']['combatPower']==123456789 and len(d['snapshot']['equipment'])==16, d)
with contextlib.redirect_stdout(io.StringIO()) as o: rc=check_hexa.main([])
check('check: unchanged → SAME, exit 0', rc==0 and 'SAME 림강혼망' in o.getvalue(), o.getvalue())
W['eq']='B'; W['cp']='130000000'
with contextlib.redirect_stdout(io.StringIO()) as o: rc=check_hexa.main(['림강혼망'])
check('check: equipment+CP changed → CHANGED list, exit 1', rc==1 and 'CHANGED 림강혼망 equipment,combatPower' in o.getvalue(), o.getvalue())
with contextlib.redirect_stdout(io.StringIO()): set_hexa.main(['다른캐','9.5','--no-snapshot'])
check('--no-snapshot → value only', 'snapshot' not in json.load(open(hs.HEXA))['characters']['다른캐'])
print('FAILS:',fails); sys.exit(1 if fails else 0)
