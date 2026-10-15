"""Build the no-JavaScript home from the same published snapshot as the live UI."""
import html
import json
from pathlib import Path

def published_rows(path):
    try:
        snapshot=json.loads(Path(path).read_text())
        return [r for r in snapshot.get('rankings',[]) if r.get('ranking_type')=='T100' and r.get('as_of_date')==snapshot.get('asOfDate')]
    except (OSError,ValueError,TypeError):return []

def render_home(rows):
    blocks=[]
    for domain,href in [('CPR','cpr.html'),('GOV','gov.html'),('UNI','uni.html'),('ENT','star.html')]:
        members=sorted([r for r in rows if r.get('domain')==domain],key=lambda r:(int(r['rank']),r['name']))[:5]
        items=[]
        for r in members:
            change=r.get('rank_change') if r.get('previous_rank') is not None else None
            cls='up' if change is not None and change>0 else 'down' if change is not None and change<0 else 'flat'
            text='▲ '+str(abs(change)) if cls=='up' else '▼ '+str(abs(change)) if cls=='down' else '— 0' if change==0 else '비교대기'
            items.append(f'<li><span class="t5-nm">{html.escape(r["name"])}</span><span class="t5-sc">{r["score"]:.1f}</span><span class="t5-{cls}">{text}</span></li>')
        listing=''.join(items) or '<li class="t5-empty">공개 적격 자료를 확인 중입니다.</li>'
        blocks.append(f'<a class="t5-block" href="{href}"><div class="t5-head">{domain} <span class="t5-more">TOP 5 →</span></div><ol class="t5-list">{listing}</ol></a>')
    return '<div class="hero-top5">'+''.join(blocks)+'</div>'
