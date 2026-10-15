"""Legacy single-file entry now routes to canonical pages.
Avoid maintaining a second, stale set of data and explanatory copy.
"""
from pathlib import Path
PAGE='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BRIDGE — SIGNALBRIDGE</title><meta name="robots" content="noindex"></head><body><p>BRIDGE의 최신 페이지로 이동합니다. <a href="index.html">홈페이지 열기</a></p><script>
(function(){var key=location.hash.slice(1).replace(/^view-/,'').split(/[?&/]/)[0],pages={home:'index',index:'index',cpr:'cpr',gov:'gov',uni:'uni',star:'star',ent:'star',methodology:'methodology',trust:'trust',about:'about','data-extraction':'data-extraction','this-week':'this-week',publicity:'publicity',contact:'contact'};location.replace((pages[key]||'index')+'.html'+location.search);})();
</script></body></html>'''
if __name__=='__main__':
 (Path(__file__).resolve().parent/'site/bridge_full_site.html').write_text(PAGE)
 print('Legacy entry routes to canonical pages.')
