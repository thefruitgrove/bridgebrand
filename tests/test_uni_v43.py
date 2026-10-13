from datetime import datetime, timezone
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"engine3"))
from uni_v43 import weighted_index, apply_daily_events, weekly_rollup, select_t100

def test_missing_r_is_not_perfect():
    dims={"B":60,"R":None,"I":None,"D":70,"G":80,"E":None}
    assert weighted_index(dims)==71.1

def test_daily_event_is_capped_and_deduplicated():
    e={"university_id":"U1","event_type":"response","axis":"R","title":"positive response",
       "source_class":"independent_media","verification_status":"cross_confirmed",
       "published_at":"2026-10-13T00:00:00+00:00","direction":1,"severity":1}
    r=apply_daily_events({"B":60,"R":None,"I":None,"D":70,"G":80,"E":None},[e,e],datetime(2026,10,13,tzinfo=timezone.utc))
    assert r["event_count"]==1 and r["dims"]["R"]>50 and r["dims"]["R"]<=57

def test_activity_sums_index_averages():
    days=[{"daily_index":70,"quality":1,"activity_points":2,"event_count":1,"dims":{"B":70},"source_ids":["a"]},
          {"daily_index":80,"quality":1,"activity_points":3,"event_count":1,"dims":{"B":80},"source_ids":["b"]}]
    w=weekly_rollup(days); assert w["weekly_index"]==75 and w["activity_points"]==5 and w["observed_days"]==2

def test_dynamic_quota():
    rows=[]
    for kind,n in (("대학",65),("전문대학",45)):
        for i in range(n): rows.append({"university_id":f"{kind}-{i}","name":str(i),"school_kind":kind,"eligible":True,"score":100-i})
    r=select_t100(rows); assert len(r["T100"])==100 and len(r["U60"])==60 and len(r["C40"])==40

if __name__=="__main__":
    tests=[v for k,v in globals().copy().items() if k.startswith("test_")]
    for t in tests: t()
    print(f"UNI v4.3 tests: {len(tests)}/{len(tests)} passed")

