"""Idempotent metadata-only brand aliases; no scoring or publication changes."""
from pathlib import Path
import json,re
TITLE='브릿지브랜드 | BRIDGEBRAND'
DESCRIPTION='브릿지브랜드(BRIDGEBRAND)는 공개자료와 공중의 관측 신호를 바탕으로 브랜드와 공중의 관계를 진단하는 브랜드지수·브랜드 분석 서비스입니다. BRIDGE의 여섯 축으로 현재 위치, 관계 구성과 변화 방향을 읽습니다.'
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
