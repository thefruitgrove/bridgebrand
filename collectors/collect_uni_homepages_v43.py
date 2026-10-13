"""Collect public university homepage changes into the UNI Signal Ledger.

Only public pages listed in config/uni_sources.json are fetched. The collector
does not bypass login, robots, or access controls. Homepage claims create a
small I-axis signal; G/E require external or official confirmation.
"""
from __future__ import annotations
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import argparse, hashlib, json, re

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in {"script","style","noscript"}: self.skip += 1
        for k,v in attrs:
            if not self.skip and k in {"alt","title"} and v: self.parts.append(v)
    def handle_endtag(self, tag):
        if tag in {"script","style","noscript"} and self.skip: self.skip -= 1
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)

CLAIM_KW = re.compile(r"글로컬|선정|수상|취업률|국가고시|세계대학|연구비|특허|기술이전|계약학과|장학금|기숙사|인증|국책사업|산학협력")

def fetch(url: str) -> tuple[str,str]:
    req=Request(url,headers={"User-Agent":"SignalBridge-UNI/4.3 (+https://bridgebrand.co.kr)"})
    with urlopen(req,timeout=20) as r:
        raw=r.read(2_000_000); charset=r.headers.get_content_charset() or "utf-8"
    html=raw.decode(charset,errors="replace"); p=TextParser(); p.feed(html)
    text=re.sub(r"\s+"," "," ".join(p.parts)).strip()[:120000]
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--registry",default="config/uni_sources.json")
    ap.add_argument("--state",default="data/uni_homepage_state.json"); ap.add_argument("--out",default="data/events/inbox_uni.jsonl")
    a=ap.parse_args(); registry=json.load(open(a.registry,encoding="utf-8")) if Path(a.registry).exists() else []
    state=json.load(open(a.state,encoding="utf-8")) if Path(a.state).exists() else {}; events=[]; now=datetime.now(timezone.utc).isoformat()
    for item in registry:
        uid=item.get("university_id"); url=item.get("homepage")
        if not uid or not url: continue
        try: text,digest=fetch(url)
        except Exception as exc:
            state.setdefault(uid,{})["last_error"]=f"{type(exc).__name__}: {exc}"; continue
        old=state.get(uid,{}).get("sha256")
        matches=list(dict.fromkeys(CLAIM_KW.findall(text)))[:12]
        state[uid]={"sha256":digest,"checked_at":now,"homepage":url,"last_error":None}
        if old and old==digest: continue
        if matches:
            events.append({"university_id":uid,"name":item.get("name"),"event_type":"claim","axis":"I",
                           "title":"대학 홈페이지 핵심 제시 내용 변경: "+", ".join(matches),"source_class":"university_owned",
                           "source_url":url,"source_id":"homepage:"+uid,"published_at":now,
                           "verification_status":"single_source","direction":0.25,"severity":min(1.0,.2+.06*len(matches))})
    Path(a.state).parent.mkdir(parents=True,exist_ok=True); Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    json.dump(state,open(a.state,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    with open(a.out,"a",encoding="utf-8") as f:
        for e in events: f.write(json.dumps(e,ensure_ascii=False)+"\n")
    print(f"homepage checked={len(registry)} new_claim_events={len(events)}")
if __name__=="__main__": main()

