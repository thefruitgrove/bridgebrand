import urllib.request,urllib.parse,urllib.error,xml.etree.ElementTree as ET,time,email.utils,datetime
names=['삼성전자','서울대학교','기아','리센느','서울특별시','연세대학교','삼성물산','신민아']
for name in names:
    q=urllib.parse.urlencode({'q':'"'+name+'"','format':'rss','setlang':'ko'})
    url='https://www.bing.com/news/search?'+q
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; BridgeNewsRSSQualityCheck/1.0)'})
        with urllib.request.urlopen(req,timeout=20) as res:root=ET.fromstring(res.read(250000));code=res.status
        items=root.findall('.//channel/item')
        dates=[];sources=[];hosts=[];matches=0
        for item in items:
            title=(item.findtext('title') or '')
            if name in title:matches+=1
            dates.append((item.findtext('pubDate') or '')[:34])
            sources.append((item.findtext('source') or '')[:40])
            hosts.append((item.findtext('link') or '')[:90])
        print(name,'HTTP',code,'items',len(items),'title_matches',matches,'pubDate',dates[:2],'source',sources[:2],'link',hosts[:1],flush=True)
    except Exception as e:print(name,'ERROR',type(e).__name__,str(e)[:220],flush=True)
    time.sleep(2)
