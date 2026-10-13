"""Conservative Google News RSS collector for UNI daily signals.

T100 and the nearest waiting candidates are checked daily. The remaining
eligible population is checked in a seven-day rotation, so every institution
can produce a signal and enter the ranking without 442 daily searches.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse, email.utils, json, re

POS=re.compile(r"선정|수상|성과|최우수|우수|취업|합격|특허|기술이전|협약|유치|개발|혁신|지원")
NEG=re.compile(r"비리|횡령|성폭력|갑질|사고|위반|제재|징계|논란|반발|중단|취소|유출")
EXPERIENCE=re.compile(r"기숙사|등록금|장학금|수업|강의|시설|학생지원|학식|통학|행정서비스")
IDENTITY=re.compile(r"특성화|글로컬|계약학과|반도체|인공지능|의과대학|간호|예술|지역혁신|국제화")
ACTION=re.compile(r"지원자|경쟁률|입학설명회|오픈캠퍼스|취업|창업|특허|기술이전|산학협력|봉사|참여")
ETHICS=re.compile(r"사과|해명|정정|시정|감사|위반|제재|징계|안전|개인정보|인증")

def parse_date(value):
    try: return email.utils.parsedate_to_datetime(value).astimezone(timezone.utc)
    except Exception: return None

def fetch(name):
    q=quote(f'"{name}" 대학교 OR 대학 when:2d')
    url=f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    req=Request(url,headers={"User-Agent":"SignalBridge-UNI/4.3 (+https://bridgebrand.co.kr)"})
    with urlopen(req,timeout=20) as r: raw=r.read(1_500_000)
    root=ET.fromstring(raw); out=[]
    for item in root.findall(".//item"):
        title=(item.findtext("title") or "").strip(); link=(item.findtext("link") or "").strip()
        pub=parse_date(item.findtext("pubDate") or ""); source=item.findtext("source") or urlparse(link).netloc
        if name.replace("대학교","") not in title: continue
        out.append((title,link,pub,source))
    return out

def targets(baseline,latest,day):
    all_rows=baseline.get("universities",[]); byid={r["university_id"]:r for r in all_rows}; picked=[]; seen=set()
    for r in latest.get("rankings",{}).get("T100",[])+latest.get("waiting",[])[:40]:
        uid=r.get("university_id")
        if uid in byid and uid not in seen: picked.append(byid[uid]); seen.add(uid)
    rotation=[r for r in all_rows if r["university_id"] not in seen and int(r["university_id"][-2:],16)%7==day%7]
    return picked+rotation

def load_json_or_empty(path):
    """Load a prior snapshot without letting one damaged cache stop collection.

    The latest snapshot is an optimisation for selecting the daily target pool,
    not a source of truth.  If a partial deployment or interrupted write leaves
    it unreadable, the collector safely falls back to the rotating population;
    the same run then recreates a valid snapshot.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"warning: ignored unreadable prior snapshot {path}: {type(exc).__name__}")
        return {}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--baseline",default="data/uni_baseline_v43.json")
    ap.add_argument("--latest",default="data/latest/uni_latest.json"); ap.add_argument("--out",default="data/events/inbox_uni.jsonl")
    a=ap.parse_args(); baseline=load_json_or_empty(a.baseline); latest=load_json_or_empty(a.latest) if Path(a.latest).exists() else {}
    if not baseline.get("universities"):
        raise RuntimeError(f"required UNI baseline is missing or unreadable: {a.baseline}")
    now=datetime.now(timezone.utc); rows=targets(baseline,latest,now.toordinal()); events=[]; failures=0
    fetched={}
    # Bounded parallelism keeps the 05:15 workflow inside its time budget
    # without creating an unbounded burst against the public RSS endpoint.
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(fetch,row["name"]):row for row in rows}
        for future in as_completed(futures):
            row=futures[future]
            try: fetched[row["university_id"]]=future.result()
            except Exception: failures+=1; fetched[row["university_id"]]=[]
    for row in rows:
        items=fetched.get(row["university_id"],[])
        for title,link,pub,source in items:
            if not pub or pub < now-timedelta(days=2): continue
            common={"university_id":row["university_id"],"name":row["name"],"title":title,"source_class":"independent_media",
                    "source_url":link,"source_id":"news:"+str(source),"published_at":pub.isoformat(),"verification_status":"single_source"}
            events.append({**common,"event_type":"response","axis":"B","direction":.25,"severity":.35})
            pos=len(POS.findall(title)); neg=len(NEG.findall(title))
            if pos or neg: events.append({**common,"event_type":"response","axis":"R","direction":1 if pos>neg else -1,"severity":min(1,.35+.15*abs(pos-neg))})
            for rx,axis,etype in ((IDENTITY,"I","claim"),(EXPERIENCE,"D","experience"),(ACTION,"G","achievement"),(ETHICS,"E","correction")):
                if rx.search(title): events.append({**common,"event_type":etype,"axis":axis,"direction":-1 if axis=="E" and neg>pos else 1,"severity":.45})
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    with open(a.out,"a",encoding="utf-8") as f:
        for e in events: f.write(json.dumps(e,ensure_ascii=False)+"\n")
    print(f"news targets={len(rows)} events={len(events)} failures={failures}")
if __name__=="__main__": main()

