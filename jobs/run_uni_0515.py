"""05:15 KST UNI close: baseline + events + weekly + dynamic T100."""
from __future__ import annotations
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse, json, os, sys

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/"engine3"))
from uni_builder_v43 import build
from uni_v43 import apply_daily_events, select_t100, weekly_rollup, weighted_index

KST=ZoneInfo("Asia/Seoul")

def read_json(path,default):
    try: return json.load(open(path,encoding="utf-8"))
    except (OSError,UnicodeError,json.JSONDecodeError): return default
def read_events(path):
    if not Path(path).exists(): return []
    out=[]
    for line in open(path,encoding="utf-8"):
        try: out.append(json.loads(line))
        except json.JSONDecodeError: continue
    return out
def event_in_window(e,start,end):
    try:
        dt=datetime.fromisoformat(str(e.get("published_at","")).replace("Z","+00:00"));
        if dt.tzinfo is None: dt=dt.replace(tzinfo=KST)
        return start <= dt.astimezone(KST) < end
    except ValueError: return False

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--xlsx",default=str(ROOT/"대학주요정보.xlsx")); ap.add_argument("--now")
    ap.add_argument("--events",default=str(ROOT/"data/events/inbox_uni.jsonl")); ap.add_argument("--data",default=str(ROOT/"data"))
    a=ap.parse_args(); data=Path(a.data); now=datetime.fromisoformat(a.now).astimezone(KST) if a.now else datetime.now(KST)
    close=datetime.combine(now.date(),time(5,15),KST)
    if now < close: close -= timedelta(days=1)
    start=close-timedelta(days=1); data_date=start.date().isoformat()
    baseline=build(a.xlsx); all_events=read_events(a.events); window_events=[e for e in all_events if event_in_window(e,start,close)]
    by_uid={}
    for e in window_events: by_uid.setdefault(e.get("university_id"),[]).append(e)
    records=[]
    for base in baseline["universities"]:
        events=by_uid.get(base["university_id"],[]); daily=apply_daily_events(base["dims"],events,close)
        quality=min(1.0,.55+.08*base["official_axis_count"]+.04*daily["source_diversity"])
        records.append({**base,**daily,"score":daily["daily_index"],"quality":round(quality,2),
                        "source_ids":sorted({str(e.get("source_id")) for e in events if e.get("source_id")}),
                        "data_date":data_date,"window_start":start.isoformat(),"window_end":close.isoformat()})
    previous=read_json(data/"latest"/"uni_latest.json",{}); members={r["university_id"] for r in previous.get("rankings",{}).get("T100",[])}
    rankings=select_t100(records,members); selected={r["university_id"] for r in rankings["T100"]}
    waiting=sorted((r for r in records if r["eligible"] and r["university_id"] not in selected),key=lambda r:-float(r["score"] or -1))[:40]
    for rank,r in enumerate(waiting,1): r["waiting_rank"]=rank
    daily_doc={"schema_version":"UNI-4.3","data_date":data_date,"run_at":now.isoformat(),"official_source":baseline["source"],
               "signal_ledger":window_events,"records":records,"rankings":rankings,"waiting":waiting}
    daydir=data/"daily"; latestdir=data/"latest"; weekdir=data/"weekly"; daydir.mkdir(parents=True,exist_ok=True); latestdir.mkdir(parents=True,exist_ok=True); weekdir.mkdir(parents=True,exist_ok=True)
    json.dump(daily_doc,open(daydir/f"uni_{data_date}.json","w",encoding="utf-8"),ensure_ascii=False,indent=2,allow_nan=False)
    json.dump(daily_doc,open(latestdir/"uni_latest.json","w",encoding="utf-8"),ensure_ascii=False,indent=2,allow_nan=False)

    monday=start.date()-timedelta(days=start.date().weekday()); days=[]
    for i in range(7):
        p=daydir/f"uni_{(monday+timedelta(days=i)).isoformat()}.json"
        if p.exists(): days.append(read_json(p,{}))
    weekly_entities=[]
    for base in records:
        uid=base["university_id"]; ds=[]
        for doc in days:
            match=next((r for r in doc.get("records",[]) if r.get("university_id")==uid),None)
            if match: ds.append(match)
        roll=weekly_rollup(ds); weekly_entities.append({"university_id":uid,"name":base["name"],**roll})
    weekly={"schema_version":"UNI-4.3","week_start":monday.isoformat(),"week_end":(monday+timedelta(days=6)).isoformat(),
            "closed_days":len(days),"entities":weekly_entities}
    json.dump(weekly,open(weekdir/f"uni_{monday.isoformat()}.json","w",encoding="utf-8"),ensure_ascii=False,indent=2,allow_nan=False)
    # Public projection: expose meanings and results, not raw variables or formulas.
    public_dir=ROOT/"site"/"data"; public_dir.mkdir(parents=True,exist_ok=True)
    def public_row(r):
        return {k:r.get(k) for k in ("university_id","name","region","school_kind","school_type","dims","daily_index",
                                      "activity_points","event_count","source_diversity","trust","t100_rank","cohort_rank","waiting_rank")}
    public={"schema_version":"UNI-4.3","data_date":data_date,"updated_at":now.isoformat(),
            "meaning":{"daily_index":"오늘 현재의 대학 공공가치 평판 수준","activity_points":"당일 유효 관심·반응·행동의 총량",
                       "NR":"관측 근거 부족으로 미산출"},
            "rankings":{k:[public_row(r) for r in v] for k,v in rankings.items()},
            "waiting":[public_row(r) for r in waiting[:20]]}
    json.dump(public,open(public_dir/"uni_latest.json","w",encoding="utf-8"),ensure_ascii=False,indent=2,allow_nan=False)
    json.dump(weekly,open(public_dir/"uni_weekly.json","w",encoding="utf-8"),ensure_ascii=False,indent=2,allow_nan=False)
    print(f"UNI close {data_date}: events={len(window_events)} T100={len(rankings['T100'])} waiting={len(waiting)} closed_days={len(days)}")
if __name__=="__main__": main()

