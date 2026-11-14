"""Idempotent metadata-only brand aliases; no scoring or publication changes."""
from pathlib import Path
import json,re
TITLE='BRIDGE Reputation Index | Reputation is a signal.'
DESCRIPTION='BRIDGE는 평판의 신호를 근거로 해석합니다. 기업·정부기관·대학·인물의 공개 평판지수, 6축 평가와 근거·신뢰수준을 살펴보세요. Evidence-Based Reputation Intelligence.'
URL='https://bridgebrand.co.kr/'
def apply_home_seo(site):
    extra='\n<link rel="canonical" href="'+URL+'">\n<meta property="og:url" content="'+URL+'">\n<script type="application/ld+json" id="bridge-website-schema">'+json.dumps({'@context':'https://schema.org','@type':'WebSite','@id':URL+'#website','name':'브릿지브랜드','alternateName':'BRIDGEBRAND','url':URL},ensure_ascii=False,separators=(',',':'))+'</script>\n'
    for path in [Path(site)/'index.html',Path(site)/'site_fix/index.html']:
        if not path.exists():continue
        text=path.read_text(encoding='utf-8')
        text=re.sub(r'<title>.*?</title>','<title>'+TITLE+'</title>',text,count=1,flags=re.S)
        for pat,val in [(r'(<meta name="description" content=")[^"]*',DESCRIPTION),(r'(<meta property="og:title" content=")[^"]*',TITLE),(r'(<meta property="og:description" content=")[^"]*',DESCRIPTION),(r'(<meta property="og:site_name" content=")[^"]*','브릿지브랜드')]:
            text=re.sub(pat,lambda m:m[1]+val,text,count=1)
        text=re.sub(r'\s*<link rel="canonical"[^>]*>|\s*<meta property="og:url"[^>]*>|\s*<script[^>]*id="bridge-website-schema"[^>]*>.*?</script>','',text,flags=re.S)
        text=text.replace('</head>',extra+'</head>',1)
        path.write_text(text,encoding='utf-8')
if __name__=='__main__':apply_home_seo(Path(__file__).resolve().parents[1]/'site')
