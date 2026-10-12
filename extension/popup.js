const st = document.getElementById('st'), go = document.getElementById('go');
const show = s => { const l = s?.last; st.textContent = l ? `마지막: ${new Date(l.at).toLocaleString('ko-KR')} · ${l.ok ? l.results.length + '개' : l.error}` : `아직 없음 (아이템 ${s?.items || 0}개)`; };
chrome.runtime.sendMessage({ type: 'status' }, show);
go.onclick = () => { go.disabled = true; st.textContent = '검색 중…'; chrome.runtime.sendMessage({ type: 'refresh' }, r => { go.disabled = false; st.textContent = r?.ok ? `완료: ${r.results.length}개 (새 검색 ${r.posts}회, 남은 ${r.remaining ?? '?'}회)${r.stop ? ' · ' + r.stop : ''}` : '실패: ' + (r?.error || '?'); }); };
