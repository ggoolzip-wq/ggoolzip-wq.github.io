"""b88: 예전 테스트 호환 — b75 '저장하시겠습니까?' 확인창(pendGuard: 캐릭터·탭 전환 시)에 자동으로 '예'를 눌러 예전 흐름(전환 = 바로 반영)을 유지.
import _legacy 만 하면 이 프로세스에서 만드는 모든 페이지에 적용됩니다."""
from playwright.sync_api._generated import Browser, BrowserContext
JS = """setInterval(()=>{ const d=document.getElementById('svAsk'); if(d&&d.querySelector('.pgav')){ const b=d.querySelector('[data-k=yes]'); if(b) b.click(); } },30)"""
def _wrap(cls):
    orig = cls.new_page
    def new_page(self, *a, **k):
        p = orig(self, *a, **k); p.add_init_script(JS)
        return p
    cls.new_page = new_page
_wrap(Browser); _wrap(BrowserContext)

# b82/b72: 키 없는 계정의 캐릭터는 숨겨지므로, 예전 테스트의 계정에는 이 가짜 키를 넣어 캐릭터가 보이게 함
LEGACY_KEY = 'test_legacy_0123456789abcdef'
