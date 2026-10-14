"""Resolve ownership from institutional homepage outbound links, never search title."""
from __future__ import annotations
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from .core import now_kst
ROOT=Path(__file__).resolve().parents[1]
SEEDS={
 'GOV-C01':'https://www.seoul.go.kr','GOV-C02':'https://www.busan.go.kr',
 'GOV-C03':'https://www.daegu.go.kr','GOV-C04':'https://www.incheon.go.kr',
 'GOV-C05':'https://www.gwangju.go.kr','GOV-C06':'https://www.daejeon.go.kr',
 'GOV-C07':'https://www.ulsan.go.kr','GOV-C08':'https://www.sejong.go.kr',
 'GOV-C09':'https://www.gg.go.kr','GOV-C10':'https://www.provin.gangwon.kr',
 'GOV-C11':'https://www.chungbuk.go.kr','GOV-C12':'https://www.chungnam.go.kr',
 'GOV-C13':'https://www.jeonbuk.go.kr','GOV-C14':'https://www.jeonnam.go.kr',
 'GOV-C15':'https://www.gb.go.kr','GOV-C16':'https://www.gyeongnam.go.kr',
 'GOV-C17':'https://www.jeju.go.kr','GOV-M24':'https://www.acrc.go.kr',
 'GOV-M08':'https://www.moe.go.kr','GOV-M10':'https://www.mcst.go.kr',
 'GOV-M06':'https://www.mois.go.kr','GOV-M17':'https://www.molit.go.kr',
}
def links(html):
    out={}
    for u in re.findall(r'https?://(?:www\.)?youtube\.com/[^\s\"\'<>]+',html):
        path=urllib.parse.urlsplit(u.replace('&amp;','&')).path.strip('/').split('/')
        if len(path)>=2 and path[0]=='channel' and re.fullmatch(r'UC[A-Za-z0-9_-]{22}',path[1]):out[('channel_id',path[1])]=u
        elif path and path[0].startswith('@'):out[('handle',path[0])]=u
        elif len(path)>=2 and path[0]=='user':out[('username',path[1])]=u
    return out

def inspect(item):
    eid,url=item
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'SignalBridgeBot/1.0 (+https://bridgebrand.co.kr)'})
        with urllib.request.urlopen(req,timeout=15) as resp:
            if urllib.parse.urlsplit(resp.geturl()).hostname!=urllib.parse.urlsplit(url).hostname:
                return eid,{'status':'review','reason':'homepage_redirect_requires_review','homepage':url}
            html=resp.read(3_000_000).decode('utf-8','replace')
        found=links(html)
        # Prefer stable channel ID when the same homepage also provides handles.
        ids=[(k,u) for k,u in found.items() if k[0]=='channel_id']
        choices=ids if ids else list(found.items())
        if len(choices)!=1:return eid,{'status':'review','homepage':url,'reason':'ambiguous_or_missing','candidates':[u for _,u in choices]}
        (kind,value),link=choices[0]
        return eid,{kind:value,'status':'verified','evidence_urls':[url],'linked_channel_url':link,'verified_at':now_kst().isoformat(),'verification_method':'institutional_homepage_outbound_link'}
    except Exception as e:return eid,{'status':'review','homepage':url,'reason':type(e).__name__}

def main():
    p=ROOT/'config/gov_youtube_channels.json';cfg=json.loads(p.read_text());reviews={}
    results=dict(ThreadPoolExecutor(max_workers=5).map(inspect,SEEDS.items()))
    for eid,row in results.items():
        if row['status']=='verified':cfg.setdefault('channels',{})[eid]=row
        else:reviews[eid]=row
    cfg['version']='2026.10-v5-official-links-1';p.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    out=ROOT/'data/gov_youtube/ownership_review.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'checked_at':now_kst().isoformat(),'review':reviews},ensure_ascii=False,indent=2))
    print(json.dumps({'verified':sum(x['status']=='verified' for x in results.values()),'review':len(reviews)}))
if __name__=='__main__':main()
