"""월드 아이콘 → src/worldicons.json  (사용법: python3 tools/build_worlds.py)
원본: 메이플스토리 공식 홈페이지 랭킹 등에서 쓰는 월드 아이콘
  https://ssl.nexon.com/s2/game/maplestory/renewal/common/world_icon/icon_N.png  (13~14px, 그대로 내장)
번호↔월드 대응: maple.gg(maple-data.dakgg.net/world/<영문>.png) 의 월드별 아이콘과 픽셀 단위로 100% 일치하는 공식 파일을 골라 확인(2026-10-10).
'챌린저스2/3/4' 처럼 숫자가 붙은 월드는 같은 아이콘(공식 icon_20/22/23 은 픽셀 동일), '버닝*' 도 같은 규칙."""
import base64,json,os
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'src'))
M={'스카니아':8,'베라':12,'루나':9,'제니스':10,'크로아':11,'유니온':7,'엘리시움':13,'이노시스':6,'레드':5,'오로라':4,
   '아케인':14,'노바':15,'에오스':3,'핼리오스':2,'챌린저스':20,'버닝':16}
out={k:'data:image/png;base64,'+base64.b64encode(open(f'assets/worldicons/icon_{n}.png','rb').read()).decode() for k,n in M.items()}
json.dump(out,open('worldicons.json','w'),ensure_ascii=False)
print(len(out),'worlds',sum(map(len,out.values())),'chars')
