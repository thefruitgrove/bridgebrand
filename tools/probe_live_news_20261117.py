import json, urllib.request, urllib.parse, urllib.error, xml.etree.ElementTree as ET
from datetime import datetime
q=urllib.parse.quote('"삼성전자"')
urls={
  'bing_rss':'https://www.bing.com/news/search?q='+q+'&format=rss&setlang=ko',
  'gdelt_json':'https://api.gdeltproject.org/api/v2/doc/doc?query='+q+'&mode=artlist&format=json&maxrecords=10&sort=datedesc',
}
for label,url in urls.items():
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; BRIDGE-SourceReliabilityCheck/1.0)','Accept':'application/rss+xml,application/json,application/xml'})
        with urllib.request.urlopen(req,timeout=20) as r:
            body=r.read(250000); print(label,'HTTP',r.status,'type',r.headers.get('content-type'),'bytes',len(body),flush=True)
        if label=='bing_rss':
            root=ET.fromstring(body)
            items=root.findall('.//channel/item')
            print(label,'ITEMS',len(items),'SAMPLES',[(x.findtext('title') or '')[:65] for x in items[:3]],flush=True)
        else:
            data=json.loads(body); items=data.get('articles',[])
            print(label,'ITEMS',len(items),'SAMPLES',[(x.get('title') or '')[:65] for x in items[:3]],flush=True)
    except Exception as exc:print(label,'ERROR',type(exc).__name__,str(exc)[:250],flush=True)
